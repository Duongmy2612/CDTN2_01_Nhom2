# Biên bản chạy thử toàn hệ thống – 21/11/2026 07:02

- Địa chỉ gọi: `http://localhost:5174` (gọi thẳng backend)
- Máy chạy: Linux 6.18.44-fc-v726, Python 3.11.15
- Phiên bản hợp đồng API: 1.5.0; dữ liệu: reviews_sample_100k.csv – 87.622 đánh giá sạch
- Job nền với dữ liệu `sample`: 168.1 giây (Kiểm tra cấu trúc file 0.2 s, Làm sạch, chuẩn hóa (R1–R9) 3.9 s, Thống kê khám phá 9.3 s, Huấn luyện 3 mô hình, kiểm tra theo thời gian 147.6 s, Tìm chủ đề phàn nàn (NMF) 1.9 s, Dự báo chỉ số hài lòng 0.0 s, Gắn mức rủi ro sản phẩm, kiểm tra ngược quy tắc 4.5 s)

**Kết quả: 27/27 lời gọi đạt.**

| API | Lời gọi | HTTP | Thời gian (ms) | Kết quả | Ghi chú |
|---|---|---|---|---|---|
| #1 health | `GET /api/health` | 200 | 2 | Đạt | phiên bản 1.5.0 |
| #5 data/quality | `GET /api/data/quality` | 200 | 2 | Đạt | 100.000 dòng gốc → 87.622 sạch |
| #7 kpi | `GET /api/kpi` | 200 | 26 | Đạt | 87.622 đánh giá, chỉ số 79.67 |
| #8 eda/score_dist | `GET /api/eda/score_dist` | 200 | 5 | Đạt | 5 điểm |
| #8 eda/monthly | `GET /api/eda/monthly` | 200 | 15 | Đạt | 125 điểm |
| #8 eda/length_by_score | `GET /api/eda/length_by_score` | 200 | 11 | Đạt | 5 điểm |
| #8 eda/keywords | `GET /api/eda/keywords` | 200 | 2 | Đạt | 30 điểm |
| #8 eda/top_products | `GET /api/eda/top_products` | 200 | 41 | Đạt | 10 điểm |
| #9 topics | `GET /api/topics` | 200 | 8 | Đạt | 9 chủ đề |
| #10 products | `GET /api/products?sort=risk&page_size=20` | 200 | 12 | Đạt | 31.111 sản phẩm |
| #11 model/metrics | `GET /api/model/metrics` | 200 | 2 | Đạt | chọn LR |
| #12 model/keywords | `GET /api/model/keywords?n=15` | 200 | 2 | Đạt |  |
| #13 reviews/mismatch | `GET /api/reviews/mismatch?page_size=8` | 200 | 7 | Đạt |  |
| #14 predict | `POST /api/predict` | 200 | 8 | Đạt | 1 sao, 5.23 ms |
| #15 satisfaction | `GET /api/satisfaction` | 200 | 13 | Đạt | 125 tháng |
| #16 forecast | `GET /api/forecast?months=12` | 200 | 13 | Đạt | ETS(A,Ad,N), 12 tháng dự báo |
| #10 products (dự báo được) | `GET /api/products?forecastable=true&sort=n_reviews&page_size=5` | 200 | 6 | Đạt |  |
| #15 satisfaction (sản phẩm) | `GET /api/satisfaction?product_id=B000NMJWZO` | 200 | 11 | Đạt | B000NMJWZO: 49 tháng |
| #16 forecast (sản phẩm) | `GET /api/forecast?product_id=B000NMJWZO&months=6` | 200 | 66 | Đạt | B000NMJWZO: dự báo được |
| #9 topics (sản phẩm) | `GET /api/topics?product_id=B000NMJWZO` | 200 | 35 | Đạt |  |
| #19 report/pdf | `GET /api/report/pdf` | 200 | 502 | Đạt |  |
| #20 export/predictions | `GET /api/export/predictions` | 200 | 146 | Đạt |  |
| #20 export/product_risk | `GET /api/export/product_risk` | 200 | 150 | Đạt |  |
| #20 export/topics | `GET /api/export/topics` | 200 | 4 | Đạt |  |
| #20 export/monthly | `GET /api/export/monthly` | 200 | 18 | Đạt |  |
| #20 export/model_metrics | `GET /api/export/model_metrics` | 200 | 4 | Đạt |  |
| #20 export/forecast | `GET /api/export/forecast` | 200 | 3 | Đạt |  |

Không gọi `/api/upload`, `/api/session/reset` (không làm mất dữ liệu đang dùng); `/api/ai/insights`, `/api/chat` chỉ gọi khi thêm `--with-ai`.
Tạo lại: `python scripts/smoke_test.py --base <địa chỉ> --kind <sample|full>`.
