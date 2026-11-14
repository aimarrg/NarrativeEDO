# -*- coding: utf-8 -*-
"""
Arte del prototipo "Nagasaki 1641: El sello de Dejima".

Estilo: ukiyo-e (grabado japonÃ©s). LÃ­nea de tinta gruesa, colores planos,
textura de papel washi, cielos en bandas (bokashi), mar con patrÃ³n seigaiha,
cartuchos y sellos rojos.

Todo se dibuja a 2x y se reduce con LANCZOS.
"""
import json
import math
import os
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, "game")
GFX = os.path.join(GAME, "graphics")
CHR = os.path.join(GAME, "characters")
FONTS = os.path.join(GAME, "fonts")

W, H = 1280, 720
S = 2

FONT_REG = os.path.join(FONTS, "NotoSans-Regular.ttf")
FONT_BOLD = os.path.join(FONTS, "NotoSans-Bold.ttf")

# Paleta de grabado: tinta sumi, azul de Prusia, indigo, bermellÃ³n, ocre, papel.
PAL = {
    "ink": (28, 25, 23),
    "ink_soft": (58, 50, 43),
    "paper": (238, 224, 196),
    "paper_l": (247, 237, 214),
    "cream": (242, 230, 203),
    "prussian": (32, 54, 80),
    "indigo": (45, 72, 102),
    "indigo_l": (72, 103, 132),
    "indigo_p": (92, 124, 150),
    "vermillion": (178, 58, 44),
    "vermillion_d": (134, 42, 34),
    "ochre": (205, 150, 76),
    "gold": (224, 181, 104),
    "wood": (126, 91, 58),
    "wood_d": (82, 58, 38),
    "wood_l": (161, 120, 78),
    "skin": (229, 186, 146),
    "skin_d": (198, 148, 112),
    "hair": (34, 30, 28),
    "moss": (96, 110, 78),
    "rose": (196, 142, 124),
}


def sc(v):
    return int(round(v * S))


def mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Pen:
    def __init__(self, img):
        self.img = img
        self.d = ImageDraw.Draw(img, "RGBA")

    def rect(self, box, fill, outline=None, width=0):
        self.d.rectangle([sc(box[0]), sc(box[1]), sc(box[2]), sc(box[3])], fill=fill,
                         outline=outline, width=sc(width) if width else 0)

    def rrect(self, box, radius, fill, outline=None, width=0):
        self.d.rounded_rectangle([sc(box[0]), sc(box[1]), sc(box[2]), sc(box[3])],
                                 radius=sc(radius), fill=fill, outline=outline,
                                 width=sc(width) if width else 0)

    def ellipse(self, box, fill, outline=None, width=0):
        self.d.ellipse([sc(box[0]), sc(box[1]), sc(box[2]), sc(box[3])], fill=fill,
                       outline=outline, width=sc(width) if width else 0)

    def poly(self, pts, fill, outline=None):
        points = [(sc(x), sc(y)) for x, y in pts]
        self.d.polygon(points, fill=fill)
        if outline:
            self.d.line(points + [points[0]], fill=outline, width=sc(3), joint="curve")

    def line(self, pts, fill, width=1, joint="curve"):
        self.d.line([(sc(x), sc(y)) for x, y in pts], fill=fill, width=max(1, sc(width)), joint=joint)

    def arc(self, box, a0, a1, fill, width=1):
        self.d.arc([sc(box[0]), sc(box[1]), sc(box[2]), sc(box[3])], a0, a1,
                   fill=fill, width=max(1, sc(width)))

    def text(self, xy, s, size, fill, font=FONT_REG, anchor="la"):
        f = ImageFont.truetype(font, sc(size))
        self.d.text((sc(xy[0]), sc(xy[1])), s, font=f, fill=fill, anchor=anchor)


def new_rgba(w=W, h=H):
    return Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))


def vgrad(img, y0, y1, stops):
    d = ImageDraw.Draw(img)
    h = sc(y1) - sc(y0)
    for i in range(h):
        t = i / max(1, h - 1)
        for k in range(len(stops) - 1):
            t0, c0 = stops[k]
            t1, c1 = stops[k + 1]
            if t0 <= t <= t1:
                f = (t - t0) / max(1e-6, t1 - t0)
                c = tuple(int(c0[j] + (c1[j] - c0[j]) * f) for j in range(3))
                d.line([(0, sc(y0) + i), (img.width, sc(y0) + i)], fill=c)
                break


def soft_glow(img, cx, cy, r, color, alpha=120):
    size = 128
    mask = Image.new("L", (size, size), 0)
    md = ImageDraw.Draw(mask)
    for i in range(size // 2, 0, -1):
        a = int(255 * (1 - i / (size / 2)) ** 2 * alpha / 255)
        md.ellipse([size / 2 - i, size / 2 - i, size / 2 + i, size / 2 + i], fill=a)
    mask = mask.resize((sc(r * 2), sc(r * 2)), Image.LANCZOS)
    glow = Image.new("RGBA", mask.size, color + (255,))
    glow.putalpha(mask)
    img.alpha_composite(glow, (sc(cx - r), sc(cy - r)))


def washi(img, strength=1.0):
    """Textura de papel washi: moteado suave y unas pocas fibras muy tenues."""
    w, h = img.size
    rng = random.Random(11)
    arr = np.asarray(img).astype(np.float32)
    yy, xx = np.mgrid[0:h, 0:w]
    mott = (np.sin(xx / (37.0 * S)) * np.sin(yy / (53.0 * S)) * 2.2
            + np.sin((xx + yy) / (91.0 * S)) * 1.4)
    noise = np.random.normal(0, 2.6, (h, w, 1))
    arr[:, :, :3] = np.clip(arr[:, :, :3] + (mott[:, :, None] + noise) * strength, 0, 255)
    out = Image.fromarray(arr.astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(out, "RGBA")
    for _ in range(int(28 * strength)):
        x = rng.randint(0, w - 1)
        y = rng.randint(0, h - 1)
        ln = rng.randint(sc(5), sc(18))
        vertical = rng.random() < 0.25
        if vertical:
            d.line([(x, y), (x + rng.randint(-1, 1), y + ln)],
                   fill=(252, 244, 226, rng.randint(6, 14)), width=1)
        else:
            d.line([(x, y), (x + ln, y + rng.randint(-1, 1))],
                   fill=(252, 244, 226, rng.randint(6, 14)), width=1)
    return out


def grain(img, amount=4):
    arr = np.asarray(img).astype(np.int16)
    noise = np.random.normal(0, amount, (img.height, img.width, 1))
    arr[:, :, :3] = np.clip(arr[:, :, :3] + noise, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), "RGBA")


def vignette(img, strength=0.10):
    w, h = img.size
    x = np.linspace(-1, 1, w)[None, :]
    y = np.linspace(-1, 1, h)[:, None]
    d = np.sqrt(x * x + y * y) / 1.414
    mask = np.clip(1 - strength * (d ** 2) * 2.2, 0.72, 1)[:, :, None]
    arr = np.asarray(img).astype(np.float32)
    arr[:, :, :3] *= mask
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


def crop_alpha(img):
    bbox = img.split()[3].getbbox()
    if not bbox:
        return None, 0, 0
    x0, y0, x1, y1 = bbox
    pad = sc(2)
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(img.width, x1 + pad)
    y1 = min(img.height, y1 + pad)
    out = img.crop((x0, y0, x1, y1)).resize(((x1 - x0) // S, (y1 - y0) // S), Image.LANCZOS)
    return out, x0 // S, y0 // S


# ---------------------------------------------------------------------------
# Motivos ukiyo-e
# ---------------------------------------------------------------------------
def _outlined(layer, color, width=3):
    """Devuelve la capa con un contorno de tinta unificado alrededor de su alfa."""
    from PIL import ImageChops
    alpha = layer.split()[3]
    grown = alpha.filter(ImageFilter.MaxFilter(width * 2 + 1))
    ring = ImageChops.subtract(grown, alpha)
    out = Image.new("RGBA", layer.size, color + (255,))
    out.putalpha(ring)
    out.alpha_composite(layer)
    return out


def cloud(img, cx, cy, w, h, fill, outline=True, rng=None):
    """Banda de nube estilizada, con lÃ³bulos solapados y contorno de tinta."""
    rng = rng or random.Random(int(cx * 7 + cy))
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    n = max(5, int(w / (h * 0.62)))
    for i in range(n):
        t = i / (n - 1)
        x = cx - w / 2 + w * t
        y = cy + math.sin(t * math.pi * 2.2 + rng.random()) * h * 0.14
        r = h * (0.52 + 0.38 * abs(math.sin(t * math.pi * 3.1 + 0.4)))
        # lÃ³bulo principal
        d.ellipse([sc(x - r), sc(y - r * 0.8), sc(x + r), sc(y + r * 0.8)], fill=fill)
        # lÃ³bulo superior ocasional
        if i % 2 == 0:
            r2 = r * 0.72
            d.ellipse([sc(x - r2 * 0.7), sc(y - r2 * 1.25),
                       sc(x + r2 * 0.9), sc(y + r2 * 0.1)], fill=fill)
    if outline:
        layer = _outlined(layer, PAL["ink_soft"], 2)
    img.alpha_composite(layer)


def seigaiha(img, x0, y0, x1, y1, base, line, r=26, alpha=210):
    """Mar con patrÃ³n de olas concÃ©ntricas (seigaiha)."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    rng = sc(r)
    step_x = sc(r * 1.55)
    step_y = sc(r * 0.58)
    row = 0
    y = sc(y0) - step_y
    while y < sc(y1) + sc(r):
        x = sc(x0) - step_x + (step_x // 2 if row % 2 else 0)
        while x < sc(x1) + sc(r):
            for k in range(3):
                rr = rng - k * sc(5)
                if rr <= 1:
                    continue
                d.arc([x - rr, y - rr, x + rr, y + rr], 180, 360,
                      fill=line + (alpha,), width=max(1, sc(1.3)))
            x += step_x
        y += step_y
        row += 1
    # recorte al Ã¡rea del mar
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rectangle([0, sc(y0 + 6), img.width, sc(y1)], fill=255)
    layer.putalpha(Image.composite(layer.split()[3], Image.new("L", img.size, 0), mask))
    img.alpha_composite(layer)


def hatch(img, pts, color, step=7, width=1, alpha=150, angle=45):
    """Rayado de grabado dentro de un polÃ­gono."""
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon([(sc(x), sc(y)) for x, y in pts], fill=255)
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    diag = (x1 - x0) + (y1 - y0)
    for i in range(0, int(diag / step) + 1):
        off = x0 - (y1 - y0) + i * step
        d.line([(sc(off), sc(y1)), (sc(off + (y1 - y0)), sc(y0))],
               fill=color + (alpha,), width=max(1, sc(width)))
    layer.putalpha(Image.composite(layer.split()[3], Image.new("L", img.size, 0), mask))
    img.alpha_composite(layer)


def seal_stamp(img, x, y, size=44, vertical="NAGASAKI"):
    """Sello rojo con texto vertical."""
    pen = Pen(img)
    pen.rrect((x, y, x + size, y + size), 3, PAL["vermillion"] + (235,),
              PAL["vermillion_d"] + (255,), 2)
    pen.rect((x + 3, y + 3, x + size - 3, y + size - 3), None,
             PAL["paper_l"] + (90,), 1)
    chars = vertical[:4]
    f = ImageFont.truetype(FONT_BOLD, sc(max(9, size / 5)))
    for i, c in enumerate(chars):
        tw = pen.d.textlength(c, font=f)
        pen.d.text((sc(x + size / 2) - tw / 2, sc(y + 5 + i * size / 5.2)), c,
                   font=f, fill=PAL["paper_l"] + (235,))


def cartouche(img, x, y, w, h, title):
    """Cartucho vertical de tÃ­tulo, como en los grabados."""
    pen = Pen(img)
    pen.rect((x, y, x + w, y + h), PAL["paper_l"] + (238,),
             PAL["ink"] + (255,), 3)
    pen.rect((x + 4, y + 4, x + w - 4, y + h - 4), None, PAL["ochre"] + (180,), 1)
    f = ImageFont.truetype(FONT_BOLD, sc(17))
    for i, ch in enumerate(title[:9]):
        tw = pen.d.textlength(ch, font=f)
        pen.d.text((sc(x + w / 2) - tw / 2, sc(y + 10 + i * 22)), ch,
                   font=f, fill=PAL["ink"] + (240,))


def mountain(img, pts, fill, hatch_col=None):
    pen = Pen(img)
    pen.poly(pts, fill, PAL["ink"] + (190,))
    if hatch_col:
        hatch(img, pts, hatch_col, step=9, width=1, alpha=70, angle=50)


# ---------------------------------------------------------------------------
# FONDOS
# ---------------------------------------------------------------------------
def bg_warehouse():
    img = new_rgba()
    # pared de yeso (kura)
    vgrad(img, 0, 600, [(0, (244, 231, 202)), (0.6, (238, 224, 194)), (1, (232, 216, 184))])
    pen = Pen(img)

    # sombra suave bajo las vigas
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    for y in (56, 148, 246):
        sd.rectangle([0, sc(y), img.width, sc(y + 16)], fill=(70, 58, 46, 60))
    shadow = shadow.filter(ImageFilter.GaussianBlur(sc(7)))
    img.alpha_composite(shadow)

    # zÃ³calo de madera
    pen.rect((0, 430, W, 600), PAL["wood_d"] + (255,))
    for x in range(0, W, 74):
        pen.line([(x, 430), (x, 600)], PAL["ink"] + (110,), 1.4)
    pen.rect((0, 424, W, 438), PAL["wood"] + (255,), PAL["ink"] + (255,), 2)
    for y in (474, 524, 574):
        pen.line([(0, y), (W, y)], PAL["ink"] + (80,), 1)

    # vigas horizontales y postes
    for y in (34, 126, 224):
        pen.rect((0, y, W, y + 22), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2)
    for x in (150, 480, 810, 1120):
        pen.rect((x, 0, x + 26, 438), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2)

    # ventana de papel (shoji)
    pen.rect((500, 96, 690, 262), PAL["cream"] + (255,), PAL["ink"] + (255,), 3)
    pen.rect((512, 108, 678, 250), (250, 238, 206, 255))
    for i in range(1, 4):
        pen.line([(512 + i * 41, 108), (512 + i * 41, 250)], PAL["wood_d"] + (235,), 2)
    for j in range(1, 4):
        pen.line([(512, 108 + j * 35), (678, 108 + j * 35)], PAL["wood_d"] + (235,), 2)
    soft_glow(img, 595, 250, 210, (255, 226, 168), 55)

    # noren Ã­ndigo con mon
    pen.rect((878, 58, 1064, 206), PAL["indigo"] + (255,), PAL["ink"] + (255,), 3)
    for i in range(1, 5):
        pen.line([(878 + i * 37, 58), (878 + i * 37, 206)], PAL["prussian"] + (235,), 1.6)
    pen.ellipse((948, 108, 996, 156), None, PAL["paper"] + (235,), 2.4)
    pen.ellipse((960, 120, 984, 144), PAL["paper"] + (235,))
    pen.line([(878, 58), (1064, 58)], PAL["wood_d"] + (255,), 4)

    # kakejiku (rollo colgado) con ola
    pen.rect((792, 246, 862, 258), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 1.5)
    pen.rect((798, 258, 856, 434), PAL["paper_l"] + (255,), PAL["ink"] + (255,), 1.8)
    pen.rect((804, 266, 850, 426), (238, 226, 198, 255))
    # ola estilizada dentro del rollo
    pen.arc((806, 300, 848, 360), 190, 340, PAL["indigo"] + (230,), 2.2)
    pen.arc((798, 322, 856, 396), 195, 335, PAL["indigo"] + (200,), 1.6)
    pen.arc((810, 344, 844, 404), 200, 330, PAL["indigo_l"] + (190,), 1.4)
    pen.poly([(812, 352), (820, 330), (828, 352)], PAL["paper_l"] + (255,),
             PAL["indigo"] + (220,))
    pen.rect((822, 394, 840, 412), PAL["vermillion"] + (235,))
    pen.rect((798, 426, 856, 438), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 1.5)

    # suelo
    pen.rect((0, 596, W, H), PAL["wood"] + (255,))
    pen.rect((0, 596, W, 612), PAL["wood_l"] + (255,), PAL["ink"] + (255,), 2)
    for y in (628, 664, 700):
        pen.line([(0, y), (W, y)], PAL["ink"] + (95,), 1.4)
    for x in range(-20, W, 138):
        pen.line([(x, 612), (x + 66, H)], PAL["wood_d"] + (95,), 1.2)

    # pila de cajas con sellos bermellÃ³n
    for (x, y, w, h) in ((44, 486, 150, 112), (84, 382, 132, 106), (26, 580, 192, 58),
                         (216, 534, 118, 86)):
        pen.rect((x, y, x + w, y + h), (150, 114, 76, 255), PAL["ink"] + (255,), 2.4)
        pen.rect((x + 7, y + 7, x + w - 7, y + h - 7), None, PAL["wood_d"] + (210,), 1)
        pen.line([(x, y), (x + w, y + h)], PAL["wood_d"] + (180,), 1.4)
        pen.line([(x + w, y), (x, y + h)], PAL["wood_d"] + (180,), 1.4)
        pen.rect((x + w / 2 - 10, y + h / 2 - 10, x + w / 2 + 10, y + h / 2 + 10),
                 PAL["vermillion"] + (225,))
        pen.rect((x + w / 2 - 5, y + h / 2 - 5, x + w / 2 + 5, y + h / 2 + 5),
                 PAL["paper_l"] + (220,))

    # barriles
    for (x, y) in ((1146, 466), (1208, 518)):
        pen.rrect((x, y, x + 66, y + 108), 12, PAL["ochre"] + (235,), PAL["ink"] + (255,), 2)
        for yy in (y + 20, y + 55, y + 90):
            pen.line([(x + 2, yy), (x + 64, yy)], PAL["wood_d"] + (235,), 2.2)

    # farolillo
    soft_glow(img, 700, 214, 230, (255, 190, 110), 90)
    pen.line([(700, 0), (700, 118)], PAL["ink"] + (255,), 2)
    pen.rrect((662, 118, 738, 212), 12, PAL["gold"] + (245,), PAL["ink"] + (255,), 2.4)
    pen.line([(664, 150), (736, 150)], PAL["vermillion"] + (120,), 1.4)
    pen.line([(664, 180), (736, 180)], PAL["vermillion"] + (120,), 1.4)

    # cuerdas y ganchos
    for x in (392, 980):
        pen.line([(x, 250), (x + 10, 466)], PAL["wood_d"] + (220,), 2)
        pen.arc((x - 8, 458, x + 26, 490), 0, 180, PAL["ink"] + (220,), 2)

    # trampilla
    pen.rect((640, 646, 830, 712), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2.4)
    pen.line([(640, 679), (830, 679)], PAL["ink"] + (200,), 2)
    pen.line([(648, 652), (822, 706)], PAL["wood"] + (120,), 1)

    # cartucho
    cartouche(img, 26, 26, 30, 150, "KURA")

    img = washi(img, 1.0)
    img = grain(img, 3)
    img = vignette(img, 0.12)
    return img.convert("RGB")


def bg_epilogue():
    img = new_rgba()
    vgrad(img, 0, 480, [(0, (44, 62, 92)), (0.32, (86, 101, 126)),
                        (0.55, (176, 148, 132)), (0.74, (230, 166, 122)),
                        (0.9, (244, 205, 158)), (1, (247, 227, 190))])
    pen = Pen(img)

    # sol naciente
    soft_glow(img, 790, 430, 230, (255, 214, 150), 110)
    pen.ellipse((718, 358, 862, 502), PAL["vermillion"] + (225,), PAL["ink"] + (80,), 2)

    # nubes
    cloud(img, 300, 160, 360, 40, PAL["paper_l"] + (226,), True)
    cloud(img, 860, 110, 320, 32, PAL["rose"] + (185,), True)
    cloud(img, 560, 280, 420, 26, PAL["paper"] + (175,), True)

    # montaÃ±as / Dejima
    mountain(img, [(0, 480), (0, 430), (150, 404), (300, 436), (470, 410), (640, 438),
                   (820, 412), (1000, 434), (1180, 408), (1280, 424), (1280, 480)],
             PAL["indigo"] + (255,), PAL["prussian"])
    mountain(img, [(0, 480), (0, 456), (200, 444), (420, 462), (640, 446),
                   (880, 460), (1120, 446), (1280, 456), (1280, 480)],
             PAL["prussian"] + (255,), None)

    # mar
    vgrad(img, 470, 650, [(0, (58, 81, 106)), (0.55, (40, 62, 88)), (1, (28, 47, 68))])
    seigaiha(img, -40, 478, W + 40, 648, PAL["prussian"], PAL["indigo_p"], r=30, alpha=120)
    seigaiha(img, -40, 545, W + 40, 648, PAL["prussian"], PAL["paper"], r=20, alpha=55)

    # isla Dejima
    pen.poly([(880, 520), (906, 486), (1000, 476), (1080, 492), (1108, 520)],
             PAL["ink"] + (210,), PAL["ink"] + (255,))
    pen.rect((910, 486, 1050, 506), PAL["wood_d"] + (235,), PAL["ink"] + (255,), 1.5)
    pen.poly([(940, 486), (966, 456), (992, 486)], PAL["wood_d"] + (235,), PAL["ink"] + (255,))

    # barco de los fugitivos
    pen.poly([(560, 626), (690, 626), (668, 650), (582, 650)], PAL["ink"] + (245,),
             PAL["ink"] + (255,))
    pen.line([(626, 626), (626, 512)], PAL["ink"] + (255,), 2.4)
    pen.poly([(630, 520), (630, 610), (700, 604)], PAL["paper"] + (235,), PAL["ink"] + (255,))
    pen.poly([(622, 524), (622, 610), (566, 602)], PAL["paper"] + (215,), PAL["ink"] + (255,))
    for i, x in enumerate((600, 620, 644, 666)):
        pen.line([(x, 628), (x, 646)], PAL["ochre"] + (200,), 2)

    # muelle
    pen.rect((0, 646, W, H), PAL["wood"] + (255,))
    pen.rect((0, 646, W, 660), PAL["wood_l"] + (255,), PAL["ink"] + (255,), 2)
    for x in range(0, W, 116):
        pen.line([(x, 660), (x + 48, H)], PAL["wood_d"] + (115,), 1.2)
    for y in (680, 710):
        pen.line([(0, y), (W, y)], PAL["wood_d"] + (120,), 1)

    # aves
    for (x, y, s_) in ((330, 190, 14), (382, 168, 9), (440, 208, 11)):
        pen.line([(x - s_, y), (x, y - s_ * 0.5), (x + s_, y)], PAL["ink"] + (190,), 2)

    cartouche(img, 24, 24, 30, 150, "DEJIMA")
    seal_stamp(img, 1160, 24, 34, "1641")

    img = washi(img, 1.0)
    img = grain(img, 3)
    img = vignette(img, 0.10)
    return img.convert("RGB")


# ---------------------------------------------------------------------------
# OBJETOS
# ---------------------------------------------------------------------------
def _outline_alpha(img):
    """Refuerza el contorno alfa para que los objetos recortados tengan lÃ­nea."""
    return img


def obj_crate():
    img = new_rgba()
    pen = Pen(img)
    x, y, w, h = 512, 498, 164, 140
    pen.ellipse((x - 10, y + h - 12, x + w + 10, y + h + 18), (20, 18, 16, 80))
    pen.rect((x, y, x + w, y + h), PAL["wood"] + (255,), PAL["ink"] + (255,), 3)
    pen.rect((x + 9, y + 9, x + w - 9, y + h - 9), (140, 103, 66, 255), None)
    for i in range(3):
        pen.line([(x + 14, y + 24 + i * 34), (x + w - 14, y + 24 + i * 34)],
                 PAL["wood_d"] + (150,), 1.4)
    pen.line([(x + 6, y + 6), (x + w - 6, y + h - 6)], PAL["wood_d"] + (220,), 3)
    pen.line([(x + w - 6, y + 6), (x + 6, y + h - 6)], PAL["wood_d"] + (220,), 3)
    # sello del gremio
    pen.rect((x + 52, y - 16, x + 110, y + 12), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2)
    pen.rect((x + 76, y - 4, x + 108, y + 30), PAL["wood"] + (255,), PAL["ink"] + (255,), 2)
    pen.ellipse((x + 82, y + 5, x + 102, y + 25), PAL["vermillion"] + (255,))
    pen.rect((x + 88, y + 10, x + 96, y + 20), PAL["paper"] + (230,))
    # cuerdas
    pen.line([(x + 24, y - 2), (x + 24, y + 36)], PAL["paper"] + (200,), 3)
    pen.line([(x + w - 24, y - 2), (x + w - 24, y + 36)], PAL["paper"] + (200,), 3)
    return img


def obj_fish():
    img = new_rgba()
    pen = Pen(img)
    x, y = 152, 516
    # tabla y pescado seco
    pen.rect((x - 4, y + 6, x + 96, y + 34), PAL["wood_l"] + (255,), PAL["ink"] + (255,), 2)
    pen.poly([(x + 8, y + 14), (x + 58, y + 8), (x + 88, y + 20), (x + 58, y + 30),
              (x + 12, y + 26)], PAL["indigo_l"] + (255,), PAL["ink"] + (255,))
    pen.poly([(x + 80, y + 14), (x + 96, y + 6), (x + 94, y + 26), (x + 80, y + 26)],
             PAL["indigo_l"] + (255,), PAL["ink"] + (255,))
    pen.ellipse((x + 24, y + 15, x + 30, y + 21), PAL["paper"] + (240,))
    for i in range(3):
        pen.arc((x + 30 + i * 14, y + 12, x + 54 + i * 14, y + 30), 200, 340,
                PAL["paper"] + (120,), 1.2)
    return img


def obj_fisher():
    img = new_rgba()
    pen = Pen(img)
    x, y = 70, 410
    pen.ellipse((x + 10, 640, x + 168, 672), (22, 20, 18, 95))
    # caÃ±a
    pen.line([(x + 42, y + 150), (x - 14, y - 46)], PAL["wood_d"] + (255,), 2.4)
    pen.line([(x - 14, y - 46), (x + 30, y + 214)], PAL["paper"] + (100,), 1)
    # cuerpo (kimono de trabajo)
    pen.poly([(x + 44, y + 72), (x + 112, y + 80), (x + 126, y + 206),
              (x + 60, y + 214), (x + 32, y + 122)], (62, 66, 74, 255), PAL["ink"] + (255,))
    pen.poly([(x + 44, y + 72), (x + 96, y + 78), (x + 92, y + 132),
              (x + 40, y + 124)], (80, 84, 92, 255))
    hatch(img, [(x + 48, y + 90), (x + 96, y + 94), (x + 90, y + 150), (x + 40, y + 140)],
          PAL["ink"], step=8, width=1, alpha=55, angle=60)
    # piernas
    pen.line([(x + 66, y + 202), (x + 56, y + 238)], (48, 48, 54, 255), 12)
    pen.line([(x + 102, y + 202), (x + 112, y + 238)], (48, 48, 54, 255), 12)
    pen.line([(x + 52, y + 238), (x + 66, y + 238)], PAL["ink"] + (255,), 4)
    pen.line([(x + 108, y + 238), (x + 122, y + 238)], PAL["ink"] + (255,), 4)
    # cabeza
    pen.ellipse((x + 56, y + 18, x + 102, y + 68), PAL["skin"] + (255,), PAL["ink"] + (255,), 2.4)
    pen.poly([(x + 58, y + 34), (x + 70, y + 24), (x + 88, y + 26), (x + 100, y + 38)],
             PAL["hair"] + (255,))
    # sombrero de paja
    pen.poly([(x + 26, y + 36), (x + 132, y + 36), (x + 80, y + 2)],
             (212, 184, 128, 255), PAL["ink"] + (255,))
    pen.line([(x + 26, y + 36), (x + 132, y + 36)], PAL["wood_d"] + (255,), 2.2)
    for i in range(4):
        pen.line([(x + 46 + i * 20, y + 34), (x + 74, y + 8)], PAL["wood_d"] + (80,), 1)
    # ojos y bigote
    pen.ellipse((x + 68, y + 48, x + 74, y + 53), PAL["ink"] + (255,))
    pen.ellipse((x + 86, y + 48, x + 92, y + 53), PAL["ink"] + (255,))
    pen.line([(x + 72, y + 60), (x + 88, y + 60)], PAL["ink_soft"] + (230,), 2)
    # brazo
    pen.line([(x + 94, y + 94), (x + 46, y + 152)], PAL["ink"] + (255,), 15)
    pen.line([(x + 94, y + 94), (x + 46, y + 152)], (70, 74, 84, 255), 11)
    return img


def obj_edict():
    img = new_rgba()
    pen = Pen(img)
    x, y = 392, 452
    # postes
    pen.line([(x + 18, y - 26), (x + 18, y + 8)], PAL["wood_d"] + (255,), 4)
    pen.line([(x + 108, y - 26), (x + 108, y + 8)], PAL["wood_d"] + (255,), 4)
    pen.rect((x, y, x + 126, y + 166), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 3)
    pen.rect((x + 8, y + 8, x + 118, y + 158), PAL["paper_l"] + (255,), PAL["ink_soft"] + (200,), 1.4)
    # texto vertical simulado
    for col in range(3):
        for i in range(7):
            w2 = 12 if (i + col) % 4 else 18
            pen.rect((x + 18 + col * 32, y + 18 + i * 18, x + 18 + col * 32 + w2,
                      y + 24 + i * 18), PAL["ink_soft"] + (210,))
    # sello rojo
    pen.rect((x + 20, y + 136, x + 52, y + 152), PAL["vermillion"] + (255,))
    pen.rect((x + 24, y + 140, x + 34, y + 148), PAL["paper_l"] + (220,))
    return img


def obj_guard():
    img = new_rgba()
    pen = Pen(img)
    x, y = 884, 386
    pen.ellipse((x + 2, 636, x + 136, 668), (18, 16, 16, 100))
    # lanza
    pen.line([(x + 24, y - 54), (x + 38, y + 250)], PAL["wood_d"] + (255,), 4)
    pen.poly([(x + 24, y - 92), (x + 38, y - 48), (x + 12, y - 46)],
             (198, 200, 204, 255), PAL["ink"] + (255,))
    # cuerpo / armadura
    pen.poly([(x + 38, y + 66), (x + 98, y + 66), (x + 114, y + 194),
              (x + 96, y + 244), (x + 44, y + 244), (x + 22, y + 194)],
             (52, 58, 74, 255), PAL["ink"] + (255,))
    for i in range(3):
        pen.line([(x + 34, y + 100 + i * 36), (x + 102, y + 100 + i * 36)],
                 PAL["ink"] + (210,), 3)
    pen.rect((x + 32, y + 156, x + 106, y + 178), PAL["vermillion"] + (255,),
             PAL["ink"] + (255,), 1.4)
    # hombreras
    pen.ellipse((x + 16, y + 58, x + 62, y + 94), (66, 72, 90, 255), PAL["ink"] + (255,), 2)
    pen.ellipse((x + 76, y + 58, x + 122, y + 94), (66, 72, 90, 255), PAL["ink"] + (255,), 2)
    # cabeza y casco
    pen.ellipse((x + 50, y + 20, x + 92, y + 64), PAL["skin"] + (255,), PAL["ink"] + (255,), 2)
    pen.ellipse((x + 34, y + 2, x + 108, y + 48), (44, 48, 60, 255), PAL["ink"] + (255,), 2.4)
    pen.poly([(x + 34, y + 24), (x + 16, y + 44), (x + 38, y + 42)], (44, 48, 60, 255),
             PAL["ink"] + (255,))
    pen.poly([(x + 108, y + 24), (x + 128, y + 44), (x + 104, y + 42)], (44, 48, 60, 255),
             PAL["ink"] + (255,))
    pen.rect((x + 48, y + 36, x + 96, y + 46), (30, 32, 42, 255), PAL["ink"] + (255,), 1)
    pen.line([(x + 60, y + 56), (x + 84, y + 56)], PAL["ink_soft"] + (220,), 2)
    # brazos
    pen.line([(x + 36, y + 104), (x + 28, y + 176)], PAL["ink"] + (255,), 15)
    pen.line([(x + 102, y + 104), (x + 112, y + 174)], PAL["ink"] + (255,), 15)
    return img


def obj_guard_eating():
    img = new_rgba()
    pen = Pen(img)
    x, y = 900, 452
    pen.ellipse((x - 4, 628, x + 142, 660), (18, 16, 16, 100))
    # guardia sentado
    pen.poly([(x + 30, y + 60), (x + 100, y + 60), (x + 120, y + 150),
              (x + 22, y + 152)], (52, 58, 74, 255), PAL["ink"] + (255,))
    pen.poly([(x + 26, y + 136), (x + 104, y + 136), (x + 128, y + 178),
              (x + 14, y + 178)], (66, 72, 90, 255), PAL["ink"] + (255,))
    pen.line([(x + 22, y + 156), (x + 4, y + 178)], PAL["ink"] + (255,), 12)
    pen.line([(x + 118, y + 152), (x + 136, y + 178)], PAL["ink"] + (255,), 12)
    # cabeza
    pen.ellipse((x + 48, y + 10, x + 94, y + 58), PAL["skin"] + (255,), PAL["ink"] + (255,), 2)
    pen.ellipse((x + 34, y - 6, x + 108, y + 36), (44, 48, 60, 255), PAL["ink"] + (255,), 2)
    pen.line([(x + 50, y + 10), (x + 92, y + 10)], PAL["ink"] + (255,), 5)
    # pescado en la mano
    pen.line([(x + 96, y + 86), (x + 126, y + 110)], PAL["skin"] + (255,), 8)
    pen.poly([(x + 120, y + 100), (x + 158, y + 108), (x + 130, y + 126)],
             PAL["indigo_l"] + (255,), PAL["ink"] + (255,))
    pen.ellipse((x + 128, y + 108, x + 134, y + 114), PAL["paper"] + (240,))
    return img


def obj_door():
    img = new_rgba()
    pen = Pen(img)
    x, y = 1022, 356
    pen.rect((x, y + 244, x + 190, y + 268), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2)
    pen.rect((x - 6, y + 236, x + 196, y + 248), PAL["wood_l"] + (255,), PAL["ink"] + (255,), 2)
    pen.rect((x, y, x + 190, y + 242), PAL["ink"] + (255,))
    # panel corredizo entreabierto
    pen.rect((x + 10, y + 12, x + 92, y + 236), PAL["wood"] + (255,), PAL["ink"] + (255,), 2)
    for i in range(7):
        pen.line([(x + 16, y + 30 + i * 29), (x + 86, y + 30 + i * 29)],
                 PAL["wood_d"] + (190,), 1.2)
    pen.rect((x + 92, y + 12, x + 104, y + 236), PAL["gold"] + (255,))
    soft_glow(img, x + 100, y + 124, 80, (255, 196, 110), 55)
    # panel derecho cerrado
    pen.rect((x + 104, y + 12, x + 180, y + 236), (118, 84, 54, 255), PAL["ink"] + (255,), 2)
    for i in range(5):
        pen.line([(x + 110, y + 36 + i * 40), (x + 174, y + 36 + i * 40)],
                 PAL["wood_d"] + (180,), 1.2)
    # noren
    pen.rect((x - 8, y - 8, x + 198, y + 40), PAL["indigo"] + (255,), PAL["ink"] + (255,), 2.4)
    for i in range(1, 6):
        pen.line([(x - 8 + i * 34, y - 8), (x - 8 + i * 34, y + 40)], PAL["prussian"] + (220,), 1.4)
    pen.ellipse((x + 78, y + 2, x + 118, y + 32), None, PAL["paper"] + (235,), 2)
    pen.ellipse((x + 88, y + 8, x + 108, y + 26), PAL["paper"] + (235,))
    return img


def obj_merchant():
    img = new_rgba()
    pen = Pen(img)
    x, y = 742, 356
    pen.ellipse((x - 10, 644, x + 224, 680), (26, 22, 18, 95))
    # abrigo largo índigo
    pen.poly([(x + 44, y + 78), (x + 146, y + 78), (x + 166, y + 232),
              (x + 138, y + 286), (x + 48, y + 286), (x + 20, y + 232)],
             (54, 74, 102, 255), PAL["ink"] + (255,))
    pen.poly([(x + 44, y + 78), (x + 96, y + 78), (x + 92, y + 284),
              (x + 48, y + 284), (x + 20, y + 232)], (68, 90, 120, 255))
    pen.line([(x + 96, y + 82), (x + 96, y + 284)], PAL["ink"] + (170,), 1.6)
    # botones dorados
    for i in range(4):
        pen.ellipse((x + 52 + i * 24, y + 120, x + 66 + i * 24, y + 134),
                    PAL["gold"] + (245,), PAL["ink"] + (180,), 1)
    # fajín bermellón
    pen.rect((x + 24, y + 200, x + 160, y + 224), PAL["vermillion"] + (245,),
             PAL["ink"] + (255,), 1.4)
    # cuello alto de encaje
    pen.poly([(x + 54, y + 70), (x + 134, y + 70), (x + 146, y + 100), (x + 42, y + 100)],
             (232, 224, 206, 255), PAL["ink"] + (255,))
    for i in range(6):
        pen.ellipse((x + 48 + i * 16, y + 80, x + 60 + i * 16, y + 94), None,
                    PAL["ink_soft"] + (120,), 1)
    # cabeza
    pen.ellipse((x + 68, y + 14, x + 122, y + 74), PAL["skin"] + (255,), PAL["ink"] + (255,), 2)
    # sombrero de ala ancha
    pen.ellipse((x + 30, y + 8, x + 160, y + 44), (62, 52, 44, 255), PAL["ink"] + (255,), 2)
    pen.ellipse((x + 60, y - 16, x + 130, y + 28), (74, 62, 52, 255), PAL["ink"] + (255,), 2)
    pen.rect((x + 58, y + 12, x + 132, y + 22), PAL["vermillion_d"] + (255,),
             PAL["ink"] + (255,), 1)
    # barba y ojos
    pen.poly([(x + 70, y + 48), (x + 120, y + 48), (x + 110, y + 76), (x + 80, y + 76)],
             (204, 160, 122, 255))
    pen.ellipse((x + 80, y + 34, x + 86, y + 39), PAL["ink"] + (255,))
    pen.ellipse((x + 104, y + 34, x + 110, y + 39), PAL["ink"] + (255,))
    pen.line([(x + 88, y + 44), (x + 104, y + 44)], PAL["skin_d"] + (180,), 1)
    # farolillo en la mano
    pen.line([(x + 158, y + 150), (x + 188, y + 220)], (54, 74, 102, 255), 8)
    soft_glow(img, x + 190, y + 238, 60, (255, 196, 110), 75)
    pen.rrect((x + 174, y + 216, x + 206, y + 262), 5, PAL["gold"] + (245,),
              PAL["ink"] + (255,), 2)
    return img


def obj_hidden():
    img = new_rgba()
    pen = Pen(img)
    x, y = 218, 456
    pen.ellipse((x - 6, 636, x + 140, 666), (26, 22, 18, 90))
    # figura agachada, ropa de campesino
    pen.ellipse((x + 28, y + 28, x + 94, y + 100), (120, 100, 80, 255), PAL["ink"] + (255,), 2)
    pen.poly([(x + 22, y + 88), (x + 106, y + 82), (x + 126, y + 172),
              (x + 18, y + 176)], (126, 106, 84, 255), PAL["ink"] + (255,))
    pen.poly([(x + 38, y + 152), (x + 112, y + 152), (x + 106, y + 210),
              (x + 46, y + 210)], (104, 86, 68, 255), PAL["ink"] + (255,))
    hatch(img, [(x + 30, y + 100), (x + 112, y + 96), (x + 118, y + 168),
                (x + 24, y + 170)], PAL["ink"], step=8, width=1, alpha=55, angle=60)
    # chal crema
    pen.poly([(x + 30, y + 82), (x + 96, y + 80), (x + 88, y + 104), (x + 40, y + 108)],
             (232, 216, 184, 255), PAL["ink"] + (200,))
    # rostro
    pen.ellipse((x + 44, y + 42, x + 84, y + 86), PAL["skin"] + (255,), PAL["ink"] + (255,), 1.6)
    pen.ellipse((x + 38, y + 26, x + 92, y + 56), PAL["hair"] + (255,), PAL["ink"] + (255,), 1.2)
    pen.ellipse((x + 54, y + 58, x + 61, y + 65), PAL["paper"] + (245,))
    pen.ellipse((x + 70, y + 58, x + 77, y + 65), PAL["paper"] + (245,))
    pen.ellipse((x + 56, y + 60, x + 60, y + 64), PAL["ink"] + (255,))
    pen.ellipse((x + 72, y + 60, x + 76, y + 64), PAL["ink"] + (255,))
    pen.line([(x + 60, y + 76), (x + 74, y + 76)], PAL["ink_soft"] + (180,), 1.2)
    return img


def obj_sack():
    img = new_rgba()
    pen = Pen(img)
    x, y = 480, 556
    pen.ellipse((x - 8, y + 84, x + 150, y + 112), (26, 22, 18, 85))
    # cuerpo del saco
    pen.poly([(x + 20, y + 30), (x + 36, y + 96), (x + 70, y + 104),
              (x + 116, y + 98), (x + 130, y + 34), (x + 112, y + 12),
              (x + 40, y + 12)], PAL["ochre"] + (245,), PAL["ink"] + (255,))
    hatch(img, [(x + 30, y + 24), (x + 120, y + 24), (x + 114, y + 92),
                (x + 38, y + 92)], PAL["wood_d"], step=9, width=1, alpha=45, angle=70)
    # cuello fruncido y cuerda
    pen.poly([(x + 42, y + 12), (x + 64, y - 12), (x + 92, y - 8), (x + 112, y + 14)],
             (176, 128, 72, 255), PAL["ink"] + (255,))
    pen.line([(x + 44, y + 14), (x + 110, y + 16)], PAL["ink"] + (255,), 3)
    pen.line([(x + 46, y + 16), (x + 34, y + 30)], PAL["paper"] + (200,), 2)
    # etiqueta con sello del inspector
    pen.line([(x + 110, y + 30), (x + 130, y + 44)], PAL["paper"] + (200,), 1.4)
    pen.rect((x + 122, y + 40, x + 152, y + 66), PAL["paper_l"] + (245,),
             PAL["ink"] + (255,), 1.2)
    pen.ellipse((x + 130, y + 46, x + 146, y + 62), PAL["vermillion"] + (255,))
    pen.rect((x + 134, y + 50, x + 142, y + 58), PAL["paper_l"] + (240,))
    return img


def obj_plaque(label, x, y, w=244, h=84):
    img = new_rgba()
    pen = Pen(img)
    # cuerdas
    pen.line([(x + 26, y - 26), (x + 20, y + 4)], PAL["paper"] + (180,), 2)
    pen.line([(x + w - 26, y - 26), (x + w - 20, y + 4)], PAL["paper"] + (180,), 2)
    pen.rect((x, y, x + w, y + h), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 3)
    pen.rect((x + 8, y + 8, x + w - 8, y + h - 8), PAL["paper"] + (252,),
             PAL["ochre"] + (200,), 1.4)
    pen.text((x + w / 2, y + h / 2 - 2), label, 27, PAL["ink"] + (255,), FONT_BOLD, "mm")
    # sello
    pen.rect((x + w - 32, y + h - 30, x + w - 14, y + h - 14), PAL["vermillion"] + (235,))
    return img


# ---------------------------------------------------------------------------
# PERSONAJE
# ---------------------------------------------------------------------------
def char_frame(pose, bob=0, stride=0):
    """Haru, joven comerciante. Sprite 96x220, pies en y=205."""
    img = new_rgba(96, 220)
    pen = Pen(img)
    cx = 46
    oy = bob
    pen.ellipse((20, 196, 76, 214), (10, 9, 9, 85))

    # piernas y sandalias geta
    if stride:
        legs = ((cx - 2, 150 + oy, cx - 18, 196), (cx + 3, 150 + oy, cx + 19, 196))
    else:
        legs = ((cx - 3, 150 + oy, cx - 7, 196), (cx + 2, 150 + oy, cx + 6, 196))
    for (x0, y0, x1, y1) in legs:
        pen.line([(x0, y0), (x1, y1)], (240, 232, 214, 255), 8)
        pen.line([(x0, y0), (x1, y1)], PAL["ink"] + (150,), 1)
        pen.rect((x1 - 10, y1 - 2, x1 + 10, y1 + 6), PAL["wood_d"] + (255,),
                 PAL["ink"] + (255,), 1.4)

    # kimono indigo con patrÃ³n asanoha
    pen.poly([(cx - 27, 76 + oy), (cx + 23, 76 + oy), (cx + 34, 158 + oy),
              (cx - 34, 158 + oy)], (46, 70, 102, 255), PAL["ink"] + (255,))
    pen.poly([(cx - 27, 76 + oy), (cx - 8, 76 + oy), (cx - 4, 156 + oy),
              (cx - 34, 156 + oy)], (62, 90, 122, 255))
    # patrÃ³n
    for i in range(5):
        for j in range(3):
            px = cx - 24 + i * 12 + (6 if j % 2 else 0)
            py = 92 + j * 18 + oy
            pen.line([(px - 4, py + 4), (px, py - 4), (px + 4, py + 4)],
                     PAL["paper"] + (70,), 1)
            pen.line([(px - 4, py + 4), (px + 4, py + 4)], PAL["paper"] + (55,), 1)
    # obi bermellÃ³n
    pen.rect((cx - 30, 120 + oy, cx + 30, 144 + oy), PAL["vermillion"] + (255,),
             PAL["ink"] + (255,), 1.4)
    pen.rect((cx - 6, 120 + oy, cx + 8, 144 + oy), PAL["gold"] + (255,))
    # cuello y rostro
    pen.poly([(cx - 10, 70 + oy), (cx + 5, 70 + oy), (cx + 3, 90 + oy),
              (cx - 14, 88 + oy)], (240, 232, 214, 255))
    pen.ellipse((cx - 17, 38 + oy, cx + 19, 82 + oy), PAL["skin"] + (255,),
                PAL["ink"] + (255,), 2)
    # pelo y chonmage
    pen.ellipse((cx - 19, 30 + oy, cx + 21, 58 + oy), PAL["hair"] + (255,), PAL["ink"] + (255,), 1.4)
    pen.rect((cx - 5, 16 + oy, cx + 12, 34 + oy), PAL["hair"] + (255,), PAL["ink"] + (255,), 1.2)
    pen.rect((cx - 1, 12 + oy, cx + 9, 20 + oy), PAL["hair"] + (255,), PAL["ink"] + (255,), 1)
    # ojos
    ex = -5 if pose == "left" else 5
    pen.line([(cx + ex - 10, 56 + oy), (cx + ex - 5, 55 + oy)], PAL["ink"] + (255,), 1.6)
    pen.line([(cx + ex + 3, 55 + oy), (cx + ex + 8, 56 + oy)], PAL["ink"] + (255,), 1.6)
    pen.ellipse((cx + ex - 8, 58 + oy, cx + ex - 5, 61 + oy), PAL["ink"] + (255,))
    pen.ellipse((cx + ex + 4, 58 + oy, cx + ex + 7, 61 + oy), PAL["ink"] + (255,))
    pen.line([(cx - 2, 66 + oy), (cx + 5, 66 + oy)], PAL["skin_d"] + (200,), 1.2)

    # mangas y brazos
    if stride:
        swing = 10
    else:
        swing = 0
    pen.line([(cx + (12 if pose == "left" else -12), 88 + oy),
              (cx + (26 if pose == "left" else -26) + swing, 136 + oy)],
             PAL["ink"] + (255,), 16)
    pen.line([(cx + (12 if pose == "left" else -12), 88 + oy),
              (cx + (26 if pose == "left" else -26) + swing, 136 + oy)],
             (46, 70, 102, 255), 12)
    pen.line([(cx + (26 if pose == "left" else -26) + swing, 136 + oy),
              (cx + (30 if pose == "left" else -30) + swing, 150 + oy)],
             PAL["skin"] + (255,), 6)
    return img.resize((96, 220), Image.LANCZOS)


def cursor_arrow():
    """Cursor grande y legible: puntero de tinta con relleno crema."""
    img = new_rgba(48, 48)
    pen = Pen(img)
    pts = [(8, 6), (8, 38), (15, 30), (22, 44), (29, 41), (22, 27), (34, 26)]
    pen.poly(pts, PAL["paper_l"] + (255,), PAL["ink"] + (255,))
    # sombra interior / brillo
    pen.line([(10, 10), (10, 32)], PAL["paper"] + (120,), 2)
    pen.ellipse((31, 29, 37, 35), PAL["vermillion"] + (255,), PAL["ink"] + (255,), 1)
    return img.resize((48, 48), Image.LANCZOS)


def bg_menu():
    """Pantalla de título: cielo de amanecer, torii, mar y botones de papel."""
    img = new_rgba()
    vgrad(img, 0, 620, [(0, (22, 35, 58)), (0.3, (44, 67, 96)),
                        (0.58, (118, 116, 128)), (0.8, (212, 162, 126)),
                        (1, (241, 205, 163))])
    pen = Pen(img)

    # sol bajo
    soft_glow(img, 1000, 214, 180, (255, 218, 158), 95)
    pen.ellipse((916, 130, 1084, 298), PAL["gold"] + (238,), PAL["vermillion"] + (110,), 2)

    # nubes
    cloud(img, 210, 118, 380, 40, PAL["paper_l"] + (228,), True)
    cloud(img, 760, 84, 340, 30, PAL["rose"] + (190,), True)
    cloud(img, 520, 300, 430, 24, PAL["paper"] + (175,), True)
    cloud(img, 1030, 336, 300, 22, PAL["paper_l"] + (150,), True)

    # montañas
    mountain(img, [(0, 540), (0, 452), (140, 418), (300, 448), (470, 414),
                   (650, 446), (820, 416), (1000, 444), (1160, 418),
                   (1280, 436), (1280, 540)],
             PAL["indigo"] + (255,), PAL["prussian"])
    mountain(img, [(0, 540), (0, 492), (190, 472), (380, 496), (600, 478),
                   (820, 498), (1040, 480), (1280, 492), (1280, 540)],
             PAL["prussian"] + (255,), PAL["ink_soft"])

    # mar
    vgrad(img, 508, 624, [(0, (40, 64, 90)), (0.6, (30, 52, 76)), (1, (23, 42, 62))])
    seigaiha(img, -40, 514, W + 40, 622, PAL["prussian"], PAL["indigo_p"], r=28, alpha=115)
    seigaiha(img, -40, 566, W + 40, 622, PAL["prussian"], PAL["paper"], r=19, alpha=45)

    # isla de Dejima al fondo derecha
    pen = Pen(img)
    pen.poly([(1040, 520), (1090, 486), (1160, 478), (1220, 492), (1280, 500),
              (1280, 522)], PAL["ink"] + (205,), PAL["ink"] + (255,))
    pen.rect((1170, 470, 1196, 494), PAL["ink"] + (215,), PAL["ink"] + (255,), 1.5)
    pen.poly([(1166, 470), (1200, 470), (1194, 460), (1172, 460)],
             PAL["ink"] + (215,), PAL["ink"] + (255,))

    # torii a la izquierda
    tx, ty = 176, 296
    pen.rect((tx - 74, ty, tx - 52, ty + 334), PAL["vermillion"] + (245,), PAL["ink"] + (255,), 2.5)
    pen.rect((tx + 52, ty, tx + 74, ty + 334), PAL["vermillion"] + (245,), PAL["ink"] + (255,), 2.5)
    pen.poly([(tx - 128, ty - 26), (tx + 128, ty - 26), (tx + 118, ty + 4), (tx - 118, ty + 4)],
             PAL["vermillion_d"] + (255,), PAL["ink"] + (255,))
    pen.poly([(tx - 104, ty + 4), (tx + 104, ty + 4), (tx + 100, ty + 22), (tx - 100, ty + 22)],
             PAL["vermillion"] + (250,), PAL["ink"] + (255,))
    pen.rect((tx - 86, ty + 128, tx + 86, ty + 148), PAL["vermillion"] + (245,), PAL["ink"] + (255,), 2)
    # sombra del torii en el agua
    pen.rect((tx - 74, ty + 334, tx - 52, ty + 372), PAL["vermillion_d"] + (70,))
    pen.rect((tx + 52, ty + 334, tx + 74, ty + 372), PAL["vermillion_d"] + (70,))

    # muelle
    pen.rect((0, 620, W, H), PAL["wood"] + (255,))
    pen.rect((0, 620, W, 634), PAL["wood_l"] + (255,), PAL["ink"] + (255,), 2)
    for y in range(644, H, 30):
        pen.line([(0, y), (W, y)], PAL["wood_d"] + (130,), 1.4)
    for x in range(-40, W + 60, 132):
        pen.line([(x, 632), (x + 46, H)], PAL["wood_d"] + (105,), 1.2)
    pen.line([(0, 620), (W, 620)], PAL["ink"] + (255,), 3)

    # ---------------- título ----------------
    d = ImageDraw.Draw(img)
    f_title = ImageFont.truetype(FONT_BOLD, sc(98))
    f_year = ImageFont.truetype(FONT_BOLD, sc(74))
    f_sub = ImageFont.truetype(FONT_BOLD, sc(23))
    d.text((sc(640), sc(112)), "NAGASAKI", font=f_title,
           fill=PAL["paper_l"] + (255,), anchor="mm",
           stroke_width=sc(4), stroke_fill=PAL["ink"] + (255,))
    d.text((sc(640), sc(212)), "1641", font=f_year,
           fill=PAL["vermillion"] + (255,), anchor="mm",
           stroke_width=sc(4), stroke_fill=PAL["ink"] + (255,))
    d.text((sc(640), sc(292)), "EL SELLO DE DEJIMA", font=f_sub,
           fill=PAL["paper_l"] + (240,), anchor="mm",
           stroke_width=sc(2), stroke_fill=PAL["ink"] + (200,))

    # ---------------- botones ----------------
    f_btn = ImageFont.truetype(FONT_BOLD, sc(30))
    buttons = [((440, 396, 840, 462), "NUEVA PARTIDA"),
               ((440, 486, 840, 552), "SALIR")]
    for (x0, y0, x1, y1), label in buttons:
        pen.rrect((x0, y0, x1, y1), 12, PAL["paper_l"] + (242,), PAL["ink"] + (255,), 3)
        pen.rrect((x0 + 12, y0 + 8, x1 - 12, y1 - 8), 8, None, PAL["ink_soft"] + (90,), 1)
        pen.rect((x0, y0, x0 + 12, y1), PAL["vermillion"] + (245,))
        d.text((sc((x0 + x1) // 2 + 6), sc((y0 + y1) // 2)), label, font=f_btn,
               fill=PAL["ink"] + (255,), anchor="mm")

    # instrucciones y crédito
    f_small = ImageFont.truetype(FONT_REG, sc(17))
    f_tiny = ImageFont.truetype(FONT_REG, sc(14))
    d.text((sc(640), sc(594)),
           "Haz clic en el suelo para caminar · Haz clic en personas y objetos para interactuar",
           font=f_small, fill=PAL["paper_l"] + (225,), anchor="mm",
           stroke_width=sc(2), stroke_fill=PAL["ink"] + (170,))
    d.text((sc(640), sc(692)), "Prototipo ukiyo-e · Visionaire Studio 5",
           font=f_tiny, fill=PAL["paper"] + (190,), anchor="mm",
           stroke_width=sc(1), stroke_fill=PAL["ink"] + (120,))

    cartouche(img, 30, 30, 34, 206, "DEJIMA")
    seal_stamp(img, 32, 250, 30, "1641")

    img = washi(img, 1.0)
    img = grain(img, 3)
    img = vignette(img, 0.14)
    return img.convert("RGB")


# ===========================================================================
# MUNDO NUEVO: casa, mercado, puerto y casa del pescador
# ===========================================================================
def tatami_floor(pen, img, y0=585):
    pen.rect((0, y0, W, H), (104, 116, 86, 255))
    row_h = 52
    for i, y in enumerate(range(y0, H, row_h)):
        tone = (108, 120, 88, 255) if i % 2 == 0 else (98, 110, 80, 255)
        pen.rect((0, y, W, min(y + row_h, H)), tone)
        pen.line([(0, y), (W, y)], (72, 82, 58, 255), 2)
        off = 0 if i % 2 == 0 else 160
        for x in range(off, W, 320):
            pen.line([(x, y), (x, y + row_h)], (72, 82, 58, 190), 1.4)
    # borde de tela de la estera
    pen.rect((0, y0, W, y0 + 6), (60, 68, 48, 255))


def wood_planks(pen, x0, y0, x1, y1, base, line, step=34):
    pen.rect((x0, y0, x1, y1), base + (255,))
    y = y0
    while y < y1:
        pen.line([(x0, y), (x1, y)], line + (140,), 1.4)
        y += step
    for x in range(int(x0), int(x1), 160):
        pen.line([(x, y0), (x, y1)], line + (60,), 1.0)


def draw_person(pen, cx, feet, h, kimono, hair, hat=False, bun=False):
    head_r = h * 0.115
    head_cy = feet - h + head_r * 1.3
    body_top = head_cy + head_r * 0.92
    # kimono
    pen.poly([(cx - h * 0.15, body_top), (cx + h * 0.15, body_top),
              (cx + h * 0.23, feet), (cx - h * 0.23, feet)],
             kimono + (255,), PAL["ink"] + (255,))
    # solapa
    pen.line([(cx, body_top + h * 0.02), (cx, feet - h * 0.02)],
             PAL["ink"] + (150,), 1.4)
    # obi
    pen.rect((cx - h * 0.18, feet - h * 0.36, cx + h * 0.18, feet - h * 0.29),
             PAL["vermillion_d"] + (225,))
    # cabeza
    pen.ellipse((cx - head_r, head_cy - head_r, cx + head_r, head_cy + head_r),
                PAL["skin"] + (255,), PAL["ink"] + (255,), 2)
    # pelo
    pen.poly([(cx - head_r * 1.02, head_cy - head_r * 0.1),
              (cx - head_r * 0.9, head_cy - head_r * 0.95),
              (cx, head_cy - head_r * 1.18),
              (cx + head_r * 0.9, head_cy - head_r * 0.95),
              (cx + head_r * 1.02, head_cy - head_r * 0.1)],
             hair + (255,), PAL["ink"] + (255,))
    if bun:
        pen.ellipse((cx - head_r * 0.34, head_cy - head_r * 1.42,
                     cx + head_r * 0.34, head_cy - head_r * 0.98),
                    hair + (255,), PAL["ink"] + (255,), 1.4)
    if hat:
        pen.poly([(cx - head_r * 2.3, head_cy - head_r * 0.55),
                  (cx + head_r * 2.3, head_cy - head_r * 0.55),
                  (cx, head_cy - head_r * 2.4)],
                 (150, 122, 82, 255), PAL["ink"] + (255,))
        pen.line([(cx - head_r * 2.3, head_cy - head_r * 0.55),
                  (cx + head_r * 2.3, head_cy - head_r * 0.55)], PAL["ink"] + (255,), 2)
    # ojos y boca
    eye_y = head_cy + head_r * 0.05
    pen.ellipse((cx - head_r * 0.52, eye_y, cx - head_r * 0.24, eye_y + head_r * 0.2),
                PAL["ink"] + (255,))
    pen.ellipse((cx + head_r * 0.24, eye_y, cx + head_r * 0.52, eye_y + head_r * 0.2),
                PAL["ink"] + (255,))
    pen.line([(cx - head_r * 0.22, head_cy + head_r * 0.55),
              (cx + head_r * 0.22, head_cy + head_r * 0.55)],
             PAL["ink_soft"] + (220,), 1.4)


def draw_family(pen, floor_y, cx, s):
    draw_person(pen, cx - 46 * s, floor_y, 108 * s, PAL["prussian"], PAL["hair"], hat=True)
    draw_person(pen, cx + 2 * s, floor_y, 100 * s, PAL["rose"], PAL["hair"], bun=True)
    draw_person(pen, cx + 54 * s, floor_y, 68 * s, PAL["indigo"], PAL["hair"])


def bg_home():
    img = new_rgba()
    vgrad(img, 0, 585, [(0, (236, 221, 192)), (0.55, (222, 200, 165)),
                        (1, (203, 178, 141))])
    pen = Pen(img)
    # techo y vigas
    pen.rect((0, 0, W, 48), PAL["wood_d"] + (255,))
    pen.rect((0, 48, W, 62), PAL["wood"] + (255,), PAL["ink"] + (255,), 2)
    for x in range(80, W, 160):
        pen.rect((x, 0, x + 18, 56), PAL["wood_d"] + (255,))
        pen.line([(x + 6, 0), (x + 6, 56)], PAL["wood_l"] + (70,), 1.4)
    # postes
    for x in (0, 552, 1232):
        pen.rect((x, 58, x + 24, 585), PAL["wood"] + (255,), PAL["ink"] + (210,), 2.4)
        pen.line([(x + 7, 60), (x + 7, 585)], PAL["wood_l"] + (80,), 1.6)

    # biombo shoji con luz de la calle
    pen.rect((700, 150, 960, 470), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 3)
    pen.rect((710, 160, 950, 460), PAL["paper_l"] + (255,))
    for i in range(1, 5):
        pen.line([(710 + i * 48, 160), (710 + i * 48, 460)], PAL["wood"] + (255,), 3)
    for j in range(1, 6):
        pen.line([(710, 160 + j * 50), (950, 160 + j * 50)], PAL["wood"] + (255,), 3)
    soft_glow(img, 830, 310, 190, (255, 240, 200), 55)

    # rollo colgado
    pen.rect((120, 160, 226, 420), PAL["paper"] + (250,), PAL["ink"] + (200,), 1.6)
    pen.rect((110, 150, 236, 162), PAL["wood_d"] + (255,))
    pen.rect((110, 418, 236, 430), PAL["wood_d"] + (255,))
    pen.poly([(140, 380), (176, 250), (194, 268), (214, 232), (212, 380)],
             PAL["indigo"] + (150,), PAL["ink_soft"] + (120,))
    pen.ellipse((196, 214, 220, 238), PAL["vermillion"] + (170,))

    # baúl bajo la foto
    pen.rect((255, 392, 500, 500), PAL["wood"] + (255,), PAL["ink"] + (255,), 2.4)
    pen.rect((265, 402, 490, 490), PAL["wood_d"] + (255,))
    pen.line([(377, 402), (377, 490)], PAL["wood_l"] + (120,), 1.4)
    for y in (428, 456):
        pen.line([(265, y), (490, y)], PAL["wood_l"] + (80,), 1.2)
    for x in (300, 454):
        pen.ellipse((x - 5, 440, x + 5, 450), PAL["gold"] + (235,), PAL["ink"] + (180,), 1)

    # suelo de tatami
    tatami_floor(pen, img, 585)

    # mesita baja con la nota
    pen.rect((330, 642, 610, 660), PAL["wood_l"] + (255,), PAL["ink"] + (255,), 2.4)
    pen.line([(344, 660), (344, 706)], PAL["wood_d"] + (255,), 8)
    pen.line([(596, 660), (596, 706)], PAL["wood_d"] + (255,), 8)
    pen.rect((320, 630, 620, 644), PAL["wood"] + (255,), PAL["ink"] + (200,), 1.6)

    # puerta corredera a la calle (derecha)
    pen.rect((1040, 150, 1212, 585), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 3)
    pen.rect((1054, 164, 1198, 571), PAL["paper"] + (255,))
    for i in range(1, 4):
        pen.line([(1054 + i * 48, 164), (1054 + i * 48, 571)], PAL["wood"] + (255,), 3)
    for j in range(1, 8):
        pen.line([(1054, 164 + j * 56), (1198, 164 + j * 56)], PAL["wood"] + (255,), 3)
    pen.ellipse((1124, 360, 1142, 378), PAL["gold"] + (230,), PAL["ink"] + (200,), 1.4)
    soft_glow(img, 1126, 430, 90, (255, 232, 180), 45)

    # cojín
    pen.ellipse((640, 664, 760, 704), (150, 62, 52, 235), PAL["ink"] + (220,), 2)
    pen.ellipse((652, 672, 748, 696), None, PAL["vermillion_d"] + (180,), 1.2)

    cartouche(img, 30, 30, 34, 196, "CASA")
    img = washi(img, 0.9)
    img = grain(img, 3)
    img = vignette(img, 0.12)
    return img.convert("RGB")


def bg_street():
    img = new_rgba()
    vgrad(img, 0, 540, [(0, (34, 52, 78)), (0.32, (74, 98, 126)),
                        (0.62, (170, 152, 138)), (0.84, (226, 184, 140)),
                        (1, (240, 210, 170))])
    pen = Pen(img)
    soft_glow(img, 1000, 320, 150, (255, 220, 160), 85)
    pen.ellipse((940, 260, 1060, 380), PAL["gold"] + (235,), PAL["vermillion"] + (110,), 2)
    cloud(img, 220, 150, 360, 40, PAL["paper_l"] + (228,), True)
    cloud(img, 760, 110, 340, 32, PAL["rose"] + (190,), True)

    # montañas y tejados lejanos
    mountain(img, [(0, 470), (0, 402), (160, 372), (340, 404), (520, 366),
                   (700, 400), (880, 370), (1060, 402), (1280, 376), (1280, 470)],
             PAL["indigo"] + (240,), PAL["prussian"])
    for x in range(-30, W, 190):
        pen.rect((x, 430, x + 170, 530), (96, 84, 72, 255), PAL["ink"] + (180,), 1.4)
        pen.poly([(x - 12, 432), (x + 85, 398), (x + 182, 432)],
                 (66, 74, 84, 255), PAL["ink"] + (200,))
        pen.line([(x + 16, 454), (x + 60, 454)], (232, 206, 160, 150), 2)
        pen.line([(x + 16, 472), (x + 60, 472)], (232, 206, 160, 120), 2)

    # calle empedrada
    pen.rect((0, 520, W, H), (176, 152, 120, 255))
    for row, y in enumerate(range(538, H, 38)):
        off = (row % 2) * 62
        for x in range(-62 + off, W, 124):
            pen.rrect((x, y, x + 110, y + 30), 7, (188, 164, 130, 255),
                      (120, 100, 76, 150), 1.2)
    pen.rect((0, 520, W, 528), (120, 100, 76, 255))

    # pozo en el centro
    pen.ellipse((588, 452, 712, 512), (128, 126, 120, 255), PAL["ink"] + (255,), 3)
    pen.ellipse((604, 462, 696, 502), (42, 46, 48, 255), PAL["ink"] + (255,), 2)
    pen.line([(606, 470), (606, 544)], PAL["wood_d"] + (255,), 6)
    pen.line([(694, 470), (694, 544)], PAL["wood_d"] + (255,), 6)
    pen.poly([(584, 470), (650, 436), (716, 470), (700, 480), (650, 452), (600, 480)],
             PAL["wood_d"] + (255,), PAL["ink"] + (255,))
    pen.rect((640, 480, 660, 512), PAL["wood_l"] + (255,), PAL["ink"] + (255,), 1.4)

    # farolillos colgados
    pen.line([(0, 118), (W, 118)], PAL["ink_soft"] + (170,), 2)
    for x in range(150, W, 240):
        pen.line([(x, 118), (x, 156)], PAL["ink_soft"] + (160,), 1.6)
        soft_glow(img, x, 180, 45, (255, 196, 120), 50)
        pen.rrect((x - 18, 152, x + 18, 206), 10, PAL["vermillion"] + (235,),
                  PAL["ink"] + (255,), 2)
        pen.line([(x - 16, 168), (x + 16, 168)], PAL["vermillion_d"] + (220,), 2)
        pen.line([(x - 16, 190), (x + 16, 190)], PAL["vermillion_d"] + (220,), 2)

    # casa de Haru, en el centro de la calle: fachada de machiya con puerta
    pen.rect((392, 428, 588, 566), (206, 186, 152, 255), PAL["ink"] + (255,), 2.2)
    pen.poly([(370, 432), (490, 382), (610, 432)], (62, 70, 84, 255),
             PAL["ink"] + (255,))
    pen.rect((370, 428, 610, 446), (74, 82, 94, 255), PAL["ink"] + (220,), 1.6)
    # celosías a los lados
    for lx in (404, 556):
        pen.rect((lx, 470, lx + 26, 552), PAL["wood_d"] + (255,),
                 PAL["ink"] + (215,), 1.4)
        for ly in range(478, 552, 12):
            pen.line([(lx + 3, ly), (lx + 23, ly)], PAL["wood_l"] + (150,), 1.2)
    # puerta corredera (la zona clicable "volver_casa")
    pen.rect((466, 448, 548, 560), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2.6)
    pen.rect((476, 458, 538, 552), (54, 44, 34, 255))
    for dx in range(484, 538, 18):
        pen.line([(dx, 458), (dx, 552)], PAL["wood_l"] + (120,), 1.2)
    pen.line([(507, 458), (507, 552)], PAL["wood_d"] + (255,), 2)
    # noren con el sello de la casa
    pen.rect((462, 448, 552, 480), PAL["indigo"] + (240,), PAL["ink"] + (230,), 1.6)
    pen.ellipse((494, 456, 520, 476), PAL["paper_l"] + (240,))
    pen.rect((500, 461, 514, 471), PAL["vermillion"] + (220,))

    cartouche(img, 30, 30, 34, 206, "CALLE")
    img = washi(img, 1.0)
    img = grain(img, 3)
    img = vignette(img, 0.13)
    return img.convert("RGB")


def bg_port():
    img = new_rgba()
    vgrad(img, 0, 420, [(0, (28, 44, 68)), (0.4, (64, 88, 118)),
                        (0.72, (150, 142, 140)), (1, (232, 190, 146))])
    pen = Pen(img)
    soft_glow(img, 300, 300, 160, (255, 220, 160), 75)
    pen.ellipse((230, 232, 370, 372), PAL["gold"] + (235,), PAL["vermillion"] + (110,), 2)
    cloud(img, 900, 120, 400, 36, PAL["paper_l"] + (220,), True)
    cloud(img, 460, 190, 320, 30, PAL["rose"] + (180,), True)

    # mar
    vgrad(img, 410, 600, [(0, (52, 82, 110)), (0.7, (34, 60, 86)), (1, (26, 48, 70))])
    seigaiha(img, -40, 414, W + 40, 600, PAL["prussian"], PAL["indigo_p"], r=28, alpha=120)
    seigaiha(img, -40, 470, W + 40, 600, PAL["prussian"], PAL["paper"], r=18, alpha=45)

    # gaviotas
    for gx, gy, gs in ((420, 150, 1.0), (490, 200, 0.7), (560, 140, 0.85)):
        pen.line([(gx - 12 * gs, gy), (gx, gy - 7 * gs), (gx + 12 * gs, gy)],
                 PAL["ink_soft"] + (210,), 1.6)

    # almacenes al fondo izquierda
    pen.poly([(0, 560), (0, 360), (120, 320), (300, 330), (390, 380), (390, 560)],
             (78, 70, 62, 255), PAL["ink"] + (220,))
    pen.poly([(-10, 366), (130, 306), (330, 322), (400, 372)],
             (56, 62, 72, 255), PAL["ink"] + (240,))
    for x in (70, 180, 290):
        pen.rect((x, 430, x + 70, 560), (52, 46, 42, 255), PAL["ink"] + (200,), 1.6)
    pen.rect((40, 400, 360, 424), PAL["wood_d"] + (255,), PAL["ink"] + (200,), 1.4)

    # barco holandés
    hull = [(770, 430), (1130, 430), (1180, 470), (1100, 500), (800, 500), (730, 466)]
    pen.poly(hull, PAL["wood_d"] + (255,), PAL["ink"] + (255,))
    pen.line([(780, 458), (1140, 458)], PAL["wood_l"] + (120,), 2)
    for mx, top in ((860, 210), (990, 170), (1090, 230)):
        pen.line([(mx, 430), (mx, top)], PAL["wood_d"] + (255,), 4)
    pen.poly([(864, 236), (992, 200), (992, 386), (864, 400)],
             PAL["paper_l"] + (240,), PAL["ink"] + (200,))
    pen.poly([(996, 206), (1086, 246), (1086, 380), (996, 386)],
             PAL["cream"] + (235,), PAL["ink"] + (200,))
    pen.line([(864, 330), (992, 316)], PAL["ink_soft"] + (90,), 1.4)
    pen.line([(996, 320), (1086, 330)], PAL["ink_soft"] + (90,), 1.4)
    pen.poly([(1090, 246), (1150, 268), (1090, 280)], PAL["vermillion"] + (225,),
             PAL["ink"] + (200,))
    pen.poly([(860, 214), (900, 224), (860, 234)], PAL["indigo"] + (220,),
             PAL["ink"] + (180,))

    # muelle de madera
    wood_planks(pen, 0, 592, W, H, PAL["wood"], PAL["wood_d"], 30)
    pen.rect((0, 592, W, 602), PAL["wood_l"] + (255,), PAL["ink"] + (255,), 2)
    for x in range(40, W, 150):
        pen.rect((x, 596, x + 16, H), PAL["wood_d"] + (130,))

    # cajas del muelle
    for bx, by, bw, bh in ((190, 486, 92, 84), (286, 502, 78, 70),
                           (236, 408, 72, 64), (330, 424, 62, 58)):
        pen.rect((bx, by, bx + bw, by + bh), PAL["wood"] + (255,), PAL["ink"] + (255,), 2)
        pen.line([(bx, by), (bx + bw, by + bh)], PAL["wood_d"] + (120,), 1.6)
        pen.line([(bx + bw, by), (bx, by + bh)], PAL["wood_d"] + (120,), 1.6)
        pen.rect((bx + bw // 2 - 7, by + bh // 2 - 7, bx + bw // 2 + 7, by + bh // 2 + 7),
                 PAL["paper_l"] + (210,), PAL["ink"] + (160,), 1)

    # cabaña del pescador (derecha)
    pen.rect((1086, 262, 1280, 590), (96, 78, 58, 255), PAL["ink"] + (240,), 3)
    pen.poly([(1070, 272), (1188, 210), (1290, 268)], (62, 66, 72, 255),
             PAL["ink"] + (240,))
    pen.rect((1122, 300, 1236, 552), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2)
    pen.rect((1132, 310, 1226, 546), (52, 42, 34, 255))
    pen.rect((1122, 300, 1236, 352), PAL["indigo"] + (235,), PAL["ink"] + (230,), 1.6)
    for i in range(3):
        pen.line([(1122 + i * 38, 300), (1122 + i * 38, 352)], PAL["paper"] + (140,), 1.4)
    soft_glow(img, 1180, 380, 90, (255, 200, 130), 55)
    soft_glow(img, 1130, 300, 70, (255, 196, 120), 45)
    pen.rrect((1092, 292, 1116, 330), 6, PAL["vermillion"] + (235,), PAL["ink"] + (255,), 2)

    cartouche(img, 30, 30, 34, 206, "PUERTO")
    img = washi(img, 1.0)
    img = grain(img, 3)
    img = vignette(img, 0.13)
    return img.convert("RGB")


def bg_fisher():
    img = new_rgba()
    wood_planks(Pen(img), 0, 0, W, 600, (128, 98, 66), (84, 60, 40), 32)
    pen = Pen(img)
    # techo
    pen.rect((0, 0, W, 54), (76, 56, 38, 255), PAL["ink"] + (255,), 2)
    for x in range(30, W, 110):
        pen.line([(x, 0), (x, 54)], (58, 42, 30, 255), 2)
    # ventana al mar
    pen.rect((468, 168, 674, 356), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 3)
    pen.rect((472, 172, 670, 272), (104, 136, 160, 255))
    pen.rect((472, 272, 670, 352), (44, 72, 98, 255))
    seigaiha(img, 472, 300, 670, 352, PAL["prussian"], PAL["paper"], r=12, alpha=90)
    pen.line([(520, 300), (600, 300)], PAL["wood_d"] + (255,), 3)
    pen.poly([(540, 300), (560, 268), (580, 300)], PAL["paper"] + (235,),
             PAL["ink"] + (200,))
    for i in range(1, 3):
        pen.line([(468 + i * 69, 168), (468 + i * 69, 356)], PAL["wood"] + (255,), 3)
    pen.line([(468, 262), (674, 262)], PAL["wood"] + (255,), 3)

    # puerta a la izquierda
    pen.rect((26, 236, 206, 600), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 3)
    pen.rect((38, 248, 194, 590), (54, 44, 34, 255))
    pen.rect((38, 248, 194, 320), PAL["paper"] + (230,))
    pen.line([(38, 320), (194, 320)], PAL["wood_d"] + (255,), 3)
    soft_glow(img, 120, 380, 95, (255, 224, 170), 55)

    # suelo
    wood_planks(pen, 0, 600, W, H, (112, 84, 56), (74, 52, 34), 26)
    pen.rect((0, 600, W, 608), PAL["wood_d"] + (255,))

    # estante con vasijas
    pen.rect((1000, 220, 1220, 236), PAL["wood_d"] + (255,), PAL["ink"] + (200,), 1.6)
    for px, ph in ((1022, 40), (1060, 54), (1102, 34)):
        pen.poly([(px, 220), (px + 22, 220), (px + 18, 220 - ph), (px + 4, 220 - ph)],
                 (118, 92, 66, 255), PAL["ink"] + (220,))

    # hogar
    pen.ellipse((520, 520, 640, 584), (120, 118, 112, 255), PAL["ink"] + (230,), 2)
    pen.ellipse((548, 534, 612, 570), (52, 40, 34, 255))
    soft_glow(img, 580, 546, 60, (255, 154, 80), 70)

    cartouche(img, 30, 30, 34, 196, "PESCA")
    img = washi(img, 0.95)
    img = grain(img, 3)
    img = vignette(img, 0.16)
    return img.convert("RGB")


def bg_castle():
    """Patio de ejecución al pie del castillo del Shogun, con escalinata."""
    img = new_rgba()
    vgrad(img, 0, 566, [(0, (28, 32, 52)), (0.26, (58, 56, 78)),
                        (0.50, (126, 88, 78)), (0.76, (204, 138, 98)),
                        (1, (238, 186, 132))])
    pen = Pen(img)

    # sol bajo y nubes rasgadas
    soft_glow(img, 1064, 356, 190, (255, 150, 90), 105)
    pen.ellipse((970, 262, 1158, 450), (214, 94, 62, 240), (150, 56, 40, 220), 2.2)
    cloud(img, 210, 116, 420, 34, (240, 216, 188, 215), True)
    cloud(img, 760, 80, 380, 28, (226, 172, 150, 195), True)
    cloud(img, 1180, 190, 300, 24, (242, 208, 172, 175), True)

    # montañas lejanas
    mountain(img, [(0, 500), (0, 418), (150, 388), (300, 424), (470, 386),
                   (660, 420), (820, 384), (1010, 416), (1180, 388),
                   (1280, 418), (1280, 500)],
             (56, 64, 82, 235), PAL["prussian"])

    # muralla de piedra (ishigaki) sobre la que se alza el castillo
    pen.poly([(0, 436), (W, 436), (W, 566), (0, 566)], (112, 104, 96, 255),
             PAL["ink"] + (235,))
    for i in range(4):
        y = 452 + i * 30
        pen.line([(0, y), (W, y)], (72, 66, 60, 130), 1.4)
        for x in range(-46 + (i % 2) * 46, W, 92):
            pen.line([(x, y), (x + 8, y + 30)], (72, 66, 60, 80), 1.2)
    pen.rect((0, 430, W, 444), (78, 72, 66, 255), PAL["ink"] + (225,), 1.8)

    # torreón: tres cuerpos con tejados
    for x0, y0, x1, y1 in ((530, 350, 1000, 444), (580, 288, 950, 350),
                           (630, 232, 900, 288)):
        pen.rect((x0, y0, x1, y1), (232, 222, 200, 255), PAL["ink"] + (215,), 1.8)
        for x in range(x0 + 26, x1 - 16, 48):
            pen.rect((x, y0 + 16, x + 20, y1 - 12), (58, 52, 46, 235))
        pen.poly([(x0 - 58, y0 + 10), (x0 - 20, y0 - 32), (x1 + 20, y0 - 32),
                  (x1 + 58, y0 + 10), (x1 + 32, y0 + 18), (x0 - 32, y0 + 18)],
                 (52, 62, 78, 255), PAL["ink"] + (245,))
        pen.line([(x0 - 48, y0 - 14), (x1 + 48, y0 - 14)],
                 PAL["indigo_p"] + (110,), 1.6)
        pen.rect((x0 - 66, y0 + 8, x0 - 50, y0 + 24), PAL["gold"] + (230,),
                 PAL["ink"] + (220,), 1.2)
        pen.rect((x1 + 50, y0 + 8, x1 + 66, y0 + 24), PAL["gold"] + (230,),
                 PAL["ink"] + (220,), 1.2)

    # remate del torreón
    pen.poly([(730, 202), (765, 160), (800, 202)], PAL["gold"] + (240,),
             PAL["ink"] + (230,))
    pen.line([(765, 160), (765, 136)], PAL["ink"] + (230,), 2.4)

    # público en lo alto de la muralla
    rng = random.Random(11)
    for i in range(9):
        x = 96 + i * 46 + rng.randint(-6, 6)
        hh = rng.choice([58, 64, 70])
        col = (50, 48, 50, 240)
        pen.poly([(x - 16, 434), (x + 16, 434), (x + 11, 434 - hh),
                  (x - 11, 434 - hh)], col, None)
        pen.ellipse((x - 8, 434 - hh - 20, x + 8, 434 - hh + 1), col, None)
    # patio de grava
    pen.rect((0, 566, W, H), (176, 166, 148, 255))
    pen.rect((0, 566, W, 576), (118, 110, 98, 255))
    for row in range(6):
        y = 592 + row * 26
        off = (row % 2) * 34
        for x in range(-34 + off, W, 68):
            pen.line([(x, y), (x + 22, y)], (150, 140, 124, 90), 1)

    # pretiles de la escalinata
    top_l, top_r, bot_l, bot_r = 706, 824, 640, 930
    top_y, bot_y, steps = 444, 708, 9
    pen.poly([(top_l - 30, top_y), (top_l, top_y), (bot_l, bot_y),
              (bot_l - 40, bot_y)], (134, 124, 112, 255), PAL["ink"] + (215,))
    pen.poly([(top_r, top_y), (top_r + 30, top_y), (bot_r + 40, bot_y),
              (bot_r, bot_y)], (134, 124, 112, 255), PAL["ink"] + (215,))

    # escalones hacia la puerta del castillo
    for i in range(steps):
        t0, t1 = i / steps, (i + 1) / steps
        y0 = top_y + (bot_y - top_y) * t0
        y1 = top_y + (bot_y - top_y) * t1
        l0 = top_l + (bot_l - top_l) * t0
        r0 = top_r + (bot_r - top_r) * t0
        l1 = top_l + (bot_l - top_l) * t1
        r1 = top_r + (bot_r - top_r) * t1
        k = 172 - i * 4
        pen.poly([(l0, y0), (r0, y0), (r1, y1), (l1, y1)],
                 (k, k - 8, k - 22, 255), (86, 78, 70, 130))
        pen.line([(l1, y1), (r1, y1)], (86, 78, 70, 200), 1.8)

    # guardias flanqueando la escalinata
    for gx, gs in ((664, 1.0), (880, 1.0)):
        draw_person(pen, gx, 446, 82 * gs, (54, 62, 82), PAL["hair"], hat=True)
        pen.line([(gx + 26, 356), (gx + 26, 444)], PAL["wood_d"] + (255,), 2.6)
        pen.poly([(gx + 26, 356), (gx + 36, 370), (gx + 26, 384)],
                 (176, 182, 190, 255), PAL["ink"] + (230,))

    # puerta del castillo al final de la escalinata
    pen.rect((716, 386, 814, 446), (40, 34, 30, 255), PAL["ink"] + (240,), 2.4)
    pen.poly([(698, 390), (765, 354), (832, 390)], (52, 62, 78, 255),
             PAL["ink"] + (240,))
    pen.line([(765, 446), (765, 394)], (86, 74, 58, 150), 1.6)

    # público en primer plano, a la derecha
    for i in range(4):
        x = 1092 + i * 44 + rng.randint(-5, 5)
        hh = rng.choice([92, 98, 104])
        col = (44, 42, 46, 245)
        pen.poly([(x - 20, 720), (x + 20, 720), (x + 14, 720 - hh),
                  (x - 14, 720 - hh)], col, None)
        pen.ellipse((x - 9, 720 - hh - 20, x + 9, 720 - hh + 2), col, None)
        pen.line([(x - 15, 720 - hh + 10), (x + 15, 720 - hh + 10)],
                 (26, 24, 26, 190), 1.3)

    # estandartes (nobori) a los lados
    for bx, s in ((96, 1), (1180, -1)):
        pen.rect((bx, 250, bx + 8, 700), PAL["wood_d"] + (255,),
                 PAL["ink"] + (220,), 1.4)
        pen.poly([(bx + 8, 266), (bx + 8 + 76 * s, 282),
                  (bx + 8 + 80 * s, 470), (bx + 8, 484)],
                 PAL["vermillion_d"] + (245,), PAL["ink"] + (235,))
        mx0, mx1 = bx + 8 + 28 * s, bx + 8 + 56 * s
        pen.ellipse((min(mx0, mx1), 336, max(mx0, mx1), 364),
                    PAL["paper_l"] + (240,))

    # cuervos
    for cx, cy, cs in ((430, 168, 1.0), (500, 128, 0.8),
                       (372, 210, 0.7), (560, 150, 0.9)):
        pen.line([(cx - 11 * cs, cy), (cx, cy - 6 * cs), (cx + 11 * cs, cy)],
                 PAL["ink"] + (215,), 1.8)

    cartouche(img, 30, 30, 34, 226, "CASTILLO")
    img = washi(img, 0.95)
    img = grain(img, 3)
    img = vignette(img, 0.18)
    return img.convert("RGB")


def bg_market():
    """Plaza del mercado de Nagasaki: el puesto de Haru, el del socio y el del rival."""
    img = new_rgba()
    vgrad(img, 0, 526, [(0, (118, 146, 168)), (0.40, (176, 186, 186)),
                        (0.72, (226, 198, 154)), (1, (242, 216, 174))])
    pen = Pen(img)

    soft_glow(img, 250, 214, 180, (255, 232, 178), 75)
    pen.ellipse((190, 154, 310, 274), (248, 230, 182, 235),
                PAL["gold"] + (150,), 2)
    cloud(img, 900, 118, 420, 40, PAL["paper_l"] + (230,), True)
    cloud(img, 520, 196, 300, 26, PAL["paper_l"] + (170,), True)

    # montañas y casa al fondo
    mountain(img, [(0, 470), (0, 396), (170, 366), (350, 400), (520, 362),
                   (700, 396), (880, 364), (1060, 398), (1280, 368), (1280, 470)],
             (72, 96, 116, 240), PAL["prussian"])
    for x in range(-40, W, 200):
        pen.rect((x, 428, x + 180, 530), (150, 126, 100, 255),
                 PAL["ink"] + (170,), 1.4)
        pen.poly([(x - 14, 430), (x + 90, 394), (x + 194, 430)],
                 (66, 74, 84, 255), PAL["ink"] + (200,))
        pen.rect((x + 60, 466, x + 104, 530), (72, 58, 48, 235))
        pen.line([(x + 14, 452), (x + 52, 452)], (232, 206, 160, 140), 2)

    # suelo de tierra apisonada
    pen.rect((0, 520, W, H), (198, 174, 140, 255))
    pen.rect((0, 520, W, 528), (140, 116, 90, 255))
    for row in range(6):
        y = 546 + row * 26
        for x in range(-40 + (row % 2) * 40, W, 80):
            pen.line([(x, y), (x + 30, y)], (168, 144, 112, 110), 1)

    # --- puestos -----------------------------------------------------------
    def puesto(cx, w, base, aw_a, aw_b, goods, seal, sign):
        x0, x1 = cx - w // 2, cx + w // 2
        top = base - 244
        # sombra en el suelo
        pen.ellipse((x0 - 18, base - 16, x1 + 18, base + 20), (120, 100, 80, 60))
        # postes
        for px in (x0 + 4, x1 - 16):
            pen.rect((px, top + 30, px + 12, base), PAL["wood_d"] + (255,),
                     PAL["ink"] + (220,), 1.4)
        # mostrador y tablas
        pen.rect((x0 + 8, base - 78, x1 - 8, base - 56), PAL["wood_l"] + (255,),
                 PAL["ink"] + (230,), 1.8)
        pen.rect((x0 + 14, base - 56, x1 - 14, base), PAL["wood"] + (255,),
                 PAL["ink"] + (230,), 1.8)
        for px in range(x0 + 30, x1 - 24, 34):
            pen.line([(px, base - 52), (px, base - 2)], (76, 54, 34, 120), 1.2)
        # faldón con el sello del puesto
        pen.rect((x0 + 18, base - 40, x0 + 76, base - 8), seal + (240,),
                 PAL["ink"] + (210,), 1.2)
        pen.ellipse((x0 + 34, base - 34, x0 + 60, base - 14),
                    PAL["paper_l"] + (240,))
        # mercancía sobre el mostrador
        for i, kind in enumerate(goods):
            gx = x0 + 44 + i * ((w - 96) / max(1, len(goods) - 1))
            if kind == "caja":
                pen.rect((gx - 18, base - 108, gx + 18, base - 78),
                         (146, 108, 70, 255), PAL["ink"] + (220,), 1.4)
                pen.line([(gx - 18, base - 108), (gx + 18, base - 78)],
                         PAL["ink_soft"] + (150,), 1.2)
            elif kind == "saco":
                pen.poly([(gx - 18, base - 80), (gx + 18, base - 80),
                          (gx + 13, base - 124), (gx - 13, base - 124)],
                         (206, 186, 148, 255), PAL["ink"] + (220,))
                pen.line([(gx - 9, base - 124), (gx + 9, base - 124)],
                         PAL["ink_soft"] + (210,), 1.6)
            elif kind == "pescado":
                pen.ellipse((gx - 20, base - 96, gx + 10, base - 78),
                            (196, 200, 196, 255), PAL["ink"] + (210,), 1.2)
                pen.poly([(gx + 10, base - 87), (gx + 22, base - 96),
                          (gx + 22, base - 78)], (196, 200, 196, 255),
                         PAL["ink"] + (210,))
                pen.ellipse((gx - 14, base - 90, gx - 10, base - 86),
                            PAL["ink"] + (200,))
            else:  # "vasija"
                pen.rect((gx - 12, base - 108, gx + 12, base - 80),
                         (120, 132, 146, 255), PAL["ink"] + (220,), 1.4)
                pen.ellipse((gx - 8, base - 114, gx + 8, base - 102),
                            (120, 132, 146, 255), PAL["ink"] + (220,), 1.2)
        # toldo a rayas
        pen.poly([(x0 - 26, top + 30), (x0, top), (x1, top), (x1 + 26, top + 30)],
                 aw_a + (250,), PAL["ink"] + (235,))
        n = 8
        step = (w + 52) / n
        for i in range(n):
            if i % 2:
                continue
            ax = x0 - 26 + i * step
            pen.poly([(ax, top + 30), (ax + step, top + 30),
                      (ax + step - 6, top + 68), (ax + 6, top + 68)],
                     aw_b + (235,), None)
        pen.line([(x0 - 26, top + 30), (x1 + 26, top + 30)], PAL["ink"] + (200,), 2)
        for i in range(n):
            ax = x0 - 26 + i * step
            pen.poly([(ax + 8, top + 68), (ax + step - 8, top + 68),
                      (ax + step - 16, top + 80), (ax + 16, top + 80)],
                     aw_b + (215,), None)
        # letrero colgado del toldo
        sx = cx - 30
        pen.line([(sx + 8, top + 62), (sx + 8, top + 96)], PAL["ink_soft"] + (200,), 1.2)
        pen.line([(sx + 52, top + 62), (sx + 52, top + 96)], PAL["ink_soft"] + (200,), 1.2)
        pen.rect((sx, top + 96, sx + 60, top + 140), PAL["wood_l"] + (255,),
                 PAL["ink"] + (235,), 1.8)
        pen.ellipse((sx + 18, top + 108, sx + 42, top + 132), PAL["paper_l"] + (245,),
                    PAL["ink_soft"] + (180,), 1.2)
        pen.rect((sx + 22, top + 112, sx + 38, top + 128), sign + (200,))

    puesto(232, 292, 620, PAL["indigo"], PAL["indigo_p"],
           ["saco", "caja", "saco"], PAL["indigo"], PAL["indigo_p"])
    puesto(640, 360, 636, PAL["vermillion"], PAL["gold"],
           ["caja", "pescado", "pescado", "caja"], PAL["vermillion"],
           PAL["vermillion_d"])
    puesto(1046, 292, 620, (86, 62, 78), PAL["gold"],
           ["vasija", "caja", "vasija"], (86, 62, 78), PAL["gold"])

    # cajas y barriles sueltos
    pen.rect((54, 652, 128, 714), (146, 108, 70, 255), PAL["ink"] + (225,), 1.8)
    pen.line([(54, 652), (128, 714)], PAL["ink_soft"] + (140,), 1.4)
    pen.rect((156, 668, 214, 714), (146, 108, 70, 255), PAL["ink"] + (225,), 1.8)
    pen.ellipse((1140, 664, 1216, 714), (126, 92, 58, 255), PAL["ink"] + (225,), 1.8)
    pen.line([(1140, 684), (1216, 684)], PAL["wood_l"] + (140,), 1.6)

    cartouche(img, 30, 30, 34, 226, "MERCADO")
    img = washi(img, 1.0)
    img = grain(img, 3)
    img = vignette(img, 0.14)
    return img.convert("RGB")


# ---------------------------------------------------------------------------
# Objetos del mundo nuevo
# ---------------------------------------------------------------------------
def obj_photo():
    img = new_rgba(160, 190)
    pen = Pen(img)
    pen.rect((0, 0, 160, 190), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 3)
    pen.rect((7, 7, 153, 183), PAL["gold"] + (200,), PAL["ink_soft"] + (200,), 1.2)
    pen.rect((12, 12, 148, 178), (226, 210, 178, 255))
    pen.rect((12, 118, 148, 178), (190, 164, 128, 255))
    pen.line([(12, 118), (148, 118)], PAL["wood_d"] + (120,), 1.2)
    draw_family(pen, 166, 80, 0.82)
    pen.rect((118, 150, 140, 172), PAL["vermillion"] + (235,))
    pen.rect((124, 156, 130, 166), PAL["paper_l"] + (235,))
    pen.rect((132, 156, 138, 166), PAL["paper_l"] + (235,))
    return img


def obj_note():
    img = new_rgba(150, 92)
    pen = Pen(img)
    pen.poly([(8, 12), (142, 4), (146, 80), (4, 88)],
             PAL["paper_l"] + (255,), PAL["ink"] + (230,))
    pen.line([(75, 7), (74, 84)], PAL["ink_soft"] + (55,), 1.2)
    for i in range(5):
        y = 24 + i * 10
        x0 = 18 + (i % 2) * 5
        pen.line([(x0, y), (x0 + 52, y - 2)], PAL["ink"] + (150,), 1.1)
    pen.line([(100, 22), (100, 56)], PAL["ink"] + (120,), 1.1)
    pen.rect((112, 62, 132, 80), PAL["vermillion"] + (240,))
    pen.rect((117, 67, 122, 75), PAL["paper_l"] + (230,))
    pen.rect((124, 67, 129, 75), PAL["paper_l"] + (230,))
    return img


def obj_photo_zoom():
    img = new_rgba()
    pen = Pen(img)
    pen.rect((0, 0, W, H), (14, 12, 10, 205))
    # marco grande
    pen.rect((322, 56, 958, 664), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 5)
    pen.rect((338, 72, 942, 648), PAL["gold"] + (220,), PAL["ink_soft"] + (200,), 2)
    pen.rect((356, 90, 924, 630), (232, 218, 190, 255), PAL["ink"] + (200,), 1.8)
    pen.rect((356, 430, 924, 630), (192, 164, 126, 255))
    pen.line([(356, 430), (924, 430)], PAL["wood_d"] + (110,), 1.6)
    # decoración de la casa
    pen.rect((386, 150, 470, 430), PAL["wood"] + (190,))
    pen.rect((810, 150, 894, 430), PAL["wood"] + (190,))
    draw_family(pen, 570, 620, 2.7)
    pen.text((640, 612), "Familia de Haru · Nagasaki, 1631", 24,
             PAL["ink"] + (225,), FONT_REG, "mm")
    pen.rect((858, 560, 900, 602), PAL["vermillion"] + (235,))
    pen.rect((868, 570, 878, 592), PAL["paper_l"] + (235,))
    pen.rect((884, 570, 892, 592), PAL["paper_l"] + (235,))
    # pista de cierre
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT_REG, sc(18))
    d.text((sc(640), sc(690)), "Haz clic para cerrar", font=f,
           fill=PAL["paper"] + (200,), anchor="mm")
    return img


def obj_tavern(variant="a", open_=False):
    img = new_rgba(360, 330)
    pen = Pen(img)
    noren_col = PAL["indigo"] if variant == "a" else PAL["vermillion_d"]
    pen.ellipse((14, 300, 346, 330), (20, 18, 16, 90))
    # cuerpo de madera
    pen.rect((16, 76, 344, 306), PAL["wood"] + (255,), PAL["ink"] + (255,), 2.6)
    for x in range(32, 344, 30):
        pen.line([(x, 80), (x, 302)], PAL["wood_d"] + (65,), 1.2)
    pen.rect((8, 292, 352, 314), (150, 142, 130, 255), PAL["ink"] + (220,), 1.6)
    pen.rect((8, 288, 352, 300), PAL["wood_l"] + (255,), PAL["ink"] + (220,), 1.4)
    # tejado
    if variant == "a":
        pen.poly([(0, 82), (180, 16), (360, 82), (338, 100), (180, 44), (22, 100)],
                 (52, 62, 78, 255), PAL["ink"] + (255,))
        for i in range(4):
            pen.line([(34 + i * 74, 84 - i * 14), (326 - i * 74, 84 - i * 14)],
                     PAL["indigo_l"] + (120,), 1.4)
    else:
        pen.poly([(0, 84), (180, 24), (360, 84), (340, 102), (180, 52), (20, 102)],
                 (108, 78, 52, 255), PAL["ink"] + (255,))
        for i in range(5):
            pen.line([(26 + i * 68, 96 - i * 12), (334 - i * 68, 96 - i * 12)],
                     PAL["wood_l"] + (110,), 1.4)
    pen.rect((4, 78, 356, 94), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2)

    # puerta
    if not open_:
        pen.rect((92, 118, 268, 292), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2.4)
        pen.rect((102, 128, 176, 284), PAL["wood"] + (255,), PAL["ink_soft"] + (200,), 1.6)
        pen.rect((184, 128, 258, 284), PAL["wood"] + (255,), PAL["ink_soft"] + (200,), 1.6)
        for x in (128, 210):
            pen.rect((x, 148, x + 22, 262), PAL["wood_l"] + (45,))
        pen.line([(96, 206), (264, 206)], (206, 186, 142, 255), 5)
        pen.ellipse((172, 198, 188, 214), (206, 186, 142, 255), PAL["ink"] + (200,), 1.4)
        pen.rect((134, 224, 226, 264), PAL["paper_l"] + (250,), PAL["ink"] + (255,), 1.6)
        pen.text((180, 244), "CERRADO", 13, PAL["ink"] + (255,), FONT_BOLD, "mm")
    else:
        pen.rect((92, 118, 268, 292), (30, 24, 20, 255), PAL["ink"] + (255,), 2.4)
        soft_glow(img, 180, 236, 92, (255, 188, 108), 95)
        # mesas y clientes insinuados
        pen.rect((112, 246, 168, 266), PAL["wood_l"] + (255,), PAL["ink"] + (200,), 1.4)
        pen.rect((192, 238, 250, 258), PAL["wood_l"] + (255,), PAL["ink"] + (200,), 1.4)
        pen.ellipse((126, 214, 152, 244), (70, 56, 46, 255))
        pen.ellipse((206, 208, 232, 238), (70, 56, 46, 255))
        # noren
        pen.rect((92, 118, 268, 168), noren_col + (240,), PAL["ink"] + (230,), 1.6)
        for i in (1, 2):
            pen.line([(92 + i * 59, 120), (92 + i * 59, 166)], PAL["paper"] + (130,), 1.4)
        pen.ellipse((170, 130, 190, 150), PAL["paper_l"] + (220,))
        soft_glow(img, 180, 306, 80, (255, 190, 110), 55)

    # letrero vertical
    pen.rect((26, 108, 66, 250), PAL["paper"] + (250,), PAL["ink"] + (255,), 2)
    pen.rect((31, 113, 61, 245), None, PAL["vermillion"] + (120,), 1)
    label = "GRULLA" if variant == "a" else "FAROL"
    for i, ch in enumerate(label):
        pen.text((46, 130 + i * 20), ch, 14, PAL["ink"] + (255,), FONT_BOLD, "mm")

    # farolillo
    pen.line([(316, 94), (316, 118)], PAL["ink_soft"] + (200,), 1.6)
    soft_glow(img, 316, 150, 46, (255, 196, 120), 95 if open_ else 40)
    pen.ellipse((294, 120, 338, 176), PAL["gold"] + (245,) if open_ else (196, 170, 118, 230),
                PAL["ink"] + (255,), 2)
    pen.line([(294, 148), (338, 148)], PAL["vermillion_d"] + (170,), 1.4)
    # fija el lienzo completo para que abierta y cerrada queden alineadas
    img.putpixel((0, 0), (0, 0, 0, 1))
    img.putpixel((img.width - 1, img.height - 1), (0, 0, 0, 1))
    return img


def obj_net():
    img = new_rgba(240, 170)
    pen = Pen(img)
    pen.line([(14, 12), (14, 78)], PAL["wood_d"] + (255,), 4)
    pen.line([(226, 12), (226, 78)], PAL["wood_d"] + (255,), 4)
    pen.line([(14, 20), (226, 16)], PAL["wood_d"] + (255,), 3)
    # malla
    for i in range(9):
        x = 24 + i * 24
        pen.line([(x, 22), (x + 40, 156)], (196, 178, 140, 190), 1.2)
        pen.line([(x, 22), (x - 40, 156)], (196, 178, 140, 190), 1.2)
    pen.line([(10, 74), (230, 70)], PAL["ochre"] + (220,), 3)
    # flotadores
    for x in (38, 84, 130, 176, 212):
        pen.ellipse((x - 9, 58, x + 9, 74), PAL["vermillion"] + (230,),
                    PAL["ink"] + (200,), 1.2)
    # pez enredado
    pen.poly([(120, 120), (152, 110), (176, 126), (150, 138)],
             (140, 160, 176, 255), PAL["ink"] + (220,))
    pen.ellipse((124, 122, 132, 130), PAL["ink"] + (255,))
    return img


def obj_guillotine(blade_down=False):
    """Guillotina del cadalso. blade_down=True para el instante del golpe."""
    img = new_rgba(250, 350)
    pen = Pen(img)
    wood = (110, 78, 50)
    wood_l = (146, 108, 74)
    steel = (178, 184, 192)
    pen.ellipse((28, 324, 222, 350), (18, 16, 14, 95))
    # base
    pen.rect((34, 306, 216, 330), wood + (255,), PAL["ink"] + (255,), 2.2)
    # montantes
    pen.rect((46, 34, 76, 310), wood + (255,), PAL["ink"] + (255,), 2.2)
    pen.rect((174, 34, 204, 310), wood + (255,), PAL["ink"] + (255,), 2.2)
    pen.line([(54, 40), (54, 300)], wood_l + (110,), 1.6)
    pen.line([(182, 40), (182, 300)], wood_l + (110,), 1.6)
    # travesaño superior
    pen.rect((24, 20, 226, 54), wood + (255,), PAL["ink"] + (255,), 2.4)
    pen.line([(28, 30), (222, 30)], wood_l + (120,), 1.6)
    # polea
    pen.ellipse((116, 56, 136, 76), PAL["ink_soft"] + (255,),
                PAL["ink"] + (255,), 1.6)
    # cuchilla
    y0 = 196 if blade_down else 96
    pen.poly([(82, y0), (172, y0 + 32), (172, y0 + 84), (82, y0 + 52)],
             steel + (255,), PAL["ink"] + (255,))
    pen.poly([(82, y0), (172, y0 + 32), (172, y0 + 46), (82, y0 + 14)],
             (226, 232, 240, 235), None)
    pen.line([(96, y0 + 22), (158, y0 + 46)], (250, 252, 255, 190), 2)
    if not blade_down:
        pen.line([(126, 74), (126, y0)], (196, 172, 132, 255), 2.6)
    # cepo
    pen.rect((42, 258, 208, 296), wood_l + (255,), PAL["ink"] + (255,), 2.2)
    pen.ellipse((106, 262, 144, 292), (22, 18, 16, 255), PAL["ink"] + (255,), 1.8)
    # refuerzos
    pen.poly([(46, 200), (76, 252), (76, 206)], wood_l + (150,))
    pen.poly([(204, 200), (174, 252), (174, 206)], wood_l + (150,))
    return img


def obj_verdugo():
    """Verdugo encapuchado con la cuerda de la cuchilla."""
    img = new_rgba(160, 272)
    pen = Pen(img)
    robe = (46, 50, 66)
    pen.ellipse((18, 254, 142, 272), (18, 16, 14, 90))
    # piernas y sandalias
    pen.rect((56, 216, 74, 256), robe + (255,))
    pen.rect((84, 216, 102, 256), robe + (255,))
    pen.ellipse((48, 250, 80, 264), (62, 46, 36, 255), PAL["ink"] + (210,), 1.2)
    pen.ellipse((80, 250, 112, 264), (62, 46, 36, 255), PAL["ink"] + (210,), 1.2)
    # torso
    pen.poly([(48, 224), (104, 224), (112, 96), (40, 96)],
             robe + (255,), PAL["ink"] + (255,))
    # faja
    pen.rect((42, 166, 110, 182), PAL["vermillion_d"] + (245,))
    pen.rect((46, 196, 106, 206), PAL["indigo"] + (200,))
    # brazos
    pen.poly([(40, 108), (24, 176), (38, 184), (58, 122)],
             robe + (255,), PAL["ink"] + (220,))
    pen.poly([(112, 108), (130, 172), (116, 180), (96, 122)],
             robe + (255,), PAL["ink"] + (220,))
    # manos
    pen.ellipse((18, 172, 40, 194), PAL["skin"] + (255,), PAL["ink"] + (200,), 1.4)
    pen.ellipse((118, 164, 140, 186), PAL["skin"] + (255,), PAL["ink"] + (200,), 1.4)
    # capucha
    pen.poly([(40, 100), (110, 100), (118, 56), (76, 24), (32, 56)],
             robe + (255,), PAL["ink"] + (255,))
    # rostro en sombra
    pen.ellipse((56, 54, 98, 96), (28, 26, 24, 255), PAL["ink"] + (255,), 1.6)
    pen.ellipse((62, 68, 74, 79), (232, 226, 206, 235))
    pen.ellipse((80, 68, 92, 79), (232, 226, 206, 235))
    # cuerda hacia la polea
    pen.line([(132, 176), (152, 106)], (196, 172, 132, 240), 2.6)
    return img


def obj_haru_reo():
    """Haru de rodillas ante el cepo, con el kimono blanco del condenado."""
    img = new_rgba(150, 150)
    pen = Pen(img)
    white = (234, 226, 206)
    pen.ellipse((16, 130, 132, 150), (18, 16, 14, 85))
    # rodillas y vuelo del kimono
    pen.poly([(38, 146), (126, 146), (116, 118), (74, 110), (42, 120)],
             white + (255,), PAL["ink"] + (255,))
    # torso inclinado
    pen.poly([(56, 122), (108, 116), (102, 74), (66, 80)],
             white + (255,), PAL["ink"] + (255,))
    for x in (62, 80, 98):
        pen.line([(x, 122), (x - 3, 142)], (198, 186, 162, 170), 1.3)
    # obi
    pen.rect((58, 108, 108, 118), PAL["ink_soft"] + (225,))
    # manos atadas a la espalda
    pen.poly([(102, 100), (126, 118), (120, 126), (98, 110)],
             white + (255,), PAL["ink"] + (200,))
    pen.line([(108, 108), (124, 116)], PAL["ink_soft"] + (225,), 1.4)
    # cabeza inclinada
    pen.ellipse((56, 44, 96, 84), PAL["skin"] + (255,), PAL["ink"] + (255,), 2)
    pen.poly([(56, 58), (58, 40), (76, 32), (94, 40), (96, 58),
              (86, 50), (66, 50)], PAL["hair"] + (255,), PAL["ink"] + (255,))
    pen.line([(64, 66), (88, 66)], PAL["ink_soft"] + (215,), 1.2)
    return img


def obj_pause():
    img = new_rgba()
    pen = Pen(img)
    pen.rect((0, 0, W, H), (14, 12, 10, 240))
    pen.rect((300, 110, 980, 626), PAL["paper"] + (250,), PAL["ink"] + (255,), 4)
    pen.rect((316, 126, 964, 610), None, PAL["ink_soft"] + (110,), 2)
    pen.text((640, 210), "PAUSA", 62, PAL["ink"] + (255,), FONT_BOLD, "mm")
    pen.line([(470, 258), (810, 258)], PAL["vermillion"] + (200,), 2)
    buttons = [((440, 330, 840, 394), "CONTINUAR"),
               ((440, 420, 840, 484), "MENÚ PRINCIPAL"),
               ((440, 510, 840, 574), "SALIR")]
    for (x0, y0, x1, y1), label in buttons:
        pen.rrect((x0, y0, x1, y1), 10, PAL["paper_l"] + (255,),
                  PAL["ink"] + (255,), 2.6)
        pen.rect((x0, y0, x0 + 12, y1), PAL["vermillion"] + (245,))
        pen.text((640, (y0 + y1) // 2 - 2), label, 27, PAL["ink"] + (255,),
                 FONT_BOLD, "mm")
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT_REG, sc(16))
    d.text((sc(640), sc(596)), "Clic derecho o ESC para abrir el menú", font=f,
           fill=PAL["ink_soft"] + (190,), anchor="mm")
    return img


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def save(img, name, path=GFX):
    os.makedirs(path, exist_ok=True)
    if img.width > W or img.height > H:
        img = img.resize((img.width // S, img.height // S), Image.LANCZOS)
    img.save(os.path.join(path, name))
    print("  ", name, img.size)


def main():
    os.makedirs(GFX, exist_ok=True)
    os.makedirs(CHR, exist_ok=True)
    manifest = {"objects": {}, "characters": {}, "scenes": {}}

    print("Fondos...")
    save(bg_menu(), "bg_menu.png")
    save(bg_home(), "bg_home.png")
    save(bg_street(), "bg_street.png")
    save(bg_market(), "bg_market.png")
    save(bg_port(), "bg_port.png")
    save(bg_fisher(), "bg_fisher.png")
    save(bg_castle(), "bg_castle.png")
    manifest["scenes"] = {
        "menu": {"path": "graphics/bg_menu.png"},
        "castillo": {"path": "graphics/bg_castle.png"},
        "casa": {"path": "graphics/bg_home.png"},
        "calle": {"path": "graphics/bg_street.png"},
        "mercado": {"path": "graphics/bg_market.png"},
        "puerto": {"path": "graphics/bg_port.png"},
        "casa_pescador": {"path": "graphics/bg_fisher.png"},
    }

    print("Objetos...")
    objs = {
        "fisher": obj_fisher(),
        "photo": obj_photo(),
        "note": obj_note(),
        "photo_zoom": obj_photo_zoom(),
        "tavern_a_closed": obj_tavern("a", False),
        "tavern_a_open": obj_tavern("a", True),
        "tavern_b_closed": obj_tavern("b", False),
        "tavern_b_open": obj_tavern("b", True),
        "net": obj_net(),
        "guillotine_up": obj_guillotine(False),
        "guillotine_down": obj_guillotine(True),
        "verdugo": obj_verdugo(),
        "haru_reo": obj_haru_reo(),
        "pause": obj_pause(),
    }
    for key, im in objs.items():
        cropped, x, y = crop_alpha(im)
        fn = f"obj_{key}.png"
        save(cropped, fn)
        manifest["objects"][key] = {"path": f"graphics/{fn}", "x": x, "y": y,
                                    "w": cropped.width, "h": cropped.height}

    print("Personaje...")
    frames = []
    for i, (bob, stride) in enumerate([(0, 0), (-2, 1), (0, 0), (-1, -1)]):
        im = char_frame("left", bob, stride)
        fn = f"haru_walk_{i + 1}.png"
        im.save(os.path.join(CHR, fn))
        frames.append(f"characters/{fn}")
    manifest["characters"]["walk"] = frames
    idle = []
    for i, bob in enumerate([0, -1]):
        im = char_frame("left", bob, 0)
        fn = f"haru_idle_{i + 1}.png"
        im.save(os.path.join(CHR, fn))
        idle.append(f"characters/{fn}")
    manifest["characters"]["idle"] = idle
    save(cursor_arrow(), "cursor_arrow.png")

    with open(os.path.join(ROOT, "build", "art_manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
    print("OK")


if __name__ == "__main__":
    main()
