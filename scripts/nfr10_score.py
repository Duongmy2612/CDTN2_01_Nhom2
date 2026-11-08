"""Tính kết quả đánh giá NFR-10 (thực nghiệm E-A2) từ bảng chấm điểm do scripts/run_ai_batch.py tạo ra.

Hai người chấm độc lập điền cột nguoi_cham_1, nguoi_cham_2 (1 = nguyên nhân khớp với nguyên văn bằng chứng, 0 = không khớp).
    python scripts/nfr10_score.py docs/ai_batch/nfr10_cham_diem_<ngày>.csv
In ra: số nguyên nhân đã chấm, tỷ lệ khớp của từng người và khi cả hai cùng đồng ý, Cohen's κ; đạt khi khớp ≥ 80% và κ ≥ 0,6.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

TARGET_MATCH, TARGET_KAPPA = 0.80, 0.60


def cohen_kappa(a: list[int], b: list[int]) -> float:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa1, pb1 = sum(a) / n, sum(b) / n
    pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
    return 1.0 if pe == 1 else (po - pe) / (1 - pe)


def score(path: Path) -> dict:
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    done = [r for r in rows if r["nguoi_cham_1"].strip() in ("0", "1") and r["nguoi_cham_2"].strip() in ("0", "1")]
    if not done:
        raise SystemExit("Chưa có dòng nào được cả hai người chấm (cột nguoi_cham_1, nguoi_cham_2 nhận 0 hoặc 1)")
    a = [int(r["nguoi_cham_1"]) for r in done]; b = [int(r["nguoi_cham_2"]) for r in done]
    both = sum(x == 1 and y == 1 for x, y in zip(a, b)) / len(done)
    k = cohen_kappa(a, b)
    out = {"n_rows": len(rows), "n_graded": len(done), "n_results": len({r["ma_ket_qua"] for r in done}),
           "match_rater1": round(sum(a) / len(a), 3), "match_rater2": round(sum(b) / len(b), 3),
           "match_both": round(both, 3), "kappa": round(k, 3)}
    out["pass"] = out["match_both"] >= TARGET_MATCH and out["kappa"] >= TARGET_KAPPA
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    r = score(Path(sys.argv[1]))
    print(f"Đã chấm {r['n_graded']}/{r['n_rows']} nguyên nhân của {r['n_results']} kết quả")
    print(f"Tỷ lệ khớp: người 1 {r['match_rater1']:.1%}, người 2 {r['match_rater2']:.1%}, cả hai cùng đồng ý {r['match_both']:.1%}")
    print(f"Cohen's κ = {r['kappa']:.3f} → {'ĐẠT' if r['pass'] else 'CHƯA ĐẠT'} (ngưỡng khớp ≥ 80%, κ ≥ 0,6)")
