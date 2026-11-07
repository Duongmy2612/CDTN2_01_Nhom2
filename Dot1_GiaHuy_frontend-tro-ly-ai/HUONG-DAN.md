# Frontend React 9 tab, wireframe, trợ lý AI Gemini [B4–B5] · Lê Gia Huy

Phần frontend và trợ lý AI của buổi 4–5: khung React (Hello World buổi 4), wireframe 10 màn hình, dashboard 9 tab, AIService gọi Gemini kèm chatbot.

> Ngày commit trên GitHub là ngày bạn commit (hôm nay) – **không chỉnh ngày**. Nhãn `[B4]`, `[B5]`, `[PB-xx]` trong lời commit cho biết phần việc thuộc buổi/mục backlog nào; thời gian thực hiện gốc đã ghi trong nhật ký đề tài.

Đợt 1 – làm **sau** khi nhóm trưởng đã khởi tạo kho và tạo nhánh; 4 bạn làm **song song** (không ai đụng tệp của ai).

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

## 2. Chép file và commit (4 commit, dùng tài khoản Git của bạn)

Zip có 4 thư mục `commit1`…`commit4` – làm **lần lượt**: chép một thư mục → kiểm tra `git status` → commit → mới chép thư mục tiếp theo.

### Commit 1/4

Mở `commit1` → chọn tất cả → chép vào thư mục `CDTN2_01_Nhom2` → chọn **Replace**. `git status` phải thấy đúng:
```
?? Dockerfile.frontend
?? frontend/
```
```bash
git add Dockerfile.frontend frontend/
git commit -m "chore(frontend): khung React + Vite + Tailwind, gọi được /api/health [B4]"
```

### Commit 2/4

Mở `commit2` → chọn tất cả → chép vào thư mục `CDTN2_01_Nhom2` → chọn **Replace**. `git status` phải thấy đúng:
```
?? docs/
```
```bash
git add docs/
git commit -m "docs(design): wireframe 10 màn hình [B5]"
```

### Commit 3/4

Mở `commit3` → chọn tất cả → chép vào thư mục `CDTN2_01_Nhom2` → chọn **Replace**. `git status` phải thấy đúng:
```
?? frontend/src/App.jsx
?? frontend/src/api/
?? frontend/src/components/
?? frontend/src/lib/
?? frontend/src/pages/
?? frontend/src/tabs/
```
```bash
git add frontend/src/App.jsx frontend/src/api/ frontend/src/components/ frontend/src/lib/ frontend/src/pages/ frontend/src/tabs/
git commit -m "feat(ui): dashboard 9 tab, màn hình tải dữ liệu, lớp gọi 20 API [B5]"
```

### Commit 4/4

Mở `commit4` → chọn tất cả → chép vào thư mục `CDTN2_01_Nhom2` → chọn **Replace**. `git status` phải thấy đúng:
```
?? backend/services/ai_service.py
?? backend/tests/
?? frontend/src/components/Chatbot.jsx
?? frontend/src/components/InsightView.jsx
?? frontend/src/components/Markdown.jsx
?? frontend/src/lib/chatStore.js
?? frontend/src/tabs/AiTab.jsx
```
```bash
git add backend/services/ai_service.py backend/tests/ frontend/src/components/Chatbot.jsx frontend/src/components/InsightView.jsx frontend/src/components/Markdown.jsx frontend/src/lib/chatStore.js frontend/src/tabs/AiTab.jsx
git commit -m "feat(ai): trợ lý AI Gemini – nguyên nhân có bằng chứng, chatbot 10 công cụ đọc dữ liệu [B5]"
```

Nếu PR của bạn khác đã được gộp trước khi bạn `git pull`, `git status` có thể ghi chi tiết hơn (VD `?? docs/wireframes/` thay vì `?? docs/`) – vẫn đúng, miễn chỉ có tệp của bạn; lệnh `git add` giữ nguyên.

Sau commit cuối, `git status` phải sạch.

## 3. Kiểm tra

Phần này chưa chạy được riêng vì cần đủ phần của cả nhóm (VD router cần service của bạn khác). Nhóm trưởng chạy `pytest` và mở giao diện **sau khi gộp đủ 4 PR của Đợt 1** (kết quả phải là 16 passed).
Riêng phần giao diện chạy được độc lập: `cd frontend && npm ci && npm run build` phải báo `✓ built`. (Thư mục `node_modules/`, `dist/` đã bị `.gitignore` chặn.)

Có gì sai thì **chưa push**, chụp màn hình gửi My.

## 4. Push + PR

```bash
git push origin giahuy
```
GitHub → **Compare & pull request** → base `main` ← compare `giahuy`
- Title: `Frontend React 9 tab, wireframe, trợ lý AI Gemini [B4–B5]`
- Description:
  ```
  Người làm: Lê Gia Huy – Buổi 1–5 (khởi tạo, thiết kế, bản mẫu 1.2)
  - Khung React 18 + Vite 5 + Tailwind, proxy /api tới backend
  - Wireframe 10 màn hình (docs/wireframes)
  - Dashboard 9 tab, màn hình tải dữ liệu, src/api/client.js ánh xạ 20 API
  - AIService: phân tích nguyên nhân – giải pháp có review_id bằng chứng, chatbot gọi 10 công cụ đọc dữ liệu; máy chủ Gemini giả lập cho kiểm thử
  ```

Nhắn Zalo nhóm: "GiaHuy đã mở PR Frontend React 9 tab, wireframe, trợ lý AI Gemini".

## 5. Hiểu phần mình làm (để trình bày với thầy)

1. Frontend không tự tính số liệu: mọi màn hình gọi API qua `src/api/client.js`; khi chạy dev, Vite chuyển `/api` sang cổng 8000.
2. Trợ lý AI chỉ nhận nguyên nhân có **review_id bằng chứng tồn tại thật** trong dữ liệu – loại bỏ nguyên nhân Gemini bịa ra (NFR-10).
