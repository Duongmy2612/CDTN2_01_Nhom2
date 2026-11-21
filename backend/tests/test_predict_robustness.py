"""Buổi 8 – kiểm thử đầu vào bất thường của dự đoán (API #14) và công cụ predict_review của chatbot (KAYSONE Souk Anong).

B08 văn bản không có từ nào mô hình đã học (tiếng Việt) trước đây vẫn ra “1 sao – Tích cực 49 %” → nay 422 TEXT_NOT_RECOGNIZED;
B09 "<br> <br> <br>" lọt qua điều kiện tối thiểu 3 từ → nay đếm sau khi làm sạch giống dữ liệu huấn luyện (R6);
tinh chỉnh: xác suất nhóm cảm xúc cao nhất < 50 % → low_confidence = true, ghi chú nêu độ chính xác đo trên tập kiểm tra.
"""
import io
import time

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.core.state import STATE
from backend.main import app
from backend.services import ai_service as AI
from backend.tests.synth import make

client = TestClient(app)


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


def _predict(text, **kw):
    return client.post("/api/predict", json={"text": text, **kw})


def test_b08_text_with_no_known_word_is_rejected(loaded):
    r = _predict("Cà phê bị cũ, vị đắng khét và hộp giao tới bị móp méo, rất thất vọng.")
    assert r.status_code == 422
    e = r.json()["error"]
    assert e["code"] == "TEXT_NOT_RECOGNIZED" and "tiếng Anh" in e["message"] and e["details"]["n_words"] >= 10


def test_some_english_words_still_predicted_with_note(loaded):
    p = _predict("cà phê này rất dở và cũ, coffee stale awful").json()
    assert p["pred_star"] in range(1, 6) and p["known_token_ratio"] < 0.35 and "tiếng Anh" in p["note"]


@pytest.mark.parametrize("text", ["<br> <br> <br>", "<p></p> <b>ok</b>", "http://a.com www.b.com nice", "&nbsp; &nbsp; &nbsp;"])
def test_b09_words_are_counted_after_cleaning(loaded, text):
    r = _predict(text)
    assert r.status_code == 422 and r.json()["error"]["code"] == "TEXT_TOO_SHORT", text


def test_html_is_stripped_like_training_data(loaded):
    a = _predict("The coffee was stale and tastes awful, box was crushed").json()
    b = _predict("The coffee was <b>stale</b> and tastes awful,<br /><br />box was crushed http://x.com/a").json()
    assert a["proba"] == b["proba"] and a["pred_star"] == b["pred_star"]


def test_low_confidence_flag_matches_probabilities(loaded):
    texts = ["delicious, love it, highly recommend this honey", "it is okay average taste nothing special",
             "The coffee was stale and tastes awful, box was crushed", "love it but stale and it is okay",
             "average taste but delicious and stale"]
    for t in texts:
        p = _predict(t).json()
        low = max(p["sentiment_proba"].values()) < 0.5
        assert p["low_confidence"] is low, (t, p["sentiment_proba"])
        assert ("Độ tin cậy thấp" in (p["note"] or "")) is low


def test_low_confidence_accuracy_is_measured_on_test_split(monkeypatch):
    rng = np.random.default_rng(0)
    n = 400
    score = rng.choice([1, 3, 5], n)
    pn, p3 = rng.uniform(0.2, 0.45, n), rng.uniform(0.2, 0.45, n)
    pp = 1 - pn - p3
    pred = np.array(["neg", "neu", "pos"])[np.c_[pn, p3, pp].argmax(1)]
    df = pd.DataFrame({"split": ["test"] * 300 + ["train"] * 100, "score": score, "p_neg": pn, "p3": p3, "p_pos": pp,
                       "pred_sentiment": pred})
    monkeypatch.setattr(STATE, "predictions", df)
    AI._CALIB.update(version=None, acc_low=None)                    # buộc tính lại cho bảng dự đoán giả lập
    t = df[df.split == "test"]
    true = np.select([t.score <= 2, t.score == 3], ["neg", "neu"], "pos")
    low = t[["p_neg", "p3", "p_pos"]].max(axis=1) < 0.5
    want = (t.pred_sentiment.values[low] == true[low]).mean()
    assert AI.low_confidence_accuracy() == pytest.approx(want)
    AI._CALIB.update(version=None, acc_low=None)                    # không để số liệu giả lập dính sang kiểm thử khác


def test_chatbot_tool_uses_same_input_rules(loaded):
    assert AI.predict_review("Cà phê rất dở, hộp bị móp và giao hàng trễ")["code"] == "TEXT_NOT_RECOGNIZED"
    assert AI.predict_review("<br> <br> <br>")["code"] == "TEXT_TOO_SHORT"
    assert AI.predict_review("The coffee was stale and tastes awful")["pred_star"] <= 2
