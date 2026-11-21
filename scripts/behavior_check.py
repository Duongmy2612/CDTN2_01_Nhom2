"""Kiểm thử hành vi mô hình dự đoán theo kiểu CheckList (buổi 8 – kiểm thử và tinh chỉnh, phần mô hình – KAYSONE Souk Anong).

F1-macro trên tập kiểm tra chỉ cho biết mô hình đúng bao nhiêu phần trăm, không cho biết SAI Ở ĐÂU. Script này gửi các câu
tự viết, biết trước đáp án, tới API #14 (/api/predict) đang chạy để soi đúng các năng lực mà người dùng sẽ thử khi demo:

- MFT (minimum functionality test): 15 câu ngắn, mỗi câu kiểm một năng lực (khen/chê rõ, phủ định, đảo ý, mỉa mai, giao hàng,
  thú cưng, giá, viết hoa, lỗi chính tả, ngoài phạm vi tiếng Việt) – câu tiếng Việt phải bị TỪ CHỐI (TEXT_NOT_RECOGNIZED).
- INV (invariance): đổi một chi tiết không liên quan (tên món, con số, thẻ HTML, khoảng trắng) thì cảm xúc không được đổi.
- DIR (directional): thêm một câu chê/khen rõ thì xác suất tiêu cực/tích cực phải tăng (hoặc không giảm).

    python scripts/behavior_check.py                                   # backend http://localhost:8000
    python scripts/behavior_check.py --base http://localhost:8020 --tag v1.4.0 --no-save

Biên bản: docs/test_report/behavior_<ngày>.md|json. Mã thoát luôn là 0 (đây là đánh giá, không phải kiểm thử chặn CI):
câu sai được ghi thành hạn chế đã biết trong báo cáo buổi 8.
"""
from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REJECT = "TEXT_NOT_RECOGNIZED"

MFT = [
    ("Cơ bản – khen rõ", "This coffee is delicious, fresh and I will buy it again.", "pos"),
    ("Cơ bản – chê rõ", "Terrible taste, stale and the box arrived crushed. Never again.", "neg"),
    ("Cơ bản – trung tính", "It is okay, nothing special, average taste for the price.", "neu"),
    ("Phủ định – not bad", "Not bad at all, actually pretty tasty and my kids liked it.", "pos"),
    ("Phủ định – not good", "This tea is not good, not fresh and not worth the money.", "neg"),
    ("Phủ định – no complaints", "No complaints, arrived quickly and tastes great.", "pos"),
    ("Đảo ý – khen rồi chê", "Great flavor but the bag arrived torn and half of the chips were stale.", "neg"),
    ("Đảo ý – chê rồi khen", "Shipping was slow, but the cookies are the best I have ever had.", "pos"),
    ("Mỉa mai", "Oh great, another box of stale crackers. Just what I wanted.", "neg"),
    ("Giao hàng (không phải sản phẩm)", "The product itself is fine but Amazon shipping took three weeks.", "neu"),
    ("Thú cưng bị bệnh", "My dog got sick after eating these treats, please be careful.", "neg"),
    ("Giá cao", "Tastes fine but way overpriced compared to my local grocery store.", "neu"),
    ("Viết hoa, dấu câu", "AWESOME!!! BEST CHOCOLATE EVER!!!", "pos"),
    ("Lỗi chính tả", "teh cofee was horible and tastd burnt", "neg"),
    ("Ngoài phạm vi – tiếng Việt", "Cà phê rất dở, hộp bị móp và giao hàng trễ", REJECT),
]

INV = [
    ("Đổi tên món", "This coffee is delicious and fresh, I will order it again.", "This granola is delicious and fresh, I will order it again."),
    ("Đổi con số", "Bought 2 bags, both were stale and tasted awful.", "Bought 6 bags, both were stale and tasted awful."),
    ("Thêm thẻ HTML", "Great snack for the kids. Will buy again.", "Great snack for the kids.<br /><br />Will buy again."),
    ("Thêm đường dẫn", "The tea tastes like dust, very disappointed.", "The tea tastes like dust, very disappointed. http://www.amazon.com/dp/B000ABC"),
    ("Khoảng trắng, xuống dòng", "Too sweet and the texture is weird.", "Too   sweet\n\nand the texture   is weird."),
]

DIR = [
    ("Thêm câu chê → P(tiêu cực) tăng", "The cookies taste nice and arrived on time.",
     "The cookies taste nice and arrived on time. But two packs were moldy.", "neg"),
    ("Thêm câu khen → P(tích cực) tăng", "The sauce is a little salty.",
     "The sauce is a little salty. Still, my whole family loves it and we reorder every month.", "pos"),
    ("Thêm 'never again' → P(tiêu cực) tăng", "The chips were okay I suppose.",
     "The chips were okay I suppose. Never again.", "neg"),
]


def predict(base: str, text: str) -> dict:
    req = urllib.request.Request(base.rstrip("/") + "/api/predict", data=json.dumps({"text": text}).encode(),
                                 headers={"content-type": "application/json"})
    try:
        r = json.loads(urllib.request.urlopen(req, timeout=60).read())
        return {"label": r["sentiment"], "star": r["pred_star"], "proba": r["sentiment_proba"],
                "conf": max(r["sentiment_proba"].values()), "known": r.get("known_token_ratio"), "low": r.get("low_confidence")}
    except urllib.error.HTTPError as e:
        body = json.loads(e.read() or b"{}")
        return {"label": (body.get("error") or {}).get("code", f"HTTP {e.code}"), "status": e.code}


def run(base: str) -> dict:
    mft = []
    for name, text, want in MFT:
        p = predict(base, text)
        mft.append({"case": name, "text": text, "want": want, **p, "ok": p["label"] == want})
    inv = []
    for name, a, b in INV:
        pa, pb = predict(base, a), predict(base, b)
        inv.append({"case": name, "a": a, "b": b, "label_a": pa["label"], "label_b": pb["label"],
                    "delta": round(abs(pa.get("conf", 0) - pb.get("conf", 0)), 4) if pa["label"] == pb["label"] else None,
                    "ok": pa["label"] == pb["label"]})
    dirr = []
    for name, a, b, side in DIR:
        pa, pb = predict(base, a), predict(base, b)
        before, after = pa["proba"][side], pb["proba"][side]
        dirr.append({"case": name, "a": a, "b": b, "side": side, "p_before": before, "p_after": after, "ok": after >= before - 0.01})
    return {"mft": mft, "inv": inv, "dir": dirr}


def to_markdown(res: dict, base: str, tag: str) -> str:
    n = lambda xs: f"{sum(x['ok'] for x in xs)}/{len(xs)}"   # noqa: E731
    lines = [f"# Kiểm thử hành vi mô hình (CheckList) – {tag}", "",
             f"Ngày chạy: {datetime.now():%d/%m/%Y %H:%M} · máy chủ {base}", "",
             f"Tổng hợp: MFT {n(res['mft'])} · INV {n(res['inv'])} · DIR {n(res['dir'])}", "",
             "## MFT – năng lực tối thiểu", "", "| Ca | Cần | Được | Sao | Tự tin | Từ đã biết | Kết quả |", "|---|---|---|---|---|---|---|"]
    for x in res["mft"]:
        conf = f"{x['conf']:.2f}" if x.get("conf") is not None else "–"
        known = f"{x['known']:.0%}" if x.get("known") is not None else "–"
        lines.append(f"| {x['case']} | {x['want']} | {x['label']} | {x.get('star') or '–'} | {conf} | {known} | {'Đạt' if x['ok'] else 'SAI'} |")
    lines += ["", "## INV – đổi chi tiết không liên quan, cảm xúc giữ nguyên", "", "| Ca | Câu gốc | Câu đổi | Kết quả |", "|---|---|---|---|"]
    for x in res["inv"]:
        lines.append(f"| {x['case']} | {x['label_a']} | {x['label_b']} | {'Đạt' if x['ok'] else 'SAI'} |")
    lines += ["", "## DIR – thêm câu chê/khen, xác suất đổi đúng chiều", "", "| Ca | Trước | Sau | Kết quả |", "|---|---|---|---|"]
    for x in res["dir"]:
        lines.append(f"| {x['case']} | {x['p_before']:.3f} | {x['p_after']:.3f} | {'Đạt' if x['ok'] else 'SAI'} |")
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--tag", default="sau tinh chỉnh")
    ap.add_argument("--out", default=str(ROOT / "docs" / "test_report"))
    ap.add_argument("--no-save", action="store_true")
    a = ap.parse_args()
    res = run(a.base)
    md = to_markdown(res, a.base, a.tag)
    print(md)
    if not a.no_save:
        out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
        stem = f"behavior_{datetime.now():%Y%m%d}"
        (out / f"{stem}.md").write_text(md, encoding="utf-8")
        (out / f"{stem}.json").write_text(json.dumps({"tag": a.tag, "base": a.base, **res}, ensure_ascii=False, indent=1), encoding="utf-8")
        print("Đã ghi", out / f"{stem}.md")


if __name__ == "__main__":
    main()
