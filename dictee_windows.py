"""Bouton de dictée Windows sans prise de focus (Tk + API Windows)."""
import ctypes as C
from ctypes import wintypes as W
import logging
from pathlib import Path
import queue
import threading
import time
import tkinter as tk
from tkinter import messagebox
import warnings
import winreg

from affichage_bouton import LayeredSurface, load_frames, WS_EX_LAYERED
from dictee import insert_text, user32
from son_dictee import play_notification

# Toutes les API manipulant des pointeurs ont une signature explicite (Windows 64 bits).
LRESULT = C.c_ssize_t
WNDPROC = C.WINFUNCTYPE(LRESULT, W.HWND, W.UINT, W.WPARAM, W.LPARAM)
get_long = user32.GetWindowLongPtrW
get_long.argtypes = [W.HWND, C.c_int]
get_long.restype = C.c_ssize_t
set_long = user32.SetWindowLongPtrW
set_long.argtypes = [W.HWND, C.c_int, C.c_ssize_t]
set_long.restype = C.c_ssize_t
user32.CallWindowProcW.argtypes = [C.c_void_p, W.HWND, W.UINT, W.WPARAM, W.LPARAM]
user32.CallWindowProcW.restype = LRESULT
user32.GetParent.argtypes = [W.HWND]
user32.GetParent.restype = W.HWND
user32.ShowWindow.argtypes = [W.HWND, C.c_int]
user32.LoadIconW.argtypes = [W.HINSTANCE, C.c_void_p]
user32.LoadIconW.restype = W.HICON
user32.LoadImageW.argtypes = [W.HINSTANCE, W.LPCWSTR, W.UINT, C.c_int, C.c_int, W.UINT]
user32.LoadImageW.restype = W.HANDLE
user32.DestroyIcon.argtypes = [W.HICON]
user32.RegisterWindowMessageW.argtypes = [W.LPCWSTR]
user32.RegisterWindowMessageW.restype = W.UINT
user32.IsWindow.argtypes = [W.HWND]

class GUID(C.Structure):
    _fields_ = [('data1', W.DWORD), ('data2', W.WORD), ('data3', W.WORD), ('data4', C.c_ubyte * 8)]

class NotifyIcon(C.Structure):
    _fields_ = [('cbSize', W.DWORD), ('hWnd', W.HWND), ('uID', W.UINT),
                ('uFlags', W.UINT), ('uCallbackMessage', W.UINT), ('hIcon', W.HICON),
                ('szTip', W.WCHAR * 128), ('dwState', W.DWORD), ('dwStateMask', W.DWORD),
                ('szInfo', W.WCHAR * 256), ('uVersion', W.UINT),
                ('szInfoTitle', W.WCHAR * 64), ('dwInfoFlags', W.DWORD),
                ('guidItem', GUID), ('hBalloonIcon', W.HICON)]

shell32 = C.WinDLL('shell32', use_last_error=True)
shell32.Shell_NotifyIconW.argtypes = [W.DWORD, C.POINTER(NotifyIcon)]
shell32.Shell_NotifyIconW.restype = W.BOOL

STATES = {
    'loading': ('Chargement…', 'Préparation du modèle'),
    'ready': ('Dicter', 'Ctrl + Alt + Espace'),
    'recording': ('Arrêter', 'Le microphone vous écoute'),
    'busy': ('Transcription…', 'Insertion du texte en cours'),
    'recover': ('Texte à copier', 'Cliquez pour récupérer le texte'),
    'error': ('Réessayer', 'Cliquez pour voir le problème'),
}
# Les autres états ont trois images : normal, survol, appui.
ANIMATED = ('loading', 'recording', 'busy')
BUTTON_SIZE = 42
FRAMES = Path(__file__).with_name('bouton')


def windows_theme():
    """Thème des applications Windows ; clair si le réglage est indisponible."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r'Software\Microsoft\Windows\CurrentVersion\Themes\Personalize') as key:
            light, _ = winreg.QueryValueEx(key, 'AppsUseLightTheme')
        return 'clair' if light else 'sombre'
    except OSError:
        return 'clair'


class DictationApp:
    def __init__(self, preview=False):
        self.preview = preview
        self.events = queue.Queue()
        self.cancelled = threading.Event()
        self.state = 'loading'
        self.error = ''
        self.last_text = ''
        self.stream = None
        self.chunks = []
        self.target = None
        self.asr = None
        self.drag_start = None
        self.moved = False
        self.hover = self.pressed = False
        self.tick = 0
        self.shown = None
        self.layered = None  # résultat du dernier affichage ; None avant le premier
        self.closed = False
        self.frames_by_theme = {theme: load_frames(FRAMES / theme, STATES, BUTTON_SIZE)
                                for theme in ('clair', 'sombre')}
        self.theme = windows_theme()
        self.frames = self.frames_by_theme[self.theme]
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title('Dictée LinTO')
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        width = height = BUTTON_SIZE
        self.root.geometry(f'{width}x{height}+{self.root.winfo_screenwidth()-width-40}+80')
        # Le canevas ne dessine rien : il reçoit les clics, l'image vient de LayeredSurface.
        self.canvas = tk.Canvas(self.root, width=width, height=height,
                                highlightthickness=0, cursor='hand2')
        self.canvas.pack()
        self.menu = tk.Menu(self.root, tearoff=False)
        self.menu.add_command(label='Copier la dernière transcription', command=self.copy_text)
        self.menu.add_command(label='Chargement…', state='disabled')
        self.menu.add_separator()
        self.menu.add_command(label='Quitter la dictée', command=self.close)
        self.canvas.bind('<ButtonPress-1>', self.press)
        self.canvas.bind('<B1-Motion>', self.drag)
        self.canvas.bind('<ButtonRelease-1>', self.release)
        self.canvas.bind('<Button-3>', lambda e: self.popup(e.x_root, e.y_root))
        self.canvas.bind('<Enter>', lambda e: self.set_hover(True))
        self.canvas.bind('<Leave>', lambda e: self.set_hover(False))
        self.root.update_idletasks()
        self.hwnd = user32.GetParent(self.root.winfo_id()) or self.root.winfo_id()
        # WS_EX_NOACTIVATE | WS_EX_TOOLWINDOW : ne pas déplacer le curseur du document.
        # WS_EX_LAYERED : transparence par pixel (bords lisses, ombre) ; les pixels
        # entièrement transparents laissent passer les clics.
        set_long(self.hwnd, -20, get_long(self.hwnd, -20) | 0x08000000 | 0x80 | WS_EX_LAYERED)
        self.surface = LayeredSurface(self.hwnd, BUTTON_SIZE)
        self.callback = WNDPROC(self.window_proc)
        self.old_proc = set_long(self.hwnd, -4, C.cast(self.callback, C.c_void_p).value)
        self.taskbar_created = user32.RegisterWindowMessageW('TaskbarCreated')
        self.tray = NotifyIcon()
        self.tray.cbSize = C.sizeof(NotifyIcon)
        self.tray.hWnd = self.hwnd
        self.tray.uID = 1
        self.tray.uFlags = 1 | 2 | 4
        self.tray.uCallbackMessage = 0x8001
        self.icon = user32.LoadImageW(None, str(Path(__file__).with_name('bouche-en-coeur.ico')), 1, 32, 32, 0x10)
        self.tray.hIcon = self.icon or user32.LoadIconW(None, C.c_void_p(32512))
        self.tray.szTip = 'Dictée LinTO — Chargement'
        self.tray_added = bool(shell32.Shell_NotifyIconW(0, C.byref(self.tray)))
        self.hotkey = not preview and bool(user32.RegisterHotKey(self.hwnd, 1, 0x4003, 0x20))
        if not preview and not self.hotkey:
            self.error = 'Ctrl+Alt+Espace est déjà utilisé. Le bouton reste disponible.'
            logging.warning(self.error)
            self.menu.add_separator()
            self.menu.add_command(label='Ctrl+Alt+Espace déjà utilisé', state='disabled')
        self.render()
        self.root.deiconify()
        user32.ShowWindow(self.hwnd, 4)  # SW_SHOWNOACTIVATE
        self.poll_id = self.root.after(60, self.poll)
        if preview:
            self.set_state('ready')
        else:
            threading.Thread(target=self.load_model, daemon=True).start()

    def window_proc(self, hwnd, msg, wp, lp):
        try:
            if msg == 0x0021:  # WM_MOUSEACTIVATE
                return 3  # MA_NOACTIVATE, le clic continue à être distribué.
            if msg == 0x001A:  # WM_SETTINGCHANGE : les couleurs Windows ont pu changer.
                self.events.put(('theme', None))
            if msg == 0x0312 and wp == 1:
                self.events.put(('toggle', None))
                return 0
            if msg == 0x8001:
                if lp == 0x0205:  # bouton droit sur l'icône
                    self.events.put(('menu', None))
                elif lp == 0x0202:
                    user32.ShowWindow(self.hwnd, 4)
                return 0
            if msg == self.taskbar_created:
                self.tray_added = bool(shell32.Shell_NotifyIconW(0, C.byref(self.tray)))
                return 0
            if msg == 0x0010:  # WM_CLOSE
                self.events.put(('close', None))
                return 0
        except Exception:
            logging.exception('Message Windows')
        return user32.CallWindowProcW(self.old_proc, hwnd, msg, wp, lp)

    def set_state(self, state):
        self.state = state
        self.render()
        self.tray.szTip = 'Dictée LinTO — ' + STATES[state][0]
        shell32.Shell_NotifyIconW(1, C.byref(self.tray))

    def render(self):
        title, subtitle = STATES[self.state]
        if self.state == 'ready' and not self.preview and not self.hotkey:
            subtitle = 'Raccourci déjà utilisé'
        self.show_frame()
        self.menu.entryconfigure(1, label=f'{title} — {subtitle}')

    def show_frame(self):
        frames = self.frames[self.state]
        if self.state in ANIMATED:
            frame = frames[self.tick % len(frames)]
        else:
            frame = frames[2 if self.pressed else 1 if self.hover else 0]
        if frame is self.shown:
            return
        layered = self.surface.show(frame)
        if not layered and self.layered is not False:
            logging.error('Affichage du bouton impossible : %s', C.WinError(C.get_last_error()))
        self.layered = layered
        self.shown = frame

    def set_hover(self, hover):
        self.hover = hover
        self.show_frame()

    def press(self, event):
        self.drag_start = (event.x_root, event.y_root, self.root.winfo_x(), self.root.winfo_y())
        self.moved = False
        self.pressed = True
        self.show_frame()

    def drag(self, event):
        if not self.drag_start:
            return
        x, y, left, top = self.drag_start
        dx, dy = event.x_root-x, event.y_root-y
        if abs(dx) + abs(dy) > 5:
            self.moved = True
            self.pressed = False
            self.show_frame()
        if self.moved:
            self.root.geometry(f'+{max(0, left+dx)}+{max(0, top+dy)}')

    def release(self, event):
        self.pressed = False
        if self.drag_start and not self.moved:
            self.toggle()
        self.drag_start = None
        self.show_frame()

    def popup(self, x, y):
        self.menu.entryconfigure(0, state='normal' if self.last_text else 'disabled')
        try:
            self.menu.tk_popup(x, y)
        finally:
            self.menu.grab_release()

    def copy_text(self):
        if self.last_text:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.last_text)
            if self.state == 'recover':
                self.set_state('ready')

    def load_model(self):
        try:
            import numpy as np
            import sounddevice as sd
            from moteur_dictee import SAMPLE_RATE, get_asr
            self.np, self.sd, self.sample_rate = np, sd, SAMPLE_RATE
            self.asr = get_asr()
            self.events.put(('ready', None))
        except Exception as exc:
            logging.exception('Chargement du modèle')
            self.events.put(('error', str(exc)))

    def beep(self):
        play_notification()

    def toggle(self):
        if self.closed or self.state in ('loading', 'busy'):
            return
        if self.state == 'recover':
            self.copy_text()
            return
        if self.state == 'error':
            messagebox.showerror('Dictée LinTO', self.error, parent=self.root)
            if self.asr is None:
                self.set_state('loading')
                threading.Thread(target=self.load_model, daemon=True).start()
            else:
                self.set_state('ready')
            return
        if self.preview:
            self.set_state('recording' if self.state == 'ready' else 'ready')
            return
        if self.stream is None:
            self.target = user32.GetForegroundWindow()
            if not self.target or self.target == self.hwnd:
                return
            self.chunks = []
            try:
                self.stream = self.sd.InputStream(samplerate=self.sample_rate, channels=1,
                    dtype='float32', callback=self.capture)
                self.stream.start()
                self.set_state('recording')
                self.beep()
            except Exception as exc:
                self.stop_stream()
                self.error = f'Impossible de démarrer le microphone : {exc}'
                self.set_state('error')
        else:
            try:
                self.stop_stream()
                self.beep()
                if self.chunks:
                    audio = self.np.concatenate(self.chunks).ravel()
                    self.set_state('busy')
                    threading.Thread(target=self.transcribe, args=(audio, self.target), daemon=True).start()
                else:
                    self.set_state('ready')
            except Exception as exc:
                self.error = str(exc)
                self.set_state('error')

    def capture(self, data, frames, timing, status):
        if status:
            logging.warning('Microphone : %s', status)
        self.chunks.append(data.copy())

    def stop_stream(self):
        stream, self.stream = self.stream, None
        if stream is not None:
            try:
                stream.stop()
            finally:
                stream.close()

    def transcribe(self, audio, window):
        try:
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', message=r'Using the model-agnostic default `max_length`.*', category=UserWarning)
                text = self.asr({'array': audio, 'sampling_rate': self.sample_rate})['text'].strip()
            self.events.put(('text', text))
            while any(user32.GetAsyncKeyState(k) & 0x8000 for k in (0x11, 0x12, 0x20)):
                if self.cancelled.wait(.05):
                    return
            if self.cancelled.is_set():
                return
            if text and (not user32.IsWindow(window) or user32.GetForegroundWindow() != window):
                self.events.put(('recover', None))
            else:
                insert_text(text, window, self.cancelled)
                self.events.put(('ready', None))
                self.beep()
        except Exception as exc:
            logging.exception('Transcription ou insertion')
            self.events.put(('error', str(exc)))

    def poll(self):
        if self.poll_id is not None:
            self.root.after_cancel(self.poll_id)
            self.poll_id = None
        while not self.events.empty() and not self.closed:
            event, value = self.events.get_nowait()
            if event == 'toggle':
                self.toggle()
            elif event == 'menu':
                self.popup(*self.root.winfo_pointerxy())
            elif event == 'close':
                self.close()
            elif event == 'text':
                self.last_text = value
            elif event == 'theme':
                theme = windows_theme()
                if theme != self.theme:
                    self.theme = theme
                    self.frames = self.frames_by_theme[theme]
                    self.show_frame()
            elif event == 'error':
                self.error = value
                self.set_state('error')
            else:
                self.set_state(event)
        if not self.closed:
            if self.state in ANIMATED:
                self.tick += 1
                self.show_frame()
            self.poll_id = self.root.after(60, self.poll)

    def close(self):
        if self.closed:
            return
        self.closed = True
        self.cancelled.set()
        if self.poll_id is not None:
            self.root.after_cancel(self.poll_id)
            self.poll_id = None
        try:
            self.stop_stream()
        finally:
            if self.hotkey:
                user32.UnregisterHotKey(self.hwnd, 1)
            shell32.Shell_NotifyIconW(2, C.byref(self.tray))
            if self.icon:
                user32.DestroyIcon(self.icon)
            set_long(self.hwnd, -4, self.old_proc)
            self.root.destroy()
            self.surface.close()


def run(preview=False):
    # Un double lancement conserve le modèle déjà en mémoire.
    kernel = C.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [C.c_void_p, W.BOOL, W.LPCWSTR]
    kernel.CreateMutexW.restype = W.HANDLE
    kernel.CloseHandle.argtypes = [W.HANDLE]
    mutex = kernel.CreateMutexW(None, False, 'Local\\LinTO-Dictee-Flottante-v1')
    if not mutex:
        raise C.WinError(C.get_last_error())
    already_running = C.get_last_error() == 183
    try:
        if already_running:
            return
        app = DictationApp(preview=preview)
        try:
            app.root.mainloop()
        finally:
            app.close()
    finally:
        kernel.CloseHandle(mutex)


if __name__ == '__main__':
    import sys
    run(preview='--preview' in sys.argv)
