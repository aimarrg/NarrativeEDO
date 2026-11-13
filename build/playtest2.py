# -*- coding: utf-8 -*-
"""Prueba de interacción en el monitor secundario (sin tapar el principal)."""
import ctypes
import ctypes.wintypes as wt
import os
import subprocess
import sys
import time

from PIL import Image

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))

SRCCOPY = 0x00CC0020
CAPTUREBLT = 0x40000000
WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = r"C:\Temps\opencode"
MON_X, MON_Y = 2600, 60


def find_window(title_part="Nagasaki1641"):
    found = []

    @ctypes.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            if title_part in buf.value:
                found.append(hwnd)
        return True

    user32.EnumWindows(cb, 0)
    return found[0] if found else None


def client_rect(hwnd):
    rc = wt.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rc))
    pt = wt.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y, rc.right - rc.left, rc.bottom - rc.top


def capture(hwnd, name):
    out = os.path.join(OUT, name)
    x, y, w, h = client_rect(hwnd)
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    bmp = gdi32.CreateCompatibleBitmap(hdc_screen, w, h)
    gdi32.SelectObject(hdc_mem, bmp)
    ok = user32.PrintWindow(hwnd, hdc_mem, 1)
    if not ok:
        gdi32.BitBlt(hdc_mem, 0, 0, w, h, hdc_screen, x, y, SRCCOPY | CAPTUREBLT)

    class BIH(ctypes.Structure):
        _fields_ = [("biSize", wt.DWORD), ("biWidth", wt.LONG), ("biHeight", wt.LONG),
                    ("biPlanes", wt.WORD), ("biBitCount", wt.WORD),
                    ("biCompression", wt.DWORD), ("biSizeImage", wt.DWORD),
                    ("biXPelsPerMeter", wt.LONG), ("biYPelsPerMeter", wt.LONG),
                    ("biClrUsed", wt.DWORD), ("biClrImportant", wt.DWORD)]

    bi = BIH()
    bi.biSize = ctypes.sizeof(BIH)
    bi.biWidth = w
    bi.biHeight = -h
    bi.biPlanes = 1
    bi.biBitCount = 32
    buf = (ctypes.c_ubyte * (w * h * 4))()
    gdi32.GetDIBits(hdc_mem, bmp, 0, h, buf, ctypes.byref(bi), 0)
    Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB").save(out)
    gdi32.DeleteObject(bmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)
    print("captura:", out)
    return out


def move(hwnd, sx, sy):
    x, y, w, h = client_rect(hwnd)
    px = x + int(sx * w / 1280)
    py = y + int(sy * h / 720)
    user32.SetCursorPos(px, py)
    lp = (py << 16) | px
    user32.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)
    return px, py


def click(hwnd, sx, sy, wait=0.5):
    px, py = move(hwnd, sx, sy)
    lp = (py << 16) | px
    user32.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
    time.sleep(0.06)
    user32.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    time.sleep(wait)


def main():
    ved = os.path.join(ROOT, "game", "Nagasaki1641.ved")
    exe = r"C:\Program Files\Visionaire Studio 5\visplayer.exe"
    proc = subprocess.Popen([exe, ved])
    hwnd = None
    for _ in range(60):
        time.sleep(0.5)
        hwnd = find_window()
        if hwnd:
            break
    if not hwnd:
        print("no window")
        return 1
    time.sleep(2)
    user32.SetWindowPos(hwnd, 0, MON_X, MON_Y, 1280, 720,
                        0x0004 | 0x0010 | 0x0040)  # NOZORDER|NOACTIVATE|SHOWWINDOW
    time.sleep(2)
    print("rect", client_rect(hwnd))
    capture(hwnd, "s0_intro.png")

    for i in range(3):
        click(hwnd, 640, 415, 0.8)
    capture(hwnd, "s1_after3.png")

    for i in range(6):
        click(hwnd, 640, 415, 0.6)
    capture(hwnd, "s2_intro_done.png")

    click(hwnd, 700, 680, 2.0)
    capture(hwnd, "s3_walk.png")

    proc.terminate()
    return 0


if __name__ == "__main__":
    sys.exit(main())
