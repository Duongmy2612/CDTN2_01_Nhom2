"""EdaService – KPI và dữ liệu biểu đồ khám phá (FR-07, FR-08, FR-09). Thiết kế theo notebook 01_eda."""
from __future__ import annotations

import threading

import joblib
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS, CountVectorizer

from backend.core import config as C
from backend.core.state import FILES
from backend.services.data_service import model_preprocess

KW_STOP = sorted(ENGLISH_STOP_WORDS - {"not", "no", "nor", "never", "too", "very"}
                 | {"br", "amazon", "product", "products", "just", "like", "really", "got", "did", "does", "thought"})


def apply_filters(df: pd.DataFrame, f: dict | None) -> pd.DataFrame:
    """Lọc đồng thời (AND) theo tháng, mã sản phẩm, cảm xúc, số sao (FR-09)."""
    if not f:
        return df
    m = np.ones(len(df), dtype=bool)
    if f.get("date_from"):
        m &= (df.year_month >= f["date_from"]).values
    if f.get("date_to"):
        m &= (df.year_month <= f["date_to"]).values
    if f.get("product_id"):
        m &= (df.product_id == f["product_id"].strip().upper()).values
    if f.get("sentiment"):
        m &= (df.sentiment == f["sentiment"]).values
    if f.get("score"):
        m &= (df.score == int(f["score"])).values
    return df[m]


def log_odds_keywords(docs: pd.Series, sent: pd.Series, top: int = 15, min_df: int = 20) -> dict:
    """Từ/cụm từ đặc trưng nhóm Tiêu cực vs Tích cực: log-odds có prior Dirichlet (Monroe và cộng sự, 2008)."""
    mask = sent.isin(["neg", "pos"]).values
    docs, sent = docs[mask], sent[mask]
    if (sent == "neg").sum() < 20 or (sent == "pos").sum() < 20:
        return {"neg": {}, "pos": {}}
    cv = CountVectorizer(preprocessor=model_preprocess, stop_words=KW_STOP, ngram_range=(1, 2),
                         min_df=max(3, min(min_df, len(docs) // 2000)), max_features=40_000)
    X = cv.fit_transform(docs.values)
    vocab = np.array(cv.get_feature_names_out())
    neg = np.asarray(X[(sent == "neg").values].sum(0)).ravel(); pos = np.asarray(X[(sent == "pos").values].sum(0)).ravel()
    return _log_odds(neg, pos, vocab, top)


def _log_odds(neg: np.ndarray, pos: np.ndarray, vocab: np.ndarray, top: int) -> dict:
    a = (neg + pos) / max((neg + pos).sum(), 1) * 1000
    ni, nj, a0 = neg.sum(), pos.sum(), a.sum()
    d = np.log((neg + a) / (ni + a0 - neg - a)) - np.log((pos + a) / (nj + a0 - pos - a))
    z = d / np.sqrt(1 / (neg + a) + 1 / (pos + a))
    o = np.argsort(z)
    return {"neg": {vocab[i]: round(float(z[i]), 1) for i in o[::-1][:top]},
            "pos": {vocab[i]: round(float(-z[i]), 1) for i in o[:top]}}


# --------------------------------------------------------------------------- #
# Buổi 8 – chỉ mục từ khóa cho biểu đồ “Từ khóa đặc trưng” khi có bộ lọc (NFR-02, lỗi B10)
# --------------------------------------------------------------------------- #
# Trước đây mỗi lần lọc phải tách từ lại 20.000 đánh giá (≈ 2,0–2,2 giây trên bộ đầy đủ, vượt ngưỡng 2 giây).
# Nay tách từ MỘT lần cho một mẫu cố định 40.000 đánh giá tiêu cực/tích cực (≈ 4,5 giây, luồng nền ngay khi job xử lý xong – không
# làm chậm job, NFR-01) và lưu models/keyword_index.joblib; khởi động lại máy chủ chỉ nạp lại (≈ 0,03 giây). Mỗi lần lọc chỉ cộng
# các dòng thỏa bộ lọc của ma trận đã có (≈ 70 ms). Trong vài giây chỉ mục đang dựng: lấy mẫu 3.000 dòng để vẫn ≤ 2 giây.
# Bộ lọc quá hẹp (vd. một sản phẩm) còn < KW_INDEX_MIN_ROWS dòng trong mẫu → tính trực tiếp trên phần đã lọc (nhỏ, nhanh).
# Chất lượng (bộ đầy đủ, 3 bộ lọc năm): 26–28/30 từ khóa trùng với cách tính trên TOÀN BỘ phần đã lọc – ngang cách cũ (26–29/30);
# mẫu 60.000 không tốt hơn rõ (27–28/30) mà dựng lâu hơn 2,4 giây.
KW_INDEX_SIZE = 40_000
KW_INDEX_MIN_ROWS = 3_000
_KW = {"version": None, "index": None, "building": None}
_KW_LOCK = threading.Lock()


def build_keyword_index(df: pd.DataFrame, version: str) -> dict | None:
    if df is None or len(df) < 2 * KW_INDEX_MIN_ROWS:
        return None
    base = df[df.sentiment.isin(["neg", "pos"])]
    smp = base.sample(min(KW_INDEX_SIZE, len(base)), random_state=C.RANDOM_STATE)
    cv = CountVectorizer(preprocessor=model_preprocess, stop_words=KW_STOP, ngram_range=(1, 2), min_df=5,
                         max_features=40_000, dtype=np.int32)
    X = cv.fit_transform((smp.summary + " . " + smp.text).values).tocsr()
    return {"version": version, "X": X, "B": (X > 0).astype(np.int32).tocsr(), "vocab": np.array(cv.get_feature_names_out()),
            "cols": smp[["year_month", "product_id", "sentiment", "score"]].reset_index(drop=True)}


def save_keyword_index(idx: dict | None) -> None:
    if idx is not None:
        FILES["kw_index"].parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(idx, FILES["kw_index"])


def set_keyword_index(idx: dict | None, version: str) -> None:
    with _KW_LOCK:
        _KW.update(version=version, index=idx, building=None)


def _load_keyword_index(version: str) -> dict | None:
    try:
        if FILES["kw_index"].exists():
            idx = joblib.load(FILES["kw_index"])
            if isinstance(idx, dict) and idx.get("version") == version:
                return idx
    except Exception:  # noqa: BLE001 – tệp hỏng: dựng lại
        pass
    return None


def _build_in_background(df: pd.DataFrame, version: str) -> None:
    try:
        idx = build_keyword_index(df, version)
        save_keyword_index(idx)
    except Exception:  # noqa: BLE001 – dựng lỗi thì giữ cách tính trực tiếp (chậm hơn nhưng đúng), không dựng lại liên tục
        idx = None
    with _KW_LOCK:
        if _KW["building"] == version:
            _KW.update(version=version, index=idx, building=None)


def keyword_index(state):
    """Chỉ mục của phiên dữ liệu hiện tại: trong bộ nhớ → nạp từ đĩa → (thiếu tệp) dựng ở luồng nền và tạm trả None."""
    v = state.version
    with _KW_LOCK:
        if _KW["version"] == v:
            return _KW["index"]
        if _KW["building"] == v or state.df is None or len(state.df) < 2 * KW_INDEX_MIN_ROWS:
            return None
        idx = _load_keyword_index(v)
        if idx is not None:
            _KW.update(version=v, index=idx, building=None)
            return idx
        _KW.update(building=v, index=None, version=None)
        threading.Thread(target=_build_in_background, args=(state.df, v), daemon=True, name="kw-index").start()
    return None


def keywords_filtered(state, d: pd.DataFrame, f: dict, top: int = 15) -> dict:
    idx = keyword_index(state)
    if idx is not None:
        c = idx["cols"]
        m = np.ones(len(c), dtype=bool)
        if f.get("date_from"):
            m &= (c.year_month >= f["date_from"]).values
        if f.get("date_to"):
            m &= (c.year_month <= f["date_to"]).values
        if f.get("product_id"):
            m &= (c.product_id == f["product_id"].strip().upper()).values
        if f.get("sentiment"):
            m &= (c.sentiment == f["sentiment"]).values
        if f.get("score"):
            m &= (c.score == int(f["score"])).values
        if m.sum() >= KW_INDEX_MIN_ROWS:
            s = c.sentiment.values[m]
            if (s == "neg").sum() < 20 or (s == "pos").sum() < 20:
                return {"neg": {}, "pos": {}}
            X, keep = idx["X"][m], np.asarray(idx["B"][m].sum(0)).ravel() >= 5      # min_df = 5 trong phần đã lọc
            neg = np.asarray(X[s == "neg"].sum(0)).ravel()[keep].astype(float)
            pos = np.asarray(X[s == "pos"].sum(0)).ravel()[keep].astype(float)
            return _log_odds(neg, pos, idx["vocab"][keep], top)
    # chưa có chỉ mục (dữ liệu xử lý bằng bản 1.4.0, chỉ mục đang dựng ở luồng nền lần đầu): lấy mẫu nhỏ hơn
    n = 20_000 if _KW["building"] is None else 3_000
    smp = d.sample(min(n, len(d)), random_state=C.RANDOM_STATE)
    return log_odds_keywords(smp.summary + " . " + smp.text, smp.sentiment, top=top, min_df=5)


def group_stats(d: pd.DataFrame, key: str) -> pd.DataFrame:
    """n, avg_score, neg_rate theo khóa – tính vector hóa (nhanh với 67 nghìn sản phẩm)."""
    g = d.score.groupby(d[key])
    out = pd.DataFrame({"n": g.size(), "avg_score": g.mean(), "neg_rate": d.sentiment.eq("neg").groupby(d[key]).mean()})
    return out.reset_index()


def precompute(df: pd.DataFrame) -> dict:
    smp = df.sample(min(150_000, len(df)), random_state=C.RANDOM_STATE)
    kw = log_odds_keywords(smp.summary + " . " + smp.text, smp.sentiment)
    return {"keywords": kw}


def kpi(state, f: dict | None) -> dict:
    d = apply_filters(state.df, f)
    n = len(d)
    avg = float(d.score.mean()) if n else 0.0
    n_high = None
    if state.products is not None:
        p = state.products
        if f and f.get("product_id"):
            p = p[p.product_id == f["product_id"].strip().upper()]
        n_high = int((p.risk_level == "high").sum())
    return {"meta": state.meta_block(f), "n_reviews": n, "n_products": int(d.product_id.nunique()),
            "n_users": int(d.user_key.nunique()), "avg_score": round(avg, 4),
            "neg_rate": round(float((d.sentiment == "neg").mean()) if n else 0.0, 4),
            "model_f1_macro": state.registry["selected_metrics"]["f1_macro3"] if state.registry else None,
            "n_high_risk_products": n_high, "satisfaction_index": round(C.satisfaction_index(avg), 2) if n else 0.0}


def chart(state, name: str, f: dict | None) -> dict:
    keyword_index(state)                        # nạp chỉ mục từ khóa (hoặc dựng ở luồng nền nếu dữ liệu xử lý bằng bản cũ)
    d = apply_filters(state.df, f)
    if name == "score_dist":
        vc = d.score.value_counts().reindex([1, 2, 3, 4, 5], fill_value=0)
        data = [{"score": int(k), "n": int(v), "share": round(v / max(len(d), 1), 4),
                 "sentiment": "neg" if k <= 2 else ("neu" if k == 3 else "pos")} for k, v in vc.items()]
    elif name == "monthly":
        g = group_stats(d, "year_month")
        # PB-08: tháng sau tháng trọn vẹn cuối (dữ liệu dừng giữa tháng) được đánh dấu partial – tab Tổng quan, Dự báo,
        # cảnh báo đều dừng ở last_full_month, nên biểu đồ Phân tích phải ghi rõ tháng này chưa trọn để số liệu không “lệch”
        lf = (state.meta or {}).get("last_full_month")
        data = [{"month": r.year_month, "n": int(r.n), "avg_score": round(r.avg_score, 4), "neg_rate": round(r.neg_rate, 4),
                 "sat_index": round(C.satisfaction_index(r.avg_score), 2), "partial": bool(lf and r.year_month > lf)}
                for r in g.itertuples()]
    elif name == "length_by_score":
        q = d.groupby("score").n_words.describe(percentiles=[.25, .5, .75])
        data = [{"score": int(s), "q1": float(r["25%"]), "median": float(r["50%"]), "q3": float(r["75%"]),
                 "mean": round(float(r["mean"]), 1), "n": int(r["count"])} for s, r in q.iterrows()]
    elif name == "keywords":
        if not f or not any(f.values()):
            kw = state.eda.get("keywords", {"neg": {}, "pos": {}})
        else:
            kw = keywords_filtered(state, d, f)
        data = [{"sentiment": "neg", "term": k, "z": v} for k, v in kw.get("neg", {}).items()] + \
               [{"sentiment": "pos", "term": k, "z": v} for k, v in kw.get("pos", {}).items()]
    elif name == "top_products":
        g = group_stats(d, "product_id").sort_values("n", ascending=False).head(10)
        data = [{"product_id": r.product_id, "n": int(r.n), "avg_score": round(r.avg_score, 3), "neg_rate": round(r.neg_rate, 4)} for r in g.itertuples()]
    else:
        raise KeyError(name)
    return {"meta": state.meta_block(f), "chart": name, "data": data}
