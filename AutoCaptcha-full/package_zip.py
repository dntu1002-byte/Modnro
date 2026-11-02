from pathlib import Path
import hashlib, json, zipfile
root = Path(r'C:\Users\Tuchuai\Downloads\AutoCaptcha-Handoff-Recreated-20261102')
archive = root.with_suffix('.zip')
if archive.exists():
    raise RuntimeError('ZIP already exists; refusing to overwrite')
provenance = json.loads((root/'PROVENANCE.json').read_text())
assert hashlib.sha256(Path(provenance['archive']).read_bytes()).hexdigest() == provenance['archive_sha256'], 'Original RAR changed'
for p in (root/'inputs/original').iterdir():
    original = Path(r'C:\Users\Tuchuai\Downloads')/p.name
    assert hashlib.sha256(p.read_bytes()).digest() == hashlib.sha256(original.read_bytes()).digest(), p.name
files = sorted(p for p in root.rglob('*') if p.is_file())
manifest = {str(p.relative_to(root)).replace('\\','/'): {'size': p.stat().st_size, 'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}
(root/'MANIFEST.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
files.append(root/'MANIFEST.json')
with zipfile.ZipFile(archive,'x',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for p in files:
        z.write(p,p.relative_to(root))
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None, 'ZIP CRC error'
    for name, item in manifest.items():
        assert hashlib.sha256(z.read(name)).hexdigest() == item['sha256'], name
    print('ZIP members:',len(z.namelist()))
checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
archive.with_suffix('.zip.sha256.txt').write_text(checksum+'  '+archive.name+'\n',encoding='ascii')
print('Original RAR and four supplied files: SHA256 unchanged')
print('ZIP integrity: all CRC and member SHA256 verified')
print('ZIP:', archive)
print('SIZE:',archive.stat().st_size)
print('SHA256:',checksum)
