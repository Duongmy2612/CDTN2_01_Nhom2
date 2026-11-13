"""Kiểm thử sprint xây dựng 2 – PB-06 (tự nhập dự đoán) và PB-07 (chủ đề phàn nàn) sau khi tích hợp (buổi 7).

- mã sản phẩm nhập kèm dự đoán được chuẩn hóa như API #13, #15, #16; có mã → trả bối cảnh sản phẩm khớp API #10;
  mã không có → vẫn dự đoán, product = null và ghi chú rõ (giao diện không mở ngăn chi tiết toàn lỗi 404)
- tổng đánh giá của các chủ đề + phần chưa xếp chủ đề = số đánh giá tiêu cực ở tab Tổng quan, Phân tích
- hợp đồng API 1.4.0 đã xuất lại vào docs/openapi.json
"""
import io
import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.schemas.api import API_CONTRACT_VERSION
from backend.tests.synth import make

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]
NEG_TEXT = "The coffee was stale and tastes awful, box was crushed"


@pytest.fixture(scope="module")
def loaded():
    buf = io.BytesIO(); make().to_csv(buf, index=False)
    r = client.post("/api/upload", files={"file": ("synth.csv", buf.getvalue(), "text/csv")})
    assert r.status_code == 202, r.text
    for _ in range(300):
        j = client.get(f"/api/jobs/{r.json()['job_id']}").json()
        if j["status"] in ("done", "failed"):
            break
        time.sleep(0.2)
    assert j["status"] == "done", j
    return j


def test_predict_with_known_product(loaded):
    row = client.get("/api/products?sort=n_reviews&page_size=5").json()["items"][0]
    pid = row["product_id"]
    r = client.post("/api/predict", json={"text": NEG_TEXT, "product_id": f"  {pid.lower()} "})
    assert r.status_code == 200, r.text
    p = r.json()
    assert p["product_id"] == pid                                     # chuẩn hóa giống #13, #15, #16
    ctx = p["product"]
    assert ctx["product_id"] == pid and ctx["n_reviews"] == row["n_reviews"] and ctx["risk_level"] == row["risk_level"]
    assert abs(ctx["avg_score"] - row["avg_score"]) < 1e-3
    assert abs(ctx["satisfaction_index"] - (row["avg_score"] - 1) / 4 * 100) < 0.01   # cùng công thức FR-19
    assert p["note"] is None or pid not in p["note"]


def test_predict_with_unknown_product(loaded):
    r = client.post("/api/predict", json={"text": NEG_TEXT, "product_id": "B0NOTEXIST"})
    assert r.status_code == 200, r.text                               # vẫn dự đoán theo nội dung
    p = r.json()
    assert p["product"] is None and p["product_id"] == "B0NOTEXIST" and "B0NOTEXIST" in p["note"]
    assert client.get("/api/forecast?product_id=B0NOTEXIST").status_code == 404   # lý do giao diện không mở chi tiết


def test_predict_without_product(loaded):
    p = client.post("/api/predict", json={"text": NEG_TEXT}).json()
    assert p["product"] is None and p["product_id"] is None


def test_topics_add_up_to_negative_reviews(loaded):
    t = client.get("/api/topics").json()
    n_neg_kpi = client.get("/api/kpi?sentiment=neg").json()["n_reviews"]
    assert t["n_negative"] == n_neg_kpi
    assert t["n_unassigned"] >= 0
    assert sum(x["n_reviews"] for x in t["topics"]) + t["n_unassigned"] == t["n_negative"]


def test_topics_of_product_add_up(loaded):
    pid = client.get("/api/products?sort=n_reviews&page_size=5").json()["items"][0]["product_id"]
    t = client.get(f"/api/topics?product_id={pid}").json()
    n_neg = client.get(f"/api/kpi?sentiment=neg&product_id={pid}").json()["n_reviews"]
    assert t["n_negative"] == n_neg
    assert sum(x["n_reviews"] for x in t["topics"]) + t["n_unassigned"] == n_neg


def test_contract_version_exported():
    assert client.get("/api/health").json()["version"] == API_CONTRACT_VERSION == "1.4.0"
    spec = json.loads((ROOT / "docs" / "openapi.json").read_text(encoding="utf-8"))
    assert spec["info"]["version"] == API_CONTRACT_VERSION, "chạy lại: python scripts/export_openapi.py"
    props = spec["components"]["schemas"]
    assert "product" in props["PredictResponse"]["properties"] and "n_unassigned" in props["TopicsResponse"]["properties"]
