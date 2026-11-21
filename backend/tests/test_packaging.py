"""Bản đóng gói chạy độc lập (buổi 9, v1.5.1): backend phục vụ giao diện đã dựng ở cùng cổng, không che API.

Dựng một thư mục dist giả (index.html + assets) trong thư mục tạm, gắn vào ứng dụng FastAPI có một API mẫu,
kiểm tra 7 tình huống: trang chủ, tệp tĩnh, đường dẫn sâu của ứng dụng một trang, API vẫn trả JSON, API không có
trả 404 JSON (không trả trang HTML), không đọc được tệp ngoài dist, không có dist thì không gắn gì.
Kèm kiểm tra file chạy: .bat xuống dòng CRLF và chỉ có ký tự ASCII (cmd.exe đọc theo bảng mã OEM), .sh/.command LF.
"""
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.core.frontend import register_frontend

ROOT = Path(__file__).resolve().parents[2]


def _app(tmp_path: Path, with_dist: bool = True):
    dist = tmp_path / "dist"
    if with_dist:
        (dist / "assets").mkdir(parents=True)
        (dist / "index.html").write_text("<html><div id=root></div>FRI</html>", encoding="utf-8")
        (dist / "assets" / "app.js").write_text("console.log('fri')", encoding="utf-8")
        (dist / "favicon.svg").write_text("<svg/>", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("KHONG_DUOC_DOC", encoding="utf-8")
    app = FastAPI()

    @app.get("/api/health")
    def health():
        return {"ok": True}

    mounted = register_frontend(app, dist)
    return TestClient(app), mounted


def test_serves_index_assets_and_spa_fallback(tmp_path):
    c, mounted = _app(tmp_path)
    assert mounted
    r = c.get("/")
    assert r.status_code == 200 and "FRI" in r.text and r.headers["content-type"].startswith("text/html")
    assert c.get("/assets/app.js").text == "console.log('fri')"
    assert c.get("/favicon.svg").text == "<svg/>"
    assert "FRI" in c.get("/san-pham/B0001").text           # đường dẫn sâu → index.html


def test_api_not_shadowed(tmp_path):
    c, _ = _app(tmp_path)
    assert c.get("/api/health").json() == {"ok": True}
    r = c.get("/api/khong-co")
    assert r.status_code == 404 and r.json()["error"]["code"] == "NOT_FOUND"
    assert c.get("/docs").status_code == 200 and "swagger" in c.get("/docs").text.lower()


def test_no_path_traversal(tmp_path):
    c, _ = _app(tmp_path)
    for p in ("/../secret.txt", "/%2e%2e/secret.txt", "/assets/../../secret.txt"):
        assert "KHONG_DUOC_DOC" not in c.get(p).text, p


def test_without_dist_nothing_mounted(tmp_path):
    c, mounted = _app(tmp_path, with_dist=False)
    assert not mounted
    assert c.get("/").status_code == 404 and c.get("/api/health").status_code == 200


def test_launcher_files_line_endings():
    bat = (ROOT / "chay_ung_dung.bat").read_bytes()
    assert b"\r\n" in bat and b"\n" not in bat.replace(b"\r\n", b"")
    bat.decode("ascii")
    for name in ("chay_ung_dung.sh", "chay_ung_dung.command", "khoi_phuc_demo.command"):
        assert b"\r\n" not in (ROOT / name).read_bytes(), name
    assert "def main" in (ROOT / "run_app.py").read_text(encoding="utf-8")


def test_launcher_picks_next_free_port():
    """Cổng đang có chương trình khác nghe thì run_app.py chuyển sang cổng kế tiếp; cổng vừa đóng vẫn dùng lại được."""
    import socket

    import run_app
    with socket.socket() as busy:
        busy.bind(("127.0.0.1", 0))
        busy.listen()
        port = busy.getsockname()[1]
        assert run_app.free_port("127.0.0.1", port) != port
    # vừa đóng (giống lúc tắt rồi mở lại ứng dụng): phải dùng lại đúng cổng đó, không nhảy sang cổng khác
    with socket.socket() as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(("127.0.0.1", 0))
        srv.listen()
        port2 = srv.getsockname()[1]
        cli = socket.create_connection(("127.0.0.1", port2))
        conn, _ = srv.accept()
        conn.close()                      # máy chủ đóng trước → kết nối nằm ở TIME_WAIT phía máy chủ
        cli.close()
    assert run_app.free_port("127.0.0.1", port2) == port2


def test_docs_page_works_offline():
    """/docs không tải gì từ Internet (trước 1.5.1: JS/CSS lấy từ cdn.jsdelivr.net → máy demo mất mạng thì trắng trang)."""
    import re

    from backend.main import app
    from backend.schemas.api import API_CONTRACT_VERSION
    c = TestClient(app)
    html = c.get("/docs").text
    assert "/static/swagger-ui/swagger-ui-bundle.js" in html and "/static/swagger-ui/swagger-ui.css" in html
    assert not re.search(r"(src|href)=['\"]https?://", html), "trang /docs còn tải tài nguyên từ Internet"
    js = c.get("/static/swagger-ui/swagger-ui-bundle.js")
    assert js.status_code == 200 and len(js.content) > 1_000_000
    assert c.get("/static/swagger-ui/swagger-ui.css").status_code == 200
    assert c.get("/openapi.json").json()["info"]["version"] == API_CONTRACT_VERSION
