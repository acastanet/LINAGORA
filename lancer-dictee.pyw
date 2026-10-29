"""Point d'entrée Windows, aussi utilisé pour l'exécutable portable."""
import ctypes
import logging
from logging.handlers import RotatingFileHandler
import sys
from chemins import data_dir

folder = None
try:
    folder = data_dir()
    handler = RotatingFileHandler(folder / 'dictee.log', maxBytes=1_000_000,
                                  backupCount=1, encoding='utf-8')
    logging.basicConfig(level=logging.WARNING, handlers=[handler],
                        format='%(asctime)s %(levelname)s %(message)s')
    # pythonw fournit des flux None ; certaines bibliothèques écrivent dessus.
    with open(folder / 'dictee-console.log', 'w', encoding='utf-8') as output:
        sys.stdout = sys.stderr = output
        if '--diagnostic' in sys.argv or '--verifier-interface' in sys.argv:
            from diagnostic_portable import main
            main()
        else:
            from dictee_windows import run
            run(preview='--preview' in sys.argv)
except Exception:
    logging.exception('Démarrage de la dictée')
    if '--diagnostic' not in sys.argv and '--verifier-interface' not in sys.argv:
        ctypes.windll.user32.MessageBoxW(None,
            f'La dictée ne peut pas démarrer. Vérifiez que le dossier est accessible en écriture.\nDiagnostics : {folder}',
            'Dictée LinTO', 0x10)
    sys.exit(1)
