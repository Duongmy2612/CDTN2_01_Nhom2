## Người làm, mục backlog
<!-- VD: KAYSONE Souk Anong – PB-06, PB-07 -->

## Thay đổi
-

## Cách kiểm tra
<!-- VD: tab Tự nhập dự đoán → nhập mã B0NOTEXIST → có ghi chú, không có nút “Xem sản phẩm” -->

## Kiểm tra trước khi gộp (Definition of Done – báo cáo buổi 3, mục 5.3)
- [ ] Đã `git pull origin main` trước khi sửa; commit bằng tài khoản Git của mình, dạng `loại(phạm vi): mô tả [PB-xx]`
- [ ] `pytest backend/tests -q` đạt trên máy mình; CI trên GitHub báo xanh
- [ ] Chạy đúng trên bộ dữ liệu mẫu chung (backend/data/sample) và đạt tiêu chí chấp nhận của mục backlog
- [ ] Không đưa `backend/.env`, dữ liệu gốc, mô hình đã huấn luyện lên GitHub
- [ ] Đổi lược đồ API thì đã tăng `API_CONTRACT_VERSION` và chạy `python scripts/export_openapi.py`
