            i = int(sid)
        except ValueError:
            i = -1
        if not 0 <= i < len(STATE.topics):
            raise ApiError(404, "TOPIC_NOT_FOUND", f"Không có chủ đề {sid}")
        t = STATE.topics[i]
        rt = STATE.review_topics[STATE.review_topics.topic_id == t["topic_id"]]
        rv = d[d.review_id.isin(rt.review_id) & (d.n_words >= 15)].merge(rt[["review_id", "topic_weight"]], on="review_id")
        rv = rv.assign(_recent=rv.year_month >= cutoff)
        rv = rv.sort_values(["_recent", "topic_weight", "helpful_num"], ascending=[False, False, False])
        rv = rv.head(C.AI_MAX_REVIEWS)
        stats = (f"chủ đề phàn nàn “{t['name']}”: {_vn(t['n_reviews'], 0)} đánh giá tiêu cực ({_pct(t['share'])} tổng đánh giá 1–2 sao); "
                 f"từ khóa: {', '.join(t['keywords'])}")
        title = t["name"]
        topic_ids = {"topic": t}
    reviews = [{"review_id": int(r.review_id), "score": int(r.score), "summary": r.summary, "date": r.review_date,
                "product_id": r.product_id, "text": _short(r.text, C.AI_REVIEW_MAX_WORDS)} for r in rv.itertuples()]
    return {"scope": scope, "id": sid, "title": title, "stats": stats, "reviews": reviews, **topic_ids}


def _evidence(ids: list[int], by_id: dict) -> list[dict]:
    return [{"review_id": i, "score": by_id[i]["score"], "summary": by_id[i]["summary"], "text": by_id[i]["text"],
             "date": by_id[i]["date"], "product_id": by_id[i]["product_id"]} for i in ids if i in by_id]


SCHEMA_NOTE = "\nLƯU Ý: lần trước trả về sai lược đồ JSON, hãy trả đúng lược đồ."
FIX_NOTE = ("\nLƯU Ý: lần trước các giải pháp sau bị thiếu ý hoặc quá ngắn: {items}. Hãy trả lại TOÀN BỘ JSON, giữ nguyên nguyên nhân và "
            "bằng chứng, nhưng viết MỖI hanh_dong thành một câu hoàn chỉnh khoảng 12 – 30 từ (làm gì, ở khâu nào, để đạt điều gì) "
            "và MỖI chi_so_theo_doi là một chỉ số đo được (ít nhất 5 từ).")


def _words(s: str | None) -> list[str]:
    return re.findall(r"[^\s.,;:!?…()“”\"']+", s or "")


def solution_problem(action: str | None, kpi: str | None) -> str | None:
    """Lý do một giải pháp chưa dùng được (None = đạt): hành động quá ngắn, bị cắt giữa chừng, hoặc chỉ số theo dõi quá ngắn."""
    w = _words(action)
    if len(w) < C.AI_MIN_ACTION_WORDS:
        return f"hành động chỉ có {len(w)} từ"
    if w[-1].lower() in C.AI_DANGLING_WORDS:
        return f"hành động bị cắt giữa chừng (kết thúc bằng “{w[-1]}”)"
    if len(_words(kpi)) < C.AI_MIN_KPI_WORDS:
        return "chỉ số theo dõi quá ngắn"
    return None


def mark_solutions(sols: list[dict]) -> int:
    """Gắn cờ complete/problem cho từng giải pháp; trả về số giải pháp chưa đạt. Dùng cả cho kết quả cũ đọc từ bộ đệm."""
    bad = 0
    for s in sols:
        p = solution_problem(s.get("action"), s.get("kpi"))
        s["complete"] = p is None
        s["problem"] = p
        bad += p is not None
    return bad


def _gemini_insight(ctx: dict) -> dict:
    """Gọi Gemini, kiểm tra lược đồ, bằng chứng và độ đầy đủ của giải pháp.

    Tối đa C.AI_MAX_CALLS lần gọi: sai lược đồ → gọi lại 1 lần kèm nhắc lỗi (vẫn sai → 502); lược đồ đúng nhưng có giải pháp
    thiếu ý (hành động < 8 từ, kết thúc bằng từ nối, chỉ số theo dõi < 4 từ) → gọi lại 1 lần, nêu rõ giải pháp cần viết lại.
    Giữ kết quả có ít giải pháp thiếu ý nhất; giải pháp vẫn thiếu sau khi gọi lại được gắn cờ để giao diện cảnh báo người dùng.
    """
    by_id = {r["review_id"]: r for r in ctx["reviews"]}
    lines = "\n".join(f"[{r['review_id']}] {r['score']} | {r['summary']} | {r['text']}" for r in ctx["reviews"])
    prompt = INSIGHT_PROMPT.format(stats=ctx["stats"], reviews=lines)
    cfg = types.GenerateContentConfig(temperature=0.2, response_mime_type="application/json", response_schema=_Out)
    best, best_bad, model, n_calls, extra = None, None, None, 0, ""
    schema_retry = fix_retry = False
    while n_calls < C.AI_MAX_CALLS:
        resp, model = generate(prompt + extra, cfg)
        n_calls += 1
        try:
            cand = _Out.model_validate_json(_strip_json(resp.text or ""))
        except ValidationError:
            if schema_retry or best is not None:
                break
            schema_retry, extra = True, SCHEMA_NOTE
            continue
        bad = [(i + 1, p) for i, s in enumerate(cand.giai_phap) if (p := solution_problem(s.hanh_dong, s.chi_so_theo_doi))]
        if best is None or len(bad) <= best_bad:
            best, best_bad = cand, len(bad)
        if bad and not fix_retry:
            fix_retry = True
            extra = FIX_NOTE.format(items="; ".join(f"giải pháp {i} ({p})" for i, p in bad))
            continue
        break
    if best is None:
        raise ApiError(502, "AI_BAD_OUTPUT", "Gemini trả về sai lược đồ JSON sau 2 lần gọi")
    out = best
    causes, keep_map, dropped = [], {}, 0
    for i, c in enumerate(out.nguyen_nhan[:5]):
        ids = [int(x) for x in c.id_bang_chung if int(x) in by_id]
        if not ids:
            dropped += 1; continue
        keep_map[i + 1] = len(causes)
        causes.append({"title": c.ten, "description": c.mo_ta, "severity": c.muc_do, "evidence_ids": ids, "evidence": _evidence(ids, by_id)})
    sols = [{"cause_index": keep_map[s.nguyen_nhan], "action": s.hanh_dong.strip(), "priority": s.uu_tien, "kpi": s.chi_so_theo_doi.strip()}
            for s in out.giai_phap if s.nguyen_nhan in keep_map]
    incomplete = mark_solutions(sols)
    note = (f"{incomplete} giải pháp vẫn thiếu ý sau khi gọi lại Gemini – cần người dùng đọc lại trước khi áp dụng" if incomplete else None)
    return {"model": model, "source": "gemini", "causes": causes, "solutions": sols, "dropped_causes": dropped, "note": note,
            "n_calls": n_calls, "incomplete_actions": incomplete}


def _strip_json(s: str) -> str:
    s = s.strip()
    if s.startswith("```"):
        s = re.sub(r"^```(json)?", "", s).rstrip("`").strip()
    return s


def _rule_insight(ctx: dict, note: str) -> dict:
    """Không có Gemini: nguyên nhân = chủ đề NMF chiếm tỷ trọng cao trong các đánh giá bằng chứng; giải pháp = bảng quy tắc FR-16."""
    by_id = {r["review_id"]: r for r in ctx["reviews"]}
    causes, sols = [], []
    if STATE.topic_model is not None and ctx["reviews"]:
        groups: dict[int, list] = {}
        for r in ctx["reviews"]:
            t = TS.transform(STATE.topic_model, STATE.topics, f"{r['summary']} . {r['text']}")
            if t:
                groups.setdefault(t["topic_id"], []).append((t["weight"], r["review_id"]))
        order = sorted(groups.items(), key=lambda kv: -len(kv[1]))
        if ctx["scope"] == "topic":
            order = order[:1] if order else []
        n = max(len(ctx["reviews"]), 1)
        # sản phẩm có < 5 đánh giá 1–2 sao thì đã gửi kèm đánh giá 3 sao (mục 5.6): gọi đúng tên, không gọi chung là “tiêu cực”
        label = "đánh giá tiêu cực" if all(r["score"] <= 2 for r in ctx["reviews"]) else "đánh giá 1–3 sao"
        for tid, items in order[:4]:
            t = STATE.topics[tid]; share = len(items) / n
            ids = [i for _, i in sorted(items, reverse=True)[:3]]
            n_neg = sum(by_id[i]["score"] <= 2 for _, i in items)
            sev = "cao" if share >= 0.35 else ("trung bình" if share >= 0.15 else "thấp")
            if n_neg == 0:                                  # chỉ có đánh giá 3 sao: không xếp mức nghiêm trọng cao
                sev = "thấp"
            causes.append({"title": t["name"], "description": f"{len(items)}/{n} {label} được gửi phân tích thuộc chủ đề này"
                           f"{'' if label == 'đánh giá tiêu cực' else f' ({n_neg} đánh giá 1–2 sao)'} "
                           f"(từ khóa: {', '.join(t['keywords'][:5])}).", "severity": sev, "evidence_ids": ids, "evidence": _evidence(ids, by_id)})
            sols.append({"cause_index": len(causes) - 1, "action": t["suggestion"], "priority": sev,
                         "kpi": "Tỷ lệ đánh giá 1–2 sao thuộc chủ đề này theo tháng; điểm TB 3 tháng"})
    mark_solutions(sols)
    return {"model": "quy tắc (chủ đề NMF + bảng gợi ý FR-16)", "source": "rule", "causes": causes, "solutions": sols,
            "dropped_causes": 0, "note": note, "n_calls": 0, "incomplete_actions": 0}


def _with_quality(res: dict) -> dict:
    """Kết quả lưu đệm từ phiên bản trước chưa có cờ độ đầy đủ: kiểm tra lại khi đọc (không gọi Gemini)."""
    sols = [dict(s) for s in res.get("solutions", [])]
    bad = mark_solutions(sols)
    res = {**res, "solutions": sols, "incomplete_actions": bad}
    if bad and res.get("source") == "gemini" and not res.get("note"):
        res["note"] = f"{bad} giải pháp thiếu ý trong kết quả đã lưu – bấm “Gọi lại” để Gemini viết lại"
    return res


def insights(scope: str, sid: str, refresh: bool) -> dict:
    _require_data()
    sid = sid.strip().upper() if scope == "product" else sid.strip()   # “b00507a02q” và “B00507A02Q” dùng chung một mục lưu đệm
