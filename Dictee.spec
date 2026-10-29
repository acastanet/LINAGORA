# -*- mode: python ; coding: utf-8 -*-
from pathlib import Path
root = Path(SPECPATH)
a = Analysis(
    [str(root / 'lancer-dictee.pyw')],
    pathex=[str(root)],
    binaries=[],
    datas=[(str(root / 'bouche-en-coeur.ico'), '.'), (str(root / 'sons' / 'do-doux.wav'), 'sons'),
           (str(root / 'bouton' / 'clair' / '*.png'), 'bouton/clair'),
           (str(root / 'bouton' / 'sombre' / '*.png'), 'bouton/sombre')],
    hiddenimports=['_sounddevice_data', 'soundfile', 'scipy.signal'],
    hookspath=[str(root / 'packaging' / 'hooks')],
    excludes=['gradio', 'matplotlib', 'pandas', 'tensorflow', 'keras', 'torchvision',
              'torchaudio', 'torchcodec', 'triton', 'IPython', 'tensorboard'],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Dictee',
          debug=False, bootloader_ignore_signals=False, strip=False,
          upx=False, console=False, icon=str(root / 'bouche-en-coeur.ico'))
coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='Dictee-LinTO-CPU')
