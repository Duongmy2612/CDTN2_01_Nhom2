# Kịch bản demo tiến độ – sprint xây dựng 1 (buổi 6, nhắc lại đầu buổi 7)

Mục tiêu: chứng minh luồng ưu tiên cao nhất của backlog chạy được đầu – cuối trên bộ mẫu chung của nhóm –
**tải CSV → làm sạch → tổng quan → so sánh mô hình** (PB-01, 02, 04, 05) – cùng hai việc hoàn thiện của sprint
(kiểm tra giải pháp Gemini, biên bản kiểm thử). Thời lượng ≈ 5 phút. Video quay sẵn `Buoi06_Demo_TienDo_Sprint1.mp4`
(1 phút 32 giây, phụ đề tiếng Việt, đoạn chờ job nền tua nhanh ×12) đi theo đúng các bước dưới đây, dùng khi máy chiếu,
mạng hoặc thời gian không cho phép chạy trực tiếp.

## Chuẩn bị (trước giờ demo 10 phút)
1. `uvicorn backend.main:app --port 8000` và `cd frontend && npm run dev`; mở http://localhost:5173 ở cửa sổ 1366 × 768.
2. Backend đang có **toàn bộ Reviews.csv** đã xử lý (để mở đầu bằng số liệu đầy đủ) và bộ đệm trợ lý AI có kết quả của B000IHNCQO.
3. Mở sẵn thư mục `docs/demo/` (file lỗi `du_lieu_loi_thieu_cot_Text.csv`) và `docs/test_report/` (biên bản kiểm thử).
4. Phương án dự phòng: mất mạng → trợ lý AI vẫn đọc kết quả đã lưu; job chạy chậm → mở video demo.

## Các bước

| # | Thao tác | Điều cần nói | Mục backlog / FR |
|---|---|---|---|
| 1 | Tab Tổng quan (toàn bộ dữ liệu) | 393.890 đánh giá sạch, chỉ số hài lòng 79,5, 39 sản phẩm rủi ro cao – đây là kết quả của bản đang chạy | PB-04 · FR-07 |
| 2 | Tab Trợ lý AI → B000IHNCQO → Phân tích | Kết quả Gemini thật đã lưu; nguyên nhân 4 có hành động bị cắt (“Xem xét nghiên cứu dòng sản phẩm”) nay được gắn cờ vàng, “Gọi lại” sẽ yêu cầu Gemini viết lại | PB-19 · FR-26 |
| 3 | Đổi dữ liệu → kéo file `du_lieu_loi_thieu_cot_Text.csv` | Báo ngay “Thiếu cột bắt buộc: Text”, dữ liệu đang dùng giữ nguyên | PB-01 · FR-02, NFR-07 |
| 4 | Chọn “Mẫu 100.000 đánh giá” | Job nền 7 bước có tiến trình; ≈ 2,7 phút trên máy 2 nhân (ngưỡng NFR-01: 3 phút) – trong lúc chờ nói về kiểm thử, CI | PB-01, 02 · FR-01, 04 – 06 |
| 5 | Mở dashboard → Tổng quan | 87.622 đánh giá sạch từ 100.000 dòng (bỏ 12.377 bản trùng) | PB-02, 04 · FR-04, 07 |
| 6 | Tab Phân tích → khối Chất lượng dữ liệu gốc | Số dòng trùng, giá trị thiếu từng cột, 20 dòng đầu (đã ẩn ProfileName) | PB-01 · FR-03 |
| 7 | Tab Mô hình ML → bảng chỉ số → “Kết quả có đáng tin không?” | 3 mô hình + baseline, đủ Accuracy – Precision – Recall – F1-macro – MAE; LR chọn trên validation; kiểm tra theo thời gian | PB-05 · FR-10, 11 |
| 8 | Tab Tự nhập dự đoán → gõ một đánh giá chê | Số sao, cảm xúc, xác suất, chỉ số hài lòng, từ ảnh hưởng, chủ đề và gợi ý – dưới 1 giây | PB-06 (làm sớm) · FR-14 |
| 9 | Mở `docs/test_report/acceptance_sample_<ngày>.md` | 14/14 ca kiểm thử FR Must đạt, mỗi ca so với phép tính độc lập bằng pandas | PB-16 |

## Câu hỏi dự kiến
- *Vì sao F1-macro trên bộ mẫu (0,691) thấp hơn bộ đầy đủ (0,712)?* – bộ mẫu chỉ có 87.622 đánh giá sạch, mô hình học trên
  70.097 đánh giá; bộ đầy đủ lấy mẫu phân tầng 100.000 đánh giá để học (đường học ở notebook 02).
- *Gemini bị chặn mạng thì sao?* – đọc kết quả đã lưu; chưa có thì phân tích theo quy tắc từ chủ đề NMF, ghi rõ nguồn.
