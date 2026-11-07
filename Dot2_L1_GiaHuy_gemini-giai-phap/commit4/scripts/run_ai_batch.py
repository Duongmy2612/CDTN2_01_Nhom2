"""Chạy trợ lý AI hàng loạt (sprint xây dựng 1, PB-19): phân tích nguyên nhân – giải pháp bằng Gemini cho mọi sản phẩm
rủi ro Cao và mọi chủ đề phàn nàn, lưu bộ đệm (FR-28), kiểm tra lại từng kết quả và chuẩn bị bảng chấm điểm NFR-10 (E-A2).

Điều kiện: backend đã xử lý dữ liệu ít nhất một lần (có backend/data/processed) và backend/.env có GEMINI_API_KEY.
Chạy từ thư mục gốc dự án:
    python scripts/run_ai_batch.py               # mục nào đã có trong bộ đệm thì đọc lại, không gọi Gemini
    python scripts/run_ai_batch.py --refresh     # gọi lại Gemini cho tất cả
    python scripts/run_ai_batch.py --limit 5     # chạy thử 5 sản phẩm đầu + các chủ đề
Kết quả ghi vào docs/ai_batch/:
    ai_batch_<ngày>.json   – từng kết quả: nguồn, model, số lần gọi, bằng chứng hợp lệ, giải pháp thiếu ý, thời gian, lỗi
    ai_batch_<ngày>.md     – bảng tóm tắt để dán vào báo cáo
    nfr10_cham_diem_<ngày>.csv – 30 kết quả (21 sản phẩm chọn ngẫu nhiên + 9 chủ đề), mỗi nguyên nhân một dòng kèm nguyên văn
                             bằng chứng; hai người chấm điền cột nguoi_cham_1, nguoi_cham_2 (1 = khớp, 0 = không khớp),
                             rồi chạy scripts/nfr10_score.py để tính tỷ lệ khớp và Cohen's κ.
Mã thoát: 0 = mọi mục chạy được bằng Gemini và không có lỗi lược đồ; 1 = có lỗi; 2 = chưa cấu hình khóa.
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv  # noqa: E402

from backend.core import config as C  # noqa: E402

load_dotenv(C.BASE_DIR / ".env")

from backend.core.errors import ApiError  # noqa: E402
from backend.core.state import STATE  # noqa: E402
from backend.services import ai_service as AI  # noqa: E402

N_GRADE_PRODUCTS = 21          # E-A2: 21 sản phẩm rủi ro Cao chọn ngẫu nhiên + 9 chủ đề = 30 kết quả


def targets(limit: int | None = None) -> list[tuple[str, str]]:
    p = STATE.products
    high = p[p.risk_level == "high"].sort_values(["delta", "neg_rate_3m"], ascending=[True, False], na_position="last")
    pids = high.product_id.tolist()[: limit or None]
    return [("product", pid) for pid in pids] + [("topic", str(t["topic_id"])) for t in (STATE.topics or [])]


def verify(res: dict, scope: str, sid: str) -> dict:
    """Kiểm tra lại độc lập với AIService: mã bằng chứng có trong dữ liệu sạch và thuộc đúng sản phẩm / chủ đề."""
    df = STATE.df.set_index("review_id")
    ids = [i for c in res.get("causes", []) for i in c["evidence_ids"]]
    exist = [i for i in ids if i in df.index]
    if scope == "product":
        right = [i for i in exist if df.at[i, "product_id"] == sid]
    else:
        rt = STATE.review_topics
        in_topic = set(rt.loc[rt.topic_id == int(sid), "review_id"])
        right = [i for i in exist if i in in_topic]
    return {"n_evidence": len(ids), "n_evidence_valid": len(right)}


def run(refresh: bool = False, delay: float = 1.0, limit: int | None = None, out_dir: Path | None = None,
        allow_rule: bool = False) -> dict:
    if not STATE.dataset_loaded:
        STATE.load_from_disk()
    if not STATE.dataset_loaded:
        raise SystemExit("Chưa có dữ liệu đã xử lý – hãy chạy backend và tải dữ liệu trước")
    if not AI.configured() and not allow_rule:
        print("Chưa cấu hình GEMINI_API_KEY trong backend/.env – không chạy được trợ lý AI bằng Gemini", file=sys.stderr)
        raise SystemExit(2)
    out_dir = Path(out_dir or ROOT / "docs" / "ai_batch"); out_dir.mkdir(parents=True, exist_ok=True)
    rows, results = [], {}
    tg = targets(limit)
    for k, (scope, sid) in enumerate(tg, 1):
        t0 = time.time(); err = None; res = None
        try:
            res = AI.insights(scope, sid, refresh)
        except ApiError as e:
            err = e.detail.get("code") if isinstance(e.detail, dict) else str(e.detail)
        except Exception as e:  # noqa: BLE001 – một mục lỗi không dừng cả lượt chạy
            err = f"{type(e).__name__}: {str(e)[:120]}"
        row = {"scope": scope, "id": sid, "error": err, "seconds": round(time.time() - t0, 2)}
        if res:
            results[f"{scope}|{sid}"] = res
            row.update({"title": res.get("title"), "source": res["source"], "model": res.get("model"), "cached": res.get("cached", False),
                        "n_calls": res.get("n_calls"), "n_causes": len(res["causes"]), "dropped_causes": res.get("dropped_causes", 0),
                        "incomplete_actions": res.get("incomplete_actions", 0), "latency_ms": res.get("latency_ms"),
                        **verify(res, scope, sid)})
        rows.append(row)
        flag = err or (f"{row['source']}, {row['n_causes']} nguyên nhân, {row['n_evidence_valid']}/{row['n_evidence']} bằng chứng hợp lệ"
                       f"{', ' + str(row['incomplete_actions']) + ' giải pháp thiếu ý' if row['incomplete_actions'] else ''}")
        print(f"[{k:>2}/{len(tg)}] {scope:<7} {sid:<11} {flag}")
        if res is not None and not res.get("cached") and k < len(tg):
            time.sleep(delay)                       # tránh vượt hạn mức số lần gọi/phút của khóa miễn phí
    summary = summarize(rows)
    stamp = time.strftime("%Y%m%d")
    base = out_dir / f"ai_batch_{stamp}"
    base.with_suffix(".json").write_text(json.dumps({"summary": summary, "rows": rows}, ensure_ascii=False, indent=1), encoding="utf-8")
    base.with_suffix(".md").write_text(to_markdown(summary, rows), encoding="utf-8")
    write_grading_csv(results, out_dir / f"nfr10_cham_diem_{stamp}.csv")
    print("\n" + to_markdown(summary, [])[:900])
    return summary


def summarize(rows: list[dict]) -> dict:
    ok = [r for r in rows if not r["error"]]
    gem = [r for r in ok if r.get("source") == "gemini"]
    ev = sum(r["n_evidence"] for r in ok); ev_ok = sum(r["n_evidence_valid"] for r in ok)
    lat = sorted(r["latency_ms"] for r in gem if r.get("latency_ms") is not None and not r.get("cached"))
    errors: dict[str, int] = {}
    for r in rows:
        if r["error"]:
            errors[r["error"]] = errors.get(r["error"], 0) + 1
    return {"date": time.strftime("%Y-%m-%d %H:%M"), "dataset_version": STATE.version, "n_targets": len(rows),
            "n_products": sum(r["scope"] == "product" for r in rows), "n_topics": sum(r["scope"] == "topic" for r in rows),
            "n_gemini": len(gem), "n_rule": sum(r.get("source") == "rule" for r in ok), "errors": errors,
            "n_causes": sum(r["n_causes"] for r in ok), "dropped_causes": sum(r["dropped_causes"] for r in ok),
            "evidence_valid_pct": round(100 * ev_ok / ev, 1) if ev else None, "n_evidence": ev,
            "retried": sum((r.get("n_calls") or 0) > 1 for r in gem), "incomplete_actions": sum(r["incomplete_actions"] for r in ok),
            "latency_mean_s": round(sum(lat) / len(lat) / 1000, 1) if lat else None,
            "latency_max_s": round(lat[-1] / 1000, 1) if lat else None,
            "models": sorted({r["model"] for r in gem if r.get("model")})}


def to_markdown(s: dict, rows: list[dict]) -> str:
    err = ", ".join(f"{k}: {v}" for k, v in s["errors"].items()) or "0"
    out = [f"# Chạy trợ lý AI hàng loạt – {s['date']} (dữ liệu {s['dataset_version']})", "",
           "| Chỉ số | Kết quả |", "|---|---|",
           f"| Số mục chạy | {s['n_targets']} ({s['n_products']} sản phẩm rủi ro Cao, {s['n_topics']} chủ đề) |",
           f"| Chạy bằng Gemini | {s['n_gemini']}/{s['n_targets']} – model {', '.join(s['models']) or '–'} |",
           f"| Lỗi (mã: số mục) | {err} |",
           f"| Nguyên nhân / bị loại vì bằng chứng sai | {s['n_causes']} / {s['dropped_causes']} |",
           f"| Bằng chứng hợp lệ (kiểm tra độc lập) | {s['evidence_valid_pct']}% của {s['n_evidence']} mã |",
           f"| Phải gọi lại vì giải pháp thiếu ý | {s['retried']} mục |",
           f"| Giải pháp vẫn thiếu ý sau khi gọi lại | {s['incomplete_actions']} |",
           f"| Thời gian trả lời Gemini (TB / lớn nhất) | {s['latency_mean_s']} s / {s['latency_max_s']} s |", ""]
    if rows:
        out += ["| # | Phạm vi | Mã | Nguồn | Gọi | Nguyên nhân | Bằng chứng hợp lệ | Thiếu ý | Thời gian (s) | Lỗi |",
                "|---|---|---|---|---|---|---|---|---|---|"]
        for i, r in enumerate(rows, 1):
            if r["error"]:
                out.append(f"| {i} | {r['scope']} | {r['id']} | – | – | – | – | – | {r['seconds']} | {r['error']} |")
            else:
                lat = "đệm" if r["cached"] else (round(r["latency_ms"] / 1000, 1) if r.get("latency_ms") else "–")
                out.append(f"| {i} | {r['scope']} | {r['id']} | {r['source']} | {r['n_calls']} | {r['n_causes']} | "
                           f"{r['n_evidence_valid']}/{r['n_evidence']} | {r['incomplete_actions']} | {lat} | |")
    return "\n".join(out) + "\n"


def write_grading_csv(results: dict, path: Path) -> int:
    """30 kết quả cho E-A2: chọn ngẫu nhiên 21 sản phẩm (random_state = 42) + toàn bộ chủ đề; mỗi nguyên nhân một dòng."""
    prods = sorted(k for k, v in results.items() if k.startswith("product|") and v["source"] == "gemini")
    topics = sorted((k for k, v in results.items() if k.startswith("topic|") and v["source"] == "gemini"), key=lambda k: int(k.split("|")[1]))
    pick = sorted(random.Random(C.RANDOM_STATE).sample(prods, min(N_GRADE_PRODUCTS, len(prods)))) + topics
    n = 0
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f)
        w.writerow(["ma_ket_qua", "stt_nguyen_nhan", "nguyen_nhan", "mo_ta", "muc_do", "ma_bang_chung", "nguyen_van_bang_chung",
                    "nguoi_cham_1", "nguoi_cham_2", "ghi_chu"])
        for key in pick:
            for i, c in enumerate(results[key]["causes"], 1):
                ev = " || ".join(f"#{e['review_id']} ({e['score']}★) {e['summary']}: {e.get('text') or ''}" for e in c["evidence"])
                w.writerow([key, i, c["title"], c["description"], c["severity"], " ".join(map(str, c["evidence_ids"])), ev, "", "", ""])
                n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--refresh", action="store_true", help="bỏ qua bộ đệm, gọi lại Gemini cho mọi mục")
    ap.add_argument("--delay", type=float, default=1.0, help="số giây nghỉ giữa hai lần gọi Gemini (mặc định 1)")
    ap.add_argument("--limit", type=int, default=None, help="chỉ chạy N sản phẩm đầu (chạy thử)")
    ap.add_argument("--out", type=Path, default=None, help="thư mục ghi kết quả (mặc định docs/ai_batch)")
    a = ap.parse_args()
    s = run(a.refresh, a.delay, a.limit, a.out)
    sys.exit(0 if not s["errors"] and s["n_gemini"] == s["n_targets"] else 1)


if __name__ == "__main__":
    main()
