# Bảng chỉ số mô hình 9 cột đọc trọn ở 1366 px [PB-05, NFR-09] · Lê Gia Huy

Buổi 6: thêm Precision/Recall làm bảng 12 cột phải cuộn ngang ở 1366 px; gộp cặp chỉ số còn 9 cột.

> Ngày commit trên GitHub là ngày bạn commit (hôm nay) – **không chỉnh ngày**. Nhãn `[B4]`, `[B5]`, `[PB-xx]` trong lời commit cho biết phần việc thuộc buổi/mục backlog nào; thời gian thực hiện gốc đã ghi trong nhật ký đề tài.

Đợt 2 · lượt 3 – làm **sau khi PR lượt 2 của Kaysone đã gộp**; ba bạn cùng lượt làm song song.

## 1. Lấy code mới nhất

Nếu máy chưa có thư mục dự án:
```bash
git clone https://github.com/Duongmy2612/CDTN2_01_Nhom2.git
cd CDTN2_01_Nhom2
git config user.name  "Lê Gia Huy"
git config user.email "<email tài khoản GitHub của bạn>"
```

Mỗi lần làm:
```bash
git checkout giahuy
git pull origin main
```

Cài môi trường (lần đầu, nếu chưa cài):
```bash
python -m venv .venv && .venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements-dev.txt
```

## 2. Chép file và commit (1 commit, dùng tài khoản Git của bạn)

Zip có 1 thư mục `commit1` – làm **lần lượt**: chép một thư mục → kiểm tra `git status` → commit → mới chép thư mục tiếp theo.

### Commit 1/1

Mở `commit1` → chọn tất cả → chép vào thư mục `CDTN2_01_Nhom2` → chọn **Replace**. `git status` phải thấy đúng:
```
 M frontend/src/tabs/ModelTab.jsx
```
```bash
git add frontend/src/tabs/ModelTab.jsx
git commit -m "fix(ui): gộp cột bảng chỉ số để đọc trọn ở màn hình 1366 px [PB-05,NFR-09]"
```

Sau commit cuối, `git status` phải sạch.

## 3. Kiểm tra

```bash
pytest backend/tests -q
```
Phải **0 failed** (làm đúng thứ tự: 17 passed).

Có gì sai thì **chưa push**, chụp màn hình gửi My.

## 4. Push + PR

```bash
git push origin giahuy
```
GitHub → **Compare & pull request** → base `main` ← compare `giahuy`
- Title: `Bảng chỉ số mô hình 9 cột đọc trọn ở 1366 px [PB-05, NFR-09]`
- Description:
  ```
  Người làm: Lê Gia Huy – Buổi 6 – sprint xây dựng 1 (bản 1.3.0)
  - Tab Mô hình ML: gộp Precision / Recall, Accuracy 3 lớp / 5 sao vào cùng cột → 9 cột, không cuộn ngang ở 1366 px
  ```

Nhắn Zalo nhóm: "GiaHuy đã mở PR Bảng chỉ số mô hình 9 cột đọc trọn ở 1366 px".

## 5. Hiểu phần mình làm (để trình bày với thầy)

1. NFR-09 yêu cầu đọc trọn ở màn hình 1366 px – kiểm tra bằng F12 → chế độ thiết bị, rộng 1366.
