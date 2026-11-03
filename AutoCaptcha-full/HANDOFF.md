# HANDOFF — AutoCaptcha

## PHIÊN 7 — công cụ nhìn ảnh đã bỏ phông + đường nhiễu; ảnh `215951` đáp án người dùng báo 37119 KHÔNG khớp
- Hiện trạng pipeline (có sẵn từ trước): phông chữ xám bị loại vì phân loại màu (`BuildColorMasksPure`: chỉ nhận trắng/đen/6 màu bão hoà); dải trên bỏ đường kẻ ngang bằng lọc trung vị theo hàng (`RemoveHorizontalLinesPure`, cửa sổ 51); legend bỏ đường kẻ bằng `RemoveLineBands` + `FillUnderOtherLines` (lượt phụ). Đường kẻ vẽ ĐÈ LÊN ký tự nên bỏ đường = để lại khe trong nét; V8.3.6 bù bằng điểm "chỉ trên ô không bị che".
- Mới: `AutoCaptcha.exe --dump-clean <in.png> <out.ppm>` xuất 3 khung (gốc / đã bỏ phông+đường / đã NỐI khe ≤4 hàng bị đường che). Ví dụ trong `work/clean/` (`clean_n6_215951.png`, `clean_user05_204012.png`). Chỉ để nhìn, không dùng trong `SolveImage`. Khung nối làm dải trên đọc được bằng mắt (user05: `A C e % H` rõ).
- Thí nghiệm (không đưa vào bản chính): nối khe ≤3–4 hàng NGAY TRƯỚC khi phân loại, tập chuẩn bỏ user03 (4 ảnh): chỉ nối (w=0) → đúng user01, user02, user04 (3/4, không cần trọng số 0.6; sai user05); nối + pha 0.6 → 3/4; chỉ pha 0.6 không nối (V8.3.6) → 4/4; không nối, không pha → 1/4. Cỡ mẫu rất nhỏ, chưa kết luận.
- Ảnh `215951` (`main` `de23d27`): V8.3.6 ra `AA#PAK` → 117915. Khung nối cho thấy dải trên: hồng `#`, trắng + đen chồng nhau (đen là `#`), đỏ `P`, vàng `A`, xanh dương `X`. Ô nhập đáp án trong ảnh có 5 gạch (5 ký tự). Người dùng báo đáp án 37119 ⇒ theo legend `p9 #7 k5 A1 X3` cần dải trên `X # A A p` (X đầu tiên, A hai lần) — KHÔNG khớp thứ tự trái→phải của ảnh (X nằm ngoài cùng bên phải, chỉ có 1 A). Chưa thêm vào `real_truth.jsonl`; cần người dùng kiểm lại đáp án / ảnh tương ứng.

## PHIÊN 6b — ảnh mới `Screenshot 2026-11-03 215951.png` (trên `main`, commit `de23d27`), CHƯA có đáp án chuẩn
V8.3.6 (.NET 8 và exe net48/Mono cho kết quả giống nhau): legend `P->9, #->7, K->5, A->1, X->3` (khớp mắt: `p→9, #→7, k→5, A→1, X→3`); dải trên 6 ký tự `AA#PAK`, đáp án **117915**, alt 117911. Điểm sát: ký tự 1 `A` 0.643 vs `P` 0.612; ký tự 6 `K` 0.667 vs `A` 0.660.
Đọc bằng mắt (KHÔNG phải ground truth, dải trên bị che nặng): hồng `#`, trắng `p`, đen `k`, đỏ `P`, vàng `A`, xanh dương `X` → `#pkPAX` = 795913. Nếu đúng thì solver sai ~4/6 ký tự (chỉ đỏ `P` và vàng `A` khớp). Chờ người dùng xác nhận trước khi thêm vào `real_truth.jsonl`.

## PHIÊN 6 — V8.3.6: chấm điểm CÓ CHÚ Ý CHE KHUẤT cho dải trên (user04 = 59971, user05 = 35197)
Nhánh `claude/autocaptcha-v836-next`. Đáp án chuẩn người dùng xác nhận: ảnh `201155` = **59971** (`user04`), ảnh `204012` = **35197** (`user05`, dải trên `ACE%H`, e thường); cả hai đã vào `work/truth/`. V8.3.5 sai cả hai (59991; 75997).
- Nguyên nhân (đã chẩn đoán bằng số liệu): mẫu khớp nguyên khối phạt cả những ô glyph bị đường kẻ màu khác đè → ký tự còn mảnh (Z xanh lá ở user04, A xanh dương và e hồng ở user05) thua `@`/`H`/`%`.
- Sửa (chỉ `ClassifyTopGlyph`): với mỗi ký tự có ô bị che, tính thêm điểm `occ` = cùng công thức `ScoreBinary2D` nhưng CHỈ trên các ô 16×16 không bị che (ô bị che = pixel có màu khác đè lên pixel của chính ký tự; cùng phép chuẩn hoá như `NormalizeSymbol16`, hàm `NormalizeSymbol16Occ` / `ScoreBinary2DVisible`). Điểm cuối = `0.4*điểm cũ + 0.6*occ`; ký tự không có ô bị che giữ nguyên. Legend không đụng. `WorkerVersion` = V8.3.6.
- Kết quả trên tập chuẩn (Linux .NET 8 và exe net48 qua Mono, giống nhau): user01 ĐÚNG, user02 ĐÚNG, **user04 ĐÚNG**, **user05 ĐÚNG**, user03 SAI (535395 vs 535113; legend `%` vẫn không nhận ra, và dải trên có 2 `%` chồng nhau — chưa sửa) → đáp án chính **4/5** (trước: 1/5). Mức ký tự dải trên (không tính user03): 21/21 so với 17/21 ở V8.3.5.
- **Cảnh báo quá khớp — ĐỌC KỸ:** trọng số 0.6 chọn bằng quét trên chính các ảnh này (21 ký tự, 4 ảnh). Quét w: 0.0–0.2 → 17/21; 0.3–0.5 → 20/21; **0.6–0.7 → 21/21**; 0.8 → 20/21; 1.0 (chỉ occ) → 18/21. Có một đoạn phẳng 0.3–0.8 nên không phải điểm dao động, nhưng không phải kiểm định độc lập. Quy tắc thêm sau khi thấy lỗi của user04/user05.
- **Biến động trên 32 ảnh cũ (KHÔNG có đáp án chuẩn dải trên): đáp án chính đổi ở 16/32 ảnh** (`work/run_linux_v835.json` = trước, `work/run_linux.json` = sau). Không biết hướng đổi là tốt hay xấu; mắt Claude không đọc chắc được các ảnh đó. Đã thử thêm "cổng biên độ" (chỉ pha khi chênh điểm top-1/top-2 nhỏ) → gần như không giảm biến động nên bỏ. KHÔNG suy ra độ chính xác từ các con số trên.
- Kiểm thử: `score_truth.py` 4/5; `test_queue_linux.py` 20/20 (sau khi tạo lại `run_linux.json` làm baseline V8.3.6); `score_legend.py` vẫn 135/157 ký hiệu, 17/32 ảnh legend đúng. `linux_build` build offline được bằng `dotnet build -c Release -o out --source /usr/lib/dotnet/library-packs` (không cần nuget.org). `AutoCaptcha.exe` build lại bằng `build_net48_roslyn.sh` (Roslyn + mono-devel ref assemblies; cần `apt install dotnet-sdk-8.0 mono-devel`).
- CHƯA kiểm chứng: Windows thật, plugin đọc `.alt.txt`, trong game, server chấp nhận đáp án; độ chính xác tổng thể (chưa có tập chuẩn đủ lớn).
- Việc tiếp: user03 (ghép mảnh khác màu chồng nhau + `%` legend bị đọc `T`/`S`); cần thêm ảnh có đáp án chuẩn để kiểm định độc lập trọng số 0.6.

## PHIÊN 5c — ảnh mới `Screenshot 2026-11-03 204012.png` (trên `main`, commit `0e662a7`), CHƯA có đáp án chuẩn
V8.3.5 (exe, Mono/Linux, không đổi mã): legend đọc `%->9, H->7, E->1, C->5, A->3` (khớp mắt: `%→9, h→7, e→1, C→5, A→3`); dải trên `HC%%H`, đáp án **75997**, alt 75977. Điểm ký tự 1 (xanh dương) `H` 0.799 vs `A` 0.656; ký tự 3 (hồng) `%` 0.540 vs `E` 0.494.
Đọc bằng mắt (KHÔNG phải ground truth): xanh dương trông là `A` to rõ, xanh lá `C`, hồng giống cung `C`, trắng `%`, đen giống `h` → có thể `ACC%h` = 35597; nếu đúng thì solver sai ≥ 2–3/5. Chờ người dùng xác nhận trước khi thêm vào `real_truth.jsonl`.

## PHIÊN 5 — chạy bản mới nhất (V8.3.5) trên ảnh người dùng vừa upload (`Screenshot 2026-11-03 201155.png`)
Nhánh `claude/autocaptcha-v836-next` (tách từ `claude/autocaptcha-v835-user02`; ảnh mới lấy từ `main`, commit `3245107`). Chạy `work/src/AutoCaptcha.exe` (V8.3.5, net48) bằng Mono 6 trên Linux — KHÔNG phải Windows thật, KHÔNG phải trong game.
- Ảnh mới (255×256): legend đọc bằng mắt `l->5, &->1, z->7, %->3, @->9`. Solver: legend ĐÚNG hoàn toàn (`L->5, Z->7, @->9, &->1, %->3`; L≡l/I trong font).
- Dải trên solver đọc `L@@@&`, đáp án chính **59991**, alt `53991`. **Người dùng xác nhận đáp án đúng là 59971** → SAI 1/5 chữ số (ký tự thứ 4, xanh lá, là `z` nhưng bị đọc `@`). Đã thêm vào tập chuẩn là `user04` (`work/truth/img/user04.png`, dải trên suy ra `L@@Z&`).
- Chẩn đoán (in thêm `items=[...]` vào debugInfo, không đổi hành vi): điểm từng ký tự dải trên — R `L` 0.717; Y `@` 0.494 (alt `%` 0.492); B `@` 0.605; **G: `@` 0.429, `%` 0.386, `Z` 0.368, `L` 0.245, `&` 0.316 (Z hạng 3, đúng là Z)**; M `&` 0.586 (alt `@` 0.562 — sát nút). Ký tự xanh lá chỉ còn các mảnh (thanh trên ngắn bị đường kẻ che, nét chéo, thanh dưới), so khớp mẫu nguyên khối không đủ phân biệt Z với @/%. Cùng nguyên nhân gốc như user03: cần so khớp có chú ý che khuất; CHƯA sửa (chỉnh luật cho đúng 1 ảnh = quá khớp).
- Chấm lại tập chuẩn (`score_truth.py`, exe qua Mono): user01 SAI chính (111391 vs 131391; alt đúng), user02 ĐÚNG, user03 SAI (535355 vs 535113), user04 SAI (59991 vs 59971) → **1/4** đáp án chính; legend đúng 3/4. Chỉ thay đổi: thêm `items=[...]` vào debugInfo (đáp án không đổi); `AutoCaptcha.exe` build lại bằng `build_net48_roslyn.sh` (dotnet-sdk-8.0 + mono-devel cài qua apt). `test_queue_linux.py` 20/20 nhưng chạy với `linux_build/out` CŨ (không build lại được: sandbox không tới nuget.org) — phần worker không đổi.
- Chưa kiểm chứng: Windows thật, plugin đọc `.alt.txt`, server chấp nhận đáp án.

## PHIÊN 4b — user03 (đáp án chuẩn 535113): V8.3.5 SAI, CHƯA SỬA
Ảnh `work/truth/img/user03.png` (chụp màn hình 253×256; bản gốc người dùng upload ở `main`: `work/img/Screenshot 2026-11-03 194407.png`). Legend đọc bằng mắt: %→1, E→7, s→9, B→5, d→3. Đáp án người dùng xác nhận **535113**; dải trên suy ra `BDB%%D` (ký tự 4 đen và 5 đỏ là HAI dấu `%` chồng lên nhau).
- V8.3.5: 535355 (`BDBDBB`, legend `T,S,D,E,B`), alt 935355 → SAI 3/6 chữ số. Điểm tin cậy dải trên chỉ 0.52–0.61 (ảnh user02: 0.93–1.0); 4/6 ký tự hơn ký tự xếp sau < 0.02.
- Nguyên nhân đã chẩn đoán (dump mặt nạ, nhưng CHƯA có bản sửa):
  1. Legend `%` (hồng) bị đọc `T`: đường kẻ đen chéo dày ~5 px cắt vòng tròn trái của `%`; sau `MorphOpen(1,3)` + loại thành phần nhỏ, mặt nạ chỉ còn nét chéo + vòng dưới (`symX0=11` đã mất vòng trái) → `%` không còn nằm trong các ứng viên (điểm T=0.625; `%` không có trong `AllSymScores`). Chữ số gán cho `%` vẫn đúng (1). Ép `T→%` thử nghiệm không đổi đáp án chính.
  2. Dải trên: giả định "mỗi màu = một ký tự". Ở đây hai `%` KHÁC MÀU chồng lên nhau, mỗi màu chỉ giữ một mảnh (đen: nét chéo + vòng; đỏ: một vòng) → không có cách nào đọc đúng mà không ghép mảnh khác màu. Ký tự vàng (d) bị đọc B (0.587 vs D 0.546).
- Hướng sửa (chưa làm, cần quyết định): so khớp mẫu có chú ý che khuất (chỉ tính điểm trên pixel không bị đường kẻ khác màu che) cho cả legend lẫn dải trên, và cho phép ghép các mảnh khác màu chồng nhau. Với 3 ảnh có đáp án chuẩn, mọi tham số mới đều dễ quá khớp → cần thêm ảnh chuẩn trước khi chỉnh.
- Tập chuẩn có PNG hiện nay: user01 (sai chính, alt đúng), user02 (đúng), user03 (sai) → 1/3 đúng đáp án chính.

## PHIÊN 4 — V8.3.5: ảnh user02 (đáp án chuẩn 11175), sửa nhầm C↔D ở dải trên
Nhánh `claude/autocaptcha-v835-user02` (tách từ `claude/autocaptcha-legend-v833`). LƯU Ý: `main` KHÔNG chứa công việc V8.3.3–V8.3.4 (main tách ra từ `b30693c`, chỉ nhận các commit "Add files via upload"); ảnh người dùng upload qua web nằm trên `main` (commit `827f338`, `work/img/Screenshot 2026-11-03 015539.png`) và được chép sang `work/truth/img/user02.png` ở nhánh này.

- Ảnh: chụp màn hình cả khung 255×253 (không phải PNG gốc 256×256). Legend đọc bằng mắt: b→1, D→3, w→9, C→5, $→7 (trùng 5/5 với solver). Đáp án người dùng xác nhận: **11175** (dải trên suy ra: `BBB$C`).
- V8.3.4 cho **11173** (dải trên `BBB$D`), alt `19173` → cả hai SAI. Nguyên nhân (dump mặt nạ, không đoán): ký tự xanh lá thật là `C` nhưng nét phải giữa bị đứt; luật cũ `midRightEmptyLoc && lowRightWallOk` cộng +0.18 cho `D` (giả định nét phải bị đường kẻ che) → D 0.663 > C 0.397.
- Sửa (V8.3.5, chỉ `ClassifyTopGlyph`): `HasConfirmedRightGap` — nếu ở 70% phải của ký tự có một dải hàng liên tiếp (≥ max(4, 18% chiều cao), trong 25–80% chiều cao) mà KHÔNG có pixel của bất kỳ màu nào (không phải đường kẻ, không phải ký tự → là nền thật) VÀ ký tự có nét cùng màu bên phải cả phía trên lẫn phía dưới khe, thì D/O/Q/B/0 −0.15, C +0.15 và bỏ luật +0.18 cho D. Đường kẻ che nét thì có pixel màu nên không kích hoạt. Điều kiện "có nét trên và dưới khe" thêm sau khi bản đầu làm `user01` hỏng (L bị đọc thành C).
- Kết quả (Linux; .NET 8 và exe net48 chạy bằng Mono): user02 → **11175 ĐÚNG** (alt 19175); 32 ảnh cũ: đáp án 32/32 trùng V8.3.3/V8.3.4; `user01` giữ nguyên (chính 111391, alt 131391 đúng); test hàng đợi 20/20 (`test_queue_linux.py` dùng `linux_build/out/AutoCaptcha`, đã build lại từ nguồn V8.3.5).
- **Cảnh báo quá khớp:** quy tắc chọn dựa trên đúng 1 ảnh (user02), kiểm hồi quy chỉ trên 33 ảnh còn lại KHÔNG có đáp án chuẩn dải trên (trừ user01) → "không đổi" chỉ chứng minh không đổi hành vi, không chứng minh đúng. Không suy ra độ chính xác. Tập chuẩn hiện: 2 ảnh có PNG (user01 sai đáp án chính nhưng alt đúng; user02 đúng), 12 đề Real vẫn thiếu PNG.
- Còn sai: user01 (đáp án chính 111391, ký tự thứ 2 `E` hồng bị đọc `L`); ký tự đỏ ở user02 điểm sát nút (B 0.634 vs W 0.618) — đúng nhưng mong manh.
- `src/AutoCaptcha.exe` build lại từ V8.3.5 bằng `scripts/build_net48_roslyn.sh` (Roslyn + ref assemblies 4.8). CHƯA chạy trên Windows thật, chưa thử trong game, chưa kiểm server chấp nhận.

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
- `work/src/AutoCaptcha.exe` (trước là bản cũ) nay build từ `CaptchaQueue.cs` V8.3.4 bằng `work/scripts/build_net48_roslyn.sh`: Roslyn (dotnet SDK 8, C# 5) biên dịch với reference assemblies .NET Framework 4.8 của mono-devel. Biên dịch 0 lỗi → không dùng API ngoài .NET 4.8. SHA256 `ea38c6c5…f970` (build không tất định: mỗi lần build ra hash khác).
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
