#!/usr/bin/env python3
"""Trích sự kiện CAPTCHA theo từng tiến trình game từ tudzday-diagnostics/*.log.
Đầu ra: work/log_events.json (mỗi captcha 1 bản ghi) — KHÔNG phải nhãn server xác nhận trực tiếp,
chỉ là bằng chứng gián tiếp từ hành vi plugin. Chạy: python3 work/scripts/build_log_labels.py"""
import re, json, glob, os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIAG = os.path.join(ROOT, 'inputs/rar_extract/diag_captcha')
OUT = os.path.join(ROOT, 'work/log_events.json')
ts_re = re.compile(r'^(\S+Z) \[(\w+)\s*\] \[(Captcha\w+)\] (.*)$')
events = []
for path in sorted(glob.glob(os.path.join(DIAG, '*.log'))):
    fname = os.path.basename(path)
    cur = None; last_field = None; last_submit_any = None
    with open(path, encoding='utf-8', errors='replace') as fh:
        for line in fh:
            m = ts_re.match(line.rstrip('\n'))
            if not m: continue
            ts, lvl, tag, msg = m.groups()
            if msg.startswith('field mvd='):
                fm = re.match(r"field mvd='([^']*)' mve='([^']*)'", msg)
                last_field = fm.groups() if fm else None
            elif msg.startswith('publish '):
                h = msg.split()[1]
                cur = {'file': fname, 'hash': h, 'publish': ts, 'mvd_at_publish': last_field[0] if last_field else None,
                       'prev_submit_in_process': last_submit_any, 'submits': [], 'warnings': []}
                events.append(cur); last_field = None
            elif cur and msg.startswith('submit '):
                sm = re.match(r'submit (\S+) \((.*)\)', msg)
                cur['submits'].append({'ts': ts, 'answer': sm.group(1), 'kind': sm.group(2)})
                last_submit_any = sm.group(1)
            elif cur and lvl == 'Warning' and 'CaptchaQueue' in tag:
                cur['warnings'].append(msg[:160])
            elif cur and msg.startswith('label '):
                cur.setdefault('labels', []).append(msg)
# kết luận gián tiếp
for i, e in enumerate(events):
    s = e['submits']; w = ' | '.join(e['warnings'])
    lan = [x for x in s if x['kind'].startswith('lan')]
    if not s:
        e['inference'] = 'NO_AUTO_SUBMIT'
    elif not lan:
        e['inference'] = 'OLD_PROTOCOL_UNKNOWN'  # '(answer file)' – plugin cũ không có kiểm tra panel
    elif len(lan) >= 2:
        e['inference'] = 'FIRST_REJECTED'        # panel còn mở 5s sau lần 1
    elif 'không có đáp án dự phòng' in w:
        e['inference'] = 'FIRST_REJECTED_NO_ALT'
    elif '20s chưa có đáp án' in w and s and s[0]['ts'] > e['publish']:
        e['inference'] = 'LATE_SUBMIT_CHECK_SKIPPED'
    else:
        e['inference'] = 'FIRST_LIKELY_ACCEPTED' # panel đóng trước kiểm tra 5s
# mvd tại publish kế tiếp cùng file = chữ cuối cùng trong ô nhập (có thể là nhập tay)
by_file = {}
for e in events: by_file.setdefault(e['file'], []).append(e)
for f, lst in by_file.items():
    for a, b in zip(lst, lst[1:]):
        a['next_mvd_same_process'] = b['mvd_at_publish']
        a['next_publish_same_process'] = b['publish']
tmp = OUT + '.tmp'
json.dump(events, open(tmp, 'w'), ensure_ascii=False, indent=1); os.replace(tmp, OUT)
from collections import Counter
print('events', len(events), Counter(e['inference'] for e in events))
