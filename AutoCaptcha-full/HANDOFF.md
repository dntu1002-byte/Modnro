# HANDOFF — AutoCaptcha (phiên Notion AI, sandbox Linux, bắt đầu 2026-11-02 19:14 +07)

Đọc file này trước. Bản bàn giao Windows trước đó giữ nguyên ở `HANDOFF_prev_windows.md`.

## Nơi lưu
- Workspace: `/data/autocaptcha/` (mọi đường dẫn dưới đây tương đối với thư mục này).
- Checkpoint ZIP: `/data/checkpoints/AutoCaptcha-checkpoint-vN.zip` (N tăng dần), đồng thời tải lên chat.
- RAR gốc 279 MB: `inputs/session3/Mod-250-PC.rar` — KHÔNG đưa vào ZIP (quá lớn); SHA256 7631583a…be4f187 khớp PROVENANCE.json.

## Mục tiêu (từ HANDOFF_prev_windows.md)
1. Xác minh giao thức worker ↔ plugin theo `work/decomp/CaptchaQueue.cs`.
2. Lập bộ nhãn theo KÝ HIỆU cho 32 ảnh `work/img/`, đánh dấu ảnh không chắc, đo độ chính xác solver.
3. Worker: giữ nguyên PNG inbox/jobs, đọc lại JSON ghi dở, cập nhật answerLength, xuất `.alt.txt`.
4. Kiểm thử trong game (chỉ người dùng làm được) trước khi kết luận server chấp nhận.

## Trạng thái việc
- [x] Tạo workspace, HANDOFF.md, xác minh SHA256 4 file đầu vào khớp `inputs/original/`.
- [x] Cài .NET 8 SDK tại `/data/.dotnet` (ngoài workspace; cài lại bằng dotnet-install.sh --channel 8.0).
- [x] Cài unrar (rarlab 7.12) tại `/data/rar/unrar`; trích log/captcha từ RAR vào `inputs/rar_extract/`.
- [x] Mục tiêu 1: xác minh giao thức plugin → `work/FINDINGS.md`.
- [x] Trích nhãn gián tiếp từ log → `work/scripts/build_log_labels.py`, `work/log_events.json`.
- [x] Xác định khóa tra là KÝ HIỆU (bằng chứng: 6 đáp án tra màu bị từ chối) → `work/FINDINGS.md`.
- [x] Build Linux .NET 8: `work/linux_build/AutoCaptchaLinux.csproj` (biên dịch nguyên `work/src/CaptchaQueue.cs`). Kết quả 32 ảnh TRÙNG 32/32 với bản Windows (`work/run_linux.json` vs `work/run3v.json`).
- [x] Nhãn LEGEND bằng mắt 32 ảnh (độ tin cậy cao) → `work/labels_legend.jsonl`; chấm: `work/scripts/score_legend.py` → `work/legend_score_v831.txt`.
      V8.3.1: 128/157 ký hiệu đúng tên, 13/32 ảnh legend đúng hoàn toàn, 2 ảnh gán sai chữ số (233AEA: u/F; 3CE6F7: b/h). Lỗi tên hay gặp: @→M (5 ảnh), a/e/u/t/d/$ thường.
- [~] Nhãn DẢI TRÊN bằng mắt: mới 4 ảnh, độ tin cậy thấp–vừa → `work/labels_visual.jsonl` (dải trên bị che nặng, đừng coi là ground truth).
- [x] Worker V8.3.2 (mục tiêu 3) VIẾT + BUILD + TEST OFFLINE LINUX (chưa build/test trên Windows, chưa thử trong game):
      `work/src/CaptchaQueue.cs` (gốc V8.3.1 lưu ở `work/src/CaptchaQueue.v8.3.1.cs.bak`). Thay đổi: giữ PNG trong inbox (marker `solved/<sha>.txt`, `failed/<sha>.txt`), đọc job JSON chịu lỗi (đọc chia sẻ, đếm ngoặc, thử lại ≤1.5 s), chờ PNG ổn định 150 ms + thử giải mã lại ≤10 s, ghi `outbox/<sha>.alt.txt` (cùng độ dài) TRƯỚC `.txt`, theo dõi answerLength 120 s (log REWRITE / LEN_MISMATCH / LEN khop), khôi phục `processing/` cũ về inbox, mutex cùng tên V8.3.1, `--queue <dir>` để test.
      Build: linux_build (net8, LangVersion 5) 0 lỗi; `work/net48_check` (net48 + C#5, ref assemblies) 0 lỗi 0 cảnh báo.
      Hồi quy: 32 ảnh one-shot trùng 32/32 với V8.3.1 (`work/run_linux_v831.json` vs `work/run_linux.json`).
      Test hàng đợi: `work/scripts/test_queue_linux.py` → `work/queue_test_linux.json` (20/20 PASS), log `work/queue_test_linux_solver.log`, `queue_test_linux_batch_solver.log`.
      Lưu ý: ảnh 71095CCA… cho đáp án 4 số (5357) → worker đánh dấu failed (ValidAnswer chỉ nhận 5–6 số, kế thừa V8.3.1); plugin thực ra nhận 3–8 ký tự.
- [ ] Chưa làm: sửa lỗi legend (@→M, gán số b/h, u/F), rồi chấm lại.

## File quan trọng
- `work/FINDINGS.md`: giao thức plugin + bằng chứng màu/ký hiệu.
- `work/scripts/build_log_labels.py`: đọc `inputs/rar_extract/diag_captcha/*.log` (chỉ dòng [Captcha*], đã lọc từ 593 log gốc) → `work/log_events.json`.
- `work/captcha_timeline.txt`: dòng Captcha của mọi log, sắp theo thời gian.
- `inputs/rar_extract/tudzday-captcha/`: solver.log, solve_legend.py, engine.cfg cũ trong RAR (đã xóa PNG trùng với work/img).
- `inputs/rar_extract/CaptchaQueue_in_rar.cs`: CaptchaQueue.cs nằm trong RAR (bản 120 KB, khác file đính kèm 141 KB).
- `work/scripts/run_offline_linux.py`: chạy bản Linux cho 32 ảnh → `work/run_linux.json`.
- `work/scripts/test_queue_linux.py`: test worker V8.3.2 (20 kiểm tra) → `work/queue_test_linux.json`.
- `make_checkpoint.py <N>`: tạo + kiểm tra ZIP checkpoint.

## Đã xác minh / giả thuyết
- Đã xác minh: 4 file đính kèm phiên này trùng byte với `inputs/original/` của gói Windows.
- Đã xác minh (log): 6 đáp án tra màu thời plugin 1.4.263 không đóng panel sau 5 s.
- Giả thuyết: panel còn mở 5 s ⇔ đáp án sai (chưa có đối chứng dương tính khi panel hiển thị).
- Giả thuyết: "FIRST_LIKELY_ACCEPTED" thời CaptchaBlocker không chứng minh được gì (plugin mất dấu panel).

## Lệnh build/test (Linux)
```bash
export DOTNET_ROOT=/data/.dotnet PATH=/data/.dotnet:$PATH
cd work/linux_build && dotnet build -c Release -o out   # đã chạy: 0 lỗi, 0 cảnh báo
cd ../.. && python3 work/scripts/run_offline_linux.py && python3 work/scripts/score_legend.py
python3 work/scripts/build_log_labels.py
python3 work/scripts/test_queue_linux.py   # 20/20 PASS (offline, Linux)
```
Trên Windows vẫn dùng `work/src/build.ps1` (chưa chạy lại trong phiên này — không có Windows).

## Bước tiếp theo
- Checkpoint v3 = V8.3.2 đã test Linux. Người dùng cần: build bằng `work/src/build.ps1` trên Windows, chạy `work/src/test_queue.py` (harness cũ, nhắm V8.3.1) hoặc thử trong game.
- Việc tiếp: sửa lỗi legend (@→M, gán số b/h, u/F) rồi chạy `score_legend.py` so với `work/legend_score_v831.txt`.
- ĐÃ XÁC MINH offline: 20/20 test queue. CHƯA xác minh: Windows build, plugin thật đọc .alt.txt, server chấp nhận đáp án.
