#!/usr/bin/env python3
"""So nhãn legend bằng mắt (work/labels_legend.jsonl) với sym_map của bộ giải (work/run_linux.json).
Báo: số ký hiệu đọc đúng tên (không phân biệt hoa thường) và lỗi gán chữ số (tên đúng, số sai)."""
import json, re, os, sys
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
run = json.load(open(os.path.join(W, sys.argv[1] if len(sys.argv) > 1 else 'run_linux.json')))
tot = ok_name = digit_err = 0; img_full = 0; rows = []
for line in open(os.path.join(W, 'labels_legend.jsonl')):
    L = json.loads(line); h = L['hash']
    det = json.loads(run[h]['details'])['details']
    sm = dict(re.findall(r'(\S)->(\d)', re.search(r'sym_map=\{([^}]*)\}', det).group(1)))
    truth = {k.upper(): v for k, v in L['legend'].items()}
    bad = []
    for k, v in truth.items():
        if k == '?': continue
        tot += 1
        if k in sm:
            ok_name += 1
            if sm[k] != v: digit_err += 1; bad.append(f'{k}:{v}≠{sm[k]}')
        else:
            bad.append(f'{k}->{v} đọc thành ' + ','.join(f'{a}' for a, b in sm.items() if b == v and a not in truth))
    digits_ok = sorted(truth.values()) == sorted(sm.values())
    if not bad: img_full += 1
    rows.append((L['i'], h, 'OK' if not bad else '; '.join(bad)))
for r in rows: print(*r)
print(f'Ký hiệu legend đọc đúng tên: {ok_name}/{tot}; lỗi gán số khi đúng tên: {digit_err}; ảnh legend hoàn toàn đúng: {img_full}/{len(rows)}')
