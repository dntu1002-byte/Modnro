# Tập đáp án chuẩn do người dùng cung cấp (12 đề "Real")
- `real_truth.jsonl`: legend, chuỗi dải trên và đáp án cho `real01`…`real12`, chép từ bảng "KIỂM CHỨNG V8.3" người dùng gửi.
  Mỗi dòng đã tự kiểm: áp legend lên chuỗi dải trên ra đúng đáp án.
- Người dùng khẳng định: đáp án dưới mỗi ô là đúng; mã trong ô trắng là đáp án SAI của bản cũ. Mình chưa tự xác minh điều này.
- **Thiếu ảnh PNG gốc.** Đặt 12 ảnh 256×256 gốc (do plugin ghi ở `inbox/<HASH>.png`, không phải ảnh chụp bảng) vào `truth/img/real01.png` … `real12.png`, rồi chạy:
  `python3 work/scripts/score_truth.py [đường-dẫn-exe]`
- 12 đề "Adv" trong bảng là biến thể giả lập của 12 đề Real (cùng dải trên, legend đảo số) nên không đưa vào làm chuẩn độc lập.
