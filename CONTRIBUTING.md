# Quy trình làm việc với Git của nhóm

Kho chung: `https://github.com/legiahuy12052005nt-cloud/CDDTN2_GR2` (quy ước chốt ở báo cáo buổi 3, mục 5.2).

## 1. Nhánh

| Nhánh | Dùng để | Ai được đẩy trực tiếp |
|---|---|---|
| `main` | Bản ổn định để demo và nộp; mỗi lần gộp từ `develop` gắn thẻ phiên bản (`v1.3.0`…) | Không ai – chỉ gộp qua pull request |
| `develop` | Tích hợp các mục backlog đã xong | Không ai – chỉ gộp qua pull request |
| `feature/PB-xx-ten-ngan` | Mỗi mục backlog (hoặc một phần của mục) một nhánh, tách từ `develop` | Người phụ trách mục đó |

Ví dụ: `feature/PB-19-gemini-giai-phap`, `feature/PB-16-bien-ban-kiem-thu`, `feature/PB-07-e-t2`.

## 2. Một vòng làm việc

```bash
git switch develop && git pull                       # lấy bản tích hợp mới nhất
git switch -c feature/PB-xx-ten-ngan                 # nhánh riêng cho việc của mình
# ... sửa mã, chạy thử ...
pytest backend/tests -q                              # kiểm thử phải đạt trước khi commit
git add <các tệp đã sửa> && git commit -m "PB-xx: mô tả ngắn việc đã làm"
git push -u origin feature/PB-xx-ten-ngan            # đẩy lên ít nhất 2 lần mỗi buổi làm việc
```

Mở pull request vào `develop` trên GitHub, điền mẫu có sẵn (danh sách kiểm tra DoD), nhờ một thành viên khác xem lại.
CI (GitHub Actions) tự chạy `pytest` và `npm run build`; chỉ gộp khi CI xanh và đã có người Approve.
Nếu `develop` đã thay đổi trong lúc mình làm: `git pull --rebase origin develop`, sửa xung đột (nếu có), chạy lại kiểm thử rồi đẩy lại.

## 3. Viết commit

- Bắt đầu bằng mã backlog: `PB-05: thêm precision, recall macro vào bảng so sánh mô hình`.
- Việc chung không thuộc mục nào (cấu hình, tài liệu): `chore: …`, `docs: …`.
- Mỗi commit một ý, chạy được; không dồn cả buổi vào một commit “Upload source code”.

## 4. Không đưa lên GitHub

`backend/.env` (khóa Gemini), `backend/data/raw|processed`, mẫu `backend/data/sample/*.csv`, `backend/models/*.joblib|*.json`,
`backend/cache/*.json`, `node_modules/` – đã có trong `.gitignore`. Lỡ commit khóa: thu hồi khóa ngay trên Google AI Studio /
Vertex AI rồi tạo khóa mới (xóa commit không làm khóa cũ hết hiệu lực).

## 5. Definition of Done (báo cáo buổi 3, mục 5.3)

1. Mã đã gộp vào `develop` sau khi được xem lại.
2. Chạy đúng trên bộ dữ liệu mẫu chung của nhóm và đạt tiêu chí chấp nhận của mục backlog.
3. Có kiểm thử tự động cho phần logic mới; `pytest` đạt.
4. Tài liệu (README, báo cáo buổi) cập nhật nếu thay đổi cách dùng hoặc hợp đồng API.
