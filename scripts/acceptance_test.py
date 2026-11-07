"""Kiểm thử chấp nhận các yêu cầu chức năng mức Must (PB-16, sprint xây dựng 1) – sinh biên bản kiểm thử.

Mỗi ca kiểm thử gọi API thật của ứng dụng (FastAPI TestClient, cùng mã với máy chủ) rồi so kết quả với một phép tính
độc lập bằng pandas trên file gốc hoặc file đã làm sạch – đúng tiêu chí chấp nhận “số liệu khớp khi nhóm kiểm tra lại
bằng pandas” của backlog buổi 3.

Chạy từ thư mục gốc dự án (không ảnh hưởng dữ liệu đang dùng của máy chủ: chạy trong thư mục tạm):
    python scripts/acceptance_test.py                 # bộ mẫu chung 100.000 dòng (backend/data/sample) – khoảng 3 phút
    python scripts/acceptance_test.py --full          # toàn bộ Reviews.csv (backend/data/raw) – khoảng 4 – 5 phút
Kết quả: docs/test_report/acceptance_<sample|full>_<ngày>.md và .json; mã thoát 0 khi mọi ca đạt.
"""
from __future__ import annotations

import argparse
import html
import io
import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

# Các ca kiểm thử: mã ca, yêu cầu, nội dung kiểm tra (đúng thứ tự FR trong SRS)
TC: list[tuple[str, str, str]] = [
    ("TC-01", "FR-01", "Tải file CSV lên, job nền chạy đủ 7 bước có tiến trình"),
    ("TC-02", "FR-02", "File thiếu cột bắt buộc / Score sai / không phải .csv bị từ chối, nêu rõ lỗi, dữ liệu đang dùng giữ nguyên"),
    ("TC-03", "FR-03", "Báo cáo chất lượng: số dòng, số dòng trùng, giá trị thiếu, khoảng thời gian, 20 dòng đầu"),
    ("TC-04", "FR-04", "Làm sạch R1 – R9: không còn trùng, rỗng, Helpfulness sai, thẻ HTML; bỏ ProfileName, UserId"),
    ("TC-05", "FR-05", "Nhãn cảm xúc đúng quy tắc 1–2 / 3 / 4–5 sao"),
    ("TC-06", "FR-06", "Lưu reviews_clean.csv; có dữ liệu mẫu dùng ngay"),
    ("TC-07", "FR-07", "KPI tổng quan khớp phép tính độc lập bằng pandas"),
    ("TC-08", "FR-08", "5 biểu đồ EDA có dữ liệu, số liệu khớp pandas"),
    ("TC-09", "FR-10", "Mô hình huấn luyện tự động trên dữ liệu đã làm sạch, dùng được để dự đoán"),
    ("TC-10", "FR-11", "So sánh ≥ 3 mô hình trên cùng tập 80/20: Accuracy, Precision, Recall, F1-macro, MAE, ma trận nhầm lẫn"),
    ("TC-11", "FR-14", "Tự nhập đánh giá → số sao, cảm xúc, xác suất, chỉ số hài lòng ≤ 1 giây; < 3 từ bị từ chối"),
    ("TC-12", "FR-18", "≥ 5 chủ đề phàn nàn, mỗi chủ đề có tên, 10 từ khóa, tỷ trọng, 3 đánh giá mẫu, xu hướng"),
    ("TC-13", "FR-19", "Chỉ số hài lòng theo tháng cho toàn bộ và từng sản phẩm, đúng công thức (TB − 1)/4 × 100"),
    ("TC-14", "FR-20", "Dự báo 3/6/12 tháng có khoảng tin cậy 95%; sản phẩm < 36 tháng báo không đủ dữ liệu; thắng mô hình ngây thơ"),
]


class Check:
    """Gom các điều kiện của một ca; ca đạt khi mọi điều kiện đạt."""

    def __init__(self):
        self.items: list[tuple[str, bool]] = []

    def __call__(self, desc: str, ok) -> bool:
        self.items.append((desc, bool(ok)))
        return bool(ok)

    @property
    def ok(self) -> bool:
        return all(o for _, o in self.items)

    def actual(self) -> str:
        return "; ".join(d for d, _ in self.items)

    def failed(self) -> list[str]:
        return [d for d, o in self.items if not o]


def vn(x, d=0) -> str:
    return f"{x:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")


def wait_job(client, job_id: str, timeout: float = 1800) -> tuple[dict, list[int]]:
    seen, t0 = [], time.time()
    while time.time() - t0 < timeout:
        j = client.get(f"/api/jobs/{job_id}").json()
        seen.append(j["progress"])
        if j["status"] in ("done", "failed"):
            return j, seen
        time.sleep(0.5)
    raise TimeoutError("job chạy quá lâu")


def independent_clean(raw: pd.DataFrame) -> dict:
    """Đếm lại kết quả làm sạch bằng pandas thuần, không dùng DataService."""
    d = raw.copy()
    d = d[pd.to_numeric(d.Score, errors="coerce").isin([1, 2, 3, 4, 5])]
    d = d[pd.to_numeric(d.Time, errors="coerce").notna()]
    d = d[d.Text.fillna("").astype(str).str.strip() != ""]
    n4 = int((d.HelpfulnessNumerator > d.HelpfulnessDenominator).sum())
    d = d[~(d.HelpfulnessNumerator > d.HelpfulnessDenominator)]
    d = d.sort_values("Id")
    n5 = int(d.duplicated(["UserId", "Time", "Text"]).sum())
    d = d.drop_duplicates(["UserId", "Time", "Text"])
    txt = d.Text.astype(str).map(html.unescape).str.replace(r"<[^>]+>", " ", regex=True).str.replace(r"(https?://\S+|www\.\S+)", " ", regex=True)
    short = int((txt.str.split().str.len() < 3).sum())
    return {"r4": n4, "r5": n5, "r7": short, "n_clean": len(d) - short}


def run_checks(client, raw: pd.DataFrame, clean_path: Path, upload_info: dict | None = None) -> list[dict]:
    """Chạy 14 ca kiểm thử trên phiên dữ liệu đang nạp. raw: file gốc vừa tải lên; clean_path: reviews_clean.csv của phiên."""
    from backend.services.data_service import model_preprocess

    clean = pd.read_csv(clean_path, dtype={"product_id": str, "user_key": str, "summary": str, "text": str}, keep_default_na=False)
    res: dict[str, Check] = {tc: Check() for tc, _, _ in TC}
    health0 = client.get("/api/health").json()
    ver0 = health0["dataset"]["dataset_version"]

    # TC-01 – FR-01
    c = res["TC-01"]
    if upload_info:
        c(f"POST /api/upload → {upload_info['status_code']}, job {upload_info['job_id']}", upload_info["status_code"] == 202)
        c(f"7/7 bước xong trong {vn(upload_info['seconds'], 0)} giây", upload_info["steps_done"] == 7)
        c(f"tiến trình tăng dần {upload_info['progress_first']}% → 100%", upload_info["progress_monotonic"])
    else:
        c("phiên đã có dữ liệu (job đã chạy trước khi kiểm thử)", health0["dataset_loaded"] and health0["model_ready"])

    # TC-02 – FR-02, NFR-07
    c = res["TC-02"]
    buf = io.BytesIO(); raw.head(300).drop(columns=["Text"]).to_csv(buf, index=False)
    r = client.post("/api/upload", files={"file": ("thieu_cot.csv", buf.getvalue(), "text/csv")})
    e = r.json().get("error", {})
    c(f"thiếu cột Text → {r.status_code} {e.get('code')} “{e.get('message')}”", r.status_code == 400 and e.get("code") == "MISSING_COLUMN" and "Text" in e.get("message", ""))
    buf = io.BytesIO(); raw.head(300).assign(Score=9).to_csv(buf, index=False)
    r = client.post("/api/upload", files={"file": ("score_sai.csv", buf.getvalue(), "text/csv")})
    c(f"Score ngoài 1–5 ở mọi dòng → {r.status_code} {r.json().get('error', {}).get('code')}", r.status_code == 400)
    r = client.post("/api/upload", files={"file": ("du_lieu.xlsx", b"PK\x03\x04", "application/vnd.ms-excel")})
    c(f"file .xlsx → {r.status_code} {r.json().get('error', {}).get('code')}", r.status_code == 415)
    h = client.get("/api/health").json()
    c("dữ liệu đang dùng giữ nguyên (cùng dataset_version)", h["dataset_loaded"] and h["dataset"]["dataset_version"] == ver0)

    # TC-03 – FR-03
    c = res["TC-03"]
    q = client.get("/api/data/quality").json()
    dup = int(raw.duplicated(["UserId", "Time", "Text"]).sum())
    t = pd.to_datetime(raw.Time, unit="s")
    miss = {k: int(v) for k, v in raw.isna().sum().items()}
    c(f"số dòng {vn(q['n_rows'])} = pandas {vn(len(raw))}", q["n_rows"] == len(raw))
    c(f"số dòng trùng {vn(q['n_duplicates'])} = pandas {vn(dup)}", q["n_duplicates"] == dup)
    c("giá trị thiếu từng cột khớp pandas", all(q["missing_by_column"].get(k) == v for k, v in miss.items()))
    c(f"khoảng thời gian {q['time_min']} – {q['time_max']}", q["time_min"] == t.min().strftime("%Y-%m-%d") and q["time_max"] == t.max().strftime("%Y-%m-%d"))
    c(f"xem trước {len(q['preview'])} dòng, không có ProfileName", len(q["preview"]) == 20 and all("ProfileName" not in p for p in q["preview"]))

    # TC-04 – FR-04
    c = res["TC-04"]
    ind = independent_clean(raw)
    log = q["clean_log"]
    c(f"{vn(log['n_raw'])} → {vn(log['n_clean'])} đánh giá; pandas độc lập {vn(ind['n_clean'])}", log["n_clean"] == ind["n_clean"] == len(clean))
    c(f"bỏ trùng {vn(log['r5_duplicates'])} = pandas {vn(ind['r5'])}; Helpfulness sai {log['r4_helpfulness_invalid']} = {ind['r4']}",
      log["r5_duplicates"] == ind["r5"] and log["r4_helpfulness_invalid"] == ind["r4"])
    c("review_id duy nhất, không còn nội dung rỗng, < 3 từ", clean.review_id.is_unique and (clean.text.str.strip() != "").all() and (clean.n_words >= 3).all())
    c("không còn thẻ HTML trong nội dung", not clean.text.str.contains(r"<\s*/?\s*[a-zA-Z][^>]*>", regex=True).any())
    c("helpful_num ≤ helpful_den ở mọi dòng", (clean.helpful_num <= clean.helpful_den).all())
    c("không có cột ProfileName, UserId (thay bằng user_key)", not ({"ProfileName", "UserId"} & set(clean.columns)) and "user_key" in clean.columns)
    c("chữ thường ở bước vector hóa: “Didn't LIKE” → “did not like”", model_preprocess("Didn't LIKE") == "did not like")

    # TC-05 – FR-05
    c = res["TC-05"]
    exp = clean.score.map({1: "neg", 2: "neg", 3: "neu", 4: "pos", 5: "pos"})
    c(f"{vn(len(clean))}/{vn(len(clean))} dòng đúng quy tắc nhãn", (exp == clean.sentiment).all())

    # TC-06 – FR-06
    c = res["TC-06"]
    c(f"reviews_clean.csv đọc được: {vn(len(clean))} dòng × {clean.shape[1]} cột", clean_path.exists() and len(clean) > 0)
    c("dữ liệu mẫu 100.000 dòng có sẵn trên máy chủ (nút “Dùng dữ liệu mẫu”)", h["sample_available"])

    # TC-07 – FR-07
    c = res["TC-07"]
    k = client.get("/api/kpi").json()
    neg = float((clean.score <= 2).mean())
    prods = client.get("/api/products?page_size=5").json()
    m = client.get("/api/model/metrics").json()
    sel = next(x for x in m["models"] if x["selected"])
    c(f"đánh giá {vn(k['n_reviews'])}, sản phẩm {vn(k['n_products'])}, người dùng {vn(k['n_users'])} khớp pandas",
      k["n_reviews"] == len(clean) and k["n_products"] == clean.product_id.nunique() and k["n_users"] == clean.user_key.nunique())
    c(f"điểm TB {vn(k['avg_score'], 4)} = {vn(clean.score.mean(), 4)}; tỷ lệ tiêu cực {vn(k['neg_rate'] * 100, 2)}% = {vn(neg * 100, 2)}%",
      abs(k["avg_score"] - clean.score.mean()) < 1e-3 and abs(k["neg_rate"] - neg) < 1e-3)
    c(f"F1-macro mô hình {vn(k['model_f1_macro'], 3)} = mô hình đang chọn; SP rủi ro cao {k['n_high_risk_products']} = bảng sản phẩm",
      abs(k["model_f1_macro"] - sel["f1_macro3"]) < 1e-9 and k["n_high_risk_products"] == prods["counts"].get("high", 0))

    # TC-08 – FR-08
    c = res["TC-08"]
    charts = {ch: client.get(f"/api/eda/{ch}") for ch in ["score_dist", "monthly", "length_by_score", "keywords", "top_products"]}
    c("5/5 biểu đồ trả 200 và có dữ liệu", all(r.status_code == 200 and r.json()["data"] for r in charts.values()))
    sd = {d["score"]: d["n"] for d in charts["score_dist"].json()["data"]}
    c("phân bố số sao khớp value_counts()", sd == {int(s): int(n) for s, n in clean.score.value_counts().items()})
    top = [d["product_id"] for d in charts["top_products"].json()["data"]]
    c(f"10 sản phẩm nhiều đánh giá nhất khớp pandas (đầu bảng {top[0]})",
      set(top) == set(clean.product_id.value_counts().head(10).index) or top[:5] == clean.product_id.value_counts().head(5).index.tolist())
    mon = charts["monthly"].json()["data"]
    c(f"tổng số đánh giá theo tháng = {vn(sum(x['n'] for x in mon))}", sum(x["n"] for x in mon) == len(clean))

    # TC-09 – FR-10
    c = res["TC-09"]
    c(f"mô hình {m['selected']} huấn luyện lúc {m['trained_at']} trên {vn(m['split']['n_dataset'])} đánh giá đã làm sạch",
      m["split"]["n_dataset"] == len(clean) and h["model_ready"])
    p = client.post("/api/predict", json={"text": "Absolutely delicious, fresh and my kids love it, will buy again"}).json()
    c(f"dự đoán được ngay sau khi xử lý: {p.get('pred_star')} sao, {p.get('sentiment')}", p.get("sentiment") == "pos")

    # TC-10 – FR-11, NFR-03
    c = res["TC-10"]
    names = {x["model"] for x in m["models"]}
    sp = m["split"]
    c(f"{len(names - {'B0'})} mô hình + baseline: {', '.join(sorted(names))}", {"LR", "NB", "SVM"} <= names)
    c(f"cùng tập {vn(sp['train'])} / {vn(sp['test'])} (80/20)", abs(sp["test"] / (sp["train"] + sp["test"]) - 0.2) < 0.01)
    need = ["acc5", "acc3", "prec_macro3", "rec_macro3", "f1_macro3", "mae"]
    c("đủ Accuracy, Precision, Recall, F1-macro, MAE cho mọi mô hình", all(x.get(f) is not None for x in m["models"] for f in need))
    c(f"ma trận nhầm lẫn 3×3 và 5×5, tổng {vn(int(np.sum(m['confusion3'])))} = tập kiểm tra",
      np.array(m["confusion3"]).shape == (3, 3) and np.array(m["confusion5"]).shape == (5, 5) and int(np.sum(m["confusion3"])) == sp["test"])
    c(f"mô hình chọn {m['selected']}: F1-macro {vn(sel['f1_macro3'], 3)} ≥ 0,65; F1 Tiêu cực {vn(sel['f1_neg'], 3)}; MAE {vn(sel['mae'], 3)}",
      sel["f1_macro3"] >= 0.65)

    # TC-11 – FR-14, NFR-02
    c = res["TC-11"]
    cases = [("The coffee arrived stale and the box was crushed, will not order again", "neg"),
             ("It is okay, nothing special but not bad either for the price", None),
             ("Great taste, fresh and crunchy, my family loves these snacks", "pos")]
    lat = []
    for text, want in cases:
        t0 = time.perf_counter(); p = client.post("/api/predict", json={"text": text}).json(); lat.append(time.perf_counter() - t0)
        okp = abs(sum(p["proba"].values()) - 1) < 1e-3 and 0 <= p["satisfaction_index"] <= 100 and 1 <= p["pred_star"] <= 5
        c(f"“{text[:32]}…” → {p['pred_star']} sao, {p['sentiment']}, chỉ số {vn(p['satisfaction_index'], 1)}", okp and (want is None or p["sentiment"] == want))
    c(f"thời gian dự đoán lớn nhất {vn(max(lat) * 1000, 0)} ms ≤ 1 giây", max(lat) <= 1.0)
    r = client.post("/api/predict", json={"text": "too short"})
    c(f"“too short” (2 từ) → {r.status_code} {r.json().get('error', {}).get('code')}", r.status_code == 422)

    # TC-12 – FR-18
    c = res["TC-12"]
    tp = client.get("/api/topics").json()["topics"]
    c(f"{len(tp)} chủ đề (≥ 5)", len(tp) >= 5)
    c("mỗi chủ đề có tên, 10 từ khóa, tỷ trọng, 3 đánh giá mẫu, xu hướng theo tháng",
      all(t["name"] and len(t["keywords"]) == 10 and 0 < t["share"] <= 1 and len(t["samples"]) == 3 and t["trend"] for t in tp))
    c(f"tổng tỷ trọng {vn(sum(t['share'] for t in tp) * 100, 1)}% của đánh giá tiêu cực", 0.98 <= sum(t["share"] for t in tp) <= 1.0001)

    # TC-13 – FR-19
    c = res["TC-13"]
    s_all = client.get("/api/satisfaction").json()["series"]
    g = clean.groupby("year_month").score.agg(["size", "mean"])
    chk = all(abs(x["avg_score"] - g.loc[x["month"], "mean"]) < 1e-3 and x["n"] == g.loc[x["month"], "size"]
              and abs(x["sat_index"] - (x["avg_score"] - 1) / 4 * 100) < 0.01 for x in s_all)
    c(f"toàn bộ: {len(s_all)} tháng, điểm TB và chỉ số khớp pandas, đúng công thức", chk and len(s_all) == len(g))
    pid = top[0]
    s_p = client.get(f"/api/satisfaction?product_id={pid}").json()["series"]
    gp = clean[clean.product_id == pid].groupby("year_month").score.mean()
    c(f"sản phẩm {pid}: {len(s_p)} tháng khớp pandas", len(s_p) == len(gp) and all(abs(x["avg_score"] - gp.loc[x["month"]]) < 1e-3 for x in s_p))

    # TC-14 – FR-20, NFR-04
    c = res["TC-14"]
    for mo in (3, 6, 12):
        f = client.get(f"/api/forecast?months={mo}").json()
        c(f"toàn bộ, {mo} tháng: {len(f['forecast'])} điểm, cận dưới ≤ dự báo ≤ cận trên",
          len(f["forecast"]) == mo and all(x["lo"] <= x["sat_index"] <= x["hi"] for x in f["forecast"]))
    bt = f.get("backtest")
    if bt:
        c(f"kiểm tra lùi 12 tháng: MAE {vn(bt['mae_model'], 2)} < ngây thơ {vn(bt['mae_naive'], 2)} điểm (NFR-04)", bt["mae_model"] < bt["mae_naive"])
    plist = client.get("/api/products?sort=n_reviews&page_size=100").json()["items"]
    short = next((x["product_id"] for x in plist if not x["forecastable"]), None)
    if short:
        fp = client.get(f"/api/forecast?product_id={short}&months=6").json()
        c(f"sản phẩm {short} (< 36 tháng): eligible = {fp['eligible']}, “{fp['message'][:40]}…”", fp["eligible"] is False and "Không đủ dữ liệu" in fp["message"])
    long_ = next((x["product_id"] for x in plist if x["forecastable"]), None)
    if long_:
        fp = client.get(f"/api/forecast?product_id={long_}&months=6").json()
        c(f"sản phẩm {long_} (≥ 36 tháng): {len(fp['forecast'])} tháng dự báo kèm khoảng tin cậy", fp["eligible"] and len(fp["forecast"]) == 6)

    out = []
    for tc, fr, desc in TC:
        ch = res[tc]
        out.append({"tc": tc, "fr": fr, "content": desc, "actual": ch.actual(), "result": "Đạt" if ch.ok else "Không đạt",
                    "failed": ch.failed(), "n_checks": len(ch.items)})
    return out


def to_markdown(rows: list[dict], meta: dict) -> str:
    n_ok = sum(r["result"] == "Đạt" for r in rows)
    lines = [f"# Biên bản kiểm thử chấp nhận – yêu cầu chức năng mức Must", "",
             f"- Ngày chạy: {meta['date']} · dữ liệu: {meta['dataset']} ({vn(meta['n_raw'])} dòng gốc) · phiên bản ứng dụng {meta['app_version']}",
             f"- Môi trường: {meta['machine']}",
             f"- Kết quả: **{n_ok}/{len(rows)} ca đạt** ({sum(r['n_checks'] for r in rows)} điều kiện kiểm tra)", "",
             "| Mã ca | Yêu cầu | Nội dung kiểm tra | Kết quả thực tế | Kết quả |", "|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r['tc']} | {r['fr']} | {r['content']} | {r['actual']} | {r['result']} |")
    return "\n".join(lines) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--full", action="store_true", help="dùng toàn bộ Reviews.csv thay cho bộ mẫu 100.000 dòng")
    ap.add_argument("--out", type=Path, default=ROOT / "docs" / "test_report")
    a = ap.parse_args()
    os.environ["FRI_WORK_DIR"] = tempfile.mkdtemp(prefix="fri_accept_")     # không đụng dữ liệu, mô hình của máy chủ
    os.environ.setdefault("GEMINI_API_KEY", "")                              # kiểm thử FR Must không gọi Gemini
    sys.path.insert(0, str(ROOT))
    from fastapi.testclient import TestClient
    from backend.core import config as C
    from backend.core.state import FILES
    from backend.main import app
    from backend.schemas.api import API_CONTRACT_VERSION
    path = (C.DATA_RAW / "Reviews.csv") if a.full else (C.DATA_SAMPLE / "reviews_sample_100k.csv")
    raw_bytes = path.read_bytes(); raw = pd.read_csv(io.BytesIO(raw_bytes))
    client = TestClient(app)
    t0 = time.time()
    r = client.post("/api/upload", files={"file": (path.name, raw_bytes, "text/csv")})
    job, seen = wait_job(client, r.json()["job_id"])
    if job["status"] != "done":
        raise SystemExit(f"Job lỗi: {job['error']}")
    info = {"status_code": r.status_code, "job_id": job["job_id"], "seconds": time.time() - t0,
            "steps_done": sum(s["status"] == "done" for s in job["steps"]), "progress_first": seen[0],
            "progress_monotonic": all(b >= a_ for a_, b in zip(seen, seen[1:])) and seen[-1] == 100}
    rows = run_checks(client, raw, FILES["reviews"], info)
    import platform
    meta = {"date": time.strftime("%Y-%m-%d %H:%M"), "dataset": path.name, "n_raw": len(raw), "app_version": API_CONTRACT_VERSION,
            "machine": f"{platform.system()} {platform.machine()}, {os.cpu_count()} CPU, Python {platform.python_version()}",
            "job_seconds": round(info["seconds"], 1), "steps": {s["name"]: s["seconds"] for s in job["steps"]}}
    a.out.mkdir(parents=True, exist_ok=True)
    stem = a.out / f"acceptance_{'full' if a.full else 'sample'}_{time.strftime('%Y%m%d')}"
    stem.with_suffix(".json").write_text(json.dumps({"meta": meta, "cases": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    stem.with_suffix(".md").write_text(to_markdown(rows, meta), encoding="utf-8")
    for x in rows:
        print(f"{x['tc']} {x['fr']:<6} {x['result']:<10} {'; '.join(x['failed'])}")
    n_ok = sum(x["result"] == "Đạt" for x in rows)
    print(f"\n{n_ok}/{len(rows)} ca đạt · job {meta['job_seconds']} giây · biên bản: {stem.with_suffix('.md')}")
    sys.exit(0 if n_ok == len(rows) else 1)


if __name__ == "__main__":
    main()
