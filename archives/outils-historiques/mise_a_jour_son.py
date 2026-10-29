"""Prépare et contrôle la mise à jour du son depuis la version portable précédente."""
from pathlib import Path
import json
import hashlib
import zlib
import zipfile

ROOT=Path(__file__).resolve().parents[1]
release=ROOT/'release'
baseline=json.loads((ROOT/'build/baseline-son.json').read_text(encoding='utf-8'))
previous=json.loads((release/'verification-portable.json').read_text(encoding='utf-8'))
old_folder=Path(previous['interface']['root']).resolve()
if not old_folder.is_relative_to((ROOT/'build').resolve()):
    raise RuntimeError('Le test doit porter sur une copie dans build')

def crc(path):
    checksum=0
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):
            checksum=zlib.crc32(block,checksum)
    return checksum & 0xffffffff

prefix='Dictee-LinTO/'
for name,meta in baseline.items():
    p=old_folder/name[len(prefix):]
    if not p.is_file() or crc(p)!=meta['crc']:
        raise RuntimeError(f'La copie précédente a changé : {name}')

patch=release/'Mise-a-jour-do-doux.zip'
with zipfile.ZipFile(release/'Dictee-LinTO-Windows-x64-portable.zip') as source:
    changed=[i for i in source.infolist() if not i.is_dir()
             and baseline.get(i.filename)!={'crc':i.CRC,'size':i.file_size}]
    with zipfile.ZipFile(patch,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as target:
        for info in changed:
            relative=info.filename[len(prefix):]
            if not (old_folder/relative).resolve().is_relative_to(old_folder):
                raise RuntimeError('Chemin de mise à jour incorrect')
            contents=source.read(info.filename)
            target.writestr(relative,contents)
            destination=old_folder/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            destination.write_bytes(contents)
        target.writestr('MISE-A-JOUR-SON.txt',
            'MISE A JOUR DU SON - DO DOUX\n\n'
            'Pour la version portable fournie précédemment.\n'
            '1. Quittez la dictée par clic droit sur le bouton.\n'
            '2. Décompressez ce ZIP dans le dossier contenant Dictee.exe,\n'
            '   en acceptant de remplacer les fichiers.\n'
            '3. Relancez Dictee.exe.\n\n'
            'Le modèle et les bibliothèques restent en place.\n'
            'Son : do central doux, 48 kHz / 24 bits stéréo, 280 ms.\n')
    for info in source.infolist():
        if not info.is_dir() and crc(old_folder/info.filename[len(prefix):])!=info.CRC:
            raise RuntimeError(f'Mise à jour incomplète : {info.filename}')
sha=hashlib.file_digest(open(patch,'rb'),'sha256').hexdigest()
patch.with_suffix('.zip.sha256').write_text(f'{sha}  {patch.name}\n',encoding='ascii')
(release/'verification-mise-a-jour-son.json').write_text(json.dumps({
    'ok':True,'base_archive_sha256':previous['archive_sha256'],
    'patch_bytes':patch.stat().st_size,'patch_sha256':sha,
    'changed_files':[i.filename[len(prefix):] for i in changed],
    'verification':'La copie précédente après application correspond à tous les fichiers du nouveau ZIP.'
},ensure_ascii=False,indent=2),encoding='utf-8')
print('MISE_A_JOUR_VALIDEE',patch.stat().st_size,'octets ;',len(changed),'fichiers')
