# Biên bản chạy thử toàn hệ thống – 07/11/2026 08:55

- Địa chỉ gọi: `http://localhost:5173` (qua frontend – proxy Vite tới backend)
- Máy chạy: Linux 6.18.44-fc-v310, Python 3.11.15
- Phiên bản hợp đồng API: 1.4.0; dữ liệu: Reviews.csv – 393.890 đánh giá sạch
- Backend đã có dữ liệu từ trước (nạp lại khi khởi động) – không chạy lại job nền

**Kết quả: 27/27 lời gọi đạt.**

| API | Lời gọi | HTTP | Thời gian (ms) | Kết quả | Ghi chú |
|---|---|---|---|---|---|
| #1 health | `GET /api/health` | 200 | 3 | Đạt | phiên bản 1.4.0 |
| #5 data/quality | `GET /api/data/quality` | 200 | 3 | Đạt | 568.454 dòng gốc → 393.890 sạch |
| #7 kpi | `GET /api/kpi` | 200 | 105 | Đạt | 393.890 đánh giá, chỉ số 79.48 |
| #8 eda/score_dist | `GET /api/eda/score_dist` | 200 | 8 | Đạt | 5 điểm |
| #8 eda/monthly | `GET /api/eda/monthly` | 200 | 61 | Đạt | 143 điểm |
| #8 eda/length_by_score | `GET /api/eda/length_by_score` | 200 | 55 | Đạt | 5 điểm |
| #8 eda/keywords | `GET /api/eda/keywords` | 200 | 4 | Đạt | 30 điểm |
| #8 eda/top_products | `GET /api/eda/top_products` | 200 | 164 | Đạt | 10 điểm |
| #9 topics | `GET /api/topics` | 200 | 24 | Đạt | 9 chủ đề |
| #10 products | `GET /api/products?sort=risk&page_size=20` | 200 | 24 | Đạt | 67.612 sản phẩm |
| #11 model/metrics | `GET /api/model/metrics` | 200 | 4 | Đạt | chọn LR |
| #12 model/keywords | `GET /api/model/keywords?n=15` | 200 | 3 | Đạt |  |
| #13 reviews/mismatch | `GET /api/reviews/mismatch?page_size=8` | 200 | 13 | Đạt |  |
| #14 predict | `POST /api/predict` | 200 | 12 | Đạt | 1 sao, 8.47 ms |
| #15 satisfaction | `GET /api/satisfaction` | 200 | 55 | Đạt | 143 tháng |
| #16 forecast | `GET /api/forecast?months=12` | 200 | 56 | Đạt | ETS(A,Ad,N), 12 tháng dự báo |
| #10 products (dự báo được) | `GET /api/products?forecastable=true&sort=n_reviews&page_size=5` | 200 | 9 | Đạt |  |
| #15 satisfaction (sản phẩm) | `GET /api/satisfaction?product_id=B002QWP89S` | 200 | 24 | Đạt | B002QWP89S: 52 tháng |
| #16 forecast (sản phẩm) | `GET /api/forecast?product_id=B002QWP89S&months=6` | 200 | 108 | Đạt | B002QWP89S: dự báo được |
| #9 topics (sản phẩm) | `GET /api/topics?product_id=B002QWP89S` | 200 | 128 | Đạt |  |
| #19 report/pdf | `GET /api/report/pdf` | 200 | 505 | Đạt |  |
| #20 export/predictions | `GET /api/export/predictions` | 200 | 202 | Đạt |  |
| #20 export/product_risk | `GET /api/export/product_risk` | 200 | 272 | Đạt |  |
| #20 export/topics | `GET /api/export/topics` | 200 | 23 | Đạt |  |
| #20 export/monthly | `GET /api/export/monthly` | 200 | 52 | Đạt |  |
| #20 export/model_metrics | `GET /api/export/model_metrics` | 200 | 6 | Đạt |  |
| #20 export/forecast | `GET /api/export/forecast` | 200 | 3 | Đạt |  |

Không gọi `/api/upload`, `/api/session/reset` (không làm mất dữ liệu đang dùng); `/api/ai/insights`, `/api/chat` chỉ gọi khi thêm `--with-ai`.
Tạo lại: `python scripts/smoke_test.py --base <địa chỉ> --kind <sample|full>`.
