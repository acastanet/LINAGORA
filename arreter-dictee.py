"""Arrête les processus Python qui exécutent ce projet de dictée."""

from pathlib import Path
import os

import psutil

script = Path(__file__).with_name("dictee.py").resolve()
current_pid = os.getpid()
for process in psutil.process_iter(["pid", "name", "cmdline"]):
    try:
        if process.pid == current_pid or process.info["name"].lower() not in ("python.exe", "pythonw.exe"):
            continue
        args = process.info["cmdline"] or []
        for arg in args[1:]:
            if not arg.lower().endswith("dictee.py"):
                continue
            path = Path(arg)
            if not path.is_absolute():
                path = Path(process.cwd()) / path
            if path.resolve() == script:
                print(f"Arrêt de l'ancienne dictée (PID {process.pid})...")
                process.terminate()
                process.wait(timeout=10)
                break
    except (psutil.NoSuchProcess, psutil.ZombieProcess):
        pass
