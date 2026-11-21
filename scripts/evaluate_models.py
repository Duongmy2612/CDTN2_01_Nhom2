"""Đánh giá mô hình và phân tích lỗi (buổi 8 – kiểm thử và tinh chỉnh).

Đọc kết quả pipeline đã lưu (data/processed, models) và xuất biên bản docs/test_report/model_eval_<bộ>_<ngày>.md|json:

1. Phân loại cảm xúc: chỉ số trên tập kiểm tra 20% so với đường cơ sở; P/R/F1 từng lớp; lỗi theo độ dài, năm, lượt hữu ích,
   độ phổ biến sản phẩm, độ tự tin; nhóm lỗi tự động kèm ví dụ (không chỉ một con số accuracy).
2. Dự báo chỉ số hài lòng: MAE, RMSE của ETS so với 3 đường cơ sở (ngây thơ, mùa vụ, TB 12 tháng) – dự báo 12 tháng một lần
   và dự báo cuốn chiếu 1 tháng; sai số theo tầm dự báo; độ nhiễu của điểm TB tháng theo số đánh giá; dự báo từng sản phẩm.
3. Quy tắc cảnh báo rủi ro: kiểm tra ngược 2 mốc, độ tách giữa các mức.
4. Chủ đề phàn nàn (NMF): tỷ lệ đánh giá chứa từ khóa của chủ đề, độ chắc của phép gán, đánh giá chưa xếp chủ đề.

Chạy:  python scripts/evaluate_models.py              (dữ liệu đang dùng của backend)
       FRI_WORK_DIR=<thư mục> python scripts/evaluate_models.py --kind full
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import warnings
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
warnings.filterwarnings("ignore")

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from sklearn.metrics import f1_score, precision_recall_fscore_support  # noqa: E402

from backend.core import config as C  # noqa: E402
from backend.core.state import FILES, read_clean  # noqa: E402
from backend.services import forecast_service as FS  # noqa: E402

SENT = {1: "neg", 2: "neg", 3: "neu", 4: "pos", 5: "pos"}
VN = {"neg": "Tiêu cực", "neu": "Trung tính", "pos": "Tích cực"}
NEGATION = re.compile(r"\b(not (bad|terrible|awful|great|good|the best|worth|as good|too)|no complaints?|can'?t complain|"
                      r"wouldn'?t (recommend|buy)|never again|not disappointed)\b", re.I)
CONTRAST = re.compile(r"\b(but|however|although|though|except|unfortunately)\b", re.I)


def r(x, k=4):
    return None if x is None or (isinstance(x, float) and np.isnan(x)) else round(float(x), k)


def snippet(text: str, n: int = 28) -> str:
    w = str(text).split()
    return " ".join(w[:n]) + (" …" if len(w) > n else "")


# --------------------------------------------------------------------------- 1. phân loại
def classification(clean: pd.DataFrame, pred: pd.DataFrame, reg: dict) -> dict:
    t = pred[pred.split == "test"].merge(clean[["review_id", "text", "summary", "n_words", "review_date", "helpful_den", "product_id"]],
                                         on="review_id", how="left")
    t["true_sent"] = t.score.map(SENT)
    t["ok"] = t.true_sent == t.pred_sentiment
    pn = 1 - t.p_neg - t.p_pos
    t["conf"] = np.maximum.reduce([t.p_neg.values, t.p_pos.values, pn.values])
    labels = ["neg", "neu", "pos"]
    p, rc, f, s = precision_recall_fscore_support(t.true_sent, t.pred_sentiment, labels=labels, zero_division=0)
    per_class = [{"class": VN[c], "precision": r(p[i]), "recall": r(rc[i]), "f1": r(f[i]), "support": int(s[i])} for i, c in enumerate(labels)]
    cm = pd.crosstab(t.true_sent, t.pred_sentiment).reindex(index=labels, columns=labels, fill_value=0)
    overall = {"n_test": int(len(t)), "acc3": r(t.ok.mean()), "f1_macro3": r(f1_score(t.true_sent, t.pred_sentiment, average="macro")),
               "acc5": r((t.score == t.pred_star).mean()), "within1": r(((t.score - t.pred_star).abs() <= 1).mean()),
               "mae_star": r((t.score - t.pred_star).abs().mean())}
    models = [{k: m.get(k) for k in ("model", "f1_macro3", "prec_macro3", "rec_macro3", "f1_neg", "f1_neu", "f1_pos", "acc5", "mae")}
              for m in reg["models"]]

    def sl(col, bins, names):
        g = t.assign(b=pd.cut(t[col], bins=bins, labels=names, right=False))
        out = []
        for name, d in g.groupby("b", observed=True):
            if len(d) < 30:
                continue
            out.append({"slice": str(name), "n": int(len(d)), "acc3": r(d.ok.mean()),
                        "f1_macro3": r(f1_score(d.true_sent, d.pred_sentiment, average="macro", labels=labels, zero_division=0)),
                        "share_neu": r((d.true_sent == "neu").mean())})
        return out

    t["year"] = pd.to_datetime(t.review_date).dt.year
    pop = clean.groupby("product_id").size()
    t["prod_n"] = t.product_id.map(pop).fillna(0)
    slices = {
        "Độ dài (số từ)": sl("n_words", [0, 20, 50, 100, 200, 1e9], ["3–19", "20–49", "50–99", "100–199", "≥ 200"]),
        "Năm đánh giá": sl("year", [0, 2008, 2010, 2011, 2012, 3000], ["≤ 2007", "2008–2009", "2010", "2011", "2012"]),
        "Lượt bình chọn hữu ích": sl("helpful_den", [0, 1, 5, 1e9], ["0", "1–4", "≥ 5"]),
        "Số đánh giá của sản phẩm": sl("prod_n", [0, 10, 100, 1e9], ["< 10", "10–99", "≥ 100"]),
        "Độ tự tin của mô hình": sl("conf", [0, .5, .7, .9, 1.01], ["< 0,5", "0,5–0,7", "0,7–0,9", "≥ 0,9"]),
    }
    # nhóm lỗi tự động – xét theo thứ tự ưu tiên, mỗi lỗi vào đúng một nhóm
    e = t[~t.ok].copy()
    txt = (e.summary.fillna("") + " . " + e.text.fillna(""))
    strong_flip = ((e.true_sent == "neg") & (e.p_pos >= .9)) | ((e.true_sent == "pos") & (e.p_neg >= .9))
    cat = np.select(
        [e.true_sent.eq("neu"), strong_flip, txt.str.contains(NEGATION), txt.str.contains(CONTRAST), e.n_words < 20],
        ["Đánh giá 3 sao (trung tính) bị xếp sang hai cực", "Số sao ngược hẳn nội dung (mô hình tự tin ≥ 0,9)",
         "Có phủ định / nói giảm (“not bad”, “no complaints”)", "Vừa khen vừa chê (“but”, “however”…)", "Quá ngắn (< 20 từ)"],
        "Khác")
    e["cat"] = cat
    rng = np.random.default_rng(C.RANDOM_STATE)
    groups = []
    for name, d in e.groupby("cat", sort=False):
        ex = d.iloc[rng.choice(len(d), size=min(2, len(d)), replace=False)]
        groups.append({"group": name, "n": int(len(d)), "share_of_errors": r(len(d) / len(e)),
                       "examples": [{"review_id": int(x.review_id), "score": int(x.score), "pred": VN[x.pred_sentiment], "conf": r(x.conf, 2),
                                     "text": snippet(x.text)} for x in ex.itertuples()]})
    groups.sort(key=lambda g: -g["n"])
    return {"overall": overall, "per_class": per_class, "confusion3": {"labels": [VN[c] for c in labels], "matrix": cm.values.tolist()},
            "models": models, "selected": reg.get("selected"), "split": reg.get("split"), "time_check": reg.get("time_check"),
            "slices": slices, "n_errors": int(len(e)), "error_groups": groups}


# --------------------------------------------------------------------------- 2. dự báo
def _ets_point(train: pd.Series, h: int) -> np.ndarray:
    return FS._ets_forecast(train, h)[1]


def forecasting(clean: pd.DataFrame, meta: dict) -> dict:
    s, T = FS._overall_series(clean, meta["last_full_month"])
    out = {"threshold_per_month": T, "series": f"{s.index[0]:%Y-%m} – {s.index[-1]:%Y-%m}", "n_months": int(len(s))}
    if len(s) < 36:
        out["note"] = "Chuỗi < 36 tháng: không đủ để kiểm tra lùi 12 tháng"
        return out
    idx = lambda a: np.asarray(a) * 25                                         # điểm sao → điểm chỉ số (thang 0–100)
    tr, te = s.iloc[:-12], s.iloc[-12:]
    fc = {"ETS (mô hình của hệ thống)": _ets_point(tr, 12), "Ngây thơ (giữ tháng cuối)": np.repeat(tr.iloc[-1], 12),
          "Mùa vụ (cùng tháng năm trước)": tr.iloc[-12:].values, "TB 12 tháng gần nhất": np.repeat(tr.iloc[-12:].mean(), 12)}
    multi = [{"model": k, "mae": r(np.mean(np.abs(idx(te.values - v))), 2), "rmse": r(np.sqrt(np.mean(idx(te.values - v) ** 2)), 2)}
             for k, v in fc.items()]
    by_h = [{"h": i + 1, "month": f"{te.index[i]:%Y-%m}", "actual": r(C.satisfaction_index(te.values[i]), 2),
             "ets_abs_err": r(abs(idx(te.values[i] - fc["ETS (mô hình của hệ thống)"][i])), 2),
             "naive_abs_err": r(abs(idx(te.values[i] - tr.iloc[-1])), 2)} for i in range(12)]
    # cuốn chiếu: mỗi tháng học lại trên toàn bộ quá khứ, dự báo đúng 1 tháng tiếp theo
    roll = {"ETS": [], "Ngây thơ": [], "Mùa vụ": []}
    for k in range(len(s) - 12, len(s)):
        hist = s.iloc[:k]
        y = s.iloc[k]
        roll["ETS"].append(y - _ets_point(hist, 1)[0]); roll["Ngây thơ"].append(y - hist.iloc[-1]); roll["Mùa vụ"].append(y - hist.iloc[-12])
    rolling = [{"model": k, "mae": r(np.mean(np.abs(idx(v))), 2), "rmse": r(np.sqrt(np.mean(idx(v) ** 2)), 2)} for k, v in roll.items()]
    # độ nhiễu của điểm TB tháng: sai số chuẩn = độ lệch chuẩn / căn số đánh giá
    g = clean.groupby("year_month").score.agg(["size", "std"])
    g = g[g.index <= meta["last_full_month"]]
    g["se_index"] = g["std"] / np.sqrt(g["size"]) * 25
    noise = []
    for lo, hi, name in [(0, 100, "< 100"), (100, T, f"100 – {T - 1}"), (T, 10 ** 9, f"≥ {T} (dùng để dự báo)")]:
        d = g[(g["size"] >= lo) & (g["size"] < hi)]
        if len(d):
            noise.append({"reviews_per_month": name, "n_months": int(len(d)), "se_index_mean": r(d.se_index.mean(), 2),
                          "months": f"{d.index.min()} – {d.index.max()}"})
    # dự báo từng sản phẩm (ARIMA(0,1,1)) so với ngây thơ – các sản phẩm đủ điều kiện
    prods = []
    try:
        p = pd.read_csv(FILES["products"], dtype={"product_id": str})
        cand = p[p.forecastable.astype(bool)].product_id.tolist()
        rng = np.random.default_rng(C.RANDOM_STATE)
        if len(cand) > 150:
            cand = list(rng.choice(cand, 150, replace=False))
        for pid in cand:
            bt = FS.product_forecast(clean, pid, meta["last_full_month"], 12).get("backtest")
            if bt:
                prods.append(bt)
    except Exception as ex:  # noqa: BLE001
        out["product_error"] = str(ex)[:200]
    prod = None
    if prods:
        mm = np.array([b["mae_model"] for b in prods]); mn = np.array([b["mae_naive"] for b in prods])
        prod = {"n_products": len(prods), "mae_model_mean": r(mm.mean(), 2), "mae_naive_mean": r(mn.mean(), 2),
                "share_model_better": r((mm < mn).mean(), 3), "mae_model_median": r(np.median(mm), 2)}
    out.update({"test": f"{te.index[0]:%Y-%m} – {te.index[-1]:%Y-%m}", "multi_step": multi, "rolling_1step": rolling,
                "by_horizon": by_h, "noise_by_volume": noise, "product_level": prod})
    return out


# --------------------------------------------------------------------------- 3. cảnh báo, 4. chủ đề
def risk() -> dict | None:
    if not FILES["risk_backtest"].exists():
        return None
    b = json.loads(FILES["risk_backtest"].read_text(encoding="utf-8"))
    s = b.get("summary") or {}
    if not s:
        return b
    lift = s["high"]["neg_next"] / s["low"]["neg_next"] if s.get("low", {}).get("neg_next") else None
    return {**b, "lift_high_vs_low": r(lift, 2)}


def topics(clean: pd.DataFrame) -> dict | None:
    if not (FILES["topics"].exists() and FILES["review_topics"].exists()):
        return None
    tp = json.loads(FILES["topics"].read_text(encoding="utf-8"))
    rt_all = pd.read_csv(FILES["review_topics"])
    rt = rt_all[rt_all.topic_id >= 0].merge(clean[["review_id", "text", "summary"]], on="review_id", how="left")
    n_neg = int((clean.sentiment == "neg").sum())
    rows = []
    for t in tp:
        d = rt[rt.topic_id == t["topic_id"]]
        kw = [k for k in t["keywords"][:5]]
        pat = re.compile(r"\b(" + "|".join(map(re.escape, kw)) + r")\b", re.I)
        has = (d.summary.fillna("") + " " + d.text.fillna("")).str.contains(pat)
        rows.append({"topic_id": t["topic_id"], "name": t["name"], "n": int(len(d)), "top5": kw,
                     "keyword_coverage": r(has.mean(), 3), "weight_median": r(d.topic_weight.median(), 4)})
    return {"n_negative": n_neg, "n_assigned": int(len(rt)), "n_unassigned": n_neg - int(len(rt)),
            "unassigned_examples": clean.set_index("review_id").loc[rt_all[rt_all.topic_id < 0].review_id, "text"].map(snippet).tolist()[:3],
            "topics": rows}


# --------------------------------------------------------------------------- biên bản
def md_table(head, rows):
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(str(c) for c in x) + " |" for x in rows])


def to_md(res: dict) -> str:
    c, f = res["classification"], res["forecast"]
    o = c["overall"]
    L = [f"# Đánh giá mô hình và phân tích lỗi – {res['kind']} ({res['date']})", "",
         f"Dữ liệu {res['dataset_version']}: {res['n_reviews']:,} đánh giá sạch. Mô hình chọn: {c['selected']}.", "",
         "## 1. Phân loại cảm xúc", "",
         f"Tập kiểm tra: {o['n_test']:,} đánh giá. Accuracy 3 lớp {o['acc3']}, F1-macro {o['f1_macro3']}; đúng số sao {o['acc5']}, "
         f"lệch ≤ 1 sao {o['within1']}, MAE {o['mae_star']} sao.", "",
         md_table(["Mô hình", "F1-macro", "P macro", "R macro", "F1 Tiêu cực", "F1 Trung tính", "F1 Tích cực", "Acc 5 mức", "MAE"],
                  [[m["model"], m["f1_macro3"], m["prec_macro3"], m["rec_macro3"], m["f1_neg"], m["f1_neu"], m["f1_pos"], m["acc5"], m["mae"]] for m in c["models"]]), "",
         md_table(["Lớp", "Precision", "Recall", "F1", "Số mẫu"], [[x["class"], x["precision"], x["recall"], x["f1"], x["support"]] for x in c["per_class"]]), "",
         "Ma trận nhầm lẫn (hàng: thật, cột: dự đoán): " + json.dumps(c["confusion3"], ensure_ascii=False), ""]
    for k, v in c["slices"].items():
        L += [f"### Theo {k.lower()}", "", md_table(["Nhóm", "Số mẫu", "Acc 3 lớp", "F1-macro", "Tỷ lệ 3 sao"],
                                                    [[x["slice"], x["n"], x["acc3"], x["f1_macro3"], x["share_neu"]] for x in v]), ""]
    L += [f"### Nhóm lỗi ({c['n_errors']:,} đánh giá bị xếp sai cảm xúc)", "",
          md_table(["Nhóm lỗi", "Số lỗi", "Tỷ lệ"], [[g["group"], g["n"], g["share_of_errors"]] for g in c["error_groups"]]), ""]
    for g in c["error_groups"]:
        for x in g["examples"]:
            L.append(f"- *{g['group']}* – #{x['review_id']} ({x['score']}★, dự đoán {x['pred']} {x['conf']}): “{x['text']}”")
    L += ["", "## 2. Dự báo chỉ số hài lòng", "",
          f"Chuỗi {f.get('series')} ({f.get('n_months')} tháng, ngưỡng {f.get('threshold_per_month')} đánh giá/tháng); kiểm tra {f.get('test')}.", ""]
    if f.get("multi_step"):
        L += ["Dự báo 12 tháng một lần:", "", md_table(["Mô hình", "MAE", "RMSE"], [[m["model"], m["mae"], m["rmse"]] for m in f["multi_step"]]), "",
              "Dự báo cuốn chiếu 1 tháng:", "", md_table(["Mô hình", "MAE", "RMSE"], [[m["model"], m["mae"], m["rmse"]] for m in f["rolling_1step"]]), "",
              md_table(["Tầm", "Tháng", "Thực tế", "Sai số ETS", "Sai số ngây thơ"],
                       [[x["h"], x["month"], x["actual"], x["ets_abs_err"], x["naive_abs_err"]] for x in f["by_horizon"]]), "",
              md_table(["Số đánh giá/tháng", "Số tháng", "Sai số chuẩn TB (điểm chỉ số)", "Giai đoạn"],
                       [[x["reviews_per_month"], x["n_months"], x["se_index_mean"], x["months"]] for x in f["noise_by_volume"]]), ""]
        if f.get("product_level"):
            pl = f["product_level"]
            L.append(f"Từng sản phẩm: {pl['n_products']} sản phẩm, MAE TB {pl['mae_model_mean']} (ngây thơ {pl['mae_naive_mean']}), "
                     f"mô hình tốt hơn ngây thơ ở {pl['share_model_better']:.0%} sản phẩm.")
    rk = res.get("risk")
    if rk and rk.get("summary"):
        L += ["", "## 3. Quy tắc cảnh báo rủi ro (kiểm tra ngược)", "",
              md_table(["Mức", "Số lượt sản phẩm", "Tỷ lệ tiêu cực 3 tháng sau", "Điểm TB 3 tháng sau"],
                       [[k, v["n_products"], v["neg_next"], v["avg_next"]] for k, v in rk["summary"].items()]), "",
              f"Tỷ lệ tiêu cực của nhóm Cao gấp {rk['lift_high_vs_low']} lần nhóm Thấp."]
    tp = res.get("topics")
    if tp:
        L += ["", "## 4. Chủ đề phàn nàn", "", f"{tp['n_assigned']:,}/{tp['n_negative']:,} đánh giá tiêu cực được gán chủ đề, {tp['n_unassigned']} chưa xếp.", "",
              md_table(["Chủ đề", "Số đánh giá", "5 từ khóa đầu", "Chứa ≥ 1 từ khóa", "Trọng số trung vị"],
                       [[f"{x['topic_id']}. {x['name']}", x["n"], ", ".join(x["top5"]), x["keyword_coverage"], x["weight_median"]] for x in tp["topics"]])]
    return "\n".join(L) + "\n"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--kind", default="sample", help="nhãn bộ dữ liệu ghi vào tên biên bản: sample | full")
    ap.add_argument("--out", default=str(ROOT / "docs" / "test_report"))
    a = ap.parse_args()
    t0 = time.time()
    clean = read_clean(FILES["reviews"])
    meta = json.loads(FILES["meta"].read_text(encoding="utf-8"))
    reg = json.loads(FILES["registry"].read_text(encoding="utf-8"))
    pred = pd.read_csv(FILES["predictions"])
    res = {"kind": a.kind, "date": time.strftime("%d/%m/%Y"), "dataset_version": meta.get("dataset_version"), "n_reviews": int(len(clean)),
           "classification": classification(clean, pred, reg), "forecast": forecasting(clean, meta), "risk": risk(), "topics": topics(clean)}
    res["seconds"] = round(time.time() - t0, 1)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    stem = out / f"model_eval_{a.kind}_{time.strftime('%Y%m%d')}"
    stem.with_suffix(".json").write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    stem.with_suffix(".md").write_text(to_md(res), encoding="utf-8")
    o = res["classification"]["overall"]
    print(f"F1-macro {o['f1_macro3']} · acc3 {o['acc3']} · {res['classification']['n_errors']} lỗi · {res['seconds']} s – biên bản: {stem}.md")


if __name__ == "__main__":
    main()
