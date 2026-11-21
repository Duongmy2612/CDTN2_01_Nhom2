"""Phục vụ giao diện React đã dựng sẵn (frontend/dist) ngay từ backend – bản đóng gói chạy độc lập (buổi 9, v1.5.1).

Khi có frontend/dist/index.html, người dùng chỉ chạy một tiến trình và mở http://localhost:8000, không cần Node.js:
- /api/..., /docs, /openapi.json giữ nguyên (đăng ký trước nên được khớp trước);
- /assets/...: tệp JS/CSS đã dựng bằng `npm run build`;
- đường dẫn khác: trả tệp tĩnh nếu có trong dist (favicon…), không thì trả index.html (ứng dụng một trang).
Đường dẫn /api/... không tồn tại vẫn trả lỗi 404 dạng JSON thống nhất {"error": {...}}, không trả trang HTML,
và không bao giờ trả tệp nằm ngoài thư mục dist.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles


def register_frontend(app: FastAPI, dist: Path) -> bool:
    """Gắn giao diện đã dựng vào app; trả False (không làm gì) nếu chưa có dist/index.html – chế độ phát triển cũ."""
    dist = Path(dist).resolve()
    index = dist / "index.html"
    if not index.is_file():
        return False
    if (dist / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=dist / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path == "api" or path.startswith("api/"):
            return JSONResponse(status_code=404, content={"error": {"code": "NOT_FOUND",
                                "message": f"Không có API /{path}", "details": None}})
        f = (dist / path).resolve()
        if path and f.is_file() and f.is_relative_to(dist):
            return FileResponse(f)
        return FileResponse(index, headers={"Cache-Control": "no-cache"})   # bản mới dựng lại thì trình duyệt lấy ngay

    return True
