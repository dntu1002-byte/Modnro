import datetime
import json
from pathlib import Path
import subprocess

src = Path(__file__).resolve().parent
work = src.parent
stamp = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=7))).isoformat()
rows = []
for image in sorted((work / 'img').glob('*.png')):
    result = subprocess.run([str(src / 'AutoCaptcha.exe'), str(image)], capture_output=True, text=True, timeout=30)
    parsed = None
    error = result.stderr
    try:
        parsed = json.loads(result.stdout)
    except (ValueError, TypeError) as exc:
        error += str(exc)
    answer = parsed.get('answer') if parsed else None
    valid = bool(answer) and len(answer) in (5, 6) and all(c in '13579' for c in answer)
    rows.append(dict(file=image.name, exit_code=result.returncode, parsed=parsed, format_valid=valid, error=error))
    print(image.name, '->', answer, 'exit=', result.returncode, flush=True)
report = {
    'origin': 'NEW WINDOWS RUN; NOT THE LOST OPUS run3v.txt',
    'time_asia_saigon': stamp,
    'ground_truth': None,
    'accuracy': 'NOT MEASURED: no trusted symbol-based labels supplied',
    'images': len(rows),
    'processes_ok': sum(row['exit_code'] == 0 and row['parsed'] is not None for row in rows),
    'format_valid': sum(row['format_valid'] for row in rows),
    'results': rows,
}
(work / 'run3v.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
lines = [report['origin'], stamp, report['accuracy']]
for row in rows:
    parsed = row['parsed'] or {}
    lines.append(f"{row['file']} -> {parsed.get('answer')} | exit={row['exit_code']} | {parsed.get('details', row['error'])}")
lines.append(f"Images={len(rows)}; processes_ok={report['processes_ok']}; format_valid={report['format_valid']}; accuracy=unknown")
(work / 'run3v.txt').write_text('\n'.join(lines) + '\n', encoding='utf-8')
print(lines[-1])
if not rows or report['processes_ok'] != len(rows):
    raise SystemExit(1)
