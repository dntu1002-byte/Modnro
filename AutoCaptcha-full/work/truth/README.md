# Tập đáp án chuẩn do người dùng cung cấp (12 đề "Real")
- `real_truth.jsonl`: legend, chuỗi dải trên và đáp án cho `real01`…`real12`, chép từ bảng "KIỂM CHỨNG V8.3" người dùng gửi.
  Mỗi dòng đã tự kiểm: áp legend lên chuỗi dải trên ra đúng đáp án.
- Người dùng khẳng định: đáp án dưới mỗi ô là đúng; mã trong ô trắng là đáp án SAI của bản cũ. Mình chưa tự xác minh điều này.
- **Thiếu ảnh PNG gốc.** Đặt 12 ảnh 256×256 gốc (do plugin ghi ở `inbox/<HASH>.png`, không phải ảnh chụp bảng) vào `truth/img/real01.png` … `real12.png`, rồi chạy:
  `python3 work/scripts/score_truth.py [đường-dẫn-exe]`
- 12 đề "Adv" trong bảng là biến thể giả lập của 12 đề Real (cùng dải trên, legend đảo số) nên không đưa vào làm chuẩn độc lập.

- `user01` = `truth/img/last_solved.png` (hash 7B465EFF2AD22518), đáp án 131391 do người dùng xác nhận; đây là ảnh duy nhất hiện có PNG. 12 đề `real01…12` vẫn thiếu PNG.

- `user02` = `truth/img/user02.png` (ảnh chụp màn hình cả khung 255×253, KHÔNG phải PNG gốc 256×256 của plugin), đáp án 11175 do người dùng xác nhận. Chuỗi dải trên `BBB$C` suy ra từ đáp án + legend.
- `user03` = `truth/img/user03.png` (ảnh chụp màn hình 253×256, không phải PNG gốc), đáp án 535113 do người dùng xác nhận; dải trên `BDB%%D` suy ra từ đáp án + legend (2 ký tự `%` chồng lên nhau: đen + đỏ).

- `user04` = `truth/img/user04.png` (ảnh chụp màn hình 255×256, không phải PNG gốc), đáp án 59971 do người dùng xác nhận; dải trên `L@@Z&` suy ra từ đáp án + legend (`l→5, &→1, z→7, %→3, @→9`).
- `user05` = `truth/img/user05.png` (ảnh chụp màn hình 253×248), đáp án 35197 do người dùng xác nhận; dải trên `ACE%H` (e thường, chữ hoa/thường không phân biệt) suy ra từ đáp án + legend (`%→9, h→7, e→1, C→5, A→3`).
