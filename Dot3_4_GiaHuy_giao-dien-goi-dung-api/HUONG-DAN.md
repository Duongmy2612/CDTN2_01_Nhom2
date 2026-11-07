# Giao diện gọi đúng API của backend, nhãn tháng ở Tổng quan [PB-03, FR-07, FR-19] · Lê Gia Huy

Phần này nhắm vào yêu cầu buổi 7: **"đảm bảo frontend gọi đúng API backend"**:
- **Kiểm thử tự động `backend/tests/test_frontend_contract.py`:** đọc mã React (`src/api/client.js` và mọi màn hình) rồi đối chiếu với hợp đồng API do FastAPI sinh ra. Không cần chạy trình duyệt nên CI chạy được mỗi lần mở PR. Bắt các lỗi chỉ lộ ra khi ghép hai phía:
  - đường dẫn, phương thức không có thật, hoặc API có mà giao diện không gọi;
  - gõ sai tên tham số (VD `forecastble`). Backend sẽ **bỏ qua im lặng**, màn hình hiện sai mà không báo lỗi;
  - trường thân yêu cầu không có trong API; `page_size` dưới mức tối thiểu 5 (backend trả 422);
  - tên biểu đồ EDA, tên bảng CSV không có ở backend; bộ lọc tab Phân tích không khớp API #7/#8; hàm thừa trong client.js.

  Có **51 ca**, trong đó 43 ca sinh tự động theo từng lời gọi `api.xxx(...)` trong giao diện.
- **Tab Tổng quan:** ô "Tháng gần nhất (09/2012)" đổi thành **"Tháng trọn vẹn gần nhất (09/2012)"**, rê chuột thấy "Dữ liệu đến 26/10/2012". Lý do: tab Phân tích có cả 10/2012 nên chữ "gần nhất" gây hiểu nhầm. Ô này dùng `last_full_month`, giống tab Dự báo và cảnh báo.
- **`client.js`, lỗi tích hợp khi mất kết nối:** chạy qua `npm run dev` (cả trong Docker) mà backend tắt thì Vite trả **500 với thân rỗng**. Giao diện cũ không nhận ra trường hợp này nên chỉ hiện "Request failed with status code 500". Nay hiện đúng "Không kết nối được backend (cổng 8000)…". Thông báo cũng không còn ghi cứng `http://localhost:8000` (trong Docker backend là `http://backend:8000`). Chú thích đầu tệp không còn ghi phiên bản cũ 1.1.0.

## 1. Lấy code mới nhất

Nếu máy chưa có thư mục dự án hoặc chưa cài môi trường (đã làm ở Đợt 1–2 thì bỏ qua):
```bash
git clone https://github.com/Duongmy2612/CDTN2_01_Nhom2.git
cd CDTN2_01_Nhom2
git config user.name  "Lê Gia Huy"
git config user.email "<email tài khoản GitHub của bạn>"
python -m venv .venv && .venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r backend/requirements-dev.txt
cd frontend && npm ci && cd ..
```
Chép `reviews_sample_100k.csv` (trong gói zip buổi 6) vào `backend/data/sample/`; `backend/.env` có khóa Gemini thì chép sang luôn.

Mỗi lần làm:
```bash
git checkout giahuy
git pull origin main
```

## 2. Chép file

Giải nén zip, mở thư mục `files`, chọn tất cả, chép vào thư mục `CDTN2_01_Nhom2` và chọn **Replace**. Không có file nào cần xóa.

Kiểm tra bằng `git status`, phải thấy đúng như sau:
```
 M frontend/src/api/client.js
 M frontend/src/tabs/OverviewTab.jsx
?? backend/tests/test_frontend_contract.py
```

## 3. Kiểm tra

```bash
pytest backend/tests -q                                   # phải 0 failed (nếu bạn gộp đầu tiên: 69 passed)
pytest backend/tests/test_frontend_contract.py -q         # 51 passed
cd frontend && npm run build && cd ..                     # build không lỗi (CI cũng chạy lệnh này)
```
**Thử cho kiểm thử bắt lỗi** (nên làm để hiểu và để demo cho thầy):
1. Mở `frontend/src/tabs/ForecastTab.jsx`, sửa `forecastable: true` thành `forecastble: true`, lưu lại.
2. `pytest backend/tests/test_frontend_contract.py -q`: thấy **1 failed** với thông báo
   `api.products gửi tham số 'forecastble' – API /api/products chỉ nhận [...]`.
3. Sửa lại như cũ (hoặc `git checkout frontend/src/tabs/ForecastTab.jsx`) và chạy lại, phải còn 51 passed.

Chạy giao diện:
```bash
uvicorn backend.main:app --port 8000
# cửa sổ thứ hai:
cd frontend && npm run dev
```
- [ ] Tab **Tổng quan** (bộ mẫu 100.000) → ô tối màu ghi **"Tháng trọn vẹn gần nhất (09/2012)" 77,6**, bên cạnh "Dự báo 10/2012 77,9". Rê chuột vào chữ thì hiện "Dữ liệu đến 26/10/2012; tháng chưa trọn không tính".
- [ ] Tắt uvicorn (Ctrl+C) rồi tải lại trang (F5) → thông báo **"Không kết nối được backend (cổng 8000) – hãy kiểm tra máy chủ FastAPI hoặc container backend đang chạy"** (bản cũ hiện "Request failed with status code 500"). Bật lại uvicorn.

Có gì sai thì **chưa commit**, chụp màn hình gửi My.

## 4. Commit (2 commit, dùng tài khoản Git của bạn)

```bash
git add frontend/src/api/client.js frontend/src/tabs/OverviewTab.jsx
git commit -m "fix(ui): ghi rõ tháng trọn vẹn gần nhất ở Tổng quan, thông báo lỗi kết nối đúng cả khi chạy Docker [FR-07,FR-19]"

git add backend/tests/test_frontend_contract.py
git commit -m "test(frontend): kiểm tra giao diện gọi đúng đường dẫn, tham số, trường dữ liệu của backend [PB-03]"
```
Sau lệnh commit, `git status` phải sạch.

## 5. Push + PR

```bash
git push origin giahuy
```
GitHub → **Compare & pull request** → base `main` ← compare `giahuy`
- Title: `Giao diện gọi đúng API của backend, nhãn tháng ở Tổng quan [PB-03, FR-07, FR-19]`
- Description:
  ```
  Người làm: Lê Gia Huy – tích hợp frontend – backend (sprint xây dựng 2, buổi 7)
  - backend/tests/test_frontend_contract.py (51 ca): đọc client.js và mọi màn hình, đối chiếu với app.openapi() – đường dẫn/phương thức, tên tham số, trường thân yêu cầu, giới hạn page_size, tên biểu đồ EDA, tên bảng CSV, bộ lọc tab Phân tích; mọi API đều có hàm gọi và mọi hàm đều được dùng. Chạy trong CI.
  - Tab Tổng quan: "Tháng trọn vẹn gần nhất" (last_full_month) – khớp với tab Dự báo, cảnh báo
  - client.js: Vite trả 500 rỗng khi backend tắt → nay báo đúng "Không kết nối được backend" (trước đây "Request failed with status code 500"), đúng cả khi chạy Docker
  Cách kiểm tra: pytest backend/tests/test_frontend_contract.py -q; thử đổi forecastable → forecastble trong ForecastTab.jsx sẽ thấy 1 failed
  ```

Nhắn Zalo nhóm: "Huy đã mở PR Giao diện gọi đúng API".

## 5b. Việc chuyển từ buổi 6: chạy trợ lý AI hàng loạt bằng Gemini thật (cần khóa Gemini và toàn bộ Reviews.csv)

Làm sau khi PR ở trên đã được gộp. Đây là mục 1 bảng 7.3 báo cáo buổi 6.
```bash
git checkout giahuy
git pull origin main
```
Trên giao diện chọn **Toàn bộ Reviews.csv** (cần file `backend/data/raw/Reviews.csv`) và chờ xử lý xong. Sau đó tắt uvicorn rồi chạy:
```bash
python scripts/run_ai_batch.py --limit 3       # chạy thử 3 sản phẩm + 9 chủ đề, xem có lỗi khóa/mạng không
python scripts/run_ai_batch.py --refresh       # chạy đủ 39 sản phẩm rủi ro Cao + 9 chủ đề (mất vài phút)
```
Kết quả nằm trong `docs/ai_batch/`. Gửi file `nfr10_cham_diem_<ngày>.csv` cho My và Kaysone chấm NFR-10. Rồi:
```bash
git add docs/ai_batch/
git commit -m "docs(ai): kết quả chạy trợ lý AI hàng loạt bằng Gemini thật – 39 sản phẩm, 9 chủ đề [PB-19,NFR-10]"
git push origin giahuy
```
Mở PR thứ hai: `Kết quả chạy trợ lý AI hàng loạt bằng Gemini thật [PB-19, NFR-10]`.

## 6. Hiểu phần mình làm (để trình bày với thầy)

1. **Vì sao cần kiểm thử này:** frontend (JavaScript) và backend (Python) là hai chương trình riêng, nối với nhau chỉ qua URL và tên tham số. Gõ sai một tên tham số thì cả hai phía vẫn chạy, không ai báo lỗi: FastAPI bỏ qua tham số lạ, nên màn hình hiện dữ liệu chưa lọc. Đây là loại lỗi tích hợp "module chạy riêng thì tốt, ghép lại mới sai" mà bài giảng buổi 7 nêu.
2. **Nguồn sự thật là hợp đồng API:** `app.openapi()` là đặc tả FastAPI tự sinh từ các lớp Pydantic (`backend/schemas/api.py`), cùng nội dung với `docs/openapi.json`. Kiểm thử so mã giao diện với đặc tả này, không so với một danh sách viết tay.
3. **Cách đọc mã React:** dùng biểu thức chính quy và một hàm đếm ngoặc (`_balanced`) để lấy đường dẫn trong `http.get('/...')` và các khóa của đối tượng như `api.products({ q, risk, page_size: 15 })`. Cách này đủ cho cách viết của dự án, không cần cài thêm thư viện phân tích JavaScript.
4. **Kiểm thử chạy trong CI:** file nằm trong `backend/tests` nên `pytest` của GitHub Actions tự chạy mỗi khi mở PR. Ai sửa API ở backend mà quên sửa giao diện (hoặc ngược lại) thì PR báo đỏ ngay.
5. **Lỗi 500 rỗng:** khi chạy dev, trình duyệt không gọi thẳng backend mà gọi Vite (cổng 5173), Vite chuyển tiếp `/api` sang cổng 8000. Backend tắt thì Vite tự trả 500 không có nội dung. Lỗi 500 thật của FastAPI luôn có nội dung, nên `status === 500 && !data` nghĩa là mất kết nối.
6. **Tháng trọn vẹn:** tab Tổng quan lấy chuỗi từ API #16. Chuỗi này dừng ở `last_full_month` (09/2012) vì 10/2012 mới có dữ liệu đến ngày 26. Đổi nhãn để người xem không so nhầm với cột 10/2012 ở tab Phân tích.
