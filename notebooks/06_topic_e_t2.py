# %% [markdown]
# # 06 – Thực nghiệm E-T2: bỏ tên nhóm hàng khỏi mô hình chủ đề phàn nàn (sprint xây dựng 1)
# Người thực hiện chính: KAYSONE Souk Anong.
#
# Notebook 03 chọn NMF k = 9; kết quả có 4 chủ đề theo **khía cạnh** (hương vị, hàng cũ – bao bì, giá, thành phần) và
# 5 chủ đề theo **nhóm hàng** (cà phê, trà, thức ăn thú cưng, sô-cô-la, không gluten). Câu hỏi E-T2: nếu thêm tên nhóm hàng
# vào danh sách từ dừng, mô hình có tách được thêm khía cạnh dùng chung cho mọi sản phẩm không?
#
# Tiêu chí (báo cáo buổi 5, bảng 5.9): **chỉ thay mô hình khi độ mạch lạc NPMI và độ dễ hiểu đều không giảm.**
# - NPMI tính trên **cùng một kho tham chiếu** (ma trận từ của mô hình hiện tại) để hai biến thể so sánh được.
# - Độ dễ hiểu đo bằng hai chỉ số không cần gán nhãn tay: (1) độ đa dạng từ khóa; (2) **độ phân tán theo sản phẩm** –
#   tỷ lệ đánh giá của một chủ đề đến từ 20 sản phẩm nhiều nhất của chính chủ đề đó (chủ đề khía cạnh trải trên nhiều
#   sản phẩm nên tỷ lệ này thấp; chủ đề nhóm hàng tập trung vào vài sản phẩm nên cao). Kèm danh sách từ khóa để nhóm đọc.

# %%
import sys, time, json
from pathlib import Path
ROOT = Path.cwd().parent if Path.cwd().name == "notebooks" else Path.cwd()
sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import NMF
from backend.core import config as C
from backend.services import data_service as DS
from backend.services import topic_service as TS
OUT = ROOT / "notebooks" / "outputs"
R = {}

df = pd.read_csv(C.DATA_PROCESSED / "reviews_clean.csv", usecols=["review_id", "product_id", "sentiment", "summary", "text"],
                 dtype={"summary": str, "text": str, "product_id": str}, keep_default_na=False)
neg = df[df.sentiment == "neg"].reset_index(drop=True)
docs = (neg.summary + " . " + neg.text).values
R["n_docs"] = len(neg)

# Tên nhóm hàng và từ chỉ loại sản phẩm (xuất hiện trong từ khóa của 5 chủ đề nhóm hàng ở notebook 03)
CATEGORY_STOP = {"coffee", "coffees", "cup", "cups", "pod", "pods", "keurig", "roast", "espresso", "beans", "bean",
                 "tea", "teas", "green", "black", "chai", "bags", "bag",
                 "dog", "dogs", "cat", "cats", "pet", "pets", "puppy", "treats", "treat", "food", "foods", "chicken",
                 "chocolate", "cocoa", "cookies", "cookie", "bars", "bar", "candy", "peanut", "butter",
                 "gluten", "free", "celiac", "wheat", "flour", "bread", "mix", "pasta", "rice", "cereal",
                 "chips", "chip", "popcorn", "crackers", "juice", "soda", "drink", "drinks", "water", "sauce", "soup", "oil", "honey"}
KW = dict(preprocessor=DS.model_preprocess, ngram_range=(1, 2), min_df=10, max_df=0.4, max_features=20_000, sublinear_tf=True)


def build(stop):
    v = TfidfVectorizer(stop_words=sorted(stop), **KW); X = v.fit_transform(docs)
    return v, X, np.array(v.get_feature_names_out())


v0, X0, vocab0 = build(TS.STOP)
v1, X1, vocab1 = build(set(TS.STOP) | CATEGORY_STOP)
R["vocab_baseline"], R["vocab_e_t2"] = len(vocab0), len(vocab1)

# Kho tham chiếu chung cho NPMI: ma trận nhị phân tài liệu × từ của mô hình hiện tại (từ của E-T2 là tập con)
B = (X0 > 0).astype(np.float32).tocsc(); dfc = np.asarray(B.sum(0)).ravel(); N = B.shape[0]
idx0 = {w: i for i, w in enumerate(vocab0)}


def npmi(words):
    ids = [idx0[w] for w in words if w in idx0]; s = []
    for a in range(len(ids)):
        for b in range(a + 1, len(ids)):
            i, j = ids[a], ids[b]; co = B[:, i].multiply(B[:, j]).sum()
            if co == 0: s.append(-1.0); continue
            pij, pi, pj = co / N, dfc[i] / N, dfc[j] / N
            s.append(np.log(pij / (pi * pj)) / -np.log(pij))
    return float(np.mean(s))


def fit(X, vocab, k):
    nmf = NMF(n_components=k, init="nndsvda", random_state=C.RANDOM_STATE, max_iter=400).fit(X)
    W = nmf.transform(X); tops = [vocab[np.argsort(c)[::-1][:10]].tolist() for c in nmf.components_]
    tid = np.where(W.max(1) > 0, W.argmax(1), -1)
    conc = []
    for t in range(k):
        p = neg.product_id.values[tid == t]
        conc.append(pd.Series(p).value_counts().head(20).sum() / max(len(p), 1))
    return {"k": k, "npmi": round(float(np.mean([npmi(t) for t in tops])), 4),
            "diversity": round(len({w for t in tops for w in t}) / (10 * k), 3),
            "top20_product_share": round(float(np.mean(conc)), 4), "tops": tops,
            "share": [round(float((tid == t).mean()), 4) for t in range(k)], "unassigned": int((tid < 0).sum())}

# %% [markdown]
# ## Chọn k cho biến thể E-T2 và so sánh với mô hình hiện tại (k = 9)

# %%
t0 = time.time()
base = fit(X0, vocab0, C.TOPIC_K)
grid = [fit(X1, vocab1, k) for k in C.TOPIC_K_RANGE]
best = max(grid, key=lambda g: g["npmi"])
same_k = next(g for g in grid if g["k"] == C.TOPIC_K)
R["seconds"] = round(time.time() - t0, 1)
R["baseline_k9"] = {k: base[k] for k in ("k", "npmi", "diversity", "top20_product_share", "unassigned")}
R["e_t2_grid"] = [{k: g[k] for k in ("k", "npmi", "diversity", "top20_product_share")} for g in grid]
R["e_t2_best"] = {k: best[k] for k in ("k", "npmi", "diversity", "top20_product_share", "unassigned")}
R["e_t2_k9"] = {k: same_k[k] for k in ("k", "npmi", "diversity", "top20_product_share", "unassigned")}
pd.DataFrame(R["e_t2_grid"])

# %% [markdown]
# ## Từ khóa hai biến thể – để nhóm đọc và đặt tên

# %%
def names(tops):
    """Gợi ý tên theo bảng mẫu của TopicService (≥ 3 từ trùng); không khớp mẫu nào thì để trống cho nhóm đặt tên."""
    out = []
    for tw in tops:
        ov, key, name = max((len(set(tw) & kw), key, name) for key, name, kw in TS.TEMPLATES)
        out.append(name if ov >= 3 else "")
    return out

R["baseline_topics"] = [{"keywords": t[:8], "share": s, "template": n} for t, s, n in zip(base["tops"], base["share"], names(base["tops"]))]
R["e_t2_topics"] = [{"keywords": t[:8], "share": s, "template": n} for t, s, n in zip(same_k["tops"], same_k["share"], names(same_k["tops"]))]
for label, items in [("Mô hình hiện tại (k = 9)", R["baseline_topics"]), ("E-T2 (k = 9)", R["e_t2_topics"])]:
    print(label)
    for i, t in enumerate(sorted(items, key=lambda t: -t["share"])):
        print(f"  {i + 1}. {t['share']:.1%}  {', '.join(t['keywords'])}  [{t['template'] or '–'}]")

# %% [markdown]
# ## Kết luận theo tiêu chí đã chốt

# %%
d_npmi = R["e_t2_best"]["npmi"] - R["baseline_k9"]["npmi"]
d_conc = R["e_t2_best"]["top20_product_share"] - R["baseline_k9"]["top20_product_share"]
d_div = R["e_t2_best"]["diversity"] - R["baseline_k9"]["diversity"]
R["delta"] = {"npmi": round(d_npmi, 4), "diversity": round(d_div, 3), "top20_product_share": round(d_conc, 4)}
R["adopt"] = bool(d_npmi >= 0 and d_div >= 0 and d_conc <= 0)
R["decision"] = ("Thay mô hình: NPMI và độ dễ hiểu đều không giảm" if R["adopt"] else
                 "Giữ mô hình hiện tại: " + ("NPMI giảm" if d_npmi < 0 else "NPMI không giảm") + ", " +
                 ("độ đa dạng giảm" if d_div < 0 else "độ đa dạng không giảm") + ", " +
                 ("chủ đề tập trung hơn vào ít sản phẩm" if d_conc > 0 else "chủ đề phân tán hơn theo sản phẩm"))
(OUT / "topic_e_t2_results.json").write_text(json.dumps(R, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({k: R[k] for k in ("baseline_k9", "e_t2_best", "e_t2_k9", "delta", "adopt", "decision")}, ensure_ascii=False, indent=1))
