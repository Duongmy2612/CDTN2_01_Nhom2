#!/usr/bin/env bash
# macOS: chép lại bộ kết quả demo (khi lỡ tải file khác đè lên) rồi mở ứng dụng.
cd "$(dirname "$0")" || exit 1
bash ./chay_ung_dung.sh --khoi-phuc-demo
echo
read -r -p "Nhấn Enter để đóng cửa sổ…" _
