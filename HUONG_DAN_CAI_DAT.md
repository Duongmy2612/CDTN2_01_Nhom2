# Hướng dẫn cài đặt và chạy FoodReview Insight (bản đóng gói 1.5.1)

Dành cho người không lập trình (giảng viên, người dùng thử). Gói nộp kèm đã có sẵn giao diện dựng sẵn, bộ mẫu 100.000 đánh giá
và **bộ kết quả demo**: toàn bộ Reviews.csv (393.890 đánh giá sạch) đã xử lý, mô hình đã huấn luyện, kết quả trợ lý AI Gemini
chạy ngày 07/11. Mở lên là có dashboard, không cần mạng (trừ lần cài đầu), không cần khóa Gemini.

## 1. Máy cần có
| Mục | Yêu cầu |
|---|---|
| Hệ điều hành | Windows 10/11, macOS 12 trở lên hoặc Linux 64 bit |
| Python | 3.11 (đã kiểm thử; 3.10 và 3.12 cũng được, 3.13 chưa được) |
| Bộ nhớ | RAM ≥ 4 GB (ứng dụng dùng khoảng 0,75 GB khi nạp toàn bộ dữ liệu); ổ đĩa trống ≥ 1,5 GB |
| Trình duyệt | Chrome hoặc Edge, màn hình rộng từ 1366 px |
| Internet | Chỉ cần ở lần chạy đầu để tải khoảng 140 MB thư viện Python |

Chưa có Python: tải Python 3.11 tại https://www.python.org/downloads/ – trên Windows nhớ tick **“Add python.exe to PATH”**
ở màn hình đầu của trình cài đặt. macOS có thể dùng `brew install python@3.11`.

## 2. Chạy (3 bước)
1. Giải nén `FoodReview_Insight_v1.5.1.zip` vào thư mục bất kỳ (ví dụ Desktop).
2. Nhấp đúp file chạy theo hệ điều hành:
   - **Windows:** `chay_ung_dung.bat`
   - **macOS:** `chay_ung_dung.command` (lần đầu macOS báo “không xác định được nhà phát triển” thì nhấp chuột phải → **Open** → **Open**)
   - **Linux:** mở Terminal trong thư mục, gõ `./chay_ung_dung.sh`
3. Chờ cửa sổ dòng lệnh báo **“Sẵn sàng … http://localhost:8000”** – trình duyệt tự mở dashboard.
   Lần đầu mất vài phút để tạo môi trường và cài thư viện; các lần sau mở được sau khoảng 10 – 20 giây.

Giữ cửa sổ dòng lệnh mở trong lúc dùng. Dừng: nhấn `Ctrl + C` hoặc đóng cửa sổ.

## 3. Thử nhanh trong 5 phút
1. **Tổng quan:** chỉ số hài lòng, xu hướng và dự báo 12 tháng, sản phẩm rủi ro.
2. **Tự nhập dự đoán:** dán một câu tiếng Anh, ví dụ *“The coffee arrived stale and the box was crushed. Very disappointed.”*
   → số sao, cảm xúc, chủ đề phàn nàn, gợi ý hành động.
3. **Sản phẩm & cảnh báo:** bấm một sản phẩm rủi ro Cao → dự báo và phân tích nguyên nhân bằng AI (kết quả Gemini đã lưu).
4. **Tải file của bạn:** nút **“Đổi dữ liệu”** ở thanh trên cùng → chọn “Mẫu 100.000 đánh giá” hoặc kéo thả file CSV
   cùng định dạng Amazon Fine Food Reviews (cần cột Score, Time, Text) – xử lý khoảng 2 – 3 phút.

Kịch bản demo đầy đủ: `docs/demo/kich_ban_demo_day_du.md`.

## 4. Tùy chọn
- **Khôi phục bộ kết quả demo** (sau khi đã tải file khác): nhấp đúp `khoi_phuc_demo.bat` (Windows) hoặc
  `khoi_phuc_demo.command` (macOS); Linux: `./chay_ung_dung.sh --khoi-phuc-demo`.
- **Bật Gemini để phân tích mới:** chép `backend/.env.example` thành `backend/.env`, điền `GEMINI_API_KEY=<khóa>`, chạy lại.
- **Cài trước, chạy sau** (chuẩn bị máy trước buổi bảo vệ, lúc có mạng): `chay_ung_dung.sh --chi-cai-dat`
  (Windows: mở cmd trong thư mục, gõ `chay_ung_dung.bat --chi-cai-dat`).
- **Cổng khác / xem từ máy khác trong cùng mạng:** `--port 8001`, `--host 0.0.0.0`. Cổng 8000 bận thì tự chuyển sang 8001, 8002…
- **Docker:** `docker compose up --build` (xem README mục 2).

## 5. Gặp sự cố
| Hiện tượng | Cách xử lý |
|---|---|
| “Không tìm thấy Python 3.10 – 3.12” | Cài Python 3.11 (mục 1), trên Windows tick “Add python.exe to PATH”, rồi chạy lại |
| Dừng ở bước cài thư viện | Kiểm tra Internet rồi chạy lại – gói đã tải không phải tải lại |
| macOS không cho mở `.command` | Nhấp chuột phải → Open; hoặc Terminal: `xattr -dr com.apple.quarantine <thư mục>` |
| Trình duyệt không tự mở | Tự mở địa chỉ in trong cửa sổ dòng lệnh (thường là http://localhost:8000) |
| Dashboard trống, báo chưa có dữ liệu | Chạy khôi phục bộ kết quả demo (mục 4) hoặc chọn “Mẫu 100.000 đánh giá” |
| Phần mềm diệt virus chặn | Cho phép thư mục ứng dụng; ứng dụng chỉ mở cổng trên chính máy (127.0.0.1) |

Gỡ ứng dụng: dừng chương trình rồi xóa cả thư mục – không cài gì ra ngoài thư mục này.
