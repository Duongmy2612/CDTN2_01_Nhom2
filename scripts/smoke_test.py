"""Chạy thử toàn bộ hệ thống sau khi cài (sprint xây dựng 2 – buổi 7, NFR-08, PB-17 làm sớm).

Gọi lần lượt các API mà giao diện dùng, qua đúng địa chỉ người dùng mở trình duyệt, để chứng minh các mô-đun đã
ghép thành một hệ thống chạy được – không chỉ chạy riêng từng phần:

    python scripts/smoke_test.py                                  # gọi thẳng backend http://localhost:8000
    python scripts/smoke_test.py --base http://localhost:5173     # đi qua frontend (proxy Vite → backend, như Docker)
    python scripts/smoke_test.py --kind full --install-minutes 9.5 # dùng toàn bộ Reviews.csv, ghi thời gian cài đã đo

Nếu backend chưa có dữ liệu, script dùng bộ dữ liệu có sẵn trên máy chủ (mẫu 100.000 dòng hoặc Reviews.csv) và chờ
job nền 7 bước. Không gọi /api/upload, /api/session/reset (không làm mất dữ liệu đang dùng) và mặc định không gọi
Gemini (/api/ai/insights, /api/chat tốn hạn mức) – thêm --with-ai để gọi. Biên bản ghi vào
docs/test_report/smoke_<sample|full>_<ngày>.md; mã thoát 1 nếu có API lỗi.
"""
from __future__ import annotations

import argparse
import json
import platform
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPORT_TABLES = ["predictions", "product_risk", "topics", "monthly", "model_metrics", "forecast"]
EDA_CHARTS = ["score_dist", "monthly", "length_by_score", "keywords", "top_products"]
PREDICT_TEXT = "The coffee arrived stale and the box was crushed. Very disappointed, I will not buy this again."


def http_caller(base: str, timeout: float = 180):
    """Trả hàm call(method, path, params, body) → (status, content_type, bytes) gọi qua HTTP thật."""
    base = base.rstrip("/")

    def call(method: str, path: str, params: dict | None = None, body: dict | None = None):
        url = base + path + ("?" + urllib.parse.urlencode(params) if params else "")
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"} if data else {})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.status, r.headers.get("Content-Type", ""), r.read()
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get("Content-Type", ""), e.read()
    return call


def _n(x) -> str:
    """Số kiểu Việt Nam: 87.622"""
    return f"{x:,}".replace(",", ".")


def _json(b: bytes):
    try:
        return json.loads(b.decode("utf-8"))
    except Exception:  # noqa: BLE001
        return None


def ensure_data(call, kind: str, wait_s: float = 900, poll_s: float = 2.0) -> dict:
    """Backend chưa có dữ liệu → dùng bộ có sẵn trên máy chủ và chờ job nền xong. Trả thông tin để ghi biên bản."""
    st, _, b = call("GET", "/api/health")
    h = _json(b) or {}
    if st != 200:
        raise RuntimeError(f"Không gọi được /api/health (HTTP {st}) – backend chưa chạy hoặc proxy chưa nối được backend")
    if h.get("dataset_loaded"):
        return {"started_job": False, "health": h}
    st, _, b = call("POST", "/api/data/sample", {"kind": kind})
    if st != 202:
        raise RuntimeError(f"Không bắt đầu được job với dữ liệu '{kind}' (HTTP {st}): {b[:300]!r}")
    job_id = _json(b)["job_id"]
    t0 = time.perf_counter()
    while time.perf_counter() - t0 < wait_s:
        j = _json(call("GET", f"/api/jobs/{job_id}")[2]) or {}
        if j.get("status") in ("done", "failed"):
            break
        time.sleep(poll_s)
    if j.get("status") != "done":
        raise RuntimeError(f"Job {job_id} không xong: {j.get('status')} – {j.get('message')}")
    return {"started_job": True, "job_id": job_id, "job_seconds": round(time.perf_counter() - t0, 1),
            "steps": [(s["label"], s["seconds"]) for s in j.get("steps", [])], "health": _json(call("GET", "/api/health")[2])}


def checks(call, with_ai: bool = False) -> list[dict]:
    """Gọi các API của giao diện; mỗi dòng: API, trạng thái, thời gian, kết quả kiểm tra nhanh nội dung."""
    rows = []

    def run(name, method, path, params=None, body=None, expect=200, check=None, kind="json"):
        t0 = time.perf_counter()
        st, ctype, b = call(method, path, params, body)
        ms = round((time.perf_counter() - t0) * 1000)
        ok, note = st == expect, ""
        data = _json(b) if kind == "json" else None
        if ok and kind == "json" and data is None:
            ok, note = False, "không phải JSON"
        elif ok and kind == "pdf" and not b.startswith(b"%PDF"):
            ok, note = False, "không phải file PDF"
        elif ok and kind == "csv" and "csv" not in ctype:
            ok, note = False, f"Content-Type {ctype}"
        if ok and check:
            try:
                note = check(data) or ""
            except AssertionError as e:
                ok, note = False, str(e) or "nội dung sai"
        elif not ok and not note:
            err = (data or {}).get("error", {}) if isinstance(data, dict) else {}
            note = f"HTTP {st} {err.get('code', '')} {err.get('message', '')}".strip()
        rows.append({"api": name, "method": method, "path": path + ("?" + urllib.parse.urlencode(params) if params else ""),
                     "status": st, "ms": ms, "ok": ok, "note": note})
        return data

    def need(cond, msg):
        if not cond:
            raise AssertionError(msg)

    run("#1 health", "GET", "/api/health", check=lambda d: need(d["dataset_loaded"] and d["model_ready"], "chưa có dữ liệu/mô hình") or f"phiên bản {d['version']}")
    run("#5 data/quality", "GET", "/api/data/quality", check=lambda d: f"{_n(d['n_rows'])} dòng gốc → {_n(d['n_clean'])} sạch")
    k = run("#7 kpi", "GET", "/api/kpi", check=lambda d: f"{_n(d['n_reviews'])} đánh giá, chỉ số {d['satisfaction_index']}")
    for c in EDA_CHARTS:
        run(f"#8 eda/{c}", "GET", f"/api/eda/{c}", check=lambda d: need(d["data"], "không có dữ liệu") or f"{len(d['data'])} điểm")
    run("#9 topics", "GET", "/api/topics", check=lambda d: f"{len(d['topics'])} chủ đề")
    p = run("#10 products", "GET", "/api/products", {"sort": "risk", "page_size": 20}, check=lambda d: f"{_n(d['page']['total'])} sản phẩm")
    run("#11 model/metrics", "GET", "/api/model/metrics", check=lambda d: f"chọn {d['selected']}")
    run("#12 model/keywords", "GET", "/api/model/keywords", {"n": 15})
    run("#13 reviews/mismatch", "GET", "/api/reviews/mismatch", {"page_size": 8})
    run("#14 predict", "POST", "/api/predict", body={"text": PREDICT_TEXT},
        check=lambda d: need(d["sentiment"] == "neg", f"đánh giá chê bị đoán là {d['sentiment']}") or f"{d['pred_star']} sao, {d['latency_ms']} ms")
    run("#15 satisfaction", "GET", "/api/satisfaction", check=lambda d: f"{len(d['series'])} tháng")
    run("#16 forecast", "GET", "/api/forecast", {"months": 12}, check=lambda d: f"{d.get('model')}, {len(d['forecast'])} tháng dự báo")
    fp = run("#10 products (dự báo được)", "GET", "/api/products", {"forecastable": "true", "sort": "n_reviews", "page_size": 5})
    pid = (fp or {}).get("items", [{}])[0].get("product_id") if (fp or {}).get("items") else ((p or {}).get("items") or [{}])[0].get("product_id")
    if pid:
        run("#15 satisfaction (sản phẩm)", "GET", "/api/satisfaction", {"product_id": pid}, check=lambda d: f"{pid}: {len(d['series'])} tháng")
        run("#16 forecast (sản phẩm)", "GET", "/api/forecast", {"product_id": pid, "months": 6},
            check=lambda d: f"{pid}: {'dự báo được' if d['eligible'] else d['message']}")
        run("#9 topics (sản phẩm)", "GET", "/api/topics", {"product_id": pid})
    if with_ai:
        hi = ((p or {}).get("items") or [{}])[0].get("product_id")
        run("#17 ai/insights", "POST", "/api/ai/insights", body={"scope": "product", "id": hi, "refresh": False},
            check=lambda d: f"{len(d.get('causes', []))} nguyên nhân, {d.get('model')}")
        run("#18 chat", "POST", "/api/chat", body={"message": "Những sản phẩm nào đang rủi ro cao?", "history": []},
            check=lambda d: f"nguồn {d.get('source')}")
    run("#19 report/pdf", "GET", "/api/report/pdf", kind="pdf")
    for t in EXPORT_TABLES:
        run(f"#20 export/{t}", "GET", f"/api/export/{t}", kind="csv")
    return rows


def write_report(rows: list[dict], info: dict, base: str, kind: str, install_minutes: float | None, out_dir: Path) -> Path:
    n_ok = sum(r["ok"] for r in rows)
    h = info.get("health") or {}
    ds = h.get("dataset") or {}
    lines = [f"# Biên bản chạy thử toàn hệ thống – {datetime.now():%d/%m/%Y %H:%M}", "",
             f"- Địa chỉ gọi: `{base}` ({'qua frontend – proxy Vite tới backend' if ':5173' in base else 'gọi thẳng backend'})",
             f"- Máy chạy: {platform.system()} {platform.release()}, Python {platform.python_version()}",
             f"- Phiên bản hợp đồng API: {h.get('version')}; dữ liệu: {ds.get('file_name')} – {_n(ds.get('n_reviews') or 0)} đánh giá sạch"
             if ds.get("n_reviews") is not None else f"- Phiên bản hợp đồng API: {h.get('version')}"]
    if install_minutes is not None:
        lines.append(f"- Thời gian cài đặt đo được (NFR-08, ngưỡng 15 phút): **{install_minutes} phút** – "
                     f"{'Đạt' if install_minutes <= 15 else 'Không đạt'}")
    if info.get("started_job"):
        lines.append(f"- Job nền với dữ liệu `{kind}`: {info['job_seconds']} giây (" +
                     ", ".join(f"{a} {b} s" for a, b in info["steps"]) + ")")
    else:
        lines.append("- Backend đã có dữ liệu từ trước (nạp lại khi khởi động) – không chạy lại job nền")
    lines += ["", f"**Kết quả: {n_ok}/{len(rows)} lời gọi đạt.**", "",
              "| API | Lời gọi | HTTP | Thời gian (ms) | Kết quả | Ghi chú |", "|---|---|---|---|---|---|"]
    lines += [f"| {r['api']} | `{r['method']} {r['path']}` | {r['status']} | {_n(r['ms'])} | {'Đạt' if r['ok'] else '**Lỗi**'} | {r['note']} |"
              for r in rows]
    lines += ["", "Không gọi `/api/upload`, `/api/session/reset` (không làm mất dữ liệu đang dùng)"
              + ("." if any(r["api"].startswith("#17") for r in rows) else "; `/api/ai/insights`, `/api/chat` chỉ gọi khi thêm `--with-ai`."),
              "Tạo lại: `python scripts/smoke_test.py --base <địa chỉ> --kind <sample|full>`."]
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"smoke_{kind}_{datetime.now():%Y%m%d}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", default="http://localhost:8000", help="http://localhost:8000 (backend) hoặc http://localhost:5173 (qua frontend)")
    ap.add_argument("--kind", choices=["sample", "full"], default="sample", help="bộ dữ liệu dùng khi backend chưa có dữ liệu")
    ap.add_argument("--with-ai", action="store_true", help="gọi thêm /api/ai/insights và /api/chat (có thể tốn hạn mức Gemini)")
    ap.add_argument("--install-minutes", type=float, default=None, help="thời gian cài đặt đã đo bằng đồng hồ (NFR-08)")
    ap.add_argument("--out", default=str(ROOT / "docs" / "test_report"))
    a = ap.parse_args(argv)
    call = http_caller(a.base)
    info = ensure_data(call, a.kind)
    rows = checks(call, a.with_ai)
    path = write_report(rows, info, a.base, a.kind, a.install_minutes, Path(a.out))
    bad = [r for r in rows if not r["ok"]]
    print(f"{len(rows) - len(bad)}/{len(rows)} lời gọi đạt – biên bản: {path}")
    for r in bad:
        print(f"  LỖI {r['api']}: {r['note']}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
