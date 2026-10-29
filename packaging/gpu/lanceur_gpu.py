"""Petit lanceur Windows pour la version locale ou GPU légère."""
import ctypes
import os
from pathlib import Path
import subprocess
import sys


def trouver_python():
    local = Path(os.environ.get('LOCALAPPDATA', '')) / 'Programs' / 'Python' / 'Python311' / 'python.exe'
    if local.is_file():
        return local
    try:
        result = subprocess.run(['py', '-3.11', '-c', 'import sys; print(sys.executable)'],
                                capture_output=True, text=True, timeout=15,
                                creationflags=subprocess.CREATE_NO_WINDOW, check=True)
    except (OSError, subprocess.SubprocessError) as exc:
        raise RuntimeError('Python 3.11 est introuvable. Vérifiez son installation et les dépendances du logiciel.') from exc
    python = Path(result.stdout.strip())
    if not python.is_file():
        raise RuntimeError('Le lanceur Python ne trouve pas Python 3.11.')
    return python


def main():
    folder = Path(sys.executable).resolve().parent if getattr(sys, 'frozen', False) else Path(__file__).resolve().parent
    gpu = Path(sys.executable).stem.lower() == 'dictee-gpu' if getattr(sys, 'frozen', False) else False
    try:
        script = folder / 'lancer-dictee.pyw'
        if not script.is_file():
            raise RuntimeError('Fichiers du logiciel introuvables. Décompressez tout le ZIP et conservez les fichiers ensemble.')
        python = trouver_python()
        diagnostic = '--diagnostic' in sys.argv or '--verifier-interface' in sys.argv
        pythonw = python.with_name('pythonw.exe')
        if not diagnostic and not pythonw.is_file():
            raise RuntimeError(f'pythonw.exe est introuvable à côté de {python}. Consultez LIRE-MOI.txt.')
        env = os.environ.copy()
        if gpu:
            env['DICTEE_GPU_LIGHT'] = '1'
        else:
            env.pop('DICTEE_GPU_LIGHT', None)
        command = [str(python if diagnostic else pythonw), str(script), *sys.argv[1:]]
        if diagnostic:
            return subprocess.run(command, cwd=folder, env=env, creationflags=subprocess.CREATE_NO_WINDOW).returncode
        subprocess.Popen(command, cwd=folder, env=env, creationflags=subprocess.CREATE_NO_WINDOW)
        return 0
    except Exception as exc:
        ctypes.windll.user32.MessageBoxW(None, str(exc), 'Dictée LinTO', 0x10)
        return 1


if __name__ == '__main__':
    sys.exit(main())
