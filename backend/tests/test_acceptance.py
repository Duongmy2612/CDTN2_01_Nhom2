"""Kiểm thử chấp nhận FR mức Must (PB-16, sprint xây dựng 1 – buổi 6).

scripts/acceptance_test.py chạy được trên phiên dữ liệu tổng hợp và các ca FR Must đạt. Bộ tổng hợp chỉ có 4 chủ đề nên
TC-12 “≥ 5 chủ đề” chỉ kiểm tra trên dữ liệu thật; chuỗi tổng hợp không có xu hướng nên ETS bằng mô hình ngây thơ – điều
kiện NFR-04 chỉ có nghĩa trên dữ liệu thật; TC-06 cần file mẫu 100.000 dòng – không có trên máy CI.
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


def _script(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    return mod


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


def test_acceptance_script(loaded):
    from backend.core.state import FILES
    acc = _script("acceptance_test")
    rows = acc.run_checks(client, make(), FILES["reviews"])
    assert [r["tc"] for r in rows] == [t[0] for t in acc.TC] and all(r["n_checks"] > 0 for r in rows)
    skip = {"TC-12"} | ({"TC-06"} if not client.get("/api/health").json()["sample_available"] else set())
    bad = [(r["tc"], f) for r in rows if r["tc"] not in skip for f in r["failed"] if "NFR-04" not in f]
    assert not bad, bad
    assert "| TC-14 |" in acc.to_markdown(rows, {"date": "x", "dataset": "synth.csv", "n_raw": 4000, "app_version": "1.3.0", "machine": "ci"})
