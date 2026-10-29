"""Vérifie le ZIP décompressé ailleurs, avec un environnement indépendant de Python."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import zipfile

ROOT=Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description='Vérifie le ZIP CPU sur un fichier audio local.')
parser.add_argument('--audio', type=Path, required=True, help='Fichier audio de référence à transcrire')
audio = parser.parse_args().audio.resolve()
if not audio.is_file():
    parser.error(f'Fichier audio introuvable : {audio}')
archive=ROOT/'release'/'Dictee-LinTO-Windows-x64-CPU-portable.zip'
workspace=Path(tempfile.mkdtemp(prefix='essai portable é ',dir=ROOT/'build'))
with zipfile.ZipFile(archive) as z:
    for member in z.infolist():
        if not (workspace/member.filename).resolve().is_relative_to(workspace):
            raise RuntimeError('Chemin hors du dossier de vérification')
    z.extractall(workspace)
folder=workspace/'Dictee-LinTO-CPU'
env=dict(os.environ)
for name in ('PYTHONHOME','PYTHONPATH','VIRTUAL_ENV','NUMBA_CACHE_DIR','TORCH_HOME','HF_HOME','HF_HUB_CACHE'):
    env.pop(name,None)
env['PATH']=str(Path(env['WINDIR'])/'System32')
env['HF_HOME']=str(workspace/'cache-vide')
env['HF_HUB_CACHE']=str(workspace/'cache-vide'/'hub')
env['HF_HUB_OFFLINE']='1'
checks={}
for name,args in [('interface',['--verifier-interface']),('transcription',['--diagnostic','--audio',str(audio)])]:
    print('Vérification :',name,flush=True)
    result=subprocess.run([str(folder/'Dictee.exe'),*args],cwd=workspace,env=env,timeout=180)
    report=folder/'donnees'/('diagnostic-interface.json' if name=='interface' else 'diagnostic.json')
    if not report.is_file():
        raise RuntimeError(f'{name} : aucun rapport ; voir {folder}/donnees')
    data=json.loads(report.read_text(encoding='utf-8'))
    print(json.dumps(data,ensure_ascii=False),flush=True)
    if result.returncode or not data.get('ok'):
        raise RuntimeError(f'{name} : échec {result.returncode}, {data}')
    checks[name]=data
if checks['interface']['size'] != [56,56]:
    raise RuntimeError('Taille du bouton inattendue')
if not checks['interface'].get('layered'):
    raise RuntimeError('Le bouton doit s\'afficher en transparence par pixel')
sound=checks['interface'].get('sound',{})
if (sound.get('rate'),sound.get('bits'),sound.get('channels'))!=(48000,24,2):
    raise RuntimeError('La notification doit être en stéréo 48 kHz / 24 bits')
if checks['transcription']['device']!='cpu' or checks['transcription']['torch']!='2.7.1+cpu':
    raise RuntimeError('La version portable doit utiliser PyTorch CPU')
if not checks['transcription'].get('text','').strip():
    raise RuntimeError('La transcription du fichier de référence est vide')
checks['archive_sha256']=hashlib.file_digest(open(archive,'rb'),'sha256').hexdigest()
checks['archive_bytes']=archive.stat().st_size
checks['unpacked_bytes']=sum(p.stat().st_size for p in folder.rglob('*') if p.is_file())
checks['method']='ZIP déplacé dans un chemin avec espaces et accent ; PATH limité à System32 ; cache Hub vide ; connexions réseau bloquées par le diagnostic.'
(ROOT/'release'/'verification-portable.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2),encoding='utf-8')
print('VALIDATION_PORTABLE_OK',flush=True)
