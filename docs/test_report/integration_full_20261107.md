# Biên bản kiểm tra tích hợp – số liệu nhất quán giữa các màn hình (07/11/2026 08:55)

- Địa chỉ gọi: `http://localhost:8000`; hợp đồng API 1.4.0
- Dữ liệu: Reviews.csv – 393.890 đánh giá sạch, 67.612 sản phẩm, tháng trọn vẹn cuối 2012-09
- Sản phẩm dùng để đối chiếu: B00507A02Q (đứng đầu tab Sản phẩm & cảnh báo)

**Kết quả: 17/17 kiểm tra khớp.**

| Nhóm | Kiểm tra | Giá trị trên từng màn hình / API | Kết quả |
|---|---|---|---|
| Số đánh giá sạch | Cùng một tổng trên 8 nguồn | Thanh tiêu đề (#1): **393.890**<br>Tổng quan KPI (#7): **393.890**<br>Chất lượng dữ liệu (#5): **393.890**<br>Phân bố số sao (#8): **393.890**<br>Số đánh giá theo tháng (#8): **393.890**<br>Chỉ số theo tháng (#15): **393.890**<br>CSV monthly (#20): **393.890**<br>CSV product_risk (#20): **393.890** | Khớp |
| Số sản phẩm | Tổng quan, Sản phẩm & cảnh báo, CSV | Thanh tiêu đề (#1): **67.612**<br>Tổng quan KPI (#7): **67.612**<br>Sản phẩm & cảnh báo (#10): **67.612**<br>Σ các mức rủi ro (#10): **67.612**<br>CSV product_risk (#20): **67.612** | Khớp |
| Sản phẩm rủi ro cao | KPI Tổng quan = bảng Sản phẩm = CSV | Tổng quan KPI (#7): **39**<br>Đếm mức (#10): **39**<br>Lọc rủi ro cao (#10): **39**<br>CSV product_risk (#20): **39** | Khớp |
| Sản phẩm rủi ro cao | Cùng mốc thời gian “tính đến” | Thanh tiêu đề (#1): **2012-09**<br>Tổng quan KPI (#7): **2012-09**<br>Sản phẩm (#10): **2012-09**<br>CSV product_risk (#20): **2012-09** | Khớp |
| Mô hình | F1-macro của mô hình chọn | Tổng quan KPI (#7): **0,7117**<br>Mô hình ML (#11): **0,7117**<br>CSV model_metrics (#20): **0,7117** | Khớp |
| Mô hình | Tự nhập dự đoán dùng đúng mô hình chọn | Mô hình ML (#11): **LR**<br>Tự nhập dự đoán (#14): **LR** | Khớp |
| Chỉ số hài lòng | Toàn kỳ: KPI = công thức (TB − 1)/4 × 100 = bình quân theo tháng | Tổng quan KPI (#7): **79,48**<br>Công thức từ điểm TB (#7): **79,48**<br>Bình quân gia quyền chuỗi tháng (#15): **79,48** | Khớp |
| Chỉ số hài lòng | 69 tháng của Tổng quan/Dự báo (#16) khớp từng tháng với #15 và CSV monthly | Số tháng lệch: **0**<br>Kỳ vọng: **0** | Khớp |
| Chỉ số hài lòng | Tháng cuối của chuỗi dự báo là tháng trọn vẹn cuối | Thanh tiêu đề (#1): **2012-09**<br>Dự báo – tháng cuối thực tế (#16): **2012-09** | Khớp |
| Chỉ số hài lòng | Tab Phân tích đánh dấu đúng tháng chưa trọn (sau tháng trọn vẹn cuối) | Tháng có partial (#8): **2012-10**<br>Tháng sau last_full_month: **2012-10** | Khớp |
| Dự báo | 12 tháng dự báo: Tổng quan/Dự báo (#16) = CSV forecast (#20) | Số tháng lệch: **0**<br>Kỳ vọng: **0** | Khớp |
| Đánh giá tiêu cực | Tổng quan, Phân tích, Chủ đề phàn nàn (đếm chính xác) | Lọc Tiêu cực (#7): **57.103**<br>Chủ đề – n_negative (#9): **57.103**<br>Σ chủ đề + chưa xếp (#9): **57.103** | Khớp |
| Đánh giá tiêu cực | Tỷ lệ tiêu cực ở Tổng quan (làm tròn 4 chữ số) × số đánh giá | Lọc Tiêu cực (#7): **57.103**<br>Tỷ lệ × số đánh giá (#7): **57.114** | Khớp |
| Đánh giá tiêu cực | Số đánh giá từng chủ đề: tab Chủ đề (#9) = CSV topics (#20) | Số chủ đề lệch: **0**<br>Kỳ vọng: **0** | Khớp |
| Sản phẩm B00507A02Q | Số đánh giá: bảng Sản phẩm, Phân tích lọc mã, chuỗi tháng, Tự nhập dự đoán | Sản phẩm (#10): **126**<br>Phân tích lọc mã (#7): **126**<br>Chỉ số theo tháng (#15): **126**<br>Tự nhập dự đoán (#14): **126** | Khớp |
| Sản phẩm B00507A02Q | Điểm TB: bảng Sản phẩm, Phân tích lọc mã, Tự nhập dự đoán | Sản phẩm (#10): **2,841**<br>Phân tích lọc mã (#7): **2,841**<br>Tự nhập dự đoán (#14): **2,841** | Khớp |
| Sản phẩm B00507A02Q | Số đánh giá tiêu cực: Phân tích lọc mã + Tiêu cực, Chủ đề của sản phẩm | Phân tích (#7): **60**<br>Chủ đề (#9): **60** | Khớp |

Số trong ngoặc là số thứ tự API trong hợp đồng (docs/openapi.json). Tạo lại: `python scripts/integration_check.py --base <địa chỉ> --kind <sample|full>`.
