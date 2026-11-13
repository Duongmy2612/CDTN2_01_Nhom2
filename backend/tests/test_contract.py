    assert 0 < len(ctx["reviews"]) <= 30 and all(len(r["text"].split()) <= 121 for r in ctx["reviews"])
    assert all("user_key" not in r for r in ctx["reviews"])
    recent = STATE.df[(STATE.df.product_id == pid) & (STATE.df.score <= 2) & (STATE.df.year_month >= AI._recent_cutoff())]
    sent_months = [r["date"][:7] for r in ctx["reviews"]]
    assert sum(m >= AI._recent_cutoff() for m in sent_months) == min(len(recent), 30)
    t = AI._insight_context("topic", "0")
    assert 0 < len(t["reviews"]) <= 30


def test_report_and_exports(loaded):
    r = client.get("/api/report/pdf")
    assert r.status_code == 200 and r.content[:4] == b"%PDF" and len(r.content) > 20_000
    for t in ["product_risk", "topics", "predictions", "monthly", "model_metrics", "forecast"]:
        r = client.get(f"/api/export/{t}")
        assert r.status_code == 200 and r.content.startswith(b"\xef\xbb\xbf"), t
    mm = pd.read_csv(io.BytesIO(client.get("/api/export/model_metrics").content), encoding="utf-8-sig")
    assert set(mm.model) == {"B0", "NB", "SVM", "LR"} and mm.split.str.contains("theo thời gian").any()
    assert client.get("/api/export/nope").status_code == 422


def test_ai_rule_mode(loaded):
    os.environ.pop("GEMINI_API_KEY", None)
    c = client.post("/api/chat", json={"message": "Những sản phẩm nào đang rủi ro cao?"}).json()
    assert c["source"] == "rule" and "rủi ro cao" in c["answer"] and c["data_used"]
    assert "|---|" not in c["answer"]                               # danh sách, không phải bảng nhiều cột trong khung chat hẹp
    c = client.post("/api/chat", json={"message": 'Có bao nhiêu đánh giá nhắc tới "stale"?'}).json()
    assert "Tìm kiếm đánh giá" in c["data_used"] and "stale" in c["answer"]
    c = client.post("/api/chat", json={"message": "Dự đoán: tốt"}).json()
    assert "tối thiểu 3 từ" in c["answer"]                       # cùng điều kiện FR-14 với API #14
    pid = client.get("/api/products?sort=risk").json()["items"][0]["product_id"]
    i = client.post("/api/ai/insights", json={"scope": "product", "id": pid}).json()
    assert i["source"] == "rule" and i["causes"] and all(c["evidence"] for c in i["causes"])
    assert client.post("/api/ai/insights", json={"scope": "product", "id": "NOPE"}).status_code == 404
    for tid in ("-1", "99", "x"):
        assert client.post("/api/ai/insights", json={"scope": "topic", "id": tid}).status_code == 404, tid


def test_ai_gemini_mode(loaded):
    base = fake_gemini.start()
    os.environ.update(GEMINI_API_KEY="AQ.fake-test-key", GEMINI_BASE_URL=base, GEMINI_MODEL="missing-model")
    AI._ACTIVE.update(mode=None, model=None)
    try:
        c = client.post("/api/chat", json={"message": "Tổng quan dữ liệu thế nào?", "context": {"page": "Tổng quan"}}).json()
        assert c["source"] == "gemini" and "get_overview" in c["answer"] and c["data_used"] == ["KPI tổng quan"], c
        assert c["model"] != "missing-model"                       # model 404 → tự chuyển model dự phòng
        c = client.post("/api/chat", json={"message": "Những sản phẩm nào rủi ro?"}).json()
        assert "list_risk_products" in c["answer"]
        c = client.post("/api/chat", json={"message": "Thời tiết Hà Nội hôm nay thế nào?"}).json()
        assert c["source"] == "gemini" and "kiến thức chung" in c["answer"] and c["data_used"] == []
        pid = client.get("/api/products?sort=risk").json()["items"][0]["product_id"]
        i = client.post("/api/ai/insights", json={"scope": "product", "id": pid, "refresh": True}).json()
        assert i["source"] == "gemini" and len(i["causes"]) == 1 and i["dropped_causes"] == 1 and len(i["solutions"]) == 1
        # hành động bị cắt ở lần gọi đầu → gọi lại 1 lần, kết quả cuối đủ ý (sprint XD1)
        assert i["n_calls"] == 2 and i["incomplete_actions"] == 0 and i["solutions"][0]["complete"] is True, i
        assert len(i["solutions"][0]["action"].split()) >= 8 and i["note"] is None
        assert client.post("/api/ai/insights", json={"scope": "product", "id": pid}).json()["cached"] is True
        i = client.post("/api/ai/insights", json={"scope": "topic", "id": "0", "refresh": True}).json()
        assert i["causes"][0]["evidence_ids"]
        # gọi lại vẫn thiếu ý → không gọi thêm lần thứ ba, gắn cờ và ghi chú để người dùng đọc lại
        s0 = i["solutions"][0]
        assert i["n_calls"] == 2 and i["incomplete_actions"] == 1 and s0["complete"] is False and "từ" in s0["problem"] and i["note"], i
        # chạy hàng loạt (scripts/run_ai_batch.py): mọi sản phẩm rủi ro Cao + mọi chủ đề, kiểm tra độc lập bằng chứng, bảng chấm NFR-10
        batch = _script("run_ai_batch")
        out = Path(tempfile.mkdtemp(prefix="ai_batch_"))
        sm = batch.run(refresh=True, delay=0, out_dir=out)
        assert sm["errors"] == {} and sm["n_gemini"] == sm["n_targets"] > sm["n_topics"] > 0 and sm["evidence_valid_pct"] == 100.0, sm
        assert sm["retried"] == sm["n_targets"] and sm["incomplete_actions"] == sm["n_topics"]   # sản phẩm sửa được, chủ đề vẫn thiếu
        assert sm["dropped_causes"] == sm["n_targets"] and (out / f"ai_batch_{time.strftime('%Y%m%d')}.md").exists()
        grade = next(out.glob("nfr10_cham_diem_*.csv"))
        rows = list(csv.DictReader(grade.open(encoding="utf-8-sig")))
        assert rows and all(r["nguyen_van_bang_chung"].startswith("#") for r in rows)
        assert len({r["ma_ket_qua"] for r in rows}) == min(21, sm["n_products"]) + sm["n_topics"]
        assert client.get("/api/health").json()["gemini_model"]
        os.environ["GEMINI_API_KEY"] = "BAD"; AI._ACTIVE.update(mode=None, model=None)
        c = client.post("/api/chat", json={"message": "Tổng quan?"}).json()
        assert c["source"] == "rule" and "không hợp lệ" in c["answer"]
    finally:
        for k in ("GEMINI_API_KEY", "GEMINI_BASE_URL", "GEMINI_MODEL"):
            os.environ.pop(k, None)
        AI._ACTIVE.update(mode=None, model=None, last_error=None)


def test_nfr10_scoring(tmp_path):
    """Cohen's κ của bảng chấm hai người: a = [1,1,0,0], b = [1,0,0,0] → p0 = 0,75, pe = 0,5 → κ = 0,5."""
    nfr = _script("nfr10_score")
    assert abs(nfr.cohen_kappa([1, 1, 0, 0], [1, 0, 0, 0]) - 0.5) < 1e-9
    f = tmp_path / "g.csv"
    rows = [["ma_ket_qua", "stt_nguyen_nhan", "nguyen_nhan", "mo_ta", "muc_do", "ma_bang_chung", "nguyen_van_bang_chung", "nguoi_cham_1", "nguoi_cham_2", "ghi_chu"]]
    rows += [[f"product|P{i}", 1, "x", "y", "cao", "1", "#1", 1, 1, ""] for i in range(9)] + [["topic|0", 1, "x", "y", "cao", "1", "#1", 0, 0, ""]]
    with f.open("w", encoding="utf-8-sig", newline="") as fh:
        csv.writer(fh).writerows(rows)
    r = nfr.score(f)
    assert r["n_graded"] == 10 and r["match_both"] == 0.9 and r["kappa"] == 1.0 and r["pass"] is True


def test_reset_last(loaded):
    r = client.post("/api/session/reset").json()
    assert r["status"] == "reset" and r["removed"]
    assert client.get("/api/kpi").status_code == 409
