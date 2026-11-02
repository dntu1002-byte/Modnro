from pathlib import Path
import hashlib, json, shutil, subprocess
root = Path(r'C:\Users\Tuchuai\Downloads\AutoCaptcha-Handoff-Recreated-20261102')
archive = Path(r'C:\Users\Tuchuai\Downloads\Mod-250-PC.rar')
seven = r'C:\Program Files\7-Zip\7z.exe'
listing = subprocess.check_output([seven, 'l', '-slt', '-sccUTF-8', str(archive)], text=True, encoding='utf-8')
entries = [line[7:] for line in listing.splitlines() if line.startswith('Path = ')]
groups = {
    'work/img': [p for p in entries if '/tudzday-captcha/inbox/' in p.replace('\\','/') and p.endswith('.png')],
    'work/jobs': [p for p in entries if '/tudzday-captcha/jobs/' in p.replace('\\','/') and p.endswith('.json')],
    'inputs/plugin': [p for p in entries if p.replace('\\','/').endswith('/BepInEx/plugins/NroPort.Plugin.dll')],
}
for dest, paths in groups.items():
    if not paths and dest != 'work/jobs':
        raise RuntimeError('Missing archive input: '+dest)
    if paths:
        subprocess.run([seven,'e','-y','-sccUTF-8','-o'+str(root/dest),str(archive),*paths], check=True, capture_output=True)
    print(dest, len(paths))
mod = Path(r'C:\Users\Tuchuai\Desktop\Mod-250-PC')
for name in ['CaptchaQueue.cs','AutoCaptcha.exe']:
    shutil.copy2(mod/name,root/'work/src'/name)
review = mod/'captcha-update-review'
for name in ['QueueHarness.cs','QueueHarness.exe','build-proof.txt','queue-test-results.json']:
    shutil.copy2(review/name,root/'work/src'/name)
tests = (review/'test_queue.py').read_text(encoding='utf-8-sig')
a = tests.index('fixture = ')
b = tests.index('expected = ',a)
tests = tests[:a] + "fixture = stage.parent / 'img/064937887D4981B0.png'\n" + tests[b:]
(root/'work/src/test_queue.py').write_text(tests,encoding='utf-8')
for name in ['pasted-text.txt','captchaqueue (1).cs','solve_legend (8).py','huong_dan_auto_captcha_toan_tap (5).md']:
    shutil.copy2(Path(r'C:\Users\Tuchuai\Downloads')/name,root/'inputs/original'/name)
manifest = {'kind':'recreated-handoff-not-original-Opus-workspace','archive':str(archive),'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'images':[]}
for p in sorted((root/'work/img').glob('*.png')):
    sha = hashlib.sha256(p.read_bytes()).hexdigest().upper()
    if p.stem != sha[:16]:
        raise RuntimeError('Image hash name mismatch: '+p.name)
    manifest['images'].append({'file':p.name,'sha256':sha})
(root/'PROVENANCE.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Verified original image SHA-256 prefixes:',len(manifest['images']))
