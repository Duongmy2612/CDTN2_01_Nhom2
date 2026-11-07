# Biên bản kiểm tra tích hợp – số liệu nhất quán giữa các màn hình (07/11/2026 08:51)

- Địa chỉ gọi: `http://localhost:5173`; hợp đồng API 1.4.0
- Dữ liệu: reviews_sample_100k.csv – 87.622 đánh giá sạch, 31.111 sản phẩm, tháng trọn vẹn cuối 2012-09
- Sản phẩm dùng để đối chiếu: B007RTR9G0 (đứng đầu tab Sản phẩm & cảnh báo)

**Kết quả: 17/17 kiểm tra khớp.**

| Nhóm | Kiểm tra | Giá trị trên từng màn hình / API | Kết quả |
|---|---|---|---|
| Số đánh giá sạch | Cùng một tổng trên 8 nguồn | Thanh tiêu đề (#1): **87.622**<br>Tổng quan KPI (#7): **87.622**<br>Chất lượng dữ liệu (#5): **87.622**<br>Phân bố số sao (#8): **87.622**<br>Số đánh giá theo tháng (#8): **87.622**<br>Chỉ số theo tháng (#15): **87.622**<br>CSV monthly (#20): **87.622**<br>CSV product_risk (#20): **87.622** | Khớp |
| Số sản phẩm | Tổng quan, Sản phẩm & cảnh báo, CSV | Thanh tiêu đề (#1): **31.111**<br>Tổng quan KPI (#7): **31.111**<br>Sản phẩm & cảnh báo (#10): **31.111**<br>Σ các mức rủi ro (#10): **31.111**<br>CSV product_risk (#20): **31.111** | Khớp |
| Sản phẩm rủi ro cao | KPI Tổng quan = bảng Sản phẩm = CSV | Tổng quan KPI (#7): **1**<br>Đếm mức (#10): **1**<br>Lọc rủi ro cao (#10): **1**<br>CSV product_risk (#20): **1** | Khớp |
| Sản phẩm rủi ro cao | Cùng mốc thời gian “tính đến” | Thanh tiêu đề (#1): **2012-09**<br>Tổng quan KPI (#7): **2012-09**<br>Sản phẩm (#10): **2012-09**<br>CSV product_risk (#20): **2012-09** | Khớp |
| Mô hình | F1-macro của mô hình chọn | Tổng quan KPI (#7): **0,6914**<br>Mô hình ML (#11): **0,6914**<br>CSV model_metrics (#20): **0,6914** | Khớp |
| Mô hình | Tự nhập dự đoán dùng đúng mô hình chọn | Mô hình ML (#11): **LR**<br>Tự nhập dự đoán (#14): **LR** | Khớp |
| Chỉ số hài lòng | Toàn kỳ: KPI = công thức (TB − 1)/4 × 100 = bình quân theo tháng | Tổng quan KPI (#7): **79,67**<br>Công thức từ điểm TB (#7): **79,67**<br>Bình quân gia quyền chuỗi tháng (#15): **79,67** | Khớp |
| Chỉ số hài lòng | 69 tháng của Tổng quan/Dự báo (#16) khớp từng tháng với #15 và CSV monthly | Số tháng lệch: **0**<br>Kỳ vọng: **0** | Khớp |
| Chỉ số hài lòng | Tháng cuối của chuỗi dự báo là tháng trọn vẹn cuối | Thanh tiêu đề (#1): **2012-09**<br>Dự báo – tháng cuối thực tế (#16): **2012-09** | Khớp |
| Chỉ số hài lòng | Tab Phân tích đánh dấu đúng tháng chưa trọn (sau tháng trọn vẹn cuối) | Tháng có partial (#8): **2012-10**<br>Tháng sau last_full_month: **2012-10** | Khớp |
| Dự báo | 12 tháng dự báo: Tổng quan/Dự báo (#16) = CSV forecast (#20) | Số tháng lệch: **0**<br>Kỳ vọng: **0** | Khớp |
| Đánh giá tiêu cực | Tổng quan, Phân tích, Chủ đề phàn nàn (đếm chính xác) | Lọc Tiêu cực (#7): **12.590**<br>Chủ đề – n_negative (#9): **12.590**<br>Σ chủ đề + chưa xếp (#9): **12.590** | Khớp |
| Đánh giá tiêu cực | Tỷ lệ tiêu cực ở Tổng quan (làm tròn 4 chữ số) × số đánh giá | Lọc Tiêu cực (#7): **12.590**<br>Tỷ lệ × số đánh giá (#7): **12.591** | Khớp |
| Đánh giá tiêu cực | Số đánh giá từng chủ đề: tab Chủ đề (#9) = CSV topics (#20) | Số chủ đề lệch: **0**<br>Kỳ vọng: **0** | Khớp |
| Sản phẩm B007RTR9G0 | Số đánh giá: bảng Sản phẩm, Phân tích lọc mã, chuỗi tháng, Tự nhập dự đoán | Sản phẩm (#10): **38**<br>Phân tích lọc mã (#7): **38**<br>Chỉ số theo tháng (#15): **38**<br>Tự nhập dự đoán (#14): **38** | Khớp |
| Sản phẩm B007RTR9G0 | Điểm TB: bảng Sản phẩm, Phân tích lọc mã, Tự nhập dự đoán | Sản phẩm (#10): **2,974**<br>Phân tích lọc mã (#7): **2,974**<br>Tự nhập dự đoán (#14): **2,974** | Khớp |
| Sản phẩm B007RTR9G0 | Số đánh giá tiêu cực: Phân tích lọc mã + Tiêu cực, Chủ đề của sản phẩm | Phân tích (#7): **16**<br>Chủ đề (#9): **16** | Khớp |

Số trong ngoặc là số thứ tự API trong hợp đồng (docs/openapi.json). Tạo lại: `python scripts/integration_check.py --base <địa chỉ> --kind <sample|full>`.
