# Kịch bản demo đầy đủ chức năng – bản 1.3.0 (buổi 6, dùng lại ở mốc giữa kỳ 2)

Mục tiêu: cho GVHD thấy toàn bộ 28 yêu cầu chức năng của SRS v1.1 chạy trên một ứng dụng, trên toàn bộ Reviews.csv, theo thứ
tự 10 màn hình. Thời lượng ≈ 8 – 10 phút nếu chạy trực tiếp; video quay sẵn `Buoi06_Demo_DayDu_ChucNang.mp4`
(3 phút 20 giây, 1366 × 768, phụ đề tiếng Việt, con trỏ được làm nổi, đoạn chờ job nền tua nhanh ×12) đi đúng các bước dưới đây.
Demo nhanh 5 phút chỉ gồm luồng ưu tiên cao: xem `kich_ban_demo_sprint1.md`.

## Chuẩn bị
1. `uvicorn backend.main:app --port 8000` và `cd frontend && npm run dev`; trình duyệt Chrome/Edge cửa sổ 1366 × 768 (NFR-09).
2. Backend đang có **toàn bộ Reviews.csv** đã xử lý; bộ đệm `backend/cache/ai_insights.json` có kết quả Gemini của B000IHNCQO.
3. Có khóa Gemini trong `backend/.env` và mạng tới Gemini thì chủ đề, chatbot trả lời bằng Gemini; không có mạng thì hệ thống tự
   chuyển sang chế độ quy tắc và ghi chú nguồn – vẫn demo được (NFR-07).
4. Mở sẵn `docs/demo/du_lieu_loi_thieu_cot_Text.csv` cho bước tải file lỗi.

## Các bước

| # | Màn hình | Thao tác | Điều cần nói | Yêu cầu |
|---|---|---|---|---|
| 1 | Tổng quan | Rê chuột trên biểu đồ chỉ số hài lòng; cuộn xuống | 393.890 đánh giá sạch, chỉ số 79,5/100, 39 sản phẩm rủi ro cao; 12 tháng dự báo nối tiếp chuỗi thực tế | FR-07, 19 |
| 2 | Phân tích (EDA) | Số sao = 1 → Áp dụng; cuộn tới từ đặc trưng, chất lượng dữ liệu gốc; Bỏ lọc | Lọc áp dụng cho mọi KPI và biểu đồ (36.302 đánh giá 1 sao); số dòng trùng, giá trị thiếu, 20 dòng đầu | FR-03, 08, 09 |
| 3 | Mô hình ML | Cuộn bảng chỉ số → kiểm tra theo thời gian → ma trận nhầm lẫn, bấm “5 sao” | 3 mô hình + đường cơ sở, đủ 5 chỉ số; LR F1-macro 0,712; từ khóa ảnh hưởng, đánh giá mâu thuẫn | FR-10 – 13 |
| 4 | Tự nhập dự đoán | Gõ một đánh giá chê → Dự đoán; bấm ví dụ “Thú cưng bị bệnh” | Số sao, cảm xúc, xác suất, chỉ số hài lòng; từ được tô màu, chủ đề gần nhất, gợi ý hành động, lịch sử | FR-14 – 17 |
| 5 | Sản phẩm & cảnh báo | Bấm dòng đầu → ngăn chi tiết; đóng; Tải CSV | Quy tắc rủi ro có kiểm tra ngược (Cao 27,4% so với Ổn định 12,2%); B00507A02Q giảm 1,53 sao | FR-19, 21, 23 |
| 6 | Dự báo | 3 tháng → 12 tháng → Từng sản phẩm → chọn sản phẩm khác | ETS MAE 0,61 < ngây thơ 1,50; dự báo riêng cho sản phẩm ≥ 36 tháng, cảnh báo độ tin cậy | FR-19, 20 |
| 7 | Trợ lý AI | Nhập B000IHNCQO → Phân tích; cuộn tới giải pháp gắn cờ; mở bằng chứng | Kết quả Gemini thật đã lưu, mỗi nguyên nhân có mã đánh giá bằng chứng; giải pháp 7 từ bị gắn cờ | FR-25, 26, 28 |
| 8 | Chủ đề phàn nàn | Chọn “Hàng cũ, hết hạn…” → cuộn → Phân tích bằng AI | 9 chủ đề NMF, xu hướng, đánh giá tiêu biểu; AI trả nguyên nhân – giải pháp có bằng chứng | FR-16, 18, 25 |
| 9 | Chatbot | Nút tròn góc phải → “Những sản phẩm nào đang rủi ro cao và vì sao?” | Trợ lý tự chọn công cụ đọc bảng cảnh báo, trả lời bằng số liệu thật | FR-27 |
| 10 | Báo cáo | Tạo và tải PDF; tải một bảng CSV | PDF tiếng Việt 5 trang trong vài giây; 6 bảng CSV UTF-8 có BOM | FR-22, 23 |
| 11 | Đổi dữ liệu | Kéo file thiếu cột Text | “Thiếu cột bắt buộc: Text”, dữ liệu đang dùng giữ nguyên | FR-02, 24 |
| 12 | Tải dữ liệu | Chọn “Mẫu 100.000 đánh giá” → chờ → Mở dashboard | Job nền 7 bước có tiến trình (≈ 2,7 phút, NFR-01); 87.622 đánh giá sạch, F1-macro 0,691 | FR-01, 04 – 06, 10 |

Sau buổi demo: chọn lại “Toàn bộ Reviews.csv” (≈ 3 – 5 phút) để máy demo trở về trạng thái ban đầu.

## Câu hỏi dự kiến
- *Vì sao chủ đề và chatbot trong video ghi “Không kết nối được Gemini”?* – máy quay video không có mạng tới Gemini; đây là chế độ
  dự phòng theo thiết kế (NFR-07). Kết quả Gemini thật được minh họa bằng bộ đệm của B000IHNCQO; lần chạy hàng loạt 39 sản phẩm và
  9 chủ đề làm trên máy nhóm bằng `python scripts/run_ai_batch.py --refresh`.
- *Dự đoán đánh giá tiếng Việt được không?* – mô hình học từ đánh giá tiếng Anh; nội dung tiếng Việt được nhận nhưng ứng dụng cảnh
  báo kết quả kém tin cậy (ví dụ “Đánh giá tiếng Việt” ở tab Tự nhập dự đoán).
