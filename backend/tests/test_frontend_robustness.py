"""Buổi 8 – giao diện hiển thị đúng các trường hợp bất thường mà backend đã xử lý (Lê Gia Huy – frontend).

Đọc tĩnh mã React (không cần npm, chạy được trong CI) và đối chiếu với hành vi thật của backend:
- mọi cảnh báo kiểm tra file mà backend có thể trả đều có “message” tiếng Việt, và trang tải file hiển thị chúng
  (v1.4.0 bỏ qua toàn bộ validation.warnings – người dùng không biết file Time mili-giây đã được đổi, Id bị đánh số lại…);
- bộ đếm từ ở tab Dự đoán đếm giống máy chủ (bỏ thẻ HTML, đường dẫn – lỗi B09) nên nút “Dự đoán” không bật cho “<br> <br> <br>”;
- tab Dự đoán hiển thị low_confidence; tab Tổng quan chỉ đọc các khóa clean_log mà backend thật sự sinh ra.
"""
import io
import re
from pathlib import Path

import pandas as pd

from backend.main import app
from backend.routers import upload as UP
from backend.services import data_service as DS
from backend.tests.synth import make

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "frontend" / "src"
UPLOAD = (SRC / "pages" / "UploadPage.jsx").read_text(encoding="utf-8")
PREDICT = (SRC / "tabs" / "PredictTab.jsx").read_text(encoding="utf-8")
OVERVIEW = (SRC / "tabs" / "OverviewTab.jsx").read_text(encoding="utf-8")


def _all_warnings() -> list[dict]:
    """Sinh đủ các loại cảnh báo mà bước đọc + kiểm tra file có thể trả."""
    df = make(300)
    out = []
    bad = df.copy(); bad.loc[:2, "Score"] = 9; bad.loc[3:5, "Time"] = 0; bad["Id"] = "x"
    out += DS.validate_schema(bad.drop(columns=["ProductId"]))["warnings"]           # INVALID_SCORE_ROWS, INVALID_TIME_ROWS, ID_RENUMBERED, MISSING_OPTIONAL
    out += DS.validate_schema(df.assign(Time=df.Time * 1000))["warnings"]           # TIME_MILLISECONDS
    buf = io.StringIO(); df.assign(Text=df.Text + " – café").to_csv(buf, index=False, sep=";")
    out += UP._read_csv(buf.getvalue().encode("cp1252"))[1]                          # DELIMITER_DETECTED, ENCODING_FALLBACK
    return out


def test_every_backend_warning_has_a_vietnamese_message():
    ws = _all_warnings()
    codes = {w["code"] for w in ws}
    assert {"INVALID_SCORE_ROWS", "INVALID_TIME_ROWS", "ID_RENUMBERED", "MISSING_OPTIONAL", "TIME_MILLISECONDS",
            "DELIMITER_DETECTED", "ENCODING_FALLBACK"} <= codes, codes
    for w in ws:
        assert isinstance(w.get("message"), str) and len(w["message"]) > 15, w


def test_upload_page_shows_validation_warnings():
    assert "validation?.warnings" in UPLOAD, "UploadPage phải đọc acc.validation.warnings của API #1/#3"
    assert "w.message" in UPLOAD and "<Warnings" in UPLOAD
    # các trường phụ mà giao diện ghép vào thông điệp phải đúng tên backend trả (rows, columns)
    used = set(re.findall(r"\bw\.(\w+)", UPLOAD))
    assert used <= {"code", "message", "rows", "columns"}, used


def _js_regexes(fn_src: str) -> list[str]:
    return [m.replace("\\/", "/") for m in re.findall(r"\.replace\(/(.+?)/g", fn_src)]


def test_word_counter_matches_server_cleaning():
    line = next(x for x in PREDICT.splitlines() if x.startswith("const countWords"))
    pats = _js_regexes(line)
    assert len(pats) == 2, pats

    def front(t: str) -> int:
        for p in pats:
            t = re.sub(p, " ", t)
        return len(t.split())

    def back(t: str) -> int:
        return len(DS.clean_text(pd.Series([t])).iloc[0].split())

    samples = ["<br> <br> <br>", "great <b>coffee</b> here", "see http://amazon.com/x and www.a.com now",
               "The coffee arrived stale.<br /><br />Never again!", "  many   spaces\n\nand lines  ", "ok"]
    for s in samples:
        assert front(s) == back(s), (s, front(s), back(s))


def test_predict_tab_shows_low_confidence_and_has_no_misleading_example():
    assert "low_confidence" in app.openapi()["components"]["schemas"]["PredictResponse"]["properties"]
    assert "r.low_confidence" in PREDICT
    # chip tiếng Việt được ghi rõ là ngoài phạm vi (v1.4.0 gọi là “Đánh giá tiếng Việt” và trả 1 sao – Tích cực 49 %)
    assert "'Đánh giá tiếng Việt'" not in PREDICT and "ngoài phạm vi" in PREDICT


def test_overview_reads_only_clean_log_keys_backend_produces():
    _, log = DS.clean_reviews(make(300))
    keys = set(re.findall(r"\blog\.(\w+)", OVERVIEW))
    assert keys and keys <= set(log), keys - set(log)
    assert {"r2_time_ms_converted", "id_renumbered"} <= keys                       # buổi 8: hiển thị chỉnh sửa tự động
