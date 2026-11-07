"""Kiểm tra tích hợp: cùng một con số phải giống nhau trên mọi màn hình (sprint xây dựng 2 – buổi 7).

Bài giảng buổi 7: “frontend gọi đúng API backend, dữ liệu hiển thị nhất quán giữa các màn hình”. Mỗi màn hình đọc một
API khác nhau (Tổng quan #7, Phân tích #8, Sản phẩm #10, Dự báo #15/#16, Chủ đề #9, Mô hình #11, Tự nhập #14, Báo cáo #20),
nên script đọc cùng một chỉ số từ tất cả các nguồn đó và đối chiếu: số đánh giá, số sản phẩm, sản phẩm rủi ro cao,
F1-macro, chỉ số hài lòng, chuỗi theo tháng, dự báo, số đánh giá tiêu cực, số liệu của một sản phẩm.

    python scripts/integration_check.py                         # backend http://localhost:8000 đang có dữ liệu
    python scripts/integration_check.py --base http://localhost:5173 --kind full

Biên bản: docs/test_report/integration_<sample|full>_<ngày>.md; mã thoát 1 nếu có chỉ số lệch.
"""
from __future__ import annotations

import argparse
import csv
import io
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from smoke_test import _json, _n, http_caller  # noqa: E402  (cùng thư mục scripts/)


def _csv(b: bytes) -> list[dict]:
    return list(csv.DictReader(io.StringIO(b.decode("utf-8-sig"))))


def _fmt(v) -> str:
    if isinstance(v, bool) or v is None:
        return "không có" if v is None else str(v)
    if isinstance(v, int):
        return _n(v)
    if isinstance(v, float):
        return f"{v:g}".replace(".", ",")
    return str(v)


def _same(values: dict, tol: float = 0.0) -> bool:
    v = [x for x in values.values()]
    if any(x is None for x in v):
        return False
    if all(isinstance(x, (int, float)) for x in v):
        return max(v) - min(v) <= tol + 1e-9
    return len(set(map(str, v))) == 1


def run_checks(call) -> tuple[list[dict], dict]:
    """Trả (các dòng kiểm tra, thông tin dữ liệu). call(method, path, params, body) → (status, content_type, bytes)."""
    def get(path, params=None):
        st, _, b = call("GET", path, params)
        if st != 200:
            raise RuntimeError(f"{path} {params or ''} → HTTP {st}: {b[:200]!r}")
        return _json(b)

    def get_csv(table):
        st, _, b = call("GET", f"/api/export/{table}")
        if st != 200:
            raise RuntimeError(f"/api/export/{table} → HTTP {st}")
        return _csv(b)

    rows: list[dict] = []

    def add(group, check, values, tol=0.0):
        rows.append({"group": group, "check": check, "values": values, "ok": _same(values, tol)})

    h = get("/api/health"); ds = h["dataset"] or {}
    k = get("/api/kpi"); q = get("/api/data/quality")
    dist = get("/api/eda/score_dist")["data"]; mon = get("/api/eda/monthly")["data"]
    sat = get("/api/satisfaction")["series"]; fc = get("/api/forecast", {"months": 12})
    prod = get("/api/products", {"sort": "risk", "page_size": 5})
    mm = get("/api/model/metrics"); tp = get("/api/topics")
    ex_month, ex_risk, ex_model = get_csv("monthly"), get_csv("product_risk"), get_csv("model_metrics")
    ex_fc, ex_topic = get_csv("forecast"), get_csv("topics")
    lf = ds.get("last_full_month")

    # 1. Số đánh giá sạch – thanh tiêu đề, Tổng quan, Phân tích, Dự báo, Sản phẩm, Báo cáo
    add("Số đánh giá sạch", "Cùng một tổng trên 8 nguồn", {
        "Thanh tiêu đề (#1)": ds.get("n_reviews"), "Tổng quan KPI (#7)": k["n_reviews"], "Chất lượng dữ liệu (#5)": q["n_clean"],
        "Phân bố số sao (#8)": sum(d["n"] for d in dist), "Số đánh giá theo tháng (#8)": sum(d["n"] for d in mon),
        "Chỉ số theo tháng (#15)": sum(d["n"] for d in sat), "CSV monthly (#20)": sum(int(r["n"]) for r in ex_month),
        "CSV product_risk (#20)": sum(int(r["n_reviews"]) for r in ex_risk)})
    # 2. Số sản phẩm
    add("Số sản phẩm", "Tổng quan, Sản phẩm & cảnh báo, CSV", {
        "Thanh tiêu đề (#1)": ds.get("n_products"), "Tổng quan KPI (#7)": k["n_products"],
        "Sản phẩm & cảnh báo (#10)": prod["page"]["total"], "Σ các mức rủi ro (#10)": sum(prod["counts"].values()),
        "CSV product_risk (#20)": len(ex_risk)})
    # 3. Sản phẩm rủi ro cao
    add("Sản phẩm rủi ro cao", "KPI Tổng quan = bảng Sản phẩm = CSV", {
        "Tổng quan KPI (#7)": k["n_high_risk_products"], "Đếm mức (#10)": prod["counts"].get("high", 0),
        "Lọc rủi ro cao (#10)": get("/api/products", {"risk": "high", "page_size": 5})["page"]["total"],
        "CSV product_risk (#20)": sum(r["risk_level"] == "high" for r in ex_risk)})
    add("Sản phẩm rủi ro cao", "Cùng mốc thời gian “tính đến”", {
        "Thanh tiêu đề (#1)": lf, "Tổng quan KPI (#7)": k["last_full_month"], "Sản phẩm (#10)": prod["as_of"],
        "CSV product_risk (#20)": ex_risk[0]["as_of"] if ex_risk else None})
    # 4. Mô hình
    sel = next(m for m in mm["models"] if m["selected"])
    add("Mô hình", "F1-macro của mô hình chọn", {
        "Tổng quan KPI (#7)": k["model_f1_macro"], "Mô hình ML (#11)": sel["f1_macro3"],
        "CSV model_metrics (#20)": next(float(r["f1_macro3"]) for r in ex_model if r["selected"] == "True")}, tol=1e-4)
    p = call("POST", "/api/predict", None, {"text": "The coffee arrived stale and the box was crushed, very disappointed"})
    add("Mô hình", "Tự nhập dự đoán dùng đúng mô hình chọn", {
        "Mô hình ML (#11)": mm["selected"], "Tự nhập dự đoán (#14)": (_json(p[2]).get("model_info") or {}).get("model")})
    # 5. Chỉ số hài lòng
    w = sum(d["n"] * d["avg_score"] for d in sat) / max(sum(d["n"] for d in sat), 1)
    add("Chỉ số hài lòng", "Toàn kỳ: KPI = công thức (TB − 1)/4 × 100 = bình quân theo tháng", {
        "Tổng quan KPI (#7)": k["satisfaction_index"], "Công thức từ điểm TB (#7)": round((k["avg_score"] - 1) / 4 * 100, 2),
        "Bình quân gia quyền chuỗi tháng (#15)": round((w - 1) / 4 * 100, 2)}, tol=0.02)
    hist = {d["month"]: d for d in fc["history"]}
    s_by = {d["month"]: d for d in sat}; e_by = {r["month"]: r for r in ex_month}
    diff = [m for m, d in hist.items() if m not in s_by or abs(s_by[m]["sat_index"] - d["sat_index"]) > 0.01 or s_by[m]["n"] != d["n"]
            or m not in e_by or abs(float(e_by[m]["sat_index"]) - d["sat_index"]) > 0.01]
    add("Chỉ số hài lòng", f"{len(hist)} tháng của Tổng quan/Dự báo (#16) khớp từng tháng với #15 và CSV monthly",
        {"Số tháng lệch": len(diff), "Kỳ vọng": 0})
    add("Chỉ số hài lòng", "Tháng cuối của chuỗi dự báo là tháng trọn vẹn cuối", {
        "Thanh tiêu đề (#1)": lf, "Dự báo – tháng cuối thực tế (#16)": fc["history"][-1]["month"] if fc["history"] else None})
    partial = [d["month"] for d in mon if d.get("partial")]
    add("Chỉ số hài lòng", "Tab Phân tích đánh dấu đúng tháng chưa trọn (sau tháng trọn vẹn cuối)", {
        "Tháng có partial (#8)": ",".join(partial) or "không có", "Tháng sau last_full_month": ",".join(m for m in (d["month"] for d in mon) if m > lf) or "không có"})
    # 6. Dự báo
    add("Dự báo", "12 tháng dự báo: Tổng quan/Dự báo (#16) = CSV forecast (#20)", {
        "Số tháng lệch": sum(abs(a["sat_index"] - float(b["sat_index"])) > 0.01 or a["month"] != b["month"] for a, b in zip(fc["forecast"], ex_fc))
        + abs(len(fc["forecast"]) - len(ex_fc)), "Kỳ vọng": 0})
    # 7. Đánh giá tiêu cực, chủ đề
    kn = get("/api/kpi", {"sentiment": "neg"})
    add("Đánh giá tiêu cực", "Tổng quan, Phân tích, Chủ đề phàn nàn (đếm chính xác)", {
        "Lọc Tiêu cực (#7)": kn["n_reviews"], "Chủ đề – n_negative (#9)": tp["n_negative"],
        "Σ chủ đề + chưa xếp (#9)": sum(t["n_reviews"] for t in tp["topics"]) + (tp.get("n_unassigned") or 0)})
    add("Đánh giá tiêu cực", "Tỷ lệ tiêu cực ở Tổng quan (làm tròn 4 chữ số) × số đánh giá", {
        "Lọc Tiêu cực (#7)": kn["n_reviews"], "Tỷ lệ × số đánh giá (#7)": round(k["neg_rate"] * k["n_reviews"])}, tol=max(1, k["n_reviews"] // 20000))
    t_by = {str(t["topic_id"]): t["n_reviews"] for t in tp["topics"]}
    add("Đánh giá tiêu cực", "Số đánh giá từng chủ đề: tab Chủ đề (#9) = CSV topics (#20)", {
        "Số chủ đề lệch": sum(t_by.get(r["topic_id"]) != int(r["n_reviews"]) for r in ex_topic) + abs(len(t_by) - len(ex_topic)), "Kỳ vọng": 0})
    # 8. Một sản phẩm cụ thể – ngăn chi tiết, Phân tích lọc theo mã, Tự nhập dự đoán kèm mã, Chủ đề của sản phẩm
    row = (prod["items"] or get("/api/products", {"sort": "n_reviews", "page_size": 5})["items"])[0]
    pid = row["product_id"]
    kp = get("/api/kpi", {"product_id": pid}); sp = get("/api/satisfaction", {"product_id": pid})["series"]
    pr = _json(call("POST", "/api/predict", None, {"text": "Stale and tasteless, the package was damaged on arrival", "product_id": pid})[2])
    ctx = pr.get("product") or {}
    add(f"Sản phẩm {pid}", "Số đánh giá: bảng Sản phẩm, Phân tích lọc mã, chuỗi tháng, Tự nhập dự đoán", {
        "Sản phẩm (#10)": row["n_reviews"], "Phân tích lọc mã (#7)": kp["n_reviews"], "Chỉ số theo tháng (#15)": sum(d["n"] for d in sp),
        "Tự nhập dự đoán (#14)": ctx.get("n_reviews")})
    add(f"Sản phẩm {pid}", "Điểm TB: bảng Sản phẩm, Phân tích lọc mã, Tự nhập dự đoán", {
        "Sản phẩm (#10)": round(row["avg_score"], 3), "Phân tích lọc mã (#7)": round(kp["avg_score"], 3),
        "Tự nhập dự đoán (#14)": round(ctx["avg_score"], 3) if ctx else None}, tol=0.001)
    tpp = get("/api/topics", {"product_id": pid}) if kp["neg_rate"] > 0 else {"n_negative": 0}
    add(f"Sản phẩm {pid}", "Số đánh giá tiêu cực: Phân tích lọc mã + Tiêu cực, Chủ đề của sản phẩm", {
        "Phân tích (#7)": get("/api/kpi", {"product_id": pid, "sentiment": "neg"})["n_reviews"], "Chủ đề (#9)": tpp["n_negative"]})
    info = {"health": h, "product_id": pid}
    return rows, info


def write_report(rows: list[dict], info: dict, base: str, kind: str, out_dir: Path) -> Path:
    ds = (info["health"] or {}).get("dataset") or {}
    n_ok = sum(r["ok"] for r in rows)
    lines = [f"# Biên bản kiểm tra tích hợp – số liệu nhất quán giữa các màn hình ({datetime.now():%d/%m/%Y %H:%M})", "",
             f"- Địa chỉ gọi: `{base}`; hợp đồng API {info['health'].get('version')}",
             f"- Dữ liệu: {ds.get('file_name')} – {_n(ds.get('n_reviews') or 0)} đánh giá sạch, {_n(ds.get('n_products') or 0)} sản phẩm, "
             f"tháng trọn vẹn cuối {ds.get('last_full_month')}",
             f"- Sản phẩm dùng để đối chiếu: {info['product_id']} (đứng đầu tab Sản phẩm & cảnh báo)", "",
             f"**Kết quả: {n_ok}/{len(rows)} kiểm tra khớp.**", "",
             "| Nhóm | Kiểm tra | Giá trị trên từng màn hình / API | Kết quả |", "|---|---|---|---|"]
    for r in rows:
        vals = "<br>".join(f"{k}: **{_fmt(v)}**" for k, v in r["values"].items())
        lines.append(f"| {r['group']} | {r['check']} | {vals} | {'Khớp' if r['ok'] else '**Lệch**'} |")
    lines += ["", "Số trong ngoặc là số thứ tự API trong hợp đồng (docs/openapi.json). Tạo lại: "
              "`python scripts/integration_check.py --base <địa chỉ> --kind <sample|full>`."]
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"integration_{kind}_{datetime.now():%Y%m%d}.md"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--kind", choices=["sample", "full"], default="sample", help="chỉ để đặt tên biên bản theo bộ dữ liệu đang dùng")
    ap.add_argument("--out", default=str(ROOT / "docs" / "test_report"))
    a = ap.parse_args(argv)
    call = http_caller(a.base)
    if not (_json(call("GET", "/api/health")[2]) or {}).get("dataset_loaded"):
        print("Backend chưa có dữ liệu – mở giao diện chọn bộ mẫu (hoặc chạy scripts/smoke_test.py) rồi chạy lại.")
        return 1
    rows, info = run_checks(call)
    path = write_report(rows, info, a.base, a.kind, Path(a.out))
    bad = [r for r in rows if not r["ok"]]
    print(f"{len(rows) - len(bad)}/{len(rows)} kiểm tra khớp – biên bản: {path}")
    for r in bad:
        print(f"  LỆCH {r['group']} – {r['check']}: {r['values']}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
