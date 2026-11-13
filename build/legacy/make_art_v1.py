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
def bg_market():
    img = new_rgba()
    vgrad(img, 0, 500, [(0, (30, 47, 72)), (0.30, (52, 79, 108)),
                        (0.55, (126, 133, 138)), (0.76, (214, 178, 137)),
                        (1, (242, 224, 188))])
    pen = Pen(img)

    # sol bajo, disco pÃ¡lido
    soft_glow(img, 1010, 286, 130, (255, 226, 170), 70)
    pen.ellipse((958, 234, 1062, 338), PAL["gold"] + (240,), PAL["vermillion"] + (120,), 2)

    # nubes en bandas
    cloud(img, 230, 150, 330, 44, PAL["paper_l"] + (232,), True)
    cloud(img, 660, 108, 400, 38, PAL["paper"] + (220,), True)
    cloud(img, 1040, 205, 360, 34, PAL["rose"] + (200,), True)
    cloud(img, 360, 300, 300, 26, PAL["paper_l"] + (185,), True)
    cloud(img, 900, 380, 340, 24, PAL["rose"] + (185,), True)

    # montaÃ±as lejanas (Inasa) en capas
    mountain(img, [(0, 500), (0, 420), (120, 372), (250, 410), (390, 368), (520, 405),
                   (660, 360), (800, 402), (960, 366), (1120, 398), (1280, 372),
                   (1280, 500)], PAL["indigo"] + (255,), PAL["prussian"])
    mountain(img, [(0, 500), (0, 455), (170, 430), (330, 458), (520, 436), (700, 462),
                   (900, 438), (1100, 460), (1280, 440), (1280, 500)],
             PAL["prussian"] + (255,), PAL["ink_soft"])

    # mar
    vgrad(img, 480, 596, [(0, (38, 62, 88)), (0.5, (30, 54, 78)), (1, (24, 44, 64))])
    seigaiha(img, -40, 486, W + 40, 592, PAL["prussian"], PAL["indigo_p"], r=24, alpha=120)
    seigaiha(img, -40, 530, W + 40, 592, PAL["prussian"], PAL["paper"], r=18, alpha=45)

    # barco holandÃ©s lejano
    pen = Pen(img)
    bx, by = 1080, 492
    pen.poly([(bx - 55, by), (bx + 55, by), (bx + 40, by + 14), (bx - 40, by + 14)],
             PAL["ink"] + (235,), PAL["ink"] + (255,))
    pen.line([(bx, by), (bx, by - 92)], PAL["ink"] + (255,), 2.4)
    pen.line([(bx - 36, by - 8), (bx + 34, by - 8)], PAL["ink"] + (230,), 2)
    pen.poly([(bx + 4, by - 88), (bx + 4, by - 34), (bx + 44, by - 40)],
             PAL["paper"] + (225,), PAL["ink"] + (255,))
    pen.poly([(bx - 4, by - 84), (bx - 4, by - 30), (bx - 32, by - 38)],
             PAL["paper"] + (210,), PAL["ink"] + (255,))
    pen.line([(bx + 46, by - 20), (bx, by - 88)], PAL["ink"] + (150,), 1)

    # muelle de madera
    pen.rect((0, 588, W, H), PAL["wood"] + (255,))
    pen.rect((0, 588, W, 602), PAL["wood_l"] + (255,), PAL["ink"] + (255,), 2)
    for y in range(612, H, 30):
        pen.line([(0, y), (W, y)], PAL["wood_d"] + (130,), 1.4)
    for x in range(-40, W + 60, 132):
        pen.line([(x, 600), (x + 46, H)], PAL["wood_d"] + (105,), 1.2)
    pen.line([(0, 588), (W, 588)], PAL["ink"] + (255,), 3)

    # almacÃ©n derecha
    pen.poly([(930, 336), (1290, 310), (1290, 236), (930, 258)], PAL["wood_d"] + (255,),
             PAL["ink"] + (255,))
    pen.rect((946, 330, 1280, 604), PAL["wood"] + (255,), PAL["ink"] + (255,), 3)
    for x in range(956, 1280, 30):
        pen.line([(x, 334), (x, 602)], PAL["wood_d"] + (95,), 1.2)
    pen.rect((946, 330, 1280, 346), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 1.5)
    # hueco de la puerta
    pen.rect((1018, 366, 1218, 604), PAL["ink"] + (255,))
    pen.rect((1010, 356, 1226, 370), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2)
    # postes y viga
    pen.rect((1004, 350, 1022, 610), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2)
    pen.rect((1214, 350, 1232, 610), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2)
    pen.rect((1000, 336, 1236, 352), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2)
    hatch(img, [(946, 346), (1280, 346), (1280, 604), (946, 604)], PAL["ink_soft"],
          step=11, width=1, alpha=40, angle=58)

    # puesto de pescado (izquierda)
    pen.rect((58, 404, 74, 620), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2)
    pen.rect((302, 404, 318, 620), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2)
    for i in range(6):
        x = 48 + i * 45
        col = PAL["paper"] + (255,) if i % 2 == 0 else PAL["vermillion"] + (245,)
        pen.poly([(x, 372), (x + 47, 372), (x + 58, 428), (x - 4, 428)], col,
                 PAL["ink"] + (255,))
    pen.rect((40, 424, 326, 436), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2)
    # mostrador
    pen.rect((68, 552, 308, 588), PAL["wood_l"] + (255,), PAL["ink"] + (255,), 2)
    pen.rect((68, 588, 308, 618), PAL["wood_d"] + (255,), PAL["ink"] + (255,), 2)
    # pescados colgados
    for i, x in enumerate((100, 142, 238, 280)):
        pen.line([(x, 436), (x, 470)], PAL["ink_soft"] + (200,), 1)
        pen.ellipse((x - 7, 468, x + 7, 500), PAL["indigo_l"] + (235,), PAL["ink"] + (255,), 1.2)
        pen.line([(x, 470), (x, 496)], PAL["paper"] + (90,), 1)
    # cajas bajo el mostrador
    pen.rect((318, 566, 396, 630), PAL["wood"] + (255,), PAL["ink"] + (255,), 2)
    pen.line([(318, 566), (396, 630)], PAL["wood_d"] + (140,), 1.4)
    pen.line([(396, 566), (318, 630)], PAL["wood_d"] + (140,), 1.4)

    # farolillos
    for cx, cy, r in ((430, 58, 34), (760, 40, 30)):
        pen.line([(cx, 0), (cx, cy - r)], PAL["ink"] + (255,), 2)
        soft_glow(img, cx, cy, r * 2.4, (255, 190, 110), 70)
        pen.rrect((cx - r * 0.52, cy - r * 0.55, cx + r * 0.52, cy + r * 0.7), 8,
                  PAL["vermillion"] + (240,), PAL["ink"] + (255,), 2)
        pen.line([(cx - r * 0.52, cy - r * 0.2), (cx + r * 0.52, cy - r * 0.2)],
                 PAL["paper"] + (130,), 1.4)
        pen.line([(cx, cy - r * 0.55), (cx, cy + r * 0.7)], PAL["vermillion_d"] + (120,), 1)

    # cartucho y sellos (esquina superior izquierda, discreta)
    cartouche(img, 24, 24, 34, 210, "NAGASAKI")
    seal_stamp(img, 26, 246, 30, "1641")

    img = washi(img, 1.0)
    img = grain(img, 3)
    img = vignette(img, 0.12)
    return img.convert("RGB")


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
    save(bg_market(), "bg_market.png")
    save(bg_warehouse(), "bg_warehouse.png")
    save(bg_epilogue(), "bg_epilogue.png")
    manifest["scenes"] = {
        "menu": {"path": "graphics/bg_menu.png"},
        "market": {"path": "graphics/bg_market.png"},
        "warehouse": {"path": "graphics/bg_warehouse.png"},
        "epilogue": {"path": "graphics/bg_epilogue.png"},
    }

    print("Objetos...")
    objs = {
        "crate": obj_crate(),
        "fish": obj_fish(),
        "fisher": obj_fisher(),
        "edict": obj_edict(),
        "guard": obj_guard(),
        "guard_eating": obj_guard_eating(),
        "door": obj_door(),
        "merchant": obj_merchant(),
        "hidden": obj_hidden(),
        "sack": obj_sack(),
        "plaque_denounce": obj_plaque("DENUNCIAR", 34, 150),
        "plaque_help": obj_plaque("AYUDAR", 1002, 150),
        "plaque_silent": obj_plaque("CALLAR", 518, 150),
        "plaque_replay": obj_plaque("VOLVER A JUGAR", 480, 616, 320, 84),
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
