"""Kiểm thử sprint xây dựng 2 – PB-08 (tháng chưa trọn) và script chạy thử toàn hệ thống (buổi 7, NFR-08).

- biểu đồ theo tháng của tab Phân tích đánh dấu tháng sau last_full_month là partial – các tab Tổng quan, Dự báo,
  cảnh báo dừng ở last_full_month nên tháng chưa trọn phải được ghi rõ để số liệu giữa các màn hình không lệch
- scripts/smoke_test.py gọi đủ các API của giao diện và mọi lời gọi đạt (chạy qua TestClient, không cần máy chủ thật)
"""
import importlib.util
import io
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.tests.synth import make

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def _smoke():
    spec = importlib.util.spec_from_file_location("smoke_test", ROOT / "scripts" / "smoke_test.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def _call(method, path, params=None, body=None):
    r = client.request(method, path, params=params, json=body)
    return r.status_code, r.headers.get("content-type", ""), r.content


@pytest.fixture(scope="module")
def loaded():
    buf = io.BytesIO(); make().to_csv(buf, index=False)        # dữ liệu tổng hợp: ngày cuối không phải cuối tháng
    r = client.post("/api/upload", files={"file": ("synth.csv", buf.getvalue(), "text/csv")})
    assert r.status_code == 202, r.text
    for _ in range(300):
        j = client.get(f"/api/jobs/{r.json()['job_id']}").json()
        if j["status"] in ("done", "failed"):
            break
        time.sleep(0.2)
    assert j["status"] == "done", j
    return client.get("/api/health").json()


def test_partial_month_marked(loaded):
    lf = loaded["dataset"]["last_full_month"]
    data = client.get("/api/eda/monthly").json()["data"]
    assert data[-1]["month"] > lf and data[-1]["partial"] is True          # tháng cuối chưa trọn
    assert all(d["partial"] == (d["month"] > lf) for d in data)
    fc = client.get("/api/forecast?months=3").json()
    assert fc["history"][-1]["month"] == lf                                 # Tổng quan, Dự báo dừng ở tháng trọn vẹn
    assert fc["forecast"][0]["month"] == data[-1]["month"]


def test_partial_month_with_filter(loaded):
    lf = loaded["dataset"]["last_full_month"]
    data = client.get("/api/eda/monthly?score=1").json()["data"]
    assert all(d["partial"] == (d["month"] > lf) for d in data)


def test_smoke_script_all_ok(loaded, tmp_path):
    smoke = _smoke()
    info = smoke.ensure_data(_call, "sample")
    assert info["started_job"] is False                                     # đã có dữ liệu → không chạy lại job
    rows = smoke.checks(_call)
    bad = [r for r in rows if not r["ok"]]
    assert not bad, bad
    assert len(rows) >= 25
    path = smoke.write_report(rows, info, "http://testserver", "sample", 9.5, tmp_path)
    text = path.read_text(encoding="utf-8")
    assert f"{len(rows)}/{len(rows)} lời gọi đạt" in text and "9.5 phút" in text
