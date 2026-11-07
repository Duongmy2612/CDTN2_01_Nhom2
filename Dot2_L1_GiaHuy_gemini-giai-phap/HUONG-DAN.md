# Kiểm tra độ đầy đủ của giải pháp Gemini, chạy hàng loạt [PB-19] · Lê Gia Huy

Buổi 6, PB-19: Gemini từng trả hành động bị cắt (“Xem xét nghiên cứu dòng sản phẩm”). Thêm lớp kiểm tra nội dung, gọi lại tối đa 3 lần, gắn cờ vàng trên giao diện; script chạy trợ lý AI hàng loạt và chấm NFR-10.

> Ngày commit trên GitHub là ngày bạn commit (hôm nay) – **không chỉnh ngày**. Nhãn `[B4]`, `[B5]`, `[PB-xx]` trong lời commit cho biết phần việc thuộc buổi/mục backlog nào; thời gian thực hiện gốc đã ghi trong nhật ký đề tài.

Đợt 2 · lượt 1 – làm **song song** với các bạn cùng lượt, ngay sau khi Đợt 1 đã gộp xong (thẻ `v1.2.0`).

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

## 2. Chép file và commit (4 commit, dùng tài khoản Git của bạn)

Zip có 4 thư mục `commit1`…`commit4` – làm **lần lượt**: chép một thư mục → kiểm tra `git status` → commit → mới chép thư mục tiếp theo.

### Commit 1/4

Mở `commit1` → chọn tất cả → chép vào thư mục `CDTN2_01_Nhom2` → chọn **Replace**. `git status` phải thấy đúng:
```
 M backend/tests/conftest.py
```
```bash
git add backend/tests/conftest.py
git commit -m "test(ai): kiểm thử không dùng khóa Gemini thật trong backend/.env [PB-19]"
```

### Commit 2/4

Mở `commit2` → chọn tất cả → chép vào thư mục `CDTN2_01_Nhom2` → chọn **Replace**. `git status` phải thấy đúng:
```
 M backend/core/config.py
 M backend/schemas/api.py
 M backend/services/ai_service.py
 M backend/tests/fake_gemini.py
 M backend/tests/test_contract.py
```
```bash
git add backend/core/config.py backend/schemas/api.py backend/services/ai_service.py backend/tests/fake_gemini.py backend/tests/test_contract.py
git commit -m "feat(ai): kiểm tra độ đầy đủ của giải pháp Gemini, gọi lại khi hành động bị cắt [PB-19]"
```

### Commit 3/4

Mở `commit3` → chọn tất cả → chép vào thư mục `CDTN2_01_Nhom2` → chọn **Replace**. `git status` phải thấy đúng:
```
 M backend/services/ai_service.py
 M frontend/src/components/InsightView.jsx
```
```bash
git add backend/services/ai_service.py frontend/src/components/InsightView.jsx
git commit -m "feat(ui): tô vàng giải pháp thiếu ý, kiểm tra lại kết quả cũ trong bộ đệm [PB-19]"
```

### Commit 4/4

Mở `commit4` → chọn tất cả → chép vào thư mục `CDTN2_01_Nhom2` → chọn **Replace**. `git status` phải thấy đúng:
```
 M backend/tests/test_contract.py
?? scripts/nfr10_score.py
?? scripts/run_ai_batch.py
```
```bash
git add backend/tests/test_contract.py scripts/nfr10_score.py scripts/run_ai_batch.py
git commit -m "feat(ai): script chạy trợ lý AI hàng loạt và tính điểm NFR-10 [PB-19,NFR-10]"
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
- Title: `Kiểm tra độ đầy đủ của giải pháp Gemini, chạy hàng loạt [PB-19]`
- Description:
  ```
  Người làm: Lê Gia Huy – Buổi 6 – sprint xây dựng 1 (bản 1.3.0)
  - conftest đặt GEMINI_API_KEY rỗng: kiểm thử không gọi Gemini thật
  - Hành động ≥ 8 từ, không kết thúc bằng từ nối, chỉ số ≥ 4 từ; thiếu → gọi lại kèm danh sách cần viết lại; vẫn thiếu → complete = false
  - Giao diện tô vàng giải pháp thiếu ý, nhắc “Gọi lại”
  - scripts/run_ai_batch.py, scripts/nfr10_score.py (tỷ lệ khớp, Cohen's κ)
  ```

Nhắn Zalo nhóm: "GiaHuy đã mở PR Kiểm tra độ đầy đủ của giải pháp Gemini, chạy hàng loạt".

## 5. Hiểu phần mình làm (để trình bày với thầy)

1. Lược đồ JSON chỉ bảo đảm **đúng định dạng**, không bảo đảm **đủ ý** – vì vậy thêm quy tắc đo được (độ dài, từ cuối).
2. Kiểm thử dùng máy chủ Gemini giả lập trả đúng câu bị cắt của buổi 5 rồi câu đủ ý → kiểm tra được việc gọi lại mà không cần mạng.
