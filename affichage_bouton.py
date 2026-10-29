"""Bouton en transparence par pixel : PNG lus par GDI+, fenêtre en couches Windows."""
import ctypes as C
from ctypes import wintypes as W

# Instances propres : les signatures déclarées ici ne touchent pas celles des autres modules.
gdiplus = C.WinDLL('gdiplus')
gdi32 = C.WinDLL('gdi32', use_last_error=True)
user32 = C.WinDLL('user32', use_last_error=True)

PARGB = 0xE200B  # PixelFormat32bppPARGB : BGRA prémultiplié, attendu par UpdateLayeredWindow
WS_EX_LAYERED = 0x80000


class StartupInput(C.Structure):
    _fields_ = [('version', C.c_uint32), ('callback', C.c_void_p),
                ('no_thread', W.BOOL), ('no_codecs', W.BOOL)]

class BitmapData(C.Structure):
    _fields_ = [('width', C.c_uint), ('height', C.c_uint), ('stride', C.c_int),
                ('format', C.c_int), ('scan0', C.c_void_p), ('reserved', C.c_size_t)]

class BitmapInfoHeader(C.Structure):
    _fields_ = [('biSize', W.DWORD), ('biWidth', W.LONG), ('biHeight', W.LONG),
                ('biPlanes', W.WORD), ('biBitCount', W.WORD), ('biCompression', W.DWORD),
                ('biSizeImage', W.DWORD), ('biXPelsPerMeter', W.LONG), ('biYPelsPerMeter', W.LONG),
                ('biClrUsed', W.DWORD), ('biClrImportant', W.DWORD)]

class BlendFunction(C.Structure):
    _fields_ = [('op', C.c_ubyte), ('flags', C.c_ubyte), ('alpha', C.c_ubyte), ('format', C.c_ubyte)]


gdiplus.GdiplusStartup.argtypes = [C.POINTER(C.c_size_t), C.POINTER(StartupInput), C.c_void_p]
gdiplus.GdiplusShutdown.argtypes = [C.c_size_t]
gdiplus.GdiplusShutdown.restype = None
gdiplus.GdipCreateBitmapFromFile.argtypes = [W.LPCWSTR, C.POINTER(C.c_void_p)]
gdiplus.GdipGetImageWidth.argtypes = [C.c_void_p, C.POINTER(C.c_uint)]
gdiplus.GdipGetImageHeight.argtypes = [C.c_void_p, C.POINTER(C.c_uint)]
gdiplus.GdipBitmapLockBits.argtypes = [C.c_void_p, C.POINTER(C.c_int * 4), C.c_uint, C.c_int,
                                       C.POINTER(BitmapData)]
gdiplus.GdipBitmapUnlockBits.argtypes = [C.c_void_p, C.POINTER(BitmapData)]
gdiplus.GdipDisposeImage.argtypes = [C.c_void_p]
gdi32.CreateCompatibleDC.argtypes = [W.HDC]
gdi32.CreateCompatibleDC.restype = W.HDC
gdi32.CreateDIBSection.argtypes = [W.HDC, C.c_void_p, W.UINT, C.POINTER(C.c_void_p), W.HANDLE, W.DWORD]
gdi32.CreateDIBSection.restype = W.HBITMAP
gdi32.SelectObject.argtypes = [W.HDC, W.HGDIOBJ]
gdi32.SelectObject.restype = W.HGDIOBJ
gdi32.DeleteObject.argtypes = [W.HGDIOBJ]
gdi32.DeleteDC.argtypes = [W.HDC]
user32.UpdateLayeredWindow.argtypes = [W.HWND, W.HDC, C.POINTER(W.POINT), C.POINTER(W.SIZE), W.HDC,
                                       C.POINTER(W.POINT), W.COLORREF, C.POINTER(BlendFunction), W.DWORD]
user32.UpdateLayeredWindow.restype = W.BOOL


def check(status, path):
    if status:
        raise OSError(f'GDI+ ({status}) : {path}')


def read_strip(path, size):
    """Découpe une bande verticale d'images size × size en images BGRA prémultipliées."""
    bitmap = C.c_void_p()
    check(gdiplus.GdipCreateBitmapFromFile(str(path), C.byref(bitmap)), path)
    try:
        width, height = C.c_uint(), C.c_uint()
        check(gdiplus.GdipGetImageWidth(bitmap, C.byref(width)), path)
        check(gdiplus.GdipGetImageHeight(bitmap, C.byref(height)), path)
        if width.value != size or not height.value or height.value % size:
            raise ValueError(f'Bande de {width.value} × {height.value} pixels inattendue : {path}')
        data = BitmapData()
        rect = (C.c_int * 4)(0, 0, width.value, height.value)
        check(gdiplus.GdipBitmapLockBits(bitmap, C.byref(rect), 1, PARGB, C.byref(data)), path)
        try:
            if data.stride != size * 4:
                raise ValueError(f'Pas de ligne inattendu : {path}')
            pixels = C.string_at(data.scan0, data.stride * height.value)
        finally:
            gdiplus.GdipBitmapUnlockBits(bitmap, C.byref(data))
    finally:
        gdiplus.GdipDisposeImage(bitmap)
    frame = size * size * 4
    return [pixels[i:i+frame] for i in range(0, len(pixels), frame)]


def load_frames(folder, names, size):
    token = C.c_size_t()
    check(gdiplus.GdiplusStartup(C.byref(token), C.byref(StartupInput(1)), None), 'démarrage')
    try:
        return {name: read_strip(folder / f'{name}.png', size) for name in names}
    finally:
        gdiplus.GdiplusShutdown(token)


class LayeredSurface:
    """Image affichée par UpdateLayeredWindow ; la fenêtre doit avoir WS_EX_LAYERED."""

    def __init__(self, hwnd, size):
        self.hwnd, self.size = hwnd, size
        self.bits = C.c_void_p()
        self.dc = gdi32.CreateCompatibleDC(None)
        header = BitmapInfoHeader(C.sizeof(BitmapInfoHeader), size, -size, 1, 32, 0)  # de haut en bas
        self.bitmap = gdi32.CreateDIBSection(self.dc, C.byref(header), 0, C.byref(self.bits), None, 0)
        if not self.dc or not self.bitmap:
            error = C.WinError(C.get_last_error())
            if self.dc:
                gdi32.DeleteDC(self.dc)
            self.dc = None
            raise error
        self.previous = gdi32.SelectObject(self.dc, self.bitmap)

    def show(self, frame):
        C.memmove(self.bits, frame, len(frame))
        size, origin = W.SIZE(self.size, self.size), W.POINT(0, 0)
        blend = BlendFunction(0, 0, 255, 1)  # AC_SRC_OVER, AC_SRC_ALPHA
        return bool(user32.UpdateLayeredWindow(self.hwnd, None, None, C.byref(size), self.dc,
                                               C.byref(origin), 0, C.byref(blend), 2))  # ULW_ALPHA

    def close(self):
        if self.dc:
            gdi32.SelectObject(self.dc, self.previous)
            gdi32.DeleteObject(self.bitmap)
            gdi32.DeleteDC(self.dc)
            self.dc = None
