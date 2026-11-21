#!/usr/bin/env bash
# macOS: nhấp đúp để chạy (lần đầu macOS chặn thì nhấp chuột phải → Open). Cửa sổ Terminal phải mở trong lúc dùng ứng dụng.
cd "$(dirname "$0")" || exit 1
bash ./chay_ung_dung.sh "$@"
echo
read -r -p "Nhấn Enter để đóng cửa sổ…" _
