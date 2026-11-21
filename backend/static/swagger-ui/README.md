# Swagger UI chạy không cần Internet (buổi 9, v1.5.1)

Tệp lấy nguyên từ gói npm `swagger-ui-dist@5.34.1` (giấy phép Apache 2.0 – xem `LICENSE`, `NOTICE`); riêng `swagger-ui.css`
bỏ dòng `sourceMappingURL`. Trang `/docs` của FastAPI mặc định tải hai tệp này từ CDN jsdelivr, nên khi máy demo không có mạng
trang tài liệu API bị trắng – `backend/main.py` cho `/docs` đọc từ thư mục này.
