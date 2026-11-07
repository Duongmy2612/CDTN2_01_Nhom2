"""Kiểm thử chạy trên thư mục tạm (FRI_WORK_DIR) để không ghi đè dữ liệu, mô hình thật của máy chủ."""
import os
import tempfile

os.environ["FRI_WORK_DIR"] = tempfile.mkdtemp(prefix="fri_test_")
# Đặt rỗng (không chỉ xóa): backend/main.py gọi load_dotenv() khi được import, mà load_dotenv không ghi đè biến đã có –
# nhờ vậy kiểm thử không bao giờ dùng khóa Gemini thật trong backend/.env của máy thành viên (gọi API thật, tốn hạn mức).
os.environ["GEMINI_API_KEY"] = ""
os.environ["GEMINI_MODEL"] = ""
