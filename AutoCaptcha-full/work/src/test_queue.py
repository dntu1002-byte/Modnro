import json
import pathlib
import shutil
import subprocess
import time
import uuid

stage = pathlib.Path(__file__).parent
root = stage / ('test-' + uuid.uuid4().hex[:8])
fixture = stage.parent / 'img/064937887D4981B0.png'
expected = json.loads(subprocess.check_output([str(stage / 'AutoCaptcha.exe'), str(fixture)], text=True))['answer']
workers = []
checks = []

def wait_for(predicate, timeout=12):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return True
        time.sleep(0.05)
    return False

def check(name, passed):
    checks.append({'name': name, 'passed': bool(passed)})
    print(('PASS ' if passed else 'FAIL ') + name, flush=True)
    assert passed, name

def start(queue):
    p = subprocess.Popen([str(stage / 'QueueHarness.exe'), str(queue)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    workers.append(p)
    return p

q = root / 'queue'
for sub in ['inbox', 'jobs', 'processing']:
    (q / sub).mkdir(parents=True, exist_ok=True)
for name in ['first', 'second']:
    shutil.copy2(fixture, q / 'inbox' / (name + '.png'))
shutil.copy2(fixture, q / 'processing/recover.png')
(q / 'inbox/corrupt.png').write_bytes(b'broken-png' * 30)
shutil.copy2(fixture, q / 'inbox/mismatch.png')
(q / 'jobs/mismatch.json').write_text('{"answerLength":6}')
try:
    worker = start(q)
    check('all pending jobs processed with no game windows', wait_for(lambda: all((q / 'outbox' / (n + '.txt')).exists() for n in ['first', 'second', 'recover'])))
    check('answer bytes contain no UTF-8 BOM', (q / 'outbox/first.txt').read_bytes() == expected.encode('ascii'))
    check('corrupt PNG isolated and retained', wait_for(lambda: (q / 'failed/corrupt.png').exists()))
    check('wrong answer length blocked', wait_for(lambda: (q / 'failed/mismatch.png').exists()) and not (q / 'outbox/mismatch.txt').exists())
    check('successful input archived', all((q / 'solved' / (n + '.png')).exists() for n in ['first', 'second', 'recover']))
    duplicate = start(q)
    check('second worker exits without killing first', wait_for(lambda: duplicate.poll() is not None) and duplicate.returncode == 0 and worker.poll() is None)
    other_q = root / 'independent'
    other = start(other_q)
    check('independent Mod queue can run concurrently', wait_for(lambda: (other_q / 'solver.log').exists()) and other.poll() is None)
    worker.terminate()
    worker.wait(timeout=5)
    restarted = start(q)
    check('worker recovers abandoned mutex after forced exit', wait_for(lambda: (q / 'solver.log').read_text(encoding='utf-8-sig').count('SAN SANG') >= 2) and restarted.poll() is None)
    check('no mouse injection API in installed source', all(s not in (stage / 'CaptchaQueue.cs').read_text(encoding='utf-8-sig') for s in ['mouse_event(', 'PostMessage(', 'BlockInput(']))
finally:
    for p in workers:
        if p.poll() is None:
            p.terminate()
            p.wait(timeout=5)
    (stage / 'queue-test-results.json').write_text(json.dumps(checks, indent=2))
print('TOTAL PASS', len(checks))
