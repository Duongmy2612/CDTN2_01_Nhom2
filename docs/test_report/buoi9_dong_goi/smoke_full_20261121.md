# Biên bản chạy thử toàn hệ thống – 21/11/2026 18:25

- Địa chỉ gọi: `http://localhost:8000` (gọi thẳng backend)
- Máy chạy: Linux 6.18.44-fc-v726, Python 3.11.15
- Phiên bản hợp đồng API: 1.5.0; dữ liệu: Reviews.csv – 393.890 đánh giá sạch
- Thời gian cài đặt đo được (NFR-08, ngưỡng 15 phút): **1.1 phút** – Đạt
- Backend đã có dữ liệu từ trước (nạp lại khi khởi động) – không chạy lại job nền

**Kết quả: 27/27 lời gọi đạt.**

| API | Lời gọi | HTTP | Thời gian (ms) | Kết quả | Ghi chú |
|---|---|---|---|---|---|
| #1 health | `GET /api/health` | 200 | 2 | Đạt | phiên bản 1.5.0 |
| #5 data/quality | `GET /api/data/quality` | 200 | 2 | Đạt | 568.454 dòng gốc → 393.890 sạch |
| #7 kpi | `GET /api/kpi` | 200 | 101 | Đạt | 393.890 đánh giá, chỉ số 79.48 |
| #8 eda/score_dist | `GET /api/eda/score_dist` | 200 | 5 | Đạt | 5 điểm |
| #8 eda/monthly | `GET /api/eda/monthly` | 200 | 64 | Đạt | 143 điểm |
| #8 eda/length_by_score | `GET /api/eda/length_by_score` | 200 | 39 | Đạt | 5 điểm |
| #8 eda/keywords | `GET /api/eda/keywords` | 200 | 2 | Đạt | 30 điểm |
| #8 eda/top_products | `GET /api/eda/top_products` | 200 | 164 | Đạt | 10 điểm |
| #9 topics | `GET /api/topics` | 200 | 29 | Đạt | 9 chủ đề |
| #10 products | `GET /api/products?sort=risk&page_size=20` | 200 | 24 | Đạt | 67.612 sản phẩm |
| #11 model/metrics | `GET /api/model/metrics` | 200 | 2 | Đạt | chọn LR |
| #12 model/keywords | `GET /api/model/keywords?n=15` | 200 | 2 | Đạt |  |
| #13 reviews/mismatch | `GET /api/reviews/mismatch?page_size=8` | 200 | 14 | Đạt |  |
| #14 predict | `POST /api/predict` | 200 | 12 | Đạt | 1 sao, 9.65 ms |
| #15 satisfaction | `GET /api/satisfaction` | 200 | 73 | Đạt | 143 tháng |
| #16 forecast | `GET /api/forecast?months=12` | 200 | 66 | Đạt | ETS(A,Ad,N), 12 tháng dự báo |
| #10 products (dự báo được) | `GET /api/products?forecastable=true&sort=n_reviews&page_size=5` | 200 | 9 | Đạt |  |
| #15 satisfaction (sản phẩm) | `GET /api/satisfaction?product_id=B002QWP89S` | 200 | 35 | Đạt | B002QWP89S: 52 tháng |
| #16 forecast (sản phẩm) | `GET /api/forecast?product_id=B002QWP89S&months=6` | 200 | 115 | Đạt | B002QWP89S: dự báo được |
| #9 topics (sản phẩm) | `GET /api/topics?product_id=B002QWP89S` | 200 | 176 | Đạt |  |
| #19 report/pdf | `GET /api/report/pdf` | 200 | 700 | Đạt |  |
| #20 export/predictions | `GET /api/export/predictions` | 200 | 220 | Đạt |  |
| #20 export/product_risk | `GET /api/export/product_risk` | 200 | 367 | Đạt |  |
| #20 export/topics | `GET /api/export/topics` | 200 | 3 | Đạt |  |
| #20 export/monthly | `GET /api/export/monthly` | 200 | 59 | Đạt |  |
| #20 export/model_metrics | `GET /api/export/model_metrics` | 200 | 4 | Đạt |  |
| #20 export/forecast | `GET /api/export/forecast` | 200 | 2 | Đạt |  |

Không gọi `/api/upload`, `/api/session/reset` (không làm mất dữ liệu đang dùng); `/api/ai/insights`, `/api/chat` chỉ gọi khi thêm `--with-ai`.
Tạo lại: `python scripts/smoke_test.py --base <địa chỉ> --kind <sample|full>`.
