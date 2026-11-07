"""Kiểm thử tích hợp (sprint xây dựng 2 – buổi 7): cùng một con số phải giống nhau trên mọi màn hình.

Chạy scripts/integration_check.py (cùng bộ kiểm tra nhóm dùng trên bộ mẫu 100.000 dòng và toàn bộ Reviews.csv) trên dữ liệu
tổng hợp qua TestClient: số đánh giá, số sản phẩm, sản phẩm rủi ro cao, F1-macro, chỉ số hài lòng, chuỗi tháng, dự báo,
số đánh giá tiêu cực theo chủ đề, số liệu của một sản phẩm ở bảng Sản phẩm – Phân tích – Tự nhập dự đoán – Chủ đề.
"""
import importlib.util
import io
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.tests.synth import make

client = TestClient(app)
ROOT = Path(__file__).resolve().parents[2]


def _script():
    sys.path.insert(0, str(ROOT / "scripts"))
    spec = importlib.util.spec_from_file_location("integration_check", ROOT / "scripts" / "integration_check.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


def _call(method, path, params=None, body=None):
    r = client.request(method, path, params=params, json=body)
    return r.status_code, r.headers.get("content-type", ""), r.content


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


def test_numbers_consistent_across_screens(loaded, tmp_path):
    ic = _script()
    rows, info = ic.run_checks(_call)
    bad = [(r["group"], r["check"], r["values"]) for r in rows if not r["ok"]]
    assert not bad, bad
    assert len(rows) >= 17 and info["product_id"]
    text = ic.write_report(rows, info, "http://testserver", "sample", tmp_path).read_text(encoding="utf-8")
    assert f"{len(rows)}/{len(rows)} kiểm tra khớp" in text


def test_check_detects_mismatch():
    """Bộ kiểm tra phải báo “Lệch” khi hai màn hình khác nhau – không phải lúc nào cũng xanh."""
    ic = _script()
    assert ic._same({"a": 10, "b": 10}) and not ic._same({"a": 10, "b": 11})
    assert ic._same({"a": 79.67, "b": 79.68}, tol=0.02) and not ic._same({"a": 1, "b": None})
    assert not ic._same({"a": "2012-09", "b": "2012-10"})
