"""Moteur partagé, indépendant de l'interface web Gradio."""
from functools import lru_cache
import os

from chemins import PORTABLE, MODEL_DIR, data_dir

MODEL = 'linagora/linto_stt_fr_fastconformer_pc'
SAMPLE_RATE = 16_000


@lru_cache(maxsize=1)
def get_asr():
    local = (MODEL_DIR / 'model.safetensors').is_file()
    gpu_light = not PORTABLE and os.environ.get('DICTEE_GPU_LIGHT') == '1'
    if (PORTABLE or gpu_light) and not local:
        raise FileNotFoundError('Le dossier modele doit accompagner le logiciel. Décompressez le ZIP entier.')
    if local:
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
        os.environ['HF_HOME'] = str(data_dir() / 'cache')
        os.environ['TORCH_HOME'] = str(data_dir() / 'cache' / 'torch')
        os.environ['NUMBA_CACHE_DIR'] = str(data_dir() / 'cache' / 'numba')
    # Configurer les variables avant d'importer Hugging Face.
    import torch
    from transformers import pipeline
    if gpu_light and not torch.cuda.is_available():
        raise RuntimeError('CUDA indisponible : la version GPU nécessite une carte NVIDIA, son pilote et '
                           'un PyTorch compatible CUDA dans le Python utilisé. Voir LIRE-MOI.txt.')
    device = 0 if gpu_light else -1 if PORTABLE else (0 if torch.cuda.is_available() else -1)
    if PORTABLE:
        torch.set_num_threads(min(4, os.cpu_count() or 1))
    return pipeline('automatic-speech-recognition',
                    model=str(MODEL_DIR) if local else MODEL, device=device)
