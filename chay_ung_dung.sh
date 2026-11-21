#!/usr/bin/env bash
# FoodReview Insight – chạy trên macOS/Linux: ./chay_ung_dung.sh  (thêm --khoi-phuc-demo, --port 8001 … nếu cần)
# Chỉ tìm Python 3.10 – 3.12 rồi giao cho run_app.py (tạo .venv, cài thư viện, chạy giao diện + API ở một cổng).
cd "$(dirname "$0")" || exit 1
PY=""
for c in .venv/bin/python python3.11 python3.12 python3.10 python3 python; do
  if command -v "$c" >/dev/null 2>&1 && "$c" -c 'import sys; sys.exit(0 if (3,10) <= sys.version_info[:2] <= (3,12) else 1)' 2>/dev/null; then
    PY="$c"; break
  fi
done
if [ -z "$PY" ]; then
  echo "[FoodReview Insight] Không tìm thấy Python 3.10 – 3.12. Cài Python 3.11 (https://www.python.org/downloads/ hoặc brew install python@3.11) rồi chạy lại."
  exit 1
fi
exec "$PY" run_app.py "$@"
