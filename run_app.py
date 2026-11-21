"""Chạy FoodReview Insight trên máy bất kỳ bằng một lệnh – bản đóng gói 1.5.1 (buổi 9, NFR-08).

    python run_app.py                      # lần đầu: tạo .venv, cài thư viện (cần Internet); các lần sau mở ngay
    python run_app.py --khoi-phuc-demo     # chép lại bộ kết quả demo (khi lỡ tải file khác đè lên)
    python run_app.py --chi-cai-dat        # chỉ cài (chuẩn bị máy trước buổi bảo vệ), không chạy
    python run_app.py --port 8001 --khong-mo-trinh-duyet

Windows: nhấp đúp chay_ung_dung.bat · macOS: chay_ung_dung.command · Linux: ./chay_ung_dung.sh (các file này chỉ tìm
Python phù hợp rồi gọi script này). Mỗi bước dưới đây bỏ qua nếu đã xong:
 1. Kiểm tra Python 3.10 – 3.12 (numpy 1.26 khóa trong requirements chưa hỗ trợ 3.13).
 2. Tạo môi trường ảo .venv cạnh file này, cài backend/requirements.txt (ghi dấu theo mã băm – đổi requirements thì cài lại).
 3. Giao diện: dùng frontend/dist dựng sẵn trong gói; không có mà máy có Node.js thì tự dựng (npm ci, npm run build).
 4. Lần đầu: chép bộ kết quả demo (demo_data/ – toàn bộ Reviews.csv đã xử lý, mô hình, kết quả trợ lý AI Gemini 07/11)
    vào backend/ để mở ra là có dashboard, không cần mạng, không cần khóa Gemini.
 5. Chọn cổng trống từ 8000, chạy máy chủ (giao diện + API cùng một cổng), chờ /api/health rồi mở trình duyệt.
Dừng: nhấn Ctrl+C hoặc đóng cửa sổ. Kết quả xử lý dữ liệu mới vẫn được lưu và nạp lại ở lần chạy sau.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
REQ = ROOT / "backend" / "requirements.txt"
DIST = ROOT / "frontend" / "dist"
DEMO = ROOT / "demo_data"
MARK = VENV / ".fri_requirements"
PY_MIN, PY_MAX = (3, 10), (3, 12)

if hasattr(sys.stdout, "reconfigure"):          # cửa sổ lệnh không hỗ trợ tiếng Việt thì thay ký tự, không dừng chương trình
    sys.stdout.reconfigure(errors="replace")


def say(msg: str) -> None:
    print(f"[FoodReview Insight] {msg}", flush=True)


def targets() -> dict[str, Path]:
    """Thư mục kết quả backend đọc khi khởi động (giống backend/core/config.py, kể cả khi đặt FRI_WORK_DIR)."""
    if os.getenv("FRI_WORK_DIR"):
        w = Path(os.environ["FRI_WORK_DIR"])
        return {"processed": w / "processed", "models": w / "models", "cache": w / "cache"}
    b = ROOT / "backend"
    return {"processed": b / "data" / "processed", "models": b / "models", "cache": b / "cache"}


def venv_python() -> Path:
    return VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def check_python() -> None:
    if not PY_MIN <= sys.version_info[:2] <= PY_MAX:
        say(f"Cần Python {PY_MIN[0]}.{PY_MIN[1]} – {PY_MAX[0]}.{PY_MAX[1]} (khuyên dùng 3.11); máy đang chạy "
            f"{platform.python_version()}. Cài Python 3.11 tại https://www.python.org/downloads/ rồi chạy lại.")
        sys.exit(1)


def ensure_venv(argv: list[str]) -> None:
    """Chưa chạy trong .venv của dự án → tạo .venv (nếu chưa có) rồi chạy lại chính script này bằng Python của .venv."""
    if Path(sys.prefix).resolve() == VENV.resolve():
        return
    if not venv_python().exists():
        say("Tạo môi trường ảo .venv (chỉ lần đầu)…")
        if subprocess.call([sys.executable, "-m", "venv", str(VENV)]) != 0 or not venv_python().exists():
            say("Không tạo được .venv. Ubuntu/Debian: cài thêm gói python3-venv (sudo apt install python3.11-venv).")
            sys.exit(1)
    sys.exit(subprocess.call([str(venv_python()), str(Path(__file__).resolve()), *argv]))


def ensure_requirements() -> None:
    want = hashlib.sha256(REQ.read_bytes()).hexdigest()
    if MARK.exists() and MARK.read_text(encoding="utf-8").strip() == want:
        return
    say("Cài thư viện Python (chỉ lần đầu, cần Internet, thường 2 – 6 phút tùy tốc độ mạng)…")
    t = time.time()
    rc = subprocess.call([sys.executable, "-m", "pip", "install", "--disable-pip-version-check", "-r", str(REQ)])
    if rc != 0:
        say("Cài thư viện chưa xong – kiểm tra kết nối Internet rồi chạy lại (các gói đã tải không phải tải lại).")
        sys.exit(rc)
    MARK.write_text(want, encoding="utf-8")
    say(f"Đã cài xong thư viện ({time.time() - t:.0f} giây).")


def ensure_frontend() -> None:
    if (DIST / "index.html").is_file():
        return
    npm = shutil.which("npm")
    if not npm:
        say("Chưa có giao diện đã dựng (frontend/dist) và máy không có Node.js. Dùng gói nộp kèm (có sẵn frontend/dist) "
            "hoặc cài Node.js 22 LTS rồi chạy lại.")
        sys.exit(1)
    say("Dựng giao diện (chỉ lần đầu: npm ci && npm run build, khoảng 1 – 2 phút)…")
    for cmd in (["ci", "--no-audit", "--no-fund"], ["run", "build"]):
        if subprocess.call([npm, *cmd], cwd=ROOT / "frontend") != 0:
            say(f"Lệnh npm {' '.join(cmd)} thất bại.")
            sys.exit(1)


def ensure_demo(reset: bool) -> None:
    if not DEMO.is_dir():
        return
    t = targets()
    if (t["processed"] / "dataset_meta.json").is_file() and not reset:
        return
    say("Chép bộ kết quả demo (toàn bộ Reviews.csv đã xử lý + kết quả trợ lý AI) vào backend…")
    for name, dst in t.items():
        src = DEMO / name
        if not src.is_dir():
            continue
        dst.mkdir(parents=True, exist_ok=True)
        for p in dst.iterdir():                    # xóa kết quả cũ (giữ .gitkeep) để không trộn hai bộ dữ liệu
            if p.name != ".gitkeep":
                shutil.rmtree(p) if p.is_dir() else p.unlink()
        shutil.copytree(src, dst, dirs_exist_ok=True)


def free_port(host: str, start: int) -> int:
    for port in range(start, start + 20):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as c:
            c.settimeout(0.3)
            if c.connect_ex(("127.0.0.1", port)) == 0:      # đã có chương trình khác nghe ở cổng này
                continue
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            # giống uvicorn: bật SO_REUSEADDR, nếu không thì cổng vừa dùng (kết nối cũ ở TIME_WAIT) bị coi là bận
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind((host, port))
                return port
            except OSError:
                continue
    say(f"Các cổng {start} – {start + 19} đều đang bận; chạy lại với --port <số cổng khác>.")
    sys.exit(1)


def open_when_ready(url: str, port: int, open_browser: bool, t0: float) -> None:
    for _ in range(600):                           # tối đa 5 phút (máy yếu nạp lại 393.890 đánh giá)
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{port}/api/health", timeout=2) as r:
                h = json.loads(r.read())
            break
        except Exception:                          # noqa: BLE001 – máy chủ chưa lên thì thử lại
            time.sleep(0.5)
    else:
        say("Máy chủ chưa trả lời sau 5 phút – xem thông báo lỗi phía trên.")
        return
    ds = h.get("dataset") or {}
    vn = lambda x: f"{x or 0:,}".replace(",", ".")             # noqa: E731 – 393890 → 393.890
    data = (f"{ds.get('file_name')} – {vn(ds.get('n_reviews'))} đánh giá, {vn(ds.get('n_products'))} sản phẩm"
            if ds else "chưa có – chọn bộ mẫu hoặc tải file CSV ở màn hình đầu")
    ai = f"Gemini ({h.get('gemini_model')})" if h.get("gemini_configured") else "chưa có khóa – dùng kết quả đã lưu và chế độ quy tắc"
    say(f"Sẵn sàng sau {time.time() - t0:.0f} giây: {url}")
    say(f"Dữ liệu: {data}. Trợ lý AI: {ai}.")
    say("Tài liệu API: " + url + "/docs · Dừng: nhấn Ctrl+C hoặc đóng cửa sổ này.")
    if open_browser:
        webbrowser.open(url)


def main() -> None:
    os.environ.setdefault("FRI_T0", str(time.time()))     # tính cả thời gian tạo .venv ở tiến trình cha
    t0 = float(os.environ["FRI_T0"])
    ap = argparse.ArgumentParser(description="Chạy FoodReview Insight (giao diện + API ở một cổng).")
    ap.add_argument("--port", type=int, default=8000, help="cổng bắt đầu tìm (mặc định 8000)")
    ap.add_argument("--host", default="127.0.0.1", help="0.0.0.0 để máy khác trong mạng LAN cùng xem")
    ap.add_argument("--khong-mo-trinh-duyet", action="store_true", help="không tự mở trình duyệt")
    ap.add_argument("--khoi-phuc-demo", action="store_true", help="chép lại bộ kết quả demo, xóa kết quả hiện có")
    ap.add_argument("--chi-cai-dat", action="store_true", help="chỉ cài thư viện, dựng giao diện, chép dữ liệu demo")
    args = ap.parse_args()

    check_python()
    ensure_venv(sys.argv[1:])
    ensure_requirements()
    ensure_frontend()
    ensure_demo(args.khoi_phuc_demo)
    if args.chi_cai_dat:
        say(f"Đã cài đặt xong sau {time.time() - t0:.0f} giây. Lần sau chạy lại (không kèm --chi-cai-dat) là mở ngay.")
        return

    port = free_port(args.host, args.port)
    url = f"http://localhost:{port}"
    say(f"Khởi động máy chủ ở {url} (nạp lại dữ liệu đã xử lý, khoảng 10 – 60 giây)…")
    os.chdir(ROOT)
    sys.path.insert(0, str(ROOT))
    threading.Thread(target=open_when_ready, args=(url, port, not args.khong_mo_trinh_duyet, t0), daemon=True).start()
    import uvicorn
    uvicorn.run("backend.main:app", host=args.host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
