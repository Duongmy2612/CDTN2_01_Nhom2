"""Kiểm thử hợp đồng API và luồng chính trên dữ liệu tổng hợp (PB-03, PB-11).

- đủ 20 đường dẫn của hợp đồng; lỗi đúng định dạng {"error": {code, message, details}}
- quy tắc làm sạch R1–R9 trên file có lỗi; mô hình dự đoán là cấu hình chọn trên validation (LR)
- chọn đánh giá bằng chứng gửi Gemini đúng mục 5.6 (≤ 30, ưu tiên 12 tháng gần nhất, không gửi user_key)
- tải file → pipeline nền 7 bước → mọi API trả dữ liệu thật đúng lược đồ
- chatbot/insights: chế độ quy tắc (không có khóa) và chế độ Gemini (máy chủ Gemini giả lập: gọi công cụ, kiểm tra bằng chứng)
"""
import csv
import importlib.util
import io
import os
import tempfile
import time
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services import ai_service as AI
from backend.tests import fake_gemini
from backend.tests.synth import make

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def _script(name: str):
    """Nạp một script trong scripts/ (không phải package) để kiểm thử hàm của nó."""
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


EXPECTED = {
    ("GET", "/api/health"), ("POST", "/api/upload"), ("GET", "/api/jobs/{job_id}"), ("POST", "/api/data/sample"),
    ("GET", "/api/data/quality"), ("POST", "/api/session/reset"), ("GET", "/api/kpi"), ("GET", "/api/eda/{chart}"),
    ("GET", "/api/topics"), ("GET", "/api/products"), ("GET", "/api/model/metrics"), ("GET", "/api/model/keywords"),
    ("GET", "/api/reviews/mismatch"), ("POST", "/api/predict"), ("GET", "/api/satisfaction"), ("GET", "/api/forecast"),
    ("POST", "/api/ai/insights"), ("POST", "/api/chat"), ("GET", "/api/report/pdf"), ("GET", "/api/export/{table}"),
}


def test_all_20_endpoints_declared():
    spec = client.get("/openapi.json").json()
    assert {(m.upper(), p) for p, ops in spec["paths"].items() for m in ops} == EXPECTED


def test_errors_before_data():
    client.post("/api/session/reset")
    assert client.get("/api/health").json()["dataset_loaded"] is False
    r = client.get("/api/kpi")
    assert r.status_code == 409 and r.json()["error"]["code"] == "DATASET_NOT_LOADED"
    r = client.post("/api/predict", json={"text": "great coffee, fresh and tasty"})
    assert r.status_code == 409 and r.json()["error"]["code"] in ("MODEL_NOT_READY", "DATASET_NOT_LOADED")


def test_clean_rules_on_messy_file():
    """R1–R9 chịu được file thực tế: UserId trống, Score sai, Text rỗng, bản ghi trùng."""
    import numpy as np
    from backend.services import data_service as DS
    df = make(300)
    df.loc[df.index[:10], "UserId"] = np.nan                     # ô UserId trống không được làm sập pipeline
    df.loc[df.index[10], "Score"] = 7                            # R1
    df.loc[df.index[11], "Text"] = "   "                         # R3
    dup = df.iloc[[20]].assign(Id=10_000, ProductId="B00DUPLIC8")  # R5: cùng (UserId, Time, Text), khác mã sản phẩm
    clean, log = DS.clean_reviews(pd.concat([df, dup], ignore_index=True))
    assert log["r1_invalid_score"] == 1 and log["r3_empty_text"] == 1 and log["r5_duplicates"] >= 1
    assert len(clean) == log["n_clean"] and clean.dup_count.min() >= 1 and clean.review_id.is_unique
    assert "ProfileName" not in clean.columns and "UserId" not in clean.columns          # R8, R9


def test_upload_errors():
    r = client.post("/api/upload", files={"file": ("bad.csv", b"Score,Time\n5,1303862400\n", "text/csv")})
    assert r.status_code == 400 and r.json()["error"]["code"] == "MISSING_COLUMN"
    r = client.post("/api/upload", files={"file": ("a.txt", b"x", "text/plain")})
    assert r.status_code == 415 and r.json()["error"]["code"] == "UNSUPPORTED_TYPE"


@pytest.fixture(scope="module")
def loaded():
    buf = io.BytesIO(); make().to_csv(buf, index=False)
    r = client.post("/api/upload", files={"file": ("synth.csv", buf.getvalue(), "text/csv")})
    assert r.status_code == 202, r.text
    job_id = r.json()["job_id"]
    for _ in range(300):
        j = client.get(f"/api/jobs/{job_id}").json()
        if j["status"] in ("done", "failed"):
            break
        time.sleep(0.2)
    assert j["status"] == "done", j
    assert [s["status"] for s in j["steps"]] == ["done"] * 7
    return j


def test_dashboard_endpoints(loaded):
    h = client.get("/api/health").json()
    assert h["dataset_loaded"] and h["model_ready"] and h["dataset"]["n_reviews"] == 4000
    k = client.get("/api/kpi").json()
    assert k["n_reviews"] == 4000 and 0 <= k["satisfaction_index"] <= 100 and k["model_f1_macro"] is not None
    assert client.get("/api/kpi?score=1").json()["n_reviews"] < 4000
    for c in ["score_dist", "monthly", "length_by_score", "keywords", "top_products"]:
        r = client.get(f"/api/eda/{c}?date_from=2009-01")
        assert r.status_code == 200 and r.json()["data"], c
    q = client.get("/api/data/quality").json()
    assert q["n_rows"] == 4000 and len(q["preview"]) == 20 and "ProfileName" not in q["preview"][0]


def test_eda_filters(loaded):
    """FR-09: lọc đồng thời; mã sản phẩm không phân biệt hoa/thường; bộ lọc mâu thuẫn trả 422 có thông điệp rõ."""
    pid = client.get("/api/eda/top_products").json()["data"][0]["product_id"]
    up = client.get(f"/api/kpi?product_id={pid}").json()
    assert up["n_reviews"] > 0
    assert client.get(f"/api/kpi?product_id=%20{pid.lower()}%20").json()["n_reviews"] == up["n_reviews"]
    both = client.get(f"/api/kpi?product_id={pid}&score=1&sentiment=neg&date_from=2008-01&date_to=2012-12").json()
    assert both["n_reviews"] == client.get(f"/api/kpi?product_id={pid}&score=1").json()["n_reviews"]
    for bad in ["score=2&sentiment=pos", "score=3&sentiment=neg", "date_from=2012-01&date_to=2011-01"]:
        r = client.get(f"/api/kpi?{bad}")
        assert r.status_code == 422 and r.json()["error"]["code"] == "VALIDATION_ERROR" and r.json()["error"]["message"], bad
        assert client.get(f"/api/eda/monthly?{bad}").status_code == 422, bad
    assert client.get("/api/kpi?product_id=NOPE").json()["n_reviews"] == 0          # AND: không có đánh giá khớp → 0, không lỗi
    m = client.get(f"/api/eda/monthly?product_id={pid}&sentiment=pos").json()["data"]
    assert m and all(x["neg_rate"] == 0 for x in m)
    assert client.get("/api/topics?product_id=NOPE").status_code == 404


def test_failed_upload_keeps_current_data(loaded):
    """FR-24 + NFR-07: file mới không dùng được (còn < 200 dòng sau làm sạch) bị từ chối, dữ liệu đang dùng không bị xóa."""
    buf = io.BytesIO(); make(150, seed=3).to_csv(buf, index=False)
    r = client.post("/api/upload", files={"file": ("small.csv", buf.getvalue(), "text/csv")})
    assert r.status_code == 202, r.text
    for _ in range(100):
        j = client.get(f"/api/jobs/{r.json()['job_id']}").json()
        if j["status"] in ("done", "failed"):
            break
        time.sleep(0.1)
    assert j["status"] == "failed" and j["error"]["code"] == "TOO_FEW_ROWS"
    h = client.get("/api/health").json()
    assert h["dataset_loaded"] and h["model_ready"] and h["dataset"]["n_reviews"] == 4000
    assert client.get("/api/kpi").json()["n_reviews"] == 4000


def test_forecast_month_gap():
    """Chuỗi toàn bộ có tháng không có đánh giá nào: không được sinh NaN (API #16 trả JSON hợp lệ)."""
    import math
    from backend.services import data_service as DS
    from backend.services import forecast_service as FS
    clean, _ = DS.clean_reviews(make(6000, months=60, seed=1))
    clean = clean[clean.year_month != "2010-06"]
    out = FS.precompute(clean, sorted(clean.year_month.unique())[-2])
    assert out["forecast"] and all(math.isfinite(p[k]) for p in out["forecast"] for k in ("sat_index", "lo", "hi"))
    assert out["series_start"] > "2010-06"


def test_model_endpoints(loaded):
    m = client.get("/api/model/metrics").json()
    assert {x["model"] for x in m["models"]} == {"B0", "NB", "SVM", "LR"} and sum(x["selected"] for x in m["models"]) == 1
    assert m["selected"] == "LR"          # cấu hình chọn trên validation (E-C1); tập kiểm tra không dùng để chọn lại
