#!/usr/bin/env python3
"""Chạy work/linux_build/out/AutoCaptcha (.NET 8) cho từng ảnh work/img/*.png → work/run_linux.json.
So sánh với work/run3v.json (bản Windows)."""
import subprocess, json, glob, os, re
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
import sys
env = dict(os.environ)
if os.path.isdir('/data/.dotnet'):
    env.update(DOTNET_ROOT='/data/.dotnet', PATH='/data/.dotnet:' + os.environ['PATH'])
# Cách dùng: run_offline_linux.py [đường-dẫn-exe] [tên-file-kết-quả]; mặc định linux_build/out/AutoCaptcha -> run_linux.json
exe = sys.argv[1] if len(sys.argv) > 1 else os.path.join(W, 'linux_build/out/AutoCaptcha')
outname = sys.argv[2] if len(sys.argv) > 2 else 'run_linux.json'
res = {}
for p in sorted(glob.glob(os.path.join(W, 'img/*.png'))):
    h = os.path.basename(p)[:16]
    r = subprocess.run([exe, p], capture_output=True, text=True, env=env, timeout=60)
    out = r.stdout.strip()
    m = re.search(r'"answer": "([^"]*)"', out)
    res[h] = {'answer': m.group(1) if m else None, 'exit': r.returncode, 'details': out[-600:], 'stderr': r.stderr[-300:]}
tmp = os.path.join(W, outname + '.tmp'); json.dump(res, open(tmp, 'w'), indent=1); os.replace(tmp, os.path.join(W, outname))
print(len(res), 'images')
