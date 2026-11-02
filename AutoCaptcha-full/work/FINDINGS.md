# Phát hiện từ dữ liệu RAR (phiên Notion AI 2026-11-02)

## Giao thức plugin 1.4.314 (đã xác minh bằng decompile `work/decomp/CaptchaQueue.cs`)
- Plugin ghi `inbox/<hash16>.png` (chỉ khi chưa tồn tại) và `jobs/<hash16>.json` (`answerLength` có thể = 0, được cập nhật lại sau trong Tick bằng cách ghi đè toàn bộ file).
- Plugin đọc `outbox/<hash>.txt`: Trim, dài 3–8, chỉ chữ/số. Nếu `answerLength>0` mà sai độ dài → chờ, KHÔNG xóa. Gửi sau ≥2,5 s kể từ publish; gửi xong xóa `.txt`.
- Sau lần 1, chờ 5 s; nếu panel vẫn mở → đọc `outbox/<hash>.alt.txt` (khác đáp án 1, đúng độ dài) → gửi lần 2, xóa `.alt.txt`. Tối đa 2 lần.
- Plugin KHÔNG đọc/xóa inbox PNG khi gửi → worker di chuyển PNG không làm hỏng plugin, nhưng mất dữ liệu nếu muốn giữ mẫu.
- `labels.jsonl`: plugin ghi khi NGƯỜI DÙNG tự bấm gửi (không phải auto). RAR không có file này.
- `ExpectedLength` chỉ > 0 khi `mvd` toàn dấu `.`; log cho thấy `mvd` luôn là đáp án cũ (lưu ở `Data/Rms/auto_captcha`) → thực tế `answerLength` hầu như = 0.

## Nhãn gián tiếp từ log (`work/scripts/build_log_labels.py` → `work/log_events.json`)
- 82 captcha trong 593 log chẩn đoán; 32/32 ảnh trong `work/img` có trong log.
- Plugin 1.4.263 (31/10 12:49–13:17Z, panel HIỂN THỊ, chưa có CaptchaBlocker): 6 ảnh, đáp án lần 1 của bộ giải tra MÀU đều KHÔNG đóng panel sau 5 s → coi là SAI:
  064937887D4981B0=75931, 9BC81C31E0A8907F=73915, 58EECCFC239586FD=75391, FBC83B9FA176E3F0=57193, F139E30763B42BE4=93517, A6A21D431DFD8016=35719.
  Cảnh báo "đã gửi 2 đáp án… panel vẫn mở" in ra 7 ms sau lần 2 → KHÔNG chứng minh lần 2 sai.
- Từ 1.4.284+ có CaptchaBlocker: sau khi gửi, Hidden bị Clear và em.ima=null → plugin không còn thấy panel → "FIRST_LIKELY_ACCEPTED" KHÔNG đáng tin (giả thuyết).
- Các ảnh 01/11 (980C, 6EDB, A743…) không có PNG trong RAR.

## Màu hay ký hiệu? (đã kiểm bằng mắt 1 ảnh)
- 064937887D4981B0: dải trên = % (hồng), l (trắng), q (đen), V (đỏ), q (vàng). Legend: k→7 hồng, l→5 trắng, q→9 đen, %→3 đỏ, V→1 vàng.
  Theo ký hiệu = 35919 (trùng V8.3.1); theo màu = 75931 = đáp án đã bị từ chối. Màu bị xáo giữa dải trên và legend → màu là mồi nhử.
- Kết luận làm việc (giả thuyết mạnh, chưa server xác nhận dương tính): tra theo KÝ HIỆU.
