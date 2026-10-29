"""Construit une archive GPU sans Python ni bibliothèques embarqués."""
import argparse
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

from construire_portable import MODEL_FILES, ROOT


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model-source', type=Path, default=ROOT / 'modele')
    args = parser.parse_args()
    for name in MODEL_FILES:
        if not (args.model_source / name).is_file():
            raise SystemExit(f'Fichier modèle manquant : {name}')
    work = ROOT / 'build' / 'lanceur-gpu'
    work.mkdir(parents=True, exist_ok=True)
    subprocess.run([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--onefile', '--windowed',
                    '--name', 'Dictee-GPU', '--icon', str(ROOT / 'bouche-en-coeur.ico'),
                    '--distpath', str(work / 'dist'), '--workpath', str(work / 'work'),
                    '--specpath', str(work), str(ROOT / 'packaging' / 'gpu' / 'lanceur_gpu.py')],
                   cwd=ROOT, check=True)
    shutil.copy2(work / 'dist' / 'Dictee-GPU.exe', ROOT / 'Dictee-LinTO.exe')
    folder = ROOT / 'dist' / 'Dictee-LinTO-GPU-Light'
    folder.mkdir(parents=True, exist_ok=True)
    shutil.copy2(work / 'dist' / 'Dictee-GPU.exe', folder / 'Dictee-GPU.exe')
    old_launcher = folder / 'Lancer-Dictee-GPU.vbs'
    if old_launcher.is_file():
        old_launcher.unlink()
    for name in ('chemins.py', 'dictee.py', 'dictee_windows.py', 'affichage_bouton.py',
                 'moteur_dictee.py', 'son_dictee.py', 'diagnostic_portable.py',
                 'lancer-dictee.pyw', 'bouche-en-coeur.ico'):
        shutil.copy2(ROOT / name, folder / name)
    for name in ('Diagnostic-GPU.bat', 'LIRE-MOI.txt'):
        shutil.copy2(ROOT / 'packaging' / 'gpu' / name, folder / name)
    for theme in ('clair', 'sombre'):
        target = folder / 'bouton' / theme
        target.mkdir(parents=True, exist_ok=True)
        for state in ('loading', 'ready', 'recording', 'busy', 'recover', 'error'):
            shutil.copy2(ROOT / 'bouton' / theme / f'{state}.png', target / f'{state}.png')
    (folder / 'sons').mkdir(exist_ok=True)
    shutil.copy2(ROOT / 'sons' / 'do-doux.wav', folder / 'sons' / 'do-doux.wav')
    shutil.copytree(args.model_source, folder / 'modele', dirs_exist_ok=True)
    (folder / 'donnees').mkdir(exist_ok=True)
    release = ROOT / 'release'
    release.mkdir(exist_ok=True)
    archive = release / 'Dictee-LinTO-Windows-x64-GPU-light.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for path in sorted(folder.rglob('*')):
            relative = path.relative_to(folder)
            if path.is_file() and relative.parts[0] != 'donnees' and '__pycache__' not in relative.parts:
                z.write(path, Path(folder.name) / relative)
        z.writestr(f'{folder.name}/donnees/', '')
    with archive.open('rb') as f:
        digest = hashlib.file_digest(f, 'sha256').hexdigest()
    archive.with_suffix('.zip.sha256').write_text(f'{digest}  {archive.name}\n', encoding='ascii')
    print(f'ZIP : {archive}\nOctets : {archive.stat().st_size}\nSHA256 : {digest}', flush=True)


if __name__ == '__main__':
    main()
