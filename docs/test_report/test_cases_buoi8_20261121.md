# Ca kiểm thử luồng chính và ngoại lệ – buổi 8

22 ca (TC8-01 – TC8-22); mỗi chức năng chính có ít nhất một ca luồng chính và một ca ngoại lệ/biên. Kết quả: bản 1.4.0 đạt 10/22, bản 1.5.0 đạt 21/22 (ca còn SAI là hạn chế đã biết L02 – mỉa mai).

| Mã | UC/FR | Loại | Bước – dữ liệu vào | Kết quả mong đợi | 1.4.0 | 1.5.0 | Người kiểm | Lỗi |
|---|---|---|---|---|---|---|---|---|
| TC8-01 | UC-01 · FR-01–06 · NFR-01 | Luồng chính | Trang Chọn dữ liệu → “Mẫu 100.000 đánh giá”; chờ job 7 bước; mở dashboard | Job xong ≤ 3 phút, 7/7 bước “done”, dashboard có số liệu | Đạt | Đạt – 169 giây; 27/27 lời gọi API | Kaysone |  |
| TC8-02 | UC-01 · FR-01 | Ngoại lệ dữ liệu | Tải D05: cột Time ghi bằng mili-giây (kiểu xuất từ JavaScript/Java) | Nhận file, đổi sang giây, báo cho người dùng | SAI – job thất bại “OutOfBoundsDatetime” | Đạt – cảnh báo, xử lý xong | Huy | B01 |
| TC8-03 | UC-01 · FR-02 | Ngoại lệ dữ liệu | Tải D21: 21/2.000 dòng Time âm hoặc quá lớn | Bỏ đúng 21 dòng theo R2, xử lý tiếp | SAI – cả job thất bại | Đạt – loại 21 dòng, có cảnh báo | Huy | B02 |
| TC8-04 | UC-01 · FR-02 | Ngoại lệ dữ liệu | Tải D18 (Id dạng “R1…”) và D20 (mọi Id = 1) | Xử lý xong, mã đánh giá duy nhất | SAI – D18 thất bại ValueError; D20 “xong” nhưng review_id trùng | Đạt – đánh số lại, cảnh báo | Huy | B03, B04 |
| TC8-05 | UC-01 · FR-01 | Ngoại lệ dữ liệu | Tải D07: CSV dùng dấu “;” (Excel bản tiếng Việt) | Tự nhận dấu phân cách | SAI – báo “Thiếu cột Score, Time, Text” | Đạt – nhận dấu “;”, có cảnh báo | Kaysone | B05 |
| TC8-06 | UC-01 · FR-01 | Ngoại lệ dữ liệu | Tải D13: file Latin-1 có “café crème brûlée” | Đọc được, khuyên lưu UTF-8 | SAI – lỗi kỹ thuật “utf-8 codec can't decode” | Đạt – đọc theo cp1252, có cảnh báo | Kaysone | B06 |
| TC8-07 | UC-01 · FR-02 | Giá trị biên | Tải D12: file chỉ có dòng tiêu đề | Báo “không có đánh giá nào” | SAI – báo nhầm “Score không có giá trị 1–5” | Đạt – NO_ROWS | Huy | B07 |
| TC8-08 | UC-01 · FR-24 · NFR-07 | Ngoại lệ dữ liệu | Đang có dữ liệu, tải file chỉ còn 10 dòng hợp lệ (D01) | Từ chối TOO_FEW_ROWS, dữ liệu đang dùng giữ nguyên | Đạt | Đạt | Kaysone |  |
| TC8-09 | UC-01 | Đồng thời | Bấm tải mẫu hai lần liên tiếp; bấm “Đổi file” khi job đang chạy | Lần 2 nhận 409 JOB_RUNNING; không xóa phiên khi đang xử lý | Đạt | Đạt | Kaysone |  |
| TC8-10 | UC-02 · FR-07–09 | Luồng chính | Bộ đầy đủ: lọc 01/2011 – 12/2011 + Tiêu cực; xem KPI và 5 biểu đồ; đổi tab | Số liệu khớp phép tính pandas; cùng chỉ số giống nhau trên mọi màn hình | Đạt | Đạt – 17/17 đối chiếu (mẫu và đầy đủ) | Thuận |  |
| TC8-11 | UC-02 · FR-09 | Giá trị biên | Gọi API với date_from = 2010-13, 2011-00, 2011-1 | 422, thông điệp tiếng Việt rõ | SAI – 2010-13 trả 200 | Đạt – 422 “yyyy-mm, tháng 01–12” | Thuận | B11 |
| TC8-12 | UC-02 · NFR-02 | Hiệu năng | Bộ đầy đủ: biểu đồ Từ khóa đặc trưng lọc năm 2011, gọi 20 lần | Trung bình ≤ 2 giây | SAI – TB 2,06 giây | Đạt – TB 0,07 giây | Thuận | B10 |
| TC8-13 | UC-04 · FR-14–16 | Luồng chính | Nhập 3 đánh giá tiếng Anh: chê rõ, khen rõ, trung tính | Đúng nhóm cảm xúc; có từ ảnh hưởng; ≤ 1 giây | Đạt | Đạt – ≈ 10 ms/lần | My |  |
| TC8-14 | UC-04 · FR-14 | Ngoại lệ dữ liệu | Nhập câu tiếng Việt “Cà phê rất dở, hộp bị móp…” | Từ chối, hướng dẫn nhập tiếng Anh | SAI – “1 sao” nhưng “Tích cực 49 %” | Đạt – 422 TEXT_NOT_RECOGNIZED | My | B08 |
| TC8-15 | UC-04 · FR-14 | Giá trị biên | Nhập “<br> <br> <br>” và “http://a.com www.b.com nice” | Báo cần ≥ 3 từ | SAI – vẫn dự đoán | Đạt – TEXT_TOO_SHORT; nút Dự đoán không bật | My | B09 |
| TC8-16 | UC-04 · FR-14 | Giá trị biên | Câu vừa khen vừa chê “Love the flavor but the bag was half empty…” | Kết quả kèm cảnh báo không chắc chắn | Một phần – không cảnh báo | Đạt – nhãn “Độ tin cậy thấp” (43 %) | My | tinh chỉnh |
| TC8-17 | UC-04 · FR-14 | Ngoại lệ dữ liệu | Nhập mã sản phẩm không có trong dữ liệu kèm đánh giá | Vẫn dự đoán, ghi chú; không mở ngăn chi tiết lỗi 404 | Đạt | Đạt | My |  |
| TC8-18 | UC-06 · FR-19–20 | Luồng chính | Tab Dự báo: 3/6/12 tháng cho toàn bộ và sản phẩm B007JFMH8M; gọi months = 7 | Có khoảng tin cậy 95 %; months = 7 → 422 | Đạt | Đạt | Huy |  |
| TC8-19 | UC-06 · FR-20 | Giá trị biên | Dự báo sản phẩm có < 36 tháng đánh giá | eligible = false, nêu số tháng hiện có | Đạt | Đạt | Huy |  |
| TC8-20 | UC-05 · UC-07 · FR-18, 21–23 | Luồng chính | Tab Chủ đề, Sản phẩm & cảnh báo → mở chi tiết → xuất PDF và 6 bảng CSV | Tải được file, số liệu khớp màn hình | Đạt | Đạt – smoke 27/27 (mẫu và đầy đủ) | Huy |  |
| TC8-21 | UC-08 · FR-25–27 | Ngoại lệ hệ thống | Trợ lý AI khi không có khóa / khóa sai / Gemini trả bằng chứng không tồn tại | Chế độ quy tắc, thông báo rõ; loại nguyên nhân có bằng chứng sai | Đạt | Đạt (Gemini giả lập trong pytest) | Huy |  |
| TC8-22 | UC-04 · FR-14 | Hành vi mô hình | Câu mỉa mai “Oh great, another box of stale crackers. Just what I wanted.” | Tiêu cực | SAI – Tích cực 58 % | SAI – hạn chế đã biết L02 | My | L02 |

## Kiểm thử chịu lỗi dữ liệu đầu vào (D01 – D22, chạy tự động bằng TestClient)

| File | 1.4.0 | 1.5.0 |
|---|---|---|
| D01 10 dòng hợp lệ | 202 · thất bại TOO_FEW_ROWS | 202 · thất bại TOO_FEW_ROWS |
| D02 200 dòng hợp lệ | 202 · xong | 202 · xong |
| D03 toàn 5 sao (1 lớp) | 202 · thất bại TOO_FEW_CLASSES | 202 · thất bại TOO_FEW_CLASSES |
| D04 không có 3 sao | 202 · thất bại TOO_FEW_CLASSES | 202 · thất bại TOO_FEW_CLASSES |
| D05 Time mili-giây | 202 · thất bại PIPELINE_FAILED | 202 · xong · TIME_MILLISECONDS |
| D06 Time dạng ngày | 400 INVALID_TIME | 400 INVALID_TIME |
| D07 phân cách ; | 400 MISSING_COLUMN | 202 · xong · DELIMITER_DETECTED |
| D08 UTF-8 BOM | 202 · xong | 202 · xong |
| D09 chỉ 3 cột bắt buộc | 202 · xong · MISSING_OPTIONAL | 202 · xong · MISSING_OPTIONAL |
| D10 Score 5.0 | 202 · xong | 202 · xong |
| D11 toàn văn bản < 3 từ | 202 · thất bại TOO_FEW_ROWS | 202 · thất bại TOO_FEW_ROWS |
| D12 chỉ có tiêu đề | 400 INVALID_SCORE | 400 NO_ROWS |
| D13 mã hóa Latin-1 | 400 CSV_PARSE_ERROR | 202 · xong · ENCODING_FALLBACK |
| D14 1 sản phẩm, 1 tháng | 202 · xong | 202 · xong |
| D15 Score lẫn chữ/rỗng | 202 · xong · INVALID_SCORE_ROWS | 202 · xong · INVALID_SCORE_ROWS |
| D16 cột đảo thứ tự, thêm cột lạ | 202 · xong | 202 · xong |
| D17 Helpfulness có chữ | 202 · xong | 202 · xong |
| D18 Id dạng chữ | 202 · thất bại PIPELINE_FAILED | 202 · xong · ID_RENUMBERED |
| D19 ProductId trống | 202 · xong | 202 · xong |
| D20 Id trùng hết | 202 · xong | 202 · xong · ID_RENUMBERED |
| D21 Time âm/quá lớn vài dòng | 202 · thất bại PIPELINE_FAILED | 202 · xong · INVALID_TIME_ROWS |
| D22 file nhị phân đuôi .csv | 400 CSV_PARSE_ERROR | 400 CSV_PARSE_ERROR |
