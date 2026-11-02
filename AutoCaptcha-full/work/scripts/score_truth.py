#!/usr/bin/env python3
"""Chấm bộ giải trên tập đáp án chuẩn work/truth/real_truth.jsonl (ảnh ở work/truth/img/).
Báo riêng: đáp án đúng nguyên chuỗi / chuỗi dải trên đúng / legend đúng. Ảnh thiếu được báo THIẾU, không tính vào mẫu số."""
import json, os, re, subprocess, sys
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
exe = sys.argv[1] if len(sys.argv) > 1 else os.path.join(W, 'linux_build/out/AutoCaptcha')
env = dict(os.environ)
if os.path.isdir('/data/.dotnet'):
    env.update(DOTNET_ROOT='/data/.dotnet', PATH='/data/.dotnet:' + os.environ['PATH'])
EQ = lambda s: s.upper().replace('I', 'L')   # l/I giống hệt trong font
n = ans_ok = top_ok = leg_ok = 0; missing = []
for line in open(os.path.join(W, 'truth/real_truth.jsonl'), encoding='utf-8'):
    T = json.loads(line); p = os.path.join(W, T['png'])
    if not os.path.exists(p): missing.append(T['id']); continue
    out = subprocess.run([exe, p], capture_output=True, text=True, env=env, timeout=60).stdout
    m = re.search(r'"answer": "([^"]*)"', out)
    got = m.group(1) if m else ''
    top = (re.search(r'top_chars=(\S*)', out) or [None, ''])[1]
    sm = dict(re.findall(r'(\S)->(\d)', (re.search(r'sym_map=\{([^}]*)\}', out) or [None, ''])[1] or ''))
    want_leg = {EQ(k): v for k, v in T['legend'].items()}
    got_leg = {EQ(k): v for k, v in sm.items()}
    a = got == T['answer']; t = EQ(top) == EQ(T['top']); l = got_leg == want_leg
    n += 1; ans_ok += a; top_ok += t; leg_ok += l
    print(f"{T['id']} ({T['note']}): đáp án {'ĐÚNG' if a else 'SAI'} got={got} want={T['answer']} | dải trên {'đúng' if t else 'sai'} got={top} want={T['top']} | legend {'đúng' if l else 'sai'}")
print(f"\nĐã chấm {n} ảnh; THIẾU ảnh: {len(missing)} {missing}")
if n: print(f"đáp án đúng {ans_ok}/{n}; dải trên đúng {top_ok}/{n}; legend đúng {leg_ok}/{n}")
