# HANDOFF — AutoCaptcha

## PHIÊN 3b — V8.3.4: ảnh thật đầu tiên có đáp án chuẩn (`work/truth/img/last_solved.png`, hash 7B465EFF2AD22518)
Người dùng xác nhận đáp án đúng = **131391** (legend đọc bằng mắt: v→7, l→1, x→5, E→3, C→9; dải trên l E l E C l). Đã thêm vào `work/truth/real_truth.jsonl` (id `user01`).

| Phiên bản | Đáp án chính | `.alt.txt` | Legend |
|---|---|---|---|
| bộ giải Python cũ (log 02/11 03:03) | 911591 | — | sai 2/5 ký hiệu (E→1, U→3) |
| V8.3.2 / V8.3.3 | 937399 | 937393 | sai 1/5 (`l` đọc thành `N`) |
| V8.3.4 | 111391 | **131391 (đúng)** | đúng 5/5 |

- Nguyên nhân `l→N`: đường kẻ vàng/đen vẽ ĐÈ lên đầu thân chữ `l` trắng (cùng cột, 7 hàng bị mất) → thân còn 12 hàng nên luật "thân hẹp" (`h>=14`) không kích hoạt, và dấu `-` của mũi tên không bị cắt.
- Sửa (V8.3.4): lượt phụ nối nét dọc bị đường kẻ KHÁC MÀU che (`FillUnderOtherLines`, khe ≤ 3 hàng); kết quả lượt phụ CHỈ được dùng để cứu ô mà luật thân hẹp nhận ra `L` (điểm đúng 0.92). Thử dùng lượt nối cho mọi ô làm 7/157 ký hiệu cũ sai thêm → không dùng.
- Không đổi gì ở 32 ảnh cũ: đáp án 32/32 trùng V8.3.3, legend vẫn 135/157 đúng tên; test hàng đợi 20/20.
- Còn sai: đáp án CHÍNH 111391 ≠ 131391 (ký tự thứ 2: `E` màu hồng bị đọc thành `L`; dải trên đọc LLLECL, đúng là LELECL). Đáp án THAY THẾ (`.alt.txt`) đúng, nên plugin sẽ đúng ở lần gửi thứ 2 — **chưa thử trong game**; nếu server tính số lần sai thì điều này có rủi ro.
- Cỡ mẫu = 1 ảnh có đáp án chuẩn; không suy ra tỷ lệ đúng. 11 đề Real còn lại vẫn thiếu PNG.

### Cập nhật 3c — `AutoCaptcha.exe` đã build lại từ V8.3.4 (nhưng CHƯA chạy trên Windows thật)
- `work/src/AutoCaptcha.exe` (trước là bản cũ) nay build từ `CaptchaQueue.cs` V8.3.4 bằng `work/scripts/build_net48_roslyn.sh`: Roslyn (dotnet SDK 8, C# 5) biên dịch với reference assemblies .NET Framework 4.8 của mono-devel. Biên dịch 0 lỗi → không dùng API ngoài .NET 4.8. SHA256 `3bc6a361…ca4d`.
- Đã chạy bằng Mono trên Linux: 32/32 ảnh trùng bản Linux .NET 8; `last_solved.png` → 111391, alt 131391; chế độ `--queue` ghi đúng `.txt` và `.alt.txt`. Mono ≠ Windows: chưa kiểm chứng trên .NET Framework thật, chưa kiểm SmartScreen/antivirus.
- Phiên khác (Wine+Mono) báo exe cũ trong repo ra cùng kết quả trên Windows thật/Mono/Wine; đó là bản CŨ, không áp dụng cho bản V8.3.4.
- Người dùng cuối chỉ cần file `AutoCaptcha.exe` (không Python, không cài thêm; Windows 10/11 có sẵn .NET Framework 4.8).

## PHIÊN 3 (Claude, sandbox Linux, 2026-11-02 ~21:20 +07) — V8.3.3: sửa nhận diện legend  ← ĐỌC PHẦN NÀY TRƯỚC
Phần "phiên Notion AI" bên dưới giữ nguyên làm lịch sử. Nhánh: `claude/autocaptcha-legend-v833`.

### Môi trường phiên này
- `/data/...` không còn. .NET 8 cài bằng `apt-get install dotnet-sdk-8.0 dotnet-targeting-pack-8.0` (sandbox không truy cập được nuget.org/dot.net).
- Build offline: `cd work/linux_build && dotnet build -c Release -o out --source /tmp/emptysrc` (thư mục rỗng để NuGet khỏi gọi mạng). `obj/` đã .gitignore.
- Script `run_offline_linux.py` / `test_queue_linux.py` không còn cố định `/data/.dotnet`; `run_offline_linux.py [exe] [tên-file-json]`.

### Đã làm
1. Dựng lại baseline: build V8.3.2 → 32/32 ảnh trùng `run_linux.json` cũ (đã lưu thành `work/run_linux_v832.json`).
2. Chẩn đoán lỗi legend bằng dump mặt nạ (không đoán):
   - `@→M`: `MorphOpen(1,3)` xóa nét ngang mỏng (cung trên/dưới của `@`, thanh ngang của `e`/`a`) → còn 3 cột dọc giống `M`.
   - `b↔h` (3CE6…): đường kẻ khác màu VẼ ĐÈ lên cung đáy của `b` → mất thông tin trong ảnh, không phục hồi được từ ảnh này. Chữ số 1/3 gán ĐÚNG; chỉ tên hai ô bị hoán đổi (cả hai ô trông như `h`).
   - `u/F` (233A…): chữ số `5` bị đường kẻ cùng màu làm dày, điểm 3 và 5 gần hòa (0.68 vs 0.67) nên hoán đổi.
3. Sửa trong `work/src/CaptchaQueue.cs` (V8.3.3, chỉ đụng nhận diện KÝ HIỆU legend; worker/queue không đổi):
   - `RemoveLineBands`: dò đường kẻ thẳng cùng màu (Hough đơn giản, |dốc| ≤ 0.7, ≥ 90 pixel), bỏ phần mỏng (run dọc ≤ 3) nằm trên đường.
   - `GeodesicGrow`: mọc lại tối đa 6 bước từ lõi "open" trong mặt nạ đã bỏ đường kẻ, giới hạn quanh ký hiệu.
   - Lấp khe ngang ≤ 4 px nếu mặt nạ thô ở giữa bật hết.
   - Hằng số `LEGEND_BRIDGE_MAX_GAP=4`, `LEGEND_LINE_MIN_SUPPORT=90`, `LEGEND_RECON_ITERS=6`.
4. Công cụ đo mới: `work/scripts/compare_legend.py A.json B.json` (liệt kê ký hiệu mới đúng/mới sai theo nhãn legend; coi I≡L vì l/I giống hệt trong Arial Bold).

### Kết quả (đo trên 32 ảnh / 157 ký hiệu nhãn bằng mắt — xem `work/legend_score_v833.txt`, `work/legend_compare_v832_vs_v833.txt`)
| | V8.3.2 | V8.3.3 |
|---|---|---|
| Ký hiệu đúng TÊN (không tính số) | 128/157 | 135/157 |
| Ký hiệu đúng tên + đúng số (I≡L) | 125/157 | 133/157 |
| Ảnh legend đúng hoàn toàn | 13/32 | 17/32 |
- Mới đúng 9, mới sai 1 (`v` ở E9CB… → đọc thành U). Quét tham số (rec 3–8, ngưỡng 60–120): vùng bằng phẳng, nhưng 3 tham số này CHỌN TRÊN CHÍNH 157 nhãn đó ⇒ số liệu là IN-SAMPLE, chưa có tập kiểm chứng độc lập; không suy ra độ chính xác ngoài tập.
- `@` VẪN CHƯA ĐÚNG ở 5/7 ảnh có `@` (290B, 58EE, 5B25, 78F2, FBC8: giờ bị đọc thành `&`/`Q` thay vì `M`; chỉ 4A51 và BAB9 đúng). Chỉ kiểm ở 290B: sau các bước cắt trong `ClassifyLegendSymbol` crop còn rộng 17 (<19) nên `@` rơi khỏi nhóm ứng viên rộng; các ảnh còn lại CHƯA kiểm nguyên nhân.
- Đáp án cuối (dải trên + legend) ĐỔI ở 12/32 ảnh so với V8.3.2 (danh sách: so `run_linux_v832.json` với `run_linux.json`). KHÔNG có ground truth cho đáp án cuối nên không biết đúng/sai; không tuyên bố cải thiện đáp án.
- Test hàng đợi Linux: 20/20 PASS với bản V8.3.3 (`work/queue_test_linux.json`). Ảnh 71095CCA… vẫn ra 4 số → đánh dấu failed như cũ.

### Cập nhật cuối phiên 3 — đáp án chuẩn do người dùng cung cấp
- Người dùng gửi bảng "KIỂM CHỨNG V8.3" và khẳng định: dòng `Top: … → đáp án` dưới mỗi ô là ĐÚNG; mã trong ô trắng là đáp án SAI của bản cũ (trước đó mình hiểu ngược). Điều này mình chưa tự xác minh.
- Đã chép 12 đề Real vào `work/truth/real_truth.jsonl` (legend + dải trên + đáp án; mỗi dòng đã tự kiểm legend×dải trên = đáp án). 12 đề Adv là biến thể giả lập (cùng dải trên, legend đảo số) nên không đưa vào chuẩn.
- 12 đề này KHÔNG nằm trong 32 ảnh của repo và chưa có PNG gốc → CHƯA chạy được. Cần người dùng đặt ảnh gốc (`inbox/<HASH>.png` của plugin) vào `work/truth/img/real01.png … real12.png`, rồi chạy `python3 work/scripts/score_truth.py`.
- V8.3.3 chưa được chấm trên tập này; không có số liệu độ chính xác cho 12 đề Real.

### CHƯA kiểm chứng
- Chưa build bằng `build.ps1`/csc trên Windows; `work/src/AutoCaptcha.exe` và `work/net48_check/out/*` là bản CŨ (V8.3.2), chưa build lại. Linux build dùng LangVersion 5 nên cú pháp tương thích C# 5, nhưng API .NET Framework 4.x chưa được biên dịch thật.
- Chưa thử trong game; chưa biết server có chấp nhận đáp án V8.3.3 hay không.
- Nhãn legend là nhãn bằng mắt của phiên trước, chưa kiểm chéo độc lập (tôi chỉ nhìn lại ~8 ô, khớp nhãn).

### Việc tiếp theo gợi ý
- Giữ `@` trong nhóm ứng viên rộng (hoặc chấm điểm bổ sung `@` trước các bước cắt), rồi đo lại bằng `compare_legend.py`.
- Cần tập nhãn mới (ảnh ngoài 32 ảnh này) để kiểm chứng độc lập trước khi tin các tham số.
- Build Windows: `work/src/build.ps1`, chạy `work/src/test_queue.py`, rồi thử trong game.

---
## PHIÊN 2 (Notion AI, sandbox Linux, bắt đầu 2026-11-02 19:14 +07) — lịch sử

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
