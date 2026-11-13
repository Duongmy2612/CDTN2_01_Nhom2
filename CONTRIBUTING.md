# Quy trình làm việc với Git của nhóm

Kho chung từ buổi 7: `https://github.com/Duongmy2612/CDTN2_01_Nhom2` (chủ kho: nhóm trưởng Dương Diễm My).
Lịch sử sprint xây dựng 1 (buổi 6, bản 1.3.0, các commit trích trong báo cáo buổi 6) vẫn nằm ở kho cũ
`https://github.com/legiahuy12052005nt-cloud/CDDTN2_GR2`. Trên kho mới, mỗi thành viên nộp lại phần mình đã làm từ buổi 4
đến buổi 7 bằng tài khoản của mình, qua pull request theo từng lượt; ngày commit là ngày nộp lên kho mới, nhãn `[B4]`, `[B5]`,
`[PB-xx]` trong lời commit cho biết phần việc thuộc buổi hay mục backlog nào.

## 1. Mỗi thành viên một nhánh

| Nhánh | Người phụ trách | Phần việc chính |
|---|---|---|
| `main` | Cả nhóm – không ai đẩy trực tiếp | Bản tích hợp để demo và nộp; chỉ gộp qua pull request; mỗi mốc gắn thẻ (`v1.4.0`…) |
| `diemmy` | Dương Diễm My (nhóm trưởng) | Dữ liệu, kiểm thử, tích hợp, tài liệu |
| `kaysone` | KAYSONE Souk Anong | Mô hình ML/NLP: dự đoán, chủ đề phàn nàn |
| `hoangthuan` | Nguyễn Hoàng Thuận | Backend, chỉ số hài lòng, dự báo, Docker |
| `giahuy` | Lê Gia Huy | Frontend, trợ lý AI, tích hợp giao diện – API |

Nhìn tab **Pull requests** (lọc theo nhánh) hoặc **Insights → Contributors** trên GitHub là biết phần nào của ai.
Mỗi người commit bằng **tài khoản Git của chính mình** – đặt một lần trên máy:

```bash
git config --global user.name  "Họ Tên"
git config --global user.email "email-dang-ky-GitHub@..."      # đúng email của tài khoản GitHub thì commit mới hiện ảnh đại diện
```

## 2. Một vòng làm việc

```bash
git checkout <nhanh-cua-minh>
git pull origin main                    # lấy bản tích hợp mới nhất (gồm phần các bạn đã gộp)
# ... sửa mã, chạy thử ...
pytest backend/tests -q                 # phải đạt hết trước khi commit
git add <đúng các tệp mình sửa>         # không dùng "git add ." để khỏi lẫn dữ liệu, tệp tạm
git commit -m "feat(predict): mô tả ngắn việc đã làm [PB-06]"
git push origin <nhanh-cua-minh>        # đẩy lên ít nhất 2 lần mỗi buổi làm việc
```

Trên GitHub: **Compare & pull request** → base `main` ← compare `<nhanh-cua-minh>`, điền mẫu có sẵn.
CI (GitHub Actions) tự chạy `pytest` và `npm run build`; nhóm trưởng gộp khi CI xanh. Gộp xong, lần làm tiếp theo
nhớ `git pull origin main` trước khi sửa.

## 3. Viết commit

Dạng `loại(phạm vi): mô tả [mã backlog]` – một commit một ý, chạy được:

| Loại | Dùng khi | Ví dụ |
|---|---|---|
| `feat` | Thêm chức năng | `feat(predict): kiểm tra mã sản phẩm khi tự nhập dự đoán [PB-06]` |
| `fix` | Sửa lỗi | `fix(topics): trả số đánh giá chưa xếp chủ đề [PB-07]` |
| `test` | Thêm/sửa kiểm thử | `test(frontend): kiểm tra giao diện gọi đúng API [PB-03]` |
| `docs` | Tài liệu, biên bản | `docs(test): biên bản chạy Docker Compose trên máy nhóm [NFR-08]` |
| `chore` | Cấu hình, công cụ | `chore(docker): frontend chỉ chạy khi backend sẵn sàng [PB-17]` |

Không dồn cả buổi vào một commit “Upload source code”.

## 4. Không đưa lên GitHub

`backend/.env` (khóa Gemini), `backend/data/raw|processed`, mẫu `backend/data/sample/*.csv`, `backend/models/*.joblib|*.json`,
`backend/cache/*.json`, `node_modules/` – đã có trong `.gitignore`. Lỡ commit khóa: thu hồi khóa ngay trên Google AI Studio /
Vertex AI rồi tạo khóa mới (xóa commit không làm khóa cũ hết hiệu lực).

## 5. Definition of Done (báo cáo buổi 3, mục 5.3)

1. Mã đã gộp vào `main` qua pull request, CI xanh.
2. Chạy đúng trên bộ dữ liệu mẫu chung của nhóm và đạt tiêu chí chấp nhận của mục backlog.
3. Có kiểm thử tự động cho phần logic mới; `pytest` đạt.
4. Tài liệu (README, báo cáo buổi) cập nhật nếu thay đổi cách dùng hoặc hợp đồng API
   (đổi lược đồ → tăng `API_CONTRACT_VERSION`, chạy `python scripts/export_openapi.py`).
