"""Contrôles explicites du paquet portable, sans enregistrer le microphone."""
import argparse
import json
import os
from pathlib import Path
import socket
import time
from chemins import ROOT, MODEL_DIR, data_dir, PORTABLE


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--diagnostic', action='store_true')
    parser.add_argument('--verifier-interface', action='store_true')
    parser.add_argument('--tester-son', action='store_true')
    parser.add_argument('--audio', type=Path)
    args = parser.parse_args()
    report = {'portable': PORTABLE, 'root': str(ROOT), 'modele': str(MODEL_DIR)}
    destination = data_dir() / ('diagnostic-interface.json' if args.verifier_interface else 'diagnostic.json')
    try:
        if args.verifier_interface:
            import wave
            from son_dictee import SOUND
            with wave.open(str(SOUND), 'rb') as wav:
                report['sound'] = {'rate': wav.getframerate(), 'bits': wav.getsampwidth()*8,
                                   'channels': wav.getnchannels(),
                                   'seconds': wav.getnframes()/wav.getframerate()}
            if args.tester_son:
                import winsound
                winsound.PlaySound(str(SOUND), winsound.SND_FILENAME | winsound.SND_NODEFAULT)
            from dictee_windows import DictationApp, get_long
            app = DictationApp(preview=True)
            app.root.update()
            report.update(size=[app.root.winfo_width(), app.root.winfo_height()],
                          noactivate=bool(get_long(app.hwnd, -20) & 0x08000000),
                          icon=bool(app.icon), tray=app.tray_added, layered=bool(app.layered))
            if not report['noactivate'] or not report['icon'] or not report['layered']:
                app.close()
                raise RuntimeError('Le bouton ne préserve pas le focus, son icône est absente '
                                   'ou son image ne s\'affiche pas')
            app.root.after(1200, app.close)
            app.root.mainloop()
        else:
            # La validation échoue sur tout accès réseau, y compris hors du Hub.
            def refuse_network(*a, **kw):
                raise RuntimeError('Réseau interdit pendant le diagnostic hors ligne')
            socket.socket.connect = refuse_network
            socket.create_connection = refuse_network
            os.environ['HF_HUB_OFFLINE'] = '1'
            start = time.perf_counter()
            from moteur_dictee import get_asr, SAMPLE_RATE
            asr = get_asr()
            import torch
            import sounddevice
            report.update(torch=torch.__version__, device=str(asr.device),
                          audio_library=sounddevice.__version__,
                          loading_seconds=round(time.perf_counter()-start, 2))
            if args.audio:
                import soundfile as sf
                import numpy as np
                audio, rate = sf.read(args.audio, dtype='float32')
                if audio.ndim > 1:
                    audio = audio.mean(axis=1)
                if rate != SAMPLE_RATE:
                    from scipy.signal import resample_poly
                    from math import gcd
                    divisor = gcd(rate, SAMPLE_RATE)
                    audio = resample_poly(audio, SAMPLE_RATE//divisor, rate//divisor)
                start = time.perf_counter()
                report['text'] = asr({'array': np.asarray(audio), 'sampling_rate': SAMPLE_RATE})['text']
                report['audio_seconds'] = round(len(audio)/SAMPLE_RATE, 2)
                report['transcription_seconds'] = round(time.perf_counter()-start, 2)
        report['ok'] = True
    except Exception as exc:
        report['ok'] = False
        report['error'] = repr(exc)
        raise
    finally:
        destination.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
