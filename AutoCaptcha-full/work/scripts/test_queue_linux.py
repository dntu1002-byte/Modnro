#!/usr/bin/env python3
"""Kiểm thử worker V8.3.2/V8.3.3 (queue-only) trên Linux bằng AutoCaptcha --queue <dir>.
Ghi: work/queue_test_linux.json, work/queue_test_linux_solver.log. Đây là test OFFLINE, không phải test trong game."""
import json, os, shutil, subprocess, time, uuid, re, pathlib, signal
W = pathlib.Path(__file__).resolve().parent.parent
EXE = W / 'linux_build/out/AutoCaptcha'
ENV = dict(os.environ)
if os.path.isdir('/data/.dotnet'):
    ENV.update(DOTNET_ROOT='/data/.dotnet', PATH='/data/.dotnet:' + os.environ['PATH'])
IMG = W / 'img'
base = json.load(open(W / 'run_linux.json'))
A = '064937887D4981B0'      # 35919 (5 so)
SIX = '233AEA7A19420FEC'    # 571719 (6 so)
root = pathlib.Path('/tmp/qtest-' + uuid.uuid4().hex[:6]); root.mkdir()
checks, procs = [], []

def wait_for(pred, timeout=15):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            if pred(): return True
        except Exception: pass
        time.sleep(0.05)
    return False

def check(name, ok, extra=''):
    checks.append({'name': name, 'passed': bool(ok), 'extra': extra})
    print(('PASS ' if ok else 'FAIL ') + name + (' | ' + extra if extra else ''), flush=True)

def start(q):
    p = subprocess.Popen([str(EXE), '--queue', str(q)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=ENV)
    procs.append(p); return p

def log(q): 
    f = q / 'solver.log'
    return f.read_text(encoding='utf-8-sig') if f.exists() else ''

q = root / 'q'
for s in ['inbox', 'jobs', 'processing']: (q / s).mkdir(parents=True)
png = lambda h: (IMG / (h + '.png'))
# --- chuẩn bị trước khi worker chạy
shutil.copy2(png(A), q / 'inbox/aaaa000000000001.png')                      # A
(q / 'jobs/aaaa000000000001.json').write_text('{"answerLength":0}')
shutil.copy2(png(A), q / 'processing/leg0000000000001.png')                   # LEGACY
shutil.copy2(png(A), q / 'inbox/bbbb000000000006.png')                      # L6 mismatch
(q / 'jobs/bbbb000000000006.json').write_text('{"answerLength":6}')
(q / 'inbox/cccc0000000000bd.png').write_bytes(b'broken-png' * 30)           # BAD
t0 = time.monotonic()
w1 = start(q)
exp_a = base[A]['answer']
check('A: solved, outbox == expected', wait_for(lambda: (q/'outbox/aaaa000000000001.txt').exists()) and (q/'outbox/aaaa000000000001.txt').read_bytes() == exp_a.encode('ascii'), exp_a)
check('A: no BOM / no newline problems (ASCII only)', (q/'outbox/aaaa000000000001.txt').read_bytes().isalnum())
check('A: inbox PNG kept', (q/'inbox/aaaa000000000001.png').exists())
check('A: solved marker', wait_for(lambda: (q/'solved/aaaa000000000001.txt').exists()))
print('  A alt file:', (q/'outbox/aaaa000000000001.alt.txt').read_text() if (q/'outbox/aaaa000000000001.alt.txt').exists() else 'none')
check('LEGACY: processing/ recovered to inbox and solved', wait_for(lambda: (q/'outbox/leg0000000000001.txt').exists()) and not (q/'processing/leg0000000000001.png').exists())
check('L6: answerLength=6 mismatch -> failed marker, no outbox', wait_for(lambda: (q/'failed/bbbb000000000006.txt').exists()) and not (q/'outbox/bbbb000000000006.txt').exists())
check('BAD: corrupt PNG -> failed after ~10 s (not before 8 s)', wait_for(lambda: (q/'failed/cccc0000000000bd.txt').exists(), 20) and (time.monotonic() - t0) >= 8, '%.1fs' % (time.monotonic()-t0))

# P: job JSON ghi dở
h = 'dddd000000000005'
shutil.copy2(png(A), q / 'inbox' / (h + '.png'))
(q / 'jobs' / (h + '.json')).write_text('{"answerLength":')
time.sleep(0.8)
early = (q/'outbox'/(h + '.txt')).exists()
(q / 'jobs' / (h + '.json')).write_text('{"answerLength":5,"x":1}')
check('P: partial job JSON -> not answered early, answered after complete', (not early) and wait_for(lambda: (q/'outbox'/(h+'.txt')).exists()) and 'len=5' in (q/'solved'/(h+'.txt')).read_text(), 'early=%s' % early)

# H: PNG ghi dở
h = 'eeee000000000007'
data = png(A).read_bytes()
(q / 'inbox' / (h + '.png')).write_bytes(data[:len(data)//2])
time.sleep(1.0)
early = (q/'failed'/(h+'.txt')).exists() or (q/'outbox'/(h+'.txt')).exists()
(q / 'inbox' / (h + '.png')).write_bytes(data)
check('H: partial PNG -> then complete -> correct answer, no failed', (not early) and wait_for(lambda: (q/'outbox'/(h+'.txt')).exists()) and (q/'outbox'/(h+'.txt')).read_text() == exp_a and not (q/'failed'/(h+'.txt')).exists(), 'early=%s' % early)

# U: answerLength đổi sau khi đã trả lời (SIX = 6 số)
h = 'ffff000000000009'
shutil.copy2(png(SIX), q / 'inbox' / (h + '.png'))
(q / 'jobs' / (h + '.json')).write_text('{"answerLength":0}')
ok = wait_for(lambda: (q/'outbox'/(h+'.txt')).exists())
first = (q/'outbox'/(h+'.txt')).read_text() if ok else None
check('U: first answer written (len 6)', first == base[SIX]['answer'], str(first))
time.sleep(0.3)
(q / 'jobs' / (h + '.json')).write_text('{"answerLength":5}')
check('U: answerLength 6->5 -> LEN_MISMATCH logged', wait_for(lambda: 'LEN_MISMATCH ' + h in log(q)))
time.sleep(0.3)
(q / 'jobs' / (h + '.json')).write_text('{"answerLength":6,"again":true}')
check('U: answerLength 5->6 -> LEN khop logged', wait_for(lambda: re.search(r'LEN ' + h + r' answerLength=6 khop', log(q)) is not None))
check('U: outbox answer unchanged by mismatch', (q/'outbox'/(h+'.txt')).read_text() == first)

# Duplicate worker
d = start(q)
check('duplicate worker exits 0, first still alive', wait_for(lambda: d.poll() is not None) and d.returncode == 0 and w1.poll() is None)
# Independent queue
q2 = root / 'q2'; q2.mkdir()
w2 = start(q2)
check('independent queue runs concurrently', wait_for(lambda: 'SAN SANG' in log(q2)) and w2.poll() is None)
# kill -9 + restart
n_solved_before = len(re.findall(r'SOLVED aaaa000000000001 ', log(q)))
w1.kill(); w1.wait(timeout=5)
w3 = start(q)
check('kill -9 + restart reacquires mutex (2x SAN SANG)', wait_for(lambda: log(q).count('SAN SANG') >= 2) and w3.poll() is None)
time.sleep(1.5)
check('restart does not re-solve already solved A', len(re.findall(r'SOLVED aaaa000000000001 ', log(q))) == n_solved_before == 1, 'n=%d' % n_solved_before)
# no input injection
src = (W / 'src/CaptchaQueue.cs').read_text(encoding='utf-8-sig')
bad = [s for s in ['mouse_event(', 'PostMessage(', 'SendMessage(', 'BlockInput(', 'SendInput(', 'SetCursorPos(', 'keybd_event('] if s in src]
check('no input-injection APIs in source', not bad, str(bad))

# Batch: 32 ảnh qua queue, so với run_linux.json
q3 = root / 'q3'
for s in ['inbox', 'jobs']: (q3 / s).mkdir(parents=True)
for p in IMG.glob('*.png'):
    shutil.copy2(p, q3 / 'inbox' / p.name)
w4 = start(q3)
def batch_done(): 
    return len(list((q3/'solved').glob('*.txt'))) + len(list((q3/'failed').glob('*.txt'))) >= 32
wait_for(batch_done, 60)
diff = []
for h, v in base.items():
    f = q3 / 'outbox' / (h + '.txt')
    got = f.read_text() if f.exists() else None
    if got != v['answer']: diff.append((h, v['answer'], got))
check('batch 32 via queue: outbox == one-shot answers (unsolvable lengths excluded as failed)', all(g is None and len(a or '') not in (5, 6) for _, a, g in diff), str(diff))
alts = {p.name: p.read_text() for p in (q3/'outbox').glob('*.alt.txt')}
print('  batch alt files:', len(alts), 'failed:', len(list((q3/'failed').glob('*.txt'))))
mism = [h for h in alts if len(alts[h]) != len(base[h[:16]]['answer'])]
check('alt files same length as primary', not mism, str(mism))
# giữ log
shutil.copy2(q / 'solver.log', W / 'queue_test_linux_solver.log')
shutil.copy2(q3 / 'solver.log', W / 'queue_test_linux_batch_solver.log')
for p in procs:
    if p.poll() is None: p.kill()
tmp = W / 'queue_test_linux.json.tmp'
tmp.write_text(json.dumps(checks, indent=1)); os.replace(tmp, W / 'queue_test_linux.json')
print('TOTAL', sum(c['passed'] for c in checks), '/', len(checks))
