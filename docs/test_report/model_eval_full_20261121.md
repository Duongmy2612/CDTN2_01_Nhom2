# Đánh giá mô hình và phân tích lỗi – full (21/11/2026)

Dữ liệu 3f6b35ee: 393,890 đánh giá sạch. Mô hình chọn: LR.

## 1. Phân loại cảm xúc

Tập kiểm tra: 20,000 đánh giá. Accuracy 3 lớp 0.8838, F1-macro 0.7117; đúng số sao 0.7176, lệch ≤ 1 sao 0.9355, MAE 0.3874 sao.

| Mô hình | F1-macro | P macro | R macro | F1 Tiêu cực | F1 Trung tính | F1 Tích cực | Acc 5 mức | MAE |
|---|---|---|---|---|---|---|---|---|
| B0 | 0.292 | 0.2598 | 0.3333 | 0.0 | 0.0 | 0.8761 | 0.6371 | 0.8206 |
| NB | 0.6837 | 0.6887 | 0.6948 | 0.7352 | 0.3778 | 0.9381 | 0.6701 | 0.476 |
| SVM | 0.6855 | 0.7787 | 0.6466 | 0.7683 | 0.3448 | 0.9433 | 0.7533 | 0.3777 |
| LR | 0.7117 | 0.7147 | 0.713 | 0.7722 | 0.4157 | 0.9471 | 0.7176 | 0.3874 |

| Lớp | Precision | Recall | F1 | Số mẫu |
|---|---|---|---|---|
| Tiêu cực | 0.7331 | 0.8158 | 0.7722 | 2899 |
| Trung tính | 0.4623 | 0.3776 | 0.4157 | 1512 |
| Tích cực | 0.9486 | 0.9455 | 0.9471 | 15589 |

Ma trận nhầm lẫn (hàng: thật, cột: dự đoán): {"labels": ["Tiêu cực", "Trung tính", "Tích cực"], "matrix": [[2365, 248, 286], [428, 571, 513], [433, 416, 14740]]}

### Theo độ dài (số từ)

| Nhóm | Số mẫu | Acc 3 lớp | F1-macro | Tỷ lệ 3 sao |
|---|---|---|---|---|
| 3–19 | 591 | 0.9272 | 0.7193 | 0.0474 |
| 20–49 | 8085 | 0.9118 | 0.7237 | 0.0564 |
| 50–99 | 6463 | 0.8781 | 0.7111 | 0.0806 |
| 100–199 | 3681 | 0.8481 | 0.6994 | 0.1002 |
| ≥ 200 | 1180 | 0.8127 | 0.669 | 0.1169 |

### Theo năm đánh giá

| Nhóm | Số mẫu | Acc 3 lớp | F1-macro | Tỷ lệ 3 sao |
|---|---|---|---|---|
| ≤ 2007 | 1133 | 0.902 | 0.6594 | 0.0494 |
| 2008–2009 | 3107 | 0.8983 | 0.7038 | 0.066 |
| 2010 | 2958 | 0.8864 | 0.7037 | 0.0696 |
| 2011 | 5803 | 0.8825 | 0.7295 | 0.0858 |
| 2012 | 6999 | 0.8744 | 0.7067 | 0.0782 |

### Theo lượt bình chọn hữu ích

| Nhóm | Số mẫu | Acc 3 lớp | F1-macro | Tỷ lệ 3 sao |
|---|---|---|---|---|
| 0 | 9526 | 0.8969 | 0.7079 | 0.0733 |
| 1–4 | 8085 | 0.8779 | 0.708 | 0.0789 |
| ≥ 5 | 2389 | 0.8514 | 0.6929 | 0.0737 |

### Theo số đánh giá của sản phẩm

| Nhóm | Số mẫu | Acc 3 lớp | F1-macro | Tỷ lệ 3 sao |
|---|---|---|---|---|
| < 10 | 7332 | 0.8948 | 0.7213 | 0.0648 |
| 10–99 | 9053 | 0.89 | 0.7052 | 0.0669 |
| ≥ 100 | 3615 | 0.8459 | 0.6964 | 0.1192 |

### Theo độ tự tin của mô hình

| Nhóm | Số mẫu | Acc 3 lớp | F1-macro | Tỷ lệ 3 sao |
|---|---|---|---|---|
| < 0,5 | 1112 | 0.4424 | 0.4252 | 0.2833 |
| 0,5–0,7 | 3006 | 0.6487 | 0.5929 | 0.2049 |
| 0,7–0,9 | 4794 | 0.8928 | 0.7494 | 0.0907 |
| ≥ 0,9 | 11088 | 0.9879 | 0.817 | 0.0132 |

### Nhóm lỗi (2,324 đánh giá bị xếp sai cảm xúc)

| Nhóm lỗi | Số lỗi | Tỷ lệ |
|---|---|---|
| Đánh giá 3 sao (trung tính) bị xếp sang hai cực | 941 | 0.4049 |
| Vừa khen vừa chê (“but”, “however”…) | 920 | 0.3959 |
| Khác | 307 | 0.1321 |
| Có phủ định / nói giảm (“not bad”, “no complaints”) | 119 | 0.0512 |
| Số sao ngược hẳn nội dung (mô hình tự tin ≥ 0,9) | 22 | 0.0095 |
| Quá ngắn (< 20 từ) | 15 | 0.0065 |

- *Đánh giá 3 sao (trung tính) bị xếp sang hai cực* – #467047 (3★, dự đoán Tích cực 0.57): “This salt has the right size and shape for Lye Pretzels. I bought it together with the Lye. The reason I gave it only THREE stars is that …”
- *Đánh giá 3 sao (trung tính) bị xếp sang hai cực* – #242409 (3★, dự đoán Tích cực 0.99): “My kids don't exactly ask for these, but they don't complain when I serve them either. Great for camping. Good for when the kids are spending the night …”
- *Vừa khen vừa chê (“but”, “however”…)* – #412591 (5★, dự đoán Trung tính 0.68): “Although I was expecting assorted flavors (and that may have been my problem with not reading the description more carefully), I was thrilled these arrived in very short …”
- *Vừa khen vừa chê (“but”, “however”…)* – #181929 (2★, dự đoán Trung tính 0.54): “i drank this tea for 4 days, only did 2 cups a day. the four days that i was drinking it, my baby was fussy and kept pulling …”
- *Khác* – #184165 (5★, dự đoán Tiêu cực 0.63): “I thought cat food was good enough for my cat. I was wrong. The kind of cat food you get for your cat matters. It matters alot. My …”
- *Khác* – #55174 (4★, dự đoán Tiêu cực 0.63): “I am buying this product because my cat has health issues. While I lived in Indiana I was able to buy it at Walmart for around 11.00 for …”
- *Có phủ định / nói giảm (“not bad”, “no complaints”)* – #538575 (4★, dự đoán Trung tính 0.54): “I prefer the Lavazza Supercrema. This is a good coffee though. I recently found a local coffee made at the Wholefoods in my area and I find the …”
- *Có phủ định / nói giảm (“not bad”, “no complaints”)* – #4313 (5★, dự đoán Trung tính 0.56): “I have been GF for 2years. I used this product for biscuits and liked them but were a little dry. As for the pancakes, I prefer another product. …”
- *Số sao ngược hẳn nội dung (mô hình tự tin ≥ 0,9)* – #39233 (1★, dự đoán Tích cực 0.95): “Ads a very pleasant taste to my stir fry experience. As tasty in my home cooking , comparable to that in a chinese restaurant. A product that I …”
- *Số sao ngược hẳn nội dung (mô hình tự tin ≥ 0,9)* – #465123 (1★, dự đoán Tích cực 0.91): “This special spice was included in a skirt steak recipe. Its unique flavor made this dish a special favorite with all 17 people who ate it.”
- *Quá ngắn (< 20 từ)* – #194270 (4★, dự đoán Trung tính 0.77): “This product didnt really make as much as a difference as i would have liked!”
- *Quá ngắn (< 20 từ)* – #173338 (5★, dự đoán Tiêu cực 0.5): “Can't seem to get this at Meijer or Wal Mart any more, don't know why.”

## 2. Dự báo chỉ số hài lòng

Chuỗi 2007-01 – 2012-09 (69 tháng, ngưỡng 700 đánh giá/tháng); kiểm tra 2011-10 – 2012-09.

Dự báo 12 tháng một lần:

| Mô hình | MAE | RMSE |
|---|---|---|
| ETS (mô hình của hệ thống) | 0.61 | 0.73 |
| Ngây thơ (giữ tháng cuối) | 1.5 | 1.55 |
| Mùa vụ (cùng tháng năm trước) | 1.15 | 1.38 |
| TB 12 tháng gần nhất | 1.12 | 1.19 |

Dự báo cuốn chiếu 1 tháng:

| Mô hình | MAE | RMSE |
|---|---|---|
| ETS | 0.43 | 0.53 |
| Ngây thơ | 0.55 | 0.66 |
| Mùa vụ | 1.15 | 1.38 |

| Tầm | Tháng | Thực tế | Sai số ETS | Sai số ngây thơ |
|---|---|---|---|---|
| 1 | 2011-10 | 78.01 | 0.54 | 1.17 |
| 2 | 2011-11 | 78.25 | 0.24 | 0.92 |
| 3 | 2011-12 | 77.32 | 1.12 | 1.85 |
| 4 | 2012-01 | 77.95 | 0.44 | 1.22 |
| 5 | 2012-02 | 77.48 | 0.86 | 1.7 |
| 6 | 2012-03 | 77.2 | 1.09 | 1.97 |
| 7 | 2012-04 | 77.62 | 0.63 | 1.56 |
| 8 | 2012-05 | 77.4 | 0.79 | 1.77 |
| 9 | 2012-06 | 76.94 | 1.21 | 2.23 |
| 10 | 2012-07 | 78.2 | 0.09 | 0.98 |
| 11 | 2012-08 | 78.06 | 0.0 | 1.11 |
| 12 | 2012-09 | 77.69 | 0.32 | 1.48 |

| Số đánh giá/tháng | Số tháng | Sai số chuẩn TB (điểm chỉ số) | Giai đoạn |
|---|---|---|---|
| < 100 | 56 | 5.93 | 1999-10 – 2005-08 |
| 100 – 699 | 16 | 2.02 | 2005-07 – 2006-12 |
| ≥ 700 (dùng để dự báo) | 70 | 0.54 | 2006-11 – 2012-09 |

Từng sản phẩm: 149 sản phẩm, MAE TB 19.63 (ngây thơ 23.43), mô hình tốt hơn ngây thơ ở 52% sản phẩm.

## 3. Quy tắc cảnh báo rủi ro (kiểm tra ngược)

| Mức | Số lượt sản phẩm | Tỷ lệ tiêu cực 3 tháng sau | Điểm TB 3 tháng sau |
|---|---|---|---|
| high | 60 | 0.2739 | 3.6937 |
| medium | 74 | 0.1987 | 3.9764 |
| low | 227 | 0.1217 | 4.2793 |

Tỷ lệ tiêu cực của nhóm Cao gấp 2.25 lần nhóm Thấp.

## 4. Chủ đề phàn nàn

57,101/57,103 đánh giá tiêu cực được gán chủ đề, 2 chưa xếp.

| Chủ đề | Số đánh giá | 5 từ khóa đầu | Chứa ≥ 1 từ khóa | Trọng số trung vị |
|---|---|---|---|---|
| 0. Hương vị, mùi, kết cấu không ngon | 11494 | taste, flavor, tastes, tasted, water | 0.879 | 0.0192 |
| 1. Cà phê nhạt/đắng, viên K-cup | 5479 | coffee, cup, cups, weak, instant | 0.968 | 0.0458 |
| 2. Hàng cũ, hết hạn, bao bì hỏng khi nhận | 11408 | box, received, stale, date, arrived | 0.553 | 0.0214 |
| 3. Trà: vị nhạt, túi lọc | 3549 | tea, green, green tea, teas, bags | 0.994 | 0.0535 |
| 4. Thức ăn thú cưng: xuất xứ, làm thú bệnh | 7999 | dog, food, dogs, eat, treats | 0.805 | 0.0324 |
| 5. Giá cao so với cửa hàng, phí giao hàng | 6110 | price, store, grocery, local, grocery store | 0.77 | 0.0313 |
| 6. Thành phần: đường, siro ngô, không tự nhiên | 5343 | sugar, ingredients, syrup, corn, corn syrup | 0.704 | 0.0264 |
| 7. Sô-cô-la, bánh quy, bơ đậu phộng | 3850 | chocolate, hot, bars, cookies, hot chocolate | 0.885 | 0.0435 |
| 8. Sản phẩm không gluten, bột làm bánh | 1869 | free, gluten, gluten free, wheat, cookies | 0.896 | 0.0445 |
