#!/usr/bin/env python3
"""Tạo /data/checkpoints/AutoCaptcha-checkpoint-v<N>.zip, kiểm tra CRC + SHA256 từng file.
Dùng: python3 make_checkpoint.py <N>. Bỏ qua RAR gốc, log đầy đủ, ảnh phóng to, bin/obj, .dotnet."""
import sys, os, zipfile, hashlib, json
root = os.path.dirname(os.path.abspath(__file__)); n = sys.argv[1]
out = f'/data/checkpoints/AutoCaptcha-checkpoint-v{n}.zip'
if os.path.exists(out): sys.exit('ZIP đã tồn tại, không ghi đè: ' + out)
SKIP_DIRS = {'inputs/session3', 'inputs/rar_extract/tudzday-diagnostics', 'inputs/rar_extract/BepInEx',
             'work/view', 'work/view_top', 'bin', 'obj', '.dotnet'}
SKIP_NAMES = {'MANIFEST.json'}
files = []
for d, dirs, fs in os.walk(root):
    rel = os.path.relpath(d, root).replace('\\', '/')
    dirs[:] = [x for x in dirs if (x if rel == '.' else rel + '/' + x) not in SKIP_DIRS and x not in ('bin', 'obj')]
    for f in fs:
        p = os.path.join(d, f); r = os.path.relpath(p, root).replace('\\', '/')
        if f in SKIP_NAMES or f.endswith(('.tmp', '.rar')) or any(k in f.lower() for k in ('password', 'token', 'secret')): continue
        files.append(r)
files.sort()
man = {r: {'size': os.path.getsize(os.path.join(root, r)), 'sha256': hashlib.sha256(open(os.path.join(root, r), 'rb').read()).hexdigest()} for r in files}
tmp = out + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for r in files: z.write(os.path.join(root, r), r)
    z.writestr('MANIFEST.json', json.dumps(man, indent=1))
with zipfile.ZipFile(tmp) as z:
    assert z.testzip() is None
    for r, m in man.items(): assert hashlib.sha256(z.read(r)).hexdigest() == m['sha256'], r
    assert 'HANDOFF.md' in z.namelist()
os.replace(tmp, out)
print('OK', out, len(files) + 1, 'files', os.path.getsize(out), 'bytes', hashlib.sha256(open(out, 'rb').read()).hexdigest())
