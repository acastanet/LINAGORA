"""Dictée LinTO locale : Ctrl+Alt+Espace démarre et arrête le micro."""

import ctypes
from ctypes import wintypes
import threading
import time
import warnings
import winsound

import numpy as np
import sounddevice as sd

from app import SAMPLE_RATE, get_asr


user32 = ctypes.WinDLL("user32", use_last_error=True)
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
user32.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
user32.GetMessageW.restype = ctypes.c_int


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.c_size_t)]


class HARDWAREINPUT(ctypes.Structure):
    _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]


class INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT), ("hi", HARDWAREINPUT)]


class INPUT(ctypes.Structure):
    _anonymous_ = ("data",)
    _fields_ = [("type", wintypes.DWORD), ("data", INPUT_UNION)]


user32.SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
user32.SendInput.restype = wintypes.UINT


def insert_text(text, window=None):
    # KEYEVENTF_UNICODE attend des unités UTF-16, y compris les paires de substitution.
    encoded = text.encode("utf-16-le")
    for i in range(0, len(encoded), 2):
        if window and user32.GetForegroundWindow() != window:
            raise RuntimeError("La fenêtre a changé pendant l'insertion")
        unit = int.from_bytes(encoded[i:i + 2], "little")
        inputs = (INPUT * 2)(
            INPUT(type=1, ki=KEYBDINPUT(0, unit, 0x0004, 0, 0)),
            INPUT(type=1, ki=KEYBDINPUT(0, unit, 0x0004 | 0x0002, 0, 0)),
        )
        if user32.SendInput(2, inputs, ctypes.sizeof(INPUT)) != 2:
            raise OSError("SendInput n'a pas pu insérer tout le texte")
        time.sleep(0.05)  # Laisser l'application traiter chaque caractère.


def main():
    print("Chargement du modèle LinTO...", flush=True)
    asr = get_asr()
    # MOD_NOREPEAT évite les bascules répétées lorsque la touche reste enfoncée.
    if not user32.RegisterHotKey(None, 1, 0x0002 | 0x0001 | 0x4000, 0x20):
        raise ctypes.WinError(ctypes.get_last_error())
    print("Prêt : Ctrl+Alt+Espace pour démarrer/arrêter. Ctrl+C pour quitter.", flush=True)
    chunks = []
    stream = None
    target = None
    busy = threading.Event()

    def transcribe(audio, window):
        try:
            print("Transcription...", flush=True)
            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", message=r"Using the model-agnostic default `max_length`.*", category=UserWarning)
                text = asr({"array": audio, "sampling_rate": SAMPLE_RATE})["text"].strip()
            print(f"Transcription : {text}", flush=True)
            # Éviter que Ctrl ou Alt encore maintenu transforme le texte en raccourcis.
            while any(user32.GetAsyncKeyState(key) & 0x8000 for key in (0x11, 0x12, 0x20)):
                time.sleep(0.05)
            if text and user32.GetForegroundWindow() == window:
                insert_text(text, window)
                print("Texte inséré.", flush=True)
            elif text:
                print("Fenêtre changée : texte non inséré, disponible ci-dessus.", flush=True)
            winsound.Beep(900, 120)
        except Exception as exc:
            print(f"Erreur de transcription ou d'insertion : {exc}", flush=True)
        finally:
            busy.clear()

    try:
        msg = wintypes.MSG()
        while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            if msg.message != 0x0312 or msg.wParam != 1:
                continue
            if busy.is_set():
                print("Transcription en cours ; raccourci ignoré.", flush=True)
            elif stream is None:
                try:
                    target = user32.GetForegroundWindow()
                    chunks.clear()
                    winsound.Beep(1100, 120)
                    stream = sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="float32",
                                            callback=lambda data, frames, timing, status: chunks.append(data.copy()))
                    stream.start()
                    print("Enregistrement...", flush=True)
                except Exception as exc:
                    if stream is not None:
                        stream.close()
                    stream = None
                    print(f"Erreur microphone : {exc}", flush=True)
            else:
                stream.stop()
                stream.close()
                stream = None
                winsound.Beep(600, 120)
                if chunks:
                    busy.set()
                    threading.Thread(target=transcribe, args=(np.concatenate(chunks).ravel(), target), daemon=True).start()
                else:
                    print("Aucun son enregistré.", flush=True)
    finally:
        if stream is not None:
            stream.close()
        user32.UnregisterHotKey(None, 1)


if __name__ == "__main__":
    main()
