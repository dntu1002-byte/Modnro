#!/usr/bin/env python3
"""So sánh 2 lần chạy offline (run_*.json) theo nhãn legend bằng mắt: liệt kê ký hiệu mới đúng / mới sai.
Dùng: compare_legend.py A.json B.json   (đường dẫn tuyệt đối, hoặc tương đối với work/)
Đúng = tên ký hiệu có trong sym_map VÀ chữ số gán đúng (không phân biệt hoa/thường;
I và L coi là MỘT lớp vì l/I giống hệt nhau trong font Arial Bold — xem inputs/original/pasted-text.txt dòng 37)."""
import json, re, os, sys
W = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

EQ = {'I': 'L'}

def correct_set(path):
    run = json.load(open(os.path.join(W, path)))
    ok = set(); tot = 0
    for line in open(os.path.join(W, 'labels_legend.jsonl')):
        L = json.loads(line); h = L['hash']
        det = json.loads(run[h]['details'])['details']
        sm = {EQ.get(k, k): v for k, v in re.findall(r'(\S)->(\d)', re.search(r'sym_map=\{([^}]*)\}', det).group(1))}
        for k, v in L['legend'].items():
            if k == '?': continue
            tot += 1
            kk = k.upper()
            if sm.get(EQ.get(kk, kk)) == v: ok.add((h, k, v))
    return ok, tot

a, tot = correct_set(sys.argv[1]); b, _ = correct_set(sys.argv[2])
print(f'A: {len(a)}/{tot}  B: {len(b)}/{tot}')
print('MỚI ĐÚNG (B có, A không):', sorted(b - a))
print('MỚI SAI  (A có, B không):', sorted(a - b))
