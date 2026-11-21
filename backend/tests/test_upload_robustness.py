"""Buổi 8 – kiểm thử chịu lỗi của API tải file và kiểm tra tham số (phần backend API – Nguyễn Hoàng Thuận).

B05 file dùng dấu ";" · B06 file mã cp1252 (Excel Windows) · B07 file chỉ có tiêu đề · B11 tháng 13 lọt qua kiểm tra.
Các ca tải lên thành công thay PL.start bằng hàm ghi lại DataFrame đã đọc (không chạy pipeline thật) để kiểm thử nhanh và
không ảnh hưởng dữ liệu của các tệp kiểm thử khác.
"""
import io

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.routers import upload as UP
from backend.services import pipeline as PL
from backend.tests.synth import make

client = TestClient(app)


@pytest.fixture()
def captured(monkeypatch):
    got = {}

    def fake_start(job, df):
        got["df"] = df
        job["status"] = "done"            # không để job “queued” làm các lần tải sau bị 409 JOB_RUNNING

    monkeypatch.setattr(PL, "start", fake_start)
    yield got


def _csv(df, sep: str = ",") -> bytes:
    buf = io.StringIO(); df.to_csv(buf, index=False, sep=sep)
    return buf.getvalue().encode("utf-8")


def _post(name: str, raw: bytes):
    return client.post("/api/upload", files={"file": (name, raw, "text/csv")})


def _warn_codes(r):
    return {w["code"] for w in r.json()["validation"]["warnings"]}


def test_b05_semicolon_delimiter_is_detected(captured):
    r = _post("excel_vn.csv", _csv(make(300), sep=";"))
    assert r.status_code == 202, r.text                                    # trước đây: 400 “Thiếu cột Score, Time, Text”
    assert "DELIMITER_DETECTED" in _warn_codes(r)
    assert {"Score", "Time", "Text"} <= set(captured["df"].columns) and len(captured["df"]) == 300


def test_tab_and_pipe_delimiters(captured):
    for sep in ("\t", "|"):
        r = _post("tab.csv", _csv(make(200), sep=sep))
        assert r.status_code == 202 and "DELIMITER_DETECTED" in _warn_codes(r), sep


def test_comma_file_with_semicolons_inside_text_stays_comma(captured):
    df = make(200)
    df["Text"] = df.Text + "; really; truly; yes"                          # dấu ; trong nội dung không làm đổi dấu phân cách
    r = _post("comma.csv", _csv(df))
    assert r.status_code == 202 and "DELIMITER_DETECTED" not in _warn_codes(r)
    assert captured["df"].Text.str.contains("; really").all()


def test_b06_cp1252_file_is_read_with_fallback(captured):
    df = make(200)
    df.loc[0, "Text"] = "Café crème – naïve “quotes” and €5 price, très bon"
    buf = io.StringIO(); df.to_csv(buf, index=False)
    r = _post("windows.csv", buf.getvalue().encode("cp1252"))
    assert r.status_code == 202, r.text                                    # trước đây: 400 CSV_PARSE_ERROR khó hiểu
    assert "ENCODING_FALLBACK" in _warn_codes(r)
    assert captured["df"].Text.iloc[0].startswith("Café crème – naïve “quotes”")


def test_utf8_bom_file_has_no_encoding_warning(captured):
    raw = "﻿".encode("utf-8") + _csv(make(200))
    r = _post("bom.csv", raw)
    assert r.status_code == 202 and "ENCODING_FALLBACK" not in _warn_codes(r)
    assert "Id" in captured["df"].columns                                  # BOM không dính vào tên cột đầu


def test_header_with_spaces_is_trimmed(captured):
    df = make(200).rename(columns={"Score": " Score ", "Text": "Text "})
    r = _post("spaces.csv", _csv(df))
    assert r.status_code == 202, r.text


def test_b07_header_only_and_errors_carry_warnings():
    r = _post("header_only.csv", b"Id,ProductId,Score,Time,Text\n")
    assert r.status_code == 400 and r.json()["error"]["code"] == "NO_ROWS"
    r = _post("semi_missing.csv", b"Score;Time\n5;1303862400\n")
    body = r.json()["error"]
    assert r.status_code == 400 and body["code"] == "MISSING_COLUMN"
    assert any(w["code"] == "DELIMITER_DETECTED" for w in body["details"]["warnings"])


def test_time_ms_upload_accepted_with_warning(captured):
    df = make(200)
    r = _post("ms.csv", _csv(df.assign(Time=df.Time * 1000)))
    assert r.status_code == 202 and "TIME_MILLISECONDS" in _warn_codes(r)


def test_read_csv_unparseable_gives_clear_error():
    with pytest.raises(Exception) as e:
        UP._read_csv(b'Score,Time,Text\n5,1303862400,"unterminated\n')
    assert getattr(e.value, "status_code", None) == 400


@pytest.mark.parametrize("q", ["date_from=2010-13", "date_to=2011-00", "date_from=2011-1", "date_from=abcd-ef"])
def test_b11_month_must_be_01_to_12(q):
    for path in ("/api/kpi", "/api/eda/monthly", "/api/satisfaction"):
        r = client.get(f"{path}?{q}")
        assert r.status_code == 422, (path, q, r.status_code)
        err = r.json()["error"]
        assert err["code"] == "VALIDATION_ERROR" and "yyyy-mm" in err["message"], err["message"]


def test_second_upload_and_reset_while_job_running_get_409(monkeypatch):
    """TC8-09: đang có job chạy thì lần tải thứ hai và “Đổi file” đều bị từ chối, không xóa phiên đang xử lý."""
    jobs = []
    monkeypatch.setattr(PL, "start", lambda job, df: jobs.append(job))      # giữ job ở trạng thái “queued”
    try:
        assert _post("a.csv", _csv(make(200))).status_code == 202
        r = _post("b.csv", _csv(make(200, seed=1)))
        assert r.status_code == 409 and r.json()["error"]["code"] == "JOB_RUNNING"
        r = client.post("/api/session/reset")
        assert r.status_code == 409 and r.json()["error"]["code"] == "JOB_RUNNING"
    finally:
        for j in jobs:
            j["status"] = "done"
