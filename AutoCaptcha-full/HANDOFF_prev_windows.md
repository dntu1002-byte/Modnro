# Đọc file này trước

Đây là GÓI BÀN GIAO TẠO LẠI trên máy Windows của người dùng ngày 02/11/2026.
Không phải bản ZIP khôi phục nguyên trạng sandbox Opus.

## Những gì tìm được và không tìm được

`pasted-text.txt` mô tả sandbox Linux `/data/...`, tài khoản `vercel-sandbox`.
Không thể truy cập sandbox đó từ máy Windows hiện tại. Đã tìm trong workspace
`D:\modnrp`, Downloads và Desktop; không tìm thấy bộ `work/src`, `work/img`,
`work/decomp`, `work/run3v.txt` của phiên đó. `D:\modnrp\work` tồn tại nhưng là
workspace cục bộ khác, không được coi là workspace Opus.

Không có mã nguyên gốc `Png.cs`, `Glyphs.cs`, `Solver.cs`, `Templates.cs`,
`Program.cs`, project hay `gen_templates.py` của Opus trong bản ghi.
Bản ghi chỉ chứa mô tả, log và một số mã decompile; không đủ khôi phục chính xác
các file nguồn đó. Không giả mạo các file hay kết quả bị mất.

## Nội dung gói này

- `inputs/original/`: bốn file người dùng cung cấp, sao chép nguyên byte.
- `inputs/plugin/NroPort.Plugin.dll`: DLL lấy trực tiếp từ RAR gốc.
- `work/img/`: đủ 32 PNG lấy trực tiếp từ RAR; tên file khớp 16 ký tự đầu SHA-256.
- `work/jobs/`: 32 JSON tương ứng từ RAR.
- `work/decomp/`: `CaptchaQueue.cs`, `CaptchaCapture.cs` decompile mới bằng
  ILSpyCmd 8.2 từ DLL đi kèm, không phải file decompile cũ của Opus.
- `work/src/CaptchaQueue.cs`: nguồn C# gộp V8.3.1 đã sửa trên máy này trong chat
  Codex; xuất phát từ file V8.3 đính kèm, không phải prototype riêng của Opus.
  PNG decoder, templates và solver đều nằm trong file này.
- `work/src/AutoCaptcha.exe`: bản .NET Framework build từ nguồn trên.
- `work/src/build.ps1`: build lại bằng compiler .NET Framework của Windows.
- `work/src/test_queue.py`, `QueueHarness.cs`, `QueueHarness.exe`: kiểm thử
  worker thật trong thư mục riêng; không tương tác game.
- `work/src/verify_offline.py`: chạy chế độ ảnh, tạo kết quả thử mới.
- `work/run3v.txt`, `run3v.json`: KẾT QUẢ MỚI chạy Windows ở lần đóng gói này.
  Không phải nội dung run3v.txt đã mất của Opus.
- `PROVENANCE.json`: nguồn dữ liệu, checksum RAR và checksum từng ảnh.
- `MANIFEST.json`: checksum các file trong gói, tạo lúc nén.

## Trạng thái và giới hạn

EXE và DLL phiên trước trong chat Codex đã build thành công. Bản gói này build
EXE lại và chạy kiểm thử hàng đợi cùng 32 ảnh; xem log và JSON kèm theo.
Chạy tiến trình thành công hay đáp án đủ 5–6 số KHÔNG chứng minh đáp án đúng.
Chưa có bộ nhãn theo KÝ HIỆU được server xác nhận; không tuyên bố 24/24 hay 100%.
Không dùng bộ nhãn cũ tra MÀU như ground truth cho bộ giải tra KÝ HIỆU.

Worker V8.3.1 hiện chỉ ghi outbox; plugin trong game điền/gửi. Không click,
không BlockInput, không giết worker khác. Khóa worker theo đường dẫn queue.
Nó chuyển PNG qua processing rồi lưu solved/failed. Vì vậy nó CHƯA đáp ứng
đúng yêu cầu cũ trong transcript là giữ nguyên PNG tại inbox. JSON được đọc
bằng regex lấy answerLength tại một thời điểm; chưa có parser/retry hoàn chỉnh
cho JSON ghi dở và answerLength thay đổi sau khi solver đã xuất đáp án.
Worker hiện chưa xuất `.alt.txt`, dù plugin có hỗ trợ.

## Việc tiếp theo

1. Xem riêng `work/decomp/CaptchaQueue.cs` để xác minh giao thức đúng DLL.
2. Đọc `work/src/CaptchaQueue.cs` theo từng hàm cần sửa, không đổ toàn bộ vào chat.
3. Xây dựng nhãn theo ký hiệu, đánh dấu ảnh không chắc rồi đo độ chính xác.
4. Nếu tiếp tục mục tiêu của Opus: bổ sung worker giữ nguyên inbox/jobs,
   đọc lại JSON ghi dở, cập nhật answerLength, xuất `.alt.txt` có kiểm chứng.
5. Kiểm thử trong game trước khi kết luận server chấp nhận đáp án.

## Lệnh dùng trong gói

```powershell
# Từ thư mục gốc sau giải nén:
& .\work\src\build.ps1
python .\work\src\verify_offline.py
python .\work\src\test_queue.py
```

Python chỉ cần cho script kiểm thử, EXE không phụ thuộc Python.
Chế độ `AutoCaptcha.exe <đường-dẫn-ảnh.png>` chạy offline, không nhập vào game.
Không tự chạy watcher chỉ để đọc gói bàn giao. Không cần RAR 279 MB để tiếp tục
đọc source, decompile và thử 32 ảnh trong gói này.
