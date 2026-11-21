"""Buổi 8 – kiểm thử chịu lỗi của dữ liệu đầu vào và chỉ mục từ khóa (phần DataService, EDA – Dương Diễm My).

Mỗi hàm kiểm thử ứng với một lỗi trong nhật ký lỗi buổi 8 (docs/test_report/bug_log_buoi8.md) và chạy lại được trên CI:
B01 Time mili-giây · B02 vài dòng Time ngoài khoảng · B03 Id không phải số · B04 Id trùng · B07 file chỉ có tiêu đề ·
B10 biểu đồ từ khóa có bộ lọc chậm hơn 2 giây (NFR-02).
"""
import threading
import time
from types import SimpleNamespace

import pandas as pd

from backend.services import data_service as DS
from backend.services import eda_service as EDA
from backend.tests.synth import make


def _codes(items):
    return {x["code"] for x in items}


def test_b01_time_in_milliseconds_is_converted():
    raw = make(600, seed=1)
    ms = raw.assign(Time=raw.Time * 1000)
    v = DS.validate_schema(ms)
    assert v["ok"] and "TIME_MILLISECONDS" in _codes(v["warnings"])
    assert DS.quality_report(ms)["time_min"] == DS.quality_report(raw)["time_min"]      # trước đây: OutOfBoundsDatetime
    c_s, _ = DS.clean_reviews(raw)
    c_ms, log = DS.clean_reviews(ms)
    assert log["r2_time_ms_converted"] == 1 and log["r2_invalid_time"] == 0
    assert (c_ms.year_month.values == c_s.year_month.values).all()                        # cùng tháng với file ghi bằng giây


def test_b02_out_of_range_time_rows_are_dropped_not_crashing():
    raw = make(600, seed=2)
    raw.loc[:4, "Time"] = [0, -5, 99_999_999_999_999, 123, 4_102_444_800]               # 1970, âm, năm 5138, 1970, năm 2100
    v = DS.validate_schema(raw)
    w = {x["code"]: x for x in v["warnings"]}
    assert v["ok"] and w["INVALID_TIME_ROWS"]["rows"] == 5
    clean, log = DS.clean_reviews(raw)
    assert log["r2_invalid_time"] == 5 and len(clean) == 595
    assert clean.review_date.min() >= "1995-01-01"                                         # review_date dạng yyyy-mm-dd


def test_time_unit_detection_uses_median_not_single_value():
    t, info = DS.normalize_time(pd.Series([1_303_862_400, 1_303_862_401, 99_999_999_999_999]))
    assert info == {"unit": "s", "n_out_of_range": 1} and t.isna().sum() == 1
    t, info = DS.normalize_time(pd.Series([1_303_862_400_000, 1_303_862_401_000, None]))
    assert info["unit"] == "ms" and t.iloc[0] == 1_303_862_400


def test_time_all_invalid_is_rejected_with_clear_message():
    raw = make(50).assign(Time="hôm qua")
    v = DS.validate_schema(raw)
    assert not v["ok"] and v["errors"][0]["code"] == "INVALID_TIME" and "1995" in v["errors"][0]["message"]


def test_b03_non_numeric_id_is_renumbered():
    raw = make(400, seed=3).assign(Id=[f"R-{i}" for i in range(400)])
    v = DS.validate_schema(raw)
    assert v["ok"] and "ID_RENUMBERED" in _codes(v["warnings"])
    clean, log = DS.clean_reviews(raw)                                                       # trước đây: ValueError
    assert log["id_renumbered"] == 1 and clean.review_id.is_unique and clean.review_id.min() >= 1


def test_b04_duplicate_ids_are_renumbered_so_review_id_stays_unique():
    raw = make(400, seed=4)
    raw["Id"] = raw.Id % 50                                                                  # 400 dòng chỉ có 50 Id khác nhau
    clean, log = DS.clean_reviews(raw)
    assert log["id_renumbered"] == 1 and clean.review_id.is_unique                         # trước đây trùng → bằng chứng AI sai
    ok = make(400, seed=4)
    clean_ok, log_ok = DS.clean_reviews(ok)
    assert log_ok["id_renumbered"] == 0 and (clean_ok.review_id.values == ok.Id.values).all()   # Id hợp lệ giữ nguyên


def test_missing_id_column_is_not_a_warning():
    raw = make(300, seed=5).drop(columns="Id")
    v = DS.validate_schema(raw)
    assert v["ok"] and "ID_RENUMBERED" not in _codes(v["warnings"])
    clean, log = DS.clean_reviews(raw)
    assert log["id_renumbered"] == 0 and clean.review_id.is_unique


def test_b07_header_only_file_reports_no_rows():
    v = DS.validate_schema(make(10).iloc[0:0])
    assert not v["ok"] and v["errors"][0]["code"] == "NO_ROWS"                              # trước đây: INVALID_SCORE gây hiểu nhầm


def _state(df, version):
    return SimpleNamespace(df=df, version=version)


def test_b10_keyword_index_matches_direct_computation_and_is_fast():
    clean, _ = DS.clean_reviews(make(12_000, n_products=40, seed=6))
    st = _state(clean, "kw-test")
    EDA.keyword_index(st)
    for _ in range(200):                                                                     # chỉ mục dựng ở luồng nền
        if EDA.keyword_index(st) is not None:
            break
        time.sleep(0.05)
    assert EDA.keyword_index(st) is not None
    f = {"date_from": "2009-01", "date_to": "2011-12"}
    d = EDA.apply_filters(clean, f)
    t0 = time.perf_counter()
    fast = EDA.keywords_filtered(st, d, f)
    assert time.perf_counter() - t0 < 0.5
    gold = EDA.log_odds_keywords(d.summary + " . " + d.text, d.sentiment, top=15, min_df=5)
    for side in ("neg", "pos"):
        a, b = list(fast[side]), list(gold[side])
        assert len(set(a[:10]) & set(b[:10])) >= 7, (side, a[:10], b[:10])                   # cùng nhóm từ đặc trưng


def test_keyword_index_too_narrow_filter_falls_back_to_direct():
    clean, _ = DS.clean_reviews(make(8_000, n_products=30, seed=7))
    st = _state(clean, "kw-narrow")
    EDA.keyword_index(st)
    for _ in range(200):
        if EDA.keyword_index(st) is not None:
            break
        time.sleep(0.05)
    pid = clean.product_id.iloc[0]
    f = {"product_id": pid}
    out = EDA.keywords_filtered(st, EDA.apply_filters(clean, f), f)
    assert set(out) == {"neg", "pos"}


def test_keyword_index_is_built_once_per_dataset_version():
    clean, _ = DS.clean_reviews(make(7_000, seed=8))
    st = _state(clean, "kw-once")
    before = threading.active_count()
    for _ in range(5):
        EDA.keyword_index(st)
    assert threading.active_count() - before <= 1                                            # không dựng lặp nhiều luồng


def test_keyword_index_is_saved_and_reloaded_without_rebuilding():
    """Pipeline dựng chỉ mục ở bước EDA và lưu đĩa; khởi động lại máy chủ chỉ nạp lại (không có khoảng chờ dựng)."""
    clean, _ = DS.clean_reviews(make(7_000, seed=9))
    idx = EDA.build_keyword_index(clean, "kw-disk")
    EDA.save_keyword_index(idx)
    EDA.set_keyword_index(None, "khác")                       # giả lập vừa khởi động: bộ nhớ chưa có chỉ mục
    before = threading.active_count()
    got = EDA.keyword_index(_state(clean, "kw-disk"))
    assert got is not None and threading.active_count() == before        # nạp từ đĩa ngay, không mở luồng dựng
    assert (got["vocab"] == idx["vocab"]).all() and got["X"].shape == idx["X"].shape
    assert EDA.keyword_index(_state(clean, "phiên-khác")) is None       # tệp của phiên khác không được dùng nhầm
