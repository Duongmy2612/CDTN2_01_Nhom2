# FoodReview Insight

Ứng dụng web phân tích và dự báo mức độ hài lòng của khách hàng từ dữ liệu đánh giá thực phẩm trên Amazon
(Chuyên đề tốt nghiệp 2 – Khoa CNTT, ĐH Văn Lang; GVHD: ThS. Hà Đồng Hưng; giảng viên giảng dạy: ThS. Nguyễn Văn Trung). Kiến trúc phân lớp: React (trình bày) – FastAPI (nghiệp vụ) –
CSV/joblib/JSON (dữ liệu); Gemini API là dịch vụ ngoài, chỉ backend gọi.

Tải file CSV (định dạng Amazon Fine Food Reviews) → backend chạy nền 7 bước: kiểm tra → làm sạch R1–R9 → EDA →
huấn luyện 3 mô hình (NB, Linear SVM, Logistic Regression) trên dữ liệu đã làm sạch, dùng Logistic Regression
(cấu hình chọn trên validation ở notebook 02) để dự đoán, kèm kiểm tra theo thời gian (học trên dữ liệu cũ, kiểm tra năm cuối) →
chủ đề phàn nàn (NMF) → dự báo chỉ số hài lòng (ETS) → gắn mức rủi ro từng sản phẩm, kèm kiểm tra ngược quy tắc.
Dashboard 9 tab đọc kết quả thật qua 20 API.

## 0. Chạy nhanh bằng gói nộp kèm (khuyên dùng – từ bản 1.5.1)
Gói `FoodReview_Insight_v1.5.1.zip` có sẵn giao diện đã dựng (`frontend/dist`), bộ mẫu 100.000 đánh giá và bộ kết quả demo
(`demo_data/`: toàn bộ Reviews.csv đã xử lý, mô hình, kết quả trợ lý AI Gemini chạy ngày 07/11). Chỉ cần Python 3.11:
1. Giải nén → nhấp đúp `chay_ung_dung.bat` (Windows) / `chay_ung_dung.command` (macOS) hoặc chạy `./chay_ung_dung.sh` (Linux).
2. Lần đầu script tự tạo `.venv`, cài `backend/requirements.txt` (tải khoảng 140 MB), chép bộ kết quả demo vào `backend/`;
   khi cửa sổ báo “Sẵn sàng … http://localhost:8000” thì trình duyệt tự mở dashboard. Lần sau mở được sau khoảng 10 giây.
3. Giao diện và API chạy chung một cổng (`http://localhost:8000`, tài liệu API ở `/docs`) – không cần Node.js, không cần mạng
   sau lần cài đầu, không cần khóa Gemini (trợ lý AI đọc kết quả đã lưu, chatbot trả lời theo quy tắc).

Hướng dẫn cho người không lập trình, cách khôi phục bộ kết quả demo và xử lý sự cố: `HUONG_DAN_CAI_DAT.md`.
Chạy từ mã nguồn trên GitHub (không có `demo_data/`): làm mục 1 rồi `python run_app.py` – script tự dựng giao diện nếu máy có Node.js.

## 1. Chuẩn bị (≈ 10 phút)
1. Cài Python 3.11, Node.js 22 LTS (hoặc Docker Desktop).
2. **Dữ liệu** (không đưa lên GitHub vì dung lượng lớn – xem `.gitignore`): tải `Reviews.csv` từ Kaggle (Amazon Fine Food Reviews,
   MD5 `c3c950ae0be8b0736477c89d052d33fd`) vào `backend/data/raw/` (tạo thư mục nếu chưa có), rồi tạo bộ mẫu 100.000 dòng
   `backend/data/sample/reviews_sample_100k.csv` bằng `python scripts/make_sample.py` – hoặc chép file mẫu này từ gói mã nguồn nhóm nộp kèm.
   Không có cả hai file vẫn chạy được: kéo thả bất kỳ file CSV đúng định dạng vào màn hình đầu.
3. **Khóa Gemini (cho trợ lý AI):** sao chép `backend/.env.example` thành `backend/.env`, điền
   `GEMINI_API_KEY=<khóa của bạn>`, lưu file rồi khởi động lại backend. Hỗ trợ khóa Google AI Studio (`AIza…`)
   và khóa Vertex AI chế độ express (`AQ.…`) – backend tự nhận loại khóa và tự chọn model còn hoạt động.
   Chưa có khóa: trợ lý vẫn trả lời câu hỏi về dữ liệu theo quy tắc; phân tích nguyên nhân dùng chủ đề NMF.

## 2. Chạy bằng Docker (một lệnh)
```bash
docker compose up --build        # backend: http://localhost:8000/docs · frontend: http://localhost:5173
```

## 3. Chạy không dùng Docker
```bash
python3.11 -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r backend/requirements-dev.txt
uvicorn backend.main:app --port 8000                        # chạy từ thư mục gốc dự án
cd frontend && npm ci && npm run dev                        # cửa sổ thứ hai → http://localhost:5173
```
Mở http://localhost:5173 → chọn “Mẫu 100.000 đánh giá” (≈ 2–3 phút) hoặc “Toàn bộ Reviews.csv” (≈ 3–4 phút),
hoặc kéo thả file CSV của bạn. Kết quả lưu ở `backend/data/processed`, `backend/models`, `backend/cache` và được nạp lại
khi khởi động máy chủ, nên lần sau mở ứng dụng vào thẳng dashboard.

Hoặc một lệnh, một cổng (bản 1.5.1): `python run_app.py` – tạo `.venv`, cài thư viện, dựng giao diện (`npm run build`) nếu
chưa có, rồi chạy giao diện + API ở http://localhost:8000 (xem mục 0).

Cũng có thể gọi API trực tiếp: `curl -X POST "http://localhost:8000/api/data/sample?kind=full"` rồi theo dõi
`GET /api/jobs/{job_id}`.

## 4. Chức năng chính (9 tab)
| Tab | Nội dung |
|---|---|
| Tổng quan | Chỉ số hài lòng, KPI, điểm cần chú ý, xu hướng + dự báo 12 tháng, phân bố sao, sản phẩm rủi ro, chủ đề phàn nàn, nhật ký làm sạch, giới hạn của phân tích |
| Phân tích (EDA) | Bộ lọc tháng/sao/cảm xúc/sản phẩm; số đánh giá và điểm theo tháng; độ dài; từ đặc trưng (log-odds); chất lượng dữ liệu gốc |
| Mô hình ML | So sánh B0/NB/SVM/LR, ma trận nhầm lẫn 3 lớp/5 sao, từ khóa tăng/giảm số sao, đánh giá mâu thuẫn, kiểm tra theo thời gian, đối chiếu notebook 02 |
| Tự nhập dự đoán | Dự đoán số sao, cảm xúc, chỉ số hài lòng, tô màu từ ảnh hưởng, chủ đề + gợi ý hành động, lịch sử |
| Sản phẩm & cảnh báo | Bảng 67 nghìn sản phẩm: tìm, lọc, sắp xếp, phân trang; 2 loại tín hiệu (đang giảm điểm / tiêu cực kéo dài); kiểm tra ngược quy tắc; ngăn chi tiết sản phẩm có dự báo và phân tích AI |
| Chủ đề phàn nàn | 9 chủ đề NMF, từ khóa, xu hướng, đánh giá mẫu, gợi ý; phân tích nguyên nhân bằng AI |
| Dự báo | Toàn bộ (ETS) hoặc từng sản phẩm (ARIMA(0,1,1)), 3/6/12 tháng, khoảng tin cậy 95%, kiểm tra lùi |
| Trợ lý AI | Nguyên nhân – giải pháp có bằng chứng review_id; chatbot đọc dữ liệu hệ thống qua 10 công cụ + kiến thức chung |
| Báo cáo | PDF tiếng Việt, 6 bảng CSV (cảnh báo, chủ đề, dự đoán, chuỗi tháng, dự báo, chỉ số mô hình), thông tin phiên, đổi dữ liệu / xóa phiên |

## 5. Tái lập kết quả phân tích của buổi 5 (EDA, baseline)
```bash
python -m ipykernel install --user --name fri311
cd notebooks
jupytext --to ipynb 0*_*.py
jupyter nbconvert --to notebook --execute --inplace 01_eda.ipynb   # lần lượt 01 → 05
```
Thứ tự bắt buộc: 01 (tạo `reviews_clean.csv`) → 02, 03, 04, 05; 06 (thực nghiệm E-T2 của sprint 1) dùng kết quả của 01. Mọi bước dùng `random_state = 42`.

## 6. Kiểm thử
```bash
pytest backend/tests -q
```
128 ca kiểm thử (11 tệp) chạy trên dữ liệu tổng hợp (`backend/tests/synth.py`) trong thư mục tạm, không ghi đè dữ liệu thật
(`pytest.ini` ở thư mục gốc đã khai báo `pythonpath = .` nên chạy thẳng lệnh trên, không cần cài gói):
đủ 20 API, định dạng lỗi, quy tắc làm sạch R1–R9 trên file có lỗi (UserId trống, Score sai, Text rỗng, bản ghi trùng),
pipeline 7 bước, mọi API trả dữ liệu đúng lược đồ, kiểm tra theo thời gian (giai đoạn học trước giai đoạn kiểm tra),
sắp xếp cảnh báo (cùng mức: giảm điểm mạnh nhất trước) và loại tín hiệu khớp lý do, kiểm tra ngược quy tắc, 6 bảng CSV, bộ lọc FR-09 (lọc đồng thời, mã sản phẩm không phân biệt hoa/thường,
bộ lọc mâu thuẫn → 422), tải file không dùng được không làm mất dữ liệu đang có, dự báo khi chuỗi có tháng trống,
dự đoán, cách chọn đánh giá bằng chứng gửi Gemini, PDF/CSV,
trợ lý AI ở chế độ quy tắc và chế độ Gemini (máy chủ Gemini giả lập `backend/tests/fake_gemini.py`: gọi công cụ, tự chuyển model khi 404,
loại nguyên nhân có bằng chứng không tồn tại, gọi lại khi giải pháp thiếu ý, khóa sai → suy giảm có kiểm soát),
chạy trợ lý AI hàng loạt và tính điểm NFR-10, các ca kiểm thử chấp nhận FR Must của `scripts/acceptance_test.py`.
Từ bản 1.4.0 thêm kiểm thử tích hợp (buổi 7): `test_frontend_contract.py` đọc mã React và đối chiếu với hợp đồng API
(đường dẫn, tên tham số, trường thân yêu cầu, giới hạn page_size, tên biểu đồ, tên bảng CSV – 43 ca sinh theo từng lời gọi
trong giao diện); `test_integration.py` kiểm tra cùng một con số giống nhau trên mọi màn hình; `test_predict_topics.py`,
`test_smoke_partial.py` cho các sửa đổi của sprint xây dựng 2; `test_acceptance.py` chạy kiểm thử chấp nhận FR Must (buổi 6).
Từ bản 1.5.0 thêm 41 ca kiểm thử hồi quy cho các lỗi tìm được ở buổi 8 (mỗi lỗi B01–B11 có ít nhất một ca, chạy trên 1.4.0 thì
35/41 ca thất bại): `test_data_robustness.py` (Time mili-giây, Id trùng/không phải số, file chỉ có tiêu đề, chỉ mục từ khóa),
`test_upload_robustness.py` (dấu phân cách `;` tab `|`, bảng mã cp1252, BOM, tháng 13, tải file khi đang có job), `test_predict_robustness.py` (văn bản
không có từ nào mô hình biết, đếm từ sau khi bỏ HTML, cờ độ tin cậy thấp), `test_frontend_robustness.py` (giao diện hiển thị
cảnh báo kiểm tra file, bộ đếm từ khớp máy chủ).
Bản 1.5.1 thêm `test_packaging.py` (7 ca): backend phục vụ giao diện đã dựng ở cùng cổng mà không che `/api`, `/docs`, API không
có vẫn trả 404 dạng JSON, không đọc được tệp ngoài `frontend/dist`, file chạy `.bat` xuống dòng CRLF và chỉ dùng ký tự ASCII,
`run_app.py` bỏ qua cổng đang bận nhưng dùng lại được cổng vừa tắt, trang `/docs` không tải gì từ Internet.
Kiểm thử không bao giờ dùng khóa thật trong `backend/.env` (conftest đặt khóa rỗng trước khi nạp ứng dụng).
CI trên GitHub (`.github/workflows/ci.yml`) chạy lại `pytest` và `npm run build` mỗi lần mở pull request vào `main`.

**Chạy thử toàn hệ thống và kiểm tra tích hợp (buổi 7)** – khi backend (và frontend) đang chạy:
```bash
python scripts/smoke_test.py --base http://localhost:5173        # gọi 27 lời gọi API qua frontend → docs/test_report/smoke_*.md
python scripts/integration_check.py --base http://localhost:5173 # 17 đối chiếu số liệu giữa các màn hình → integration_*.md
```

**Đánh giá mô hình và kiểm thử hành vi (buổi 8)** – sau khi backend đã xử lý dữ liệu:
```bash
FRI_WORK_DIR=<thư mục dữ liệu của backend> python scripts/evaluate_models.py --kind full   # → docs/test_report/model_eval_*.md
python scripts/behavior_check.py                                    # 15 câu MFT + 5 cặp INV + 3 cặp DIR → behavior_*.md
```
`evaluate_models.py` tính lại trên toàn bộ tập kiểm tra: P/R/F1 từng lớp, ma trận nhầm lẫn, độ chính xác theo nhóm (độ dài,
năm, độ phổ biến sản phẩm, độ tự tin), nhóm lỗi tự động (phủ định, đảo ý “but”), sai số dự báo theo số bước, kiểm tra lùi dự
báo theo sản phẩm, độ nâng (lift) của quy tắc cảnh báo, độ phủ từ khóa chủ đề.

**Kiểm thử chấp nhận FR Must (biên bản kiểm thử):** `python scripts/acceptance_test.py` (bộ mẫu 100.000 dòng, ≈ 3 phút) hoặc
`--full` (toàn bộ Reviews.csv, ≈ 5 phút). Script tải file qua API trong thư mục tạm (không đụng dữ liệu đang dùng), chạy 14 ca
kiểm thử cho 14 yêu cầu chức năng mức Must, so mỗi kết quả với phép tính độc lập bằng pandas và ghi biên bản vào
`docs/test_report/acceptance_<sample|full>_<ngày>.md`.

## 7. Cấu trúc thư mục
```
run_app.py · chay_ung_dung.bat|.command|.sh · khoi_phuc_demo.bat|.command · HUONG_DAN_CAI_DAT.md   (bản đóng gói 1.5.1)
demo_data/ processed · models · cache – bộ kết quả demo, chỉ có trong gói zip (không đưa lên GitHub)
backend/   main.py · core/ (config, state, deps, errors, frontend) · routers/ (7 router, 20 API) · schemas/api.py (hợp đồng API 1.5.0)
           services/ data · eda · model · topic · forecast · alert · ai · report · pipeline
           data/ (raw, sample, processed) · models/ · cache/ · tests/
frontend/  React 18 + Vite 5 + Tailwind 3 + Recharts · src/api/client.js ánh xạ 20 API · src/tabs/ (9 tab)
notebooks/ 01_eda · 02_model_baseline · 03_topic_baseline · 04_forecast_baseline · 05_risk_rule · 06_topic_e_t2 (+ figures/, outputs/)
docs/      openapi.json · schema_sqlite.sql · erd.png · wireframes/ · screens/ · test_report/ (biên bản kiểm thử) · demo/ (kịch bản demo) · ai_batch/
scripts/   make_sample.py · export_openapi.py · acceptance_test.py · run_ai_batch.py · nfr10_score.py · smoke_test.py · integration_check.py
           evaluate_models.py · behavior_check.py (buổi 8)
.github/   workflows/ci.yml (pytest + build) · pull_request_template.md (danh sách kiểm tra DoD)
```

## 8. Quy ước làm việc
Kho chung `https://github.com/Duongmy2612/CDTN2_01_Nhom2`: mỗi thành viên một nhánh (`diemmy`, `kaysone`, `hoangthuan`,
`giahuy`), commit bằng tài khoản Git của mình theo dạng `loại(phạm vi): mô tả [PB-xx]`, gộp vào `main` qua pull request khi CI
xanh; không đưa `backend/.env`, dữ liệu gốc, mô hình đã huấn luyện lên GitHub – chi tiết ở `CONTRIBUTING.md`. Đổi lược đồ API phải tăng `API_CONTRACT_VERSION` và cập nhật `docs/openapi.json`
(`python scripts/export_openapi.py`).
Sơ đồ trong tài liệu thiết kế: `python docs/diagrams/erd_build.py` (ERD) và
`mmdc -i docs/diagrams/seq_upload.mmd -o docs/seq_upload.png -c docs/diagrams/mmd_config.json -s 2` (tương tự cho seq_predict).

## 9. Thay đổi phiên bản 1.5.1 (buổi 9 – triển khai, đóng gói chạy độc lập)
Hợp đồng API giữ nguyên 1.5.0 (không đổi API nào); bản 1.5.1 chỉ thay cách cài đặt và chạy để demo không phụ thuộc máy lập trình.
- **Một cổng, không cần Node.js khi chạy:** có `frontend/dist` thì backend phục vụ luôn giao diện (`backend/core/frontend.py`) –
  `/api`, `/docs` giữ nguyên, API không có vẫn trả 404 JSON, không đọc được tệp ngoài `dist`. Chế độ phát triển cũ (Vite 5173) và
  Docker Compose không đổi.
- **Một lần nhấp đúp:** `run_app.py` + `chay_ung_dung.bat|.command|.sh` kiểm tra Python 3.10–3.12, tạo `.venv`, cài thư viện (ghi dấu
  theo mã băm requirements), dựng giao diện nếu thiếu, chép bộ kết quả demo ở lần đầu, chọn cổng trống, chờ `/api/health` rồi mở
  trình duyệt; `khoi_phuc_demo.*` đưa ứng dụng về bộ dữ liệu demo. Hướng dẫn cho người không lập trình: `HUONG_DAN_CAI_DAT.md`.
- **Gói nộp kèm** `FoodReview_Insight_v1.5.1.zip` (134 MB): mã nguồn, `frontend/dist`, bộ mẫu 100.000 dòng, `demo_data/`
  (toàn bộ Reviews.csv đã xử lý – phiên bản dữ liệu `3f6b35ee`, mô hình, 48 kết quả Gemini ngày 07/11); không có `backend/.env`.
- **Kiểm thử trên môi trường sạch** (21/11, Linux 2 CPU, Python 3.11, giải nén mới, `.venv` mới, không dùng bộ đệm pip): cài đặt
  25 – 104 giây ở 4 lần đo (phụ thuộc mạng, tải khoảng 140 MB thư viện), sẵn sàng sau 10 giây mỗi lần mở, ứng dụng dùng khoảng
  0,74 GB RAM. Gọi qua đúng cổng 8000: chạy thử 27/27 API, kiểm tra tích hợp 17/17 chỉ số, kiểm thử chấp nhận 14/14 FR Must
  (job bộ mẫu 160,9 giây) – biên bản trong `docs/test_report/buoi9_dong_goi/`.
- **Lỗi tìm được khi thử gói:** (1) tắt rồi mở lại ngay thì ứng dụng nhảy sang cổng 8001, 8002 vì bước chọn cổng coi cổng có kết nối
  cũ ở trạng thái TIME_WAIT là “bận” → bật `SO_REUSEADDR` giống uvicorn; (2) máy không có Internet thì trang tài liệu API `/docs`
  trắng vì Swagger UI tải JS/CSS từ CDN → đóng kèm `swagger-ui-dist` 5.34.1 trong `backend/static/swagger-ui` (Apache 2.0), bỏ
  `/redoc`. Cả hai có ca hồi quy trong `test_packaging.py`.
- **Chưa kiểm chứng trên máy thật:** file `.bat` (Windows) và `.command` (macOS) – máy kiểm thử là Linux; nhóm chạy thử và đo
  NFR-08 trên máy thành viên trước buổi 10.

## 10. Thay đổi phiên bản 1.5.0 (buổi 8 – kiểm thử và tinh chỉnh)
Nhóm kiểm thử ngoài luồng chính: 22 ca TC8, 22 file dữ liệu “xấu” (D01–D22), 40 lời gọi API với tham số biên/sai, 23 câu kiểm thử
hành vi mô hình, đo thời gian 20 lần/API trên bộ đầy đủ (393.890 đánh giá). Tìm được 11 lỗi (B01–B11): đã sửa hết 4 lỗi mức Cao, 4 lỗi
mức Trung bình và 3 lỗi Thấp; mỗi lỗi có ca kiểm thử hồi quy. Hợp đồng API 1.4.0 → 1.5.0: chỉ thêm mã lỗi, cảnh báo, trường tùy
chọn `low_confidence` và siết mẫu tháng – không đổi tên hay xóa trường nào.
- **Dữ liệu đầu vào (Dương Diễm My):** cột Time ghi bằng mili-giây làm cả pipeline dừng (OutOfBoundsDatetime) → tự nhận đơn vị
  theo trung vị, đổi sang giây, cảnh báo `TIME_MILLISECONDS` (B01); vài dòng Time âm/quá lớn làm hỏng cả file → bỏ đúng các
  dòng đó theo R2, cảnh báo `INVALID_TIME_ROWS` (B02); Id không phải số → lỗi ValueError, Id trùng → `review_id` trùng làm sai
  bằng chứng của trợ lý AI → đánh số lại, cảnh báo `ID_RENUMBERED` (B03, B04); file chỉ có dòng tiêu đề báo nhầm “Score không
  hợp lệ” → `NO_ROWS` (B07). Biểu đồ từ khóa có bộ lọc mất 2,1–2,4 giây trên bộ đầy đủ (vượt NFR-02) → chỉ mục từ khóa dựng
  một lần ở luồng nền ngay khi xử lý xong và lưu đĩa (khởi động lại chỉ nạp lại), mỗi lần lọc ≈ 0,07 giây (B10).
- **API tải file, tham số (Nguyễn Hoàng Thuận):** file Excel xuất bằng dấu `;` bị báo “Thiếu cột Score, Time, Text” → tự nhận
  dấu phân cách `, ; tab |` theo dòng tiêu đề, cảnh báo `DELIMITER_DETECTED` (B05); file cp1252/Latin-1 bị lỗi khó hiểu → đọc lại
  theo bảng mã dự phòng, cảnh báo `ENCODING_FALLBACK` (B06); tháng `2010-13` được chấp nhận → mẫu `yyyy-mm` tháng 01–12, thông
  điệp lỗi tiếng Việt (B11).
- **Dự đoán (KAYSONE Souk Anong):** câu tiếng Việt (0 % từ mô hình biết) vẫn ra “1 sao – Tích cực 49 %” → 422
  `TEXT_NOT_RECOGNIZED` (B08); `<br> <br> <br>` qua được điều kiện 3 từ → đếm từ sau khi làm sạch giống dữ liệu huấn luyện và
  dự đoán trên văn bản đã làm sạch (B09). Tinh chỉnh từ phân tích lỗi: dự đoán có xác suất nhóm cao nhất < 50 % (trên tập kiểm
  tra chỉ đúng ≈ 44 %) trả `low_confidence = true` kèm ghi chú. Thêm `scripts/evaluate_models.py`, `scripts/behavior_check.py`.
- **Giao diện (Lê Gia Huy):** trang tải file hiển thị các cảnh báo kiểm tra file (trước đây bị bỏ qua); bộ đếm từ của tab Dự đoán
  đếm giống máy chủ; nhãn “Độ tin cậy thấp”; chip tiếng Việt đổi thành “Tiếng Việt (ngoài phạm vi)”; tab Tổng quan ghi các chỉnh
  sửa tự động khi làm sạch.

## 11. Thay đổi phiên bản 1.4.0 (sprint xây dựng 2 – buổi 7: tích hợp các mô-đun)
Hợp đồng API 1.3.0 → 1.4.0, chỉ thêm trường tùy chọn nên tương thích ngược; `docs/openapi.json` đã xuất lại. Nhóm chạy cả
luồng trên bộ mẫu, đối chiếu cùng một con số trên mọi màn hình (`scripts/integration_check.py`): bản 1.3.0 khớp 13/17,
lệch ở 4 chỗ dưới đây; bản 1.4.0 khớp 17/17.
- **Tự nhập dự đoán kèm mã sản phẩm (PB-06 – KAYSONE Souk Anong):** trước đây backend bỏ qua mã sản phẩm, giao diện vẫn hiện nút
  “Xem sản phẩm” kể cả với mã không có → ngăn chi tiết toàn lỗi 404. Nay mã được chuẩn hóa như API #13, #15, #16; có mã → API #14
  trả `product` (số đánh giá, điểm TB, chỉ số hài lòng, mức rủi ro – cùng số với tab Sản phẩm) và giao diện so sánh với đánh giá
  vừa nhập; không có mã → vẫn dự đoán, ghi chú rõ, không mở ngăn chi tiết.
- **Chủ đề phàn nàn (PB-07 – KAYSONE Souk Anong):** API #9 trả `n_unassigned` (đánh giá tiêu cực không chứa từ nào trong từ điển
  NMF) để tổng các chủ đề + phần chưa xếp đúng bằng số đánh giá tiêu cực ở Tổng quan, Phân tích.
- **Tháng chưa trọn (PB-08 – Nguyễn Hoàng Thuận):** biểu đồ theo tháng của tab Phân tích có trường `partial`, vẽ cột nhạt và ghi
  chú cho tháng dữ liệu dừng giữa chừng (10/2012) – tab Tổng quan, Dự báo, cảnh báo đều dừng ở tháng trọn vẹn trước đó.
- **Docker Compose (PB-17 làm sớm, NFR-08 – Nguyễn Hoàng Thuận):** frontend chỉ chạy khi backend đã trả `/api/health`; bỏ
  `backend/data` (gắn bằng volume) khỏi ngữ cảnh build. `scripts/smoke_test.py` gọi 27 lời gọi API qua đúng địa chỉ người dùng
  mở (qua proxy của frontend) và ghi biên bản.
- **Giao diện gọi đúng API (PB-03 – Lê Gia Huy):** `backend/tests/test_frontend_contract.py` đối chiếu `src/api/client.js` và mọi
  màn hình với hợp đồng API trong CI; tab Tổng quan ghi rõ “Tháng trọn vẹn gần nhất”; thông báo mất kết nối đúng cả khi chạy Docker.
- **Kiểm tra tích hợp, quy trình Git (Dương Diễm My):** `scripts/integration_check.py` + `backend/tests/test_integration.py`;
  chuyển sang kho `CDTN2_01_Nhom2`, mỗi thành viên một nhánh (`CONTRIBUTING.md`, mẫu pull request).

## 12. Thay đổi phiên bản 1.3.0 (sprint xây dựng 1 – buổi 6)
Hợp đồng API 1.2.0 → 1.3.0, chỉ thêm trường tùy chọn nên tương thích ngược; `docs/openapi.json` đã xuất lại.
- **Trợ lý AI – kiểm tra độ đầy đủ của giải pháp (PB-19):** hành động Gemini trả về phải ≥ 8 từ, không kết thúc bằng từ nối
  (“và”, “của”, “dòng”…), chỉ số theo dõi ≥ 4 từ. Thiếu ý → gọi lại 1 lần kèm danh sách giải pháp cần viết lại (tối đa 3 lần gọi
  cho một phân tích, tính cả lần sửa lược đồ); vẫn thiếu thì gắn cờ `complete = false`, lý do `problem`, giao diện tô vàng và nhắc
  “Gọi lại”. Kết quả cũ trong bộ đệm được kiểm tra lại khi đọc. Trường mới của API #17: `n_calls`, `incomplete_actions`.
- **Chạy trợ lý AI hàng loạt:** `python scripts/run_ai_batch.py [--refresh]` phân tích mọi sản phẩm rủi ro Cao và mọi chủ đề, lưu bộ
  đệm, kiểm tra lại độc lập từng mã bằng chứng, xuất `docs/ai_batch/ai_batch_<ngày>.md|json` và bảng chấm điểm NFR-10
  (`nfr10_cham_diem_<ngày>.csv`: 21 sản phẩm chọn ngẫu nhiên + 9 chủ đề). Hai người chấm xong chạy
  `python scripts/nfr10_score.py <file.csv>` để có tỷ lệ khớp và Cohen's κ.
- **Bảng so sánh mô hình (PB-05):** thêm Precision, Recall trung bình macro 3 lớp (`prec_macro3`, `rec_macro3` – API #11) cho đủ
  Accuracy – Precision – Recall – F1-macro – MAE theo tiêu chí chấp nhận của backlog; có trong tab Mô hình, PDF, CSV `model_metrics`.
- **Thực nghiệm E-T2** (`notebooks/06_topic_e_t2`): bỏ tên nhóm hàng khỏi mô hình chủ đề – NPMI giảm 0,241 → 0,203 (k tốt nhất = 12),
  độ đa dạng 0,978 → 0,917; chủ đề trải đều hơn theo sản phẩm nhưng ở k = 9 có 3 chủ đề không khớp mẫu tên nào (42,5% đánh giá
  tiêu cực) → **giữ mô hình hiện tại** theo tiêu chí đã chốt (chỉ thay khi NPMI và độ dễ hiểu đều không giảm).
- **Demo** (`docs/demo/`): `kich_ban_demo_sprint1.md` (demo nhanh luồng ưu tiên cao, khoảng 5 phút) và `kich_ban_demo_day_du.md`
  (đủ 10 màn hình, 28 yêu cầu chức năng); ảnh `docs/screens/` chụp lại trên bản 1.3.0, giữ tên file và khung hình 1440 × 900 (1,5×);
  `swagger.png` dựng từ `docs/openapi.json` bằng Swagger UI chạy cục bộ.
- **Kiểm thử chấp nhận FR Must** (`scripts/acceptance_test.py`, mục 6) và **CI GitHub Actions**; quy trình Git trong `CONTRIBUTING.md`;
  `.gitattributes` thống nhất ký tự xuống dòng giữa máy Windows và Linux.

## 13. Thay đổi phiên bản 1.2.0 (sau buổi demo 5)
Hợp đồng API 1.1.0 → 1.2.0, chỉ bổ sung trường tùy chọn và bảng xuất mới nên tương thích ngược; `docs/openapi.json` đã xuất lại.
- **Cảnh báo sản phẩm:** thêm trường `signal` – `decline` (điểm TB 3 tháng giảm ≥ 0,25 sao, tức “bị đánh giá thấp dần”) hoặc
  `negative` (điểm không giảm nhưng tỷ lệ tiêu cực cao kéo dài); lý do ghi rõ loại tín hiệu. Sắp theo mức rủi ro: trong cùng mức,
  sản phẩm giảm điểm mạnh nhất đứng trước (trước đây sắp theo tỷ lệ tiêu cực nên một sản phẩm đang tăng điểm đứng đầu danh sách).
- **Kiểm tra ngược quy tắc cảnh báo** (như notebook 05) chạy trong pipeline: gắn mức tại 6 và 3 tháng trước tháng cuối,
  xem tỷ lệ tiêu cực 3 tháng tiếp theo theo từng mức; hiển thị ở tab Sản phẩm, trong PDF và trường `backtest` của API #10 (`GET /api/products`).
- **Kiểm tra theo thời gian cho mô hình** (như notebook 02): LR cùng cấu hình học trên 80.000 đánh giá trước năm cuối, kiểm tra
  20.000 đánh giá của năm cuối; so với cách chia ngẫu nhiên ở tab Mô hình, trong PDF và trường `time_check` của API #11 (`GET /api/model/metrics`).
  Khi dữ liệu là bộ đầy đủ, tab Mô hình đối chiếu thêm với số liệu notebook 02 (F1-macro 0,719 trên 275.723 đánh giá học)
  để giải thích vì sao dashboard (mẫu 100.000) ra 0,714.
- **Dự báo:** biểu đồ hiện đủ chuỗi dùng để dự báo (01/2007 → 09/2012, 69 tháng) thay vì 48 tháng gần nhất.
- **Báo cáo:** thêm 2 bảng CSV `forecast` và `model_metrics` (API #20).
- **Giao diện:** bảng trong khung chatbot cuộn ngang, không bị bóp thành từng chữ; câu trả lời “sản phẩm rủi ro” của chế độ quy tắc
  dùng danh sách; nút “Hỏi trợ lý AI” thu gọn thành nút tròn (rê chuột mới hiện chữ) để không che bảng, biểu đồ; tab Tổng quan
  thêm ô “Giới hạn cần biết khi đọc kết quả”.
- **Wireframe** (`docs/wireframes/`, sinh bằng `python docs/diagrams/wireframes_build.py`): vẽ lại màn hình 2 (ô giới hạn), 4 (kiểm tra
  theo thời gian), 6 (kiểm tra ngược, nhãn loại tín hiệu), 10 (6 bảng CSV); 6 màn hình còn lại không đổi.
- **Ảnh chụp màn hình** (`docs/screens/`): chụp lại toàn bộ trên bản 1.2.0 với bộ dữ liệu đầy đủ, giữ nguyên tên file và khung hình
  của bản 1.1.0 (1440 × 900, tỷ lệ 1,5×) để tài liệu đang chèn ảnh không phải sửa: `app_upload`, `app_overview`, `app_model`,
  `app_predict`, `app_product` (ngăn chi tiết sản phẩm), `app_forecast`, `app_ai`, `swagger`. Thêm 3 ảnh: `app_products`
  (cả trang Sản phẩm & cảnh báo), `app_model_full` (cả trang Mô hình ML), `app_chatbot` (chatbot trả lời sản phẩm rủi ro cao).
- **Thời gian xử lý** tăng do có thêm kiểm tra theo thời gian: mẫu 100.000 dòng ≈ 2–3 phút, toàn bộ Reviews.csv ≈ 3–4 phút
  (đo trên máy chạy thử: 163 giây và 235 giây).

## 14. Nhóm thực hiện
| Thành viên | Nhánh | Phần phụ trách chính |
|---|---|---|
| Dương Diễm My (nhóm trưởng) | `diemmy` | EDA, làm sạch R1–R9, DataService/EdaService; quy trình Git; kiểm thử chấp nhận, kiểm tra tích hợp; README, demo |
| KAYSONE Souk Anong | `kaysone` | Mô hình phân loại (notebook 02), chủ đề phàn nàn (notebook 03, 06); ModelService, TopicService; tự nhập dự đoán |
| Lê Gia Huy | `giahuy` | Frontend React, wireframe; trợ lý AI Gemini (AIService, chatbot), chạy AI hàng loạt, NFR-10 |
| Nguyễn Hoàng Thuận | `hoangthuan` | FastAPI, hợp đồng 20 API, ERD; dự báo, cảnh báo (notebook 04, 05), job nền; Docker, CI |

Mỗi thành viên commit trên nhánh của mình bằng tài khoản GitHub riêng và mở pull request vào `main`; nhóm trưởng gộp khi CI xanh.
