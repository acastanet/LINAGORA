"""Chemins stables pour le lancement Python et le dossier Windows portable."""
from pathlib import Path
import sys

PORTABLE = bool(getattr(sys, 'frozen', False))
ROOT = Path(sys.executable).resolve().parent if PORTABLE else Path(__file__).resolve().parent
RESOURCES = Path(__file__).resolve().parent
MODEL_DIR = ROOT / 'modele'
DATA_DIR = ROOT / 'donnees'


def data_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return DATA_DIR
