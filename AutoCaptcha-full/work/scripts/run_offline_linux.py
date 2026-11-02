#!/usr/bin/env python3
"""Chạy work/linux_build/out/AutoCaptcha (.NET 8) cho từng ảnh work/img/*.png → work/run_linux.json.
So sánh với work/run3v.json (bản Windows)."""
import subprocess, json, glob, os, re
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env = dict(os.environ, DOTNET_ROOT='/data/.dotnet', PATH='/data/.dotnet:' + os.environ['PATH'])
exe = os.path.join(W, 'linux_build/out/AutoCaptcha')
res = {}
for p in sorted(glob.glob(os.path.join(W, 'img/*.png'))):
    h = os.path.basename(p)[:16]
    r = subprocess.run([exe, p], capture_output=True, text=True, env=env, timeout=60)
    out = r.stdout.strip()
    m = re.search(r'"answer": "([^"]*)"', out)
    res[h] = {'answer': m.group(1) if m else None, 'exit': r.returncode, 'details': out[-600:], 'stderr': r.stderr[-300:]}
tmp = os.path.join(W, 'run_linux.json.tmp'); json.dump(res, open(tmp, 'w'), indent=1); os.replace(tmp, os.path.join(W, 'run_linux.json'))
print(len(res), 'images')
