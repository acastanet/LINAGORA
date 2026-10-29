"""Insertion Unicode ciblée et point d'entrée de la dictée Windows."""

import ctypes
from ctypes import wintypes
import time

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


def insert_text(text, window=None, cancelled=None):
    # KEYEVENTF_UNICODE attend des unités UTF-16, y compris les paires de substitution.
    encoded = text.encode("utf-16-le")
    for i in range(0, len(encoded), 2):
        if cancelled is not None and cancelled.is_set():
            return
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
    from dictee_windows import run
    run()


if __name__ == "__main__":
    main()
