"""Construit le dossier puis le ZIP Windows portable, avec le modèle local."""
import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
MODEL_FILES = ('config.json','generation_config.json','model.safetensors',
               'processor_config.json','tokenizer.json','tokenizer_config.json')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-source', type=Path, default=ROOT/'modele')
    args = parser.parse_args()
    import torch
    if torch.version.cuda is not None:
        raise SystemExit('Utilisez un environnement PyTorch CPU pour construire ce paquet.')
    for name in MODEL_FILES:
        if not (args.model_source/name).is_file():
            raise SystemExit(f'Fichier modèle manquant : {name}')
    for output in (ROOT/'dist', ROOT/'build'):
        if not output.resolve().is_relative_to(ROOT):
            raise SystemExit(f'Dossier de construction hors du projet : {output}')
    env = dict(os.environ, HF_HOME=str(ROOT/'build'/'huggingface'), HF_HUB_OFFLINE='1',
               HF_HUB_DISABLE_TELEMETRY='1', NUMBA_CACHE_DIR=str(ROOT/'build'/'numba'))
    subprocess.run([sys.executable,'-m','PyInstaller','--noconfirm',str(ROOT/'Dictee.spec')],
                   cwd=ROOT, env=env, check=True)
    folder = ROOT/'dist'/'Dictee-LinTO-CPU'
    shutil.copytree(args.model_source, folder/'modele', dirs_exist_ok=True)
    (folder/'donnees').mkdir(exist_ok=True)
    shutil.copy2(ROOT/'packaging'/'LIRE-MOI.txt', folder/'LIRE-MOI.txt')
    shutil.copy2(ROOT/'dictee.svg', folder/'dictee.svg')
    licenses = folder/'licences'
    licenses.mkdir(exist_ok=True)
    versions = {}
    for dist in metadata.distributions():
        name = dist.metadata['Name']
        versions[name] = dist.version
        for f in dist.files or []:
            if (Path(f).name.upper().startswith(('LICENSE','LICENCE','COPYING','NOTICE'))
                or 'licenses' in str(f).lower().split('/')):
                source = Path(dist.locate_file(f))
                if source.is_file():
                    destination = licenses/name/str(f).replace('../','').replace('..\\','')
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source,destination)
    python_license = Path(sys.base_prefix)/'LICENSE.txt'
    if python_license.is_file():
        shutil.copy2(python_license, licenses/'PYTHON-LICENSE.txt')
    lock = ROOT/'requirements-portable.lock.txt'
    lock.write_text('\n'.join(f'{k}=={v}' for k,v in sorted(versions.items()))+'\n',encoding='utf-8')
    manifest = {'platform':'Windows x64','python':sys.version.split()[0], 'device':'cpu',
                'model':'linagora/linto_stt_fr_fastconformer_pc',
                'model_revision':'b37566382e88e99f8625450081c3420d4e1a0c4b',
                'packages':versions,
                'model_sha256': hashlib.file_digest(open(folder/'modele'/'model.safetensors','rb'),'sha256').hexdigest()}
    (folder/'VERSION.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
    # Les journaux et diagnostics de validation ne font pas partie du ZIP.
    release=ROOT/'release'
    release.mkdir(exist_ok=True)
    archive=release/'Dictee-LinTO-Windows-x64-CPU-portable.zip'
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
        for p in sorted(folder.rglob('*')):
            relative=p.relative_to(folder)
            if p.is_file() and relative.parts[0]!='donnees':
                z.write(p,Path('Dictee-LinTO-CPU')/relative)
        z.writestr('Dictee-LinTO-CPU/donnees/','')
    digest=hashlib.file_digest(open(archive,'rb'),'sha256').hexdigest()
    archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n',encoding='ascii')
    print(f'ZIP : {archive}\nOctets : {archive.stat().st_size}\nSHA256 : {digest}',flush=True)


if __name__=='__main__':
    main()
