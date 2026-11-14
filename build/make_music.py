# -*- coding: utf-8 -*-
"""
Música procedural para "Nagasaki 1641: El sello de Dejima".

Genera cuatro bucles (menú, mercado, almacén, epílogo) con instrumentos
sintetizados (koto, shakuhachi, taiko, campana) y los exporta a OGG mono.
No necesita samples externos: todo se calcula con numpy y se codifica con
ffmpeg (libvorbis).

Uso:  py make_music.py
"""
import math
import os
import shutil
import subprocess
import wave

import numpy as np

SR = 22050
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "game", "audio")

NOTES = {
    "D2": 73.42, "A2": 110.00, "C3": 130.81, "D3": 146.83, "F3": 174.61,
    "G3": 196.00, "A3": 220.00, "C4": 261.63, "D4": 293.66, "F4": 349.23,
    "G4": 392.00, "A4": 440.00, "C5": 523.25, "D5": 587.33,
}


def n(name):
    return NOTES[name]


# ---------------------------------------------------------------------------
# Instrumentos
# ---------------------------------------------------------------------------
def pluck(freq, dur=2.4, amp=0.40, decay=3.4, bright=0.52):
    """Cuerda pulsada tipo koto: armónicos con caída exponencial."""
    t = np.arange(int(dur * SR)) / SR
    sig = np.zeros_like(t)
    for k in range(1, 8):
        sig += (bright ** (k - 1)) / k * np.sin(2 * np.pi * freq * k * t + 0.12 * k)
    env = np.exp(-decay * t) * np.minimum(1.0, t / 0.004)
    rng = np.random.default_rng(int(freq) % 997)
    pick = rng.standard_normal(len(t)) * 0.02 * np.exp(-70 * t)
    return (sig * env + pick) * amp


def flute(freq, dur=3.0, amp=0.22):
    """Shakuhachi: seno con vibrato lento, aire y ataque suave."""
    t = np.arange(int(dur * SR)) / SR
    vib = 1.0 + 0.0045 * np.sin(2 * np.pi * 5.1 * t) * np.minimum(1.0, t / 0.6)
    sig = (np.sin(2 * np.pi * freq * t * vib)
           + 0.22 * np.sin(2 * np.pi * 2 * freq * t)
           + 0.06 * np.sin(2 * np.pi * 3 * freq * t))
    env = (np.minimum(1.0, t / 0.18)
           * np.clip((dur - t) / 0.35, 0, 1))
    rng = np.random.default_rng(7)
    breath = rng.standard_normal(len(t)) * 0.014
    return (sig + breath) * env * amp


def taiko(dur=0.55, amp=0.55, f0=96.0, f1=47.0):
    """Tambor taiko: barrido grave + golpe de ruido."""
    t = np.arange(int(dur * SR)) / SR
    f = f1 + (f0 - f1) * np.exp(-17 * t)
    body = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-7.5 * t)
    rng = np.random.default_rng(3)
    hit = rng.standard_normal(len(t)) * np.exp(-55 * t) * 0.22
    return (body + hit) * amp


def bell(freq, dur=4.0, amp=0.20):
    """Campana de templo: parciales inarmónicos y cola larga."""
    t = np.arange(int(dur * SR)) / SR
    parts = [(1.0, 0.55, 1.1), (2.76, 0.28, 1.9), (5.40, 0.14, 2.8), (8.93, 0.07, 4.2)]
    sig = np.zeros_like(t)
    for ratio, a, d in parts:
        sig += a * np.sin(2 * np.pi * freq * ratio * t) * np.exp(-d * t)
    return sig * np.minimum(1.0, t / 0.005) * amp


def drone(freq, dur, amp=0.12, detune=0.004):
    """Zumbido grave continuo, base armónica de la pieza."""
    t = np.arange(int(dur * SR)) / SR
    s = (np.sin(2 * np.pi * freq * t)
         + 0.45 * np.sin(2 * np.pi * freq * (1 + detune) * t)
         + 0.22 * np.sin(2 * np.pi * freq * 2 * t))
    lfo = 0.82 + 0.18 * np.sin(2 * np.pi * 0.06 * t)
    env = np.minimum(1.0, t / 1.6) * np.clip((dur - t) / 1.6, 0, 1)
    return s * lfo * env * amp


def wind(dur, amp=0.05):
    """Viento: ruido filtrado con vaivén lento."""
    rng = np.random.default_rng(11)
    x = rng.standard_normal(int(dur * SR))
    k = int(0.03 * SR)
    kernel = np.hanning(k)
    kernel /= kernel.sum()
    x = np.convolve(x, kernel, mode="same")
    t = np.arange(len(x)) / SR
    env = 0.55 + 0.45 * np.sin(2 * np.pi * 0.045 * t + 1.2)
    return x * env * amp


# ---------------------------------------------------------------------------
# Mezcla
# ---------------------------------------------------------------------------
def loop_buf(seconds):
    return np.zeros(int(seconds * SR))


def add(buf, sig, at):
    """Suma una señal con envoltura circular (bucle sin costuras)."""
    n = len(buf)
    i = int(at * SR) % n
    if i + len(sig) <= n:
        buf[i:i + len(sig)] += sig
    else:
        k = n - i
        buf[i:] += sig[:k]
        buf[:len(sig) - k] += sig[k:]


def reverb(x, wet=0.26, decay=2.4, length=1.3):
    n = int(length * SR)
    rng = np.random.default_rng(5)
    ir = rng.standard_normal(n) * np.exp(-decay * np.arange(n) / SR)
    ir[0] = 1.0
    ir /= np.abs(ir).sum() * 0.12 + 1.0
    size = 1 << (len(x) + n - 1).bit_length()
    y = np.fft.irfft(np.fft.rfft(x, size) * np.fft.rfft(ir, size), size)[:len(x)]
    return x * (1 - wet) + y * wet


def write_ogg(name, buf, quality=4):
    os.makedirs(OUT, exist_ok=True)
    peak = np.max(np.abs(buf)) or 1.0
    data = np.clip(buf / peak * 0.82, -1, 1)
    samples = (data * 32767).astype(np.int16)
    wav = os.path.join(OUT, name + ".wav")
    ogg = os.path.join(OUT, name + ".ogg")
    with wave.open(wav, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(SR)
        f.writeframes(samples.tobytes())
    subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", wav,
                    "-c:a", "libvorbis", "-q:a", str(quality), "-ac", "1", ogg],
                   check=True)
    os.remove(wav)
    print("  %-10s %5.1f s  %4d KB" % (name + ".ogg", len(buf) / SR,
                                       os.path.getsize(ogg) // 1024))


# ---------------------------------------------------------------------------
# Piezas
# ---------------------------------------------------------------------------
def menu_theme():
    dur = 32.0
    b = loop_buf(dur)
    add(b, drone(n("D2"), dur, 0.10), 0)
    add(b, drone(n("A2"), dur, 0.05), 0)
    # campanas lejanas
    for at, note in ((0.4, "D4"), (8.2, "A3"), (16.3, "D4"), (24.1, "F4")):
        add(b, bell(n(note), 5.0, 0.14), at)
    # melodía de koto
    melody = [(0.0, "D3"), (2.1, "F3"), (4.3, "G3"), (6.4, "A3"),
              (8.6, "C4"), (10.8, "A3"), (13.0, "G3"), (15.2, "F3"),
              (17.4, "D3"), (19.7, "F3"), (21.9, "A3"), (24.2, "C4"),
              (26.5, "D4"), (28.6, "C4"), (30.7, "A3")]
    for at, note in melody:
        add(b, pluck(n(note), 3.0, 0.30, 3.0, 0.48), at)
    # flauta
    for at, note, ln in ((4.0, "A3", 3.2), (12.6, "D4", 3.6),
                         (20.7, "C4", 3.0), (28.4, "A3", 3.4)):
        add(b, flute(n(note), ln, 0.16), at)
    return reverb(b, 0.3, 2.2, 1.5)


def market_theme():
    dur = 32.0
    b = loop_buf(dur)
    add(b, drone(n("D3"), dur, 0.06), 0)
    # pulso de taiko (negras a 96 bpm)
    beat = 0.625
    t = 0.0
    i = 0
    while t < dur:
        add(b, taiko(0.45, 0.46 if i % 4 == 0 else 0.24), t)
        t += beat
        i += 1
    # arpegio de koto en corcheas
    order = ["D3", "F3", "A3", "C4", "D4", "C4", "A3", "F3"]
    step = beat / 2
    for k in range(int(dur / step)):
        note = order[k % len(order)]
        add(b, pluck(n(note), 1.6, 0.20, 4.2, 0.55), k * step)
    # motivo de flauta cada 8 s
    for at, seq in ((1.2, [("D4", 0.5), ("C4", 0.5), ("A3", 0.9)]),
                    (9.2, [("F4", 0.5), ("D4", 0.5), ("C4", 0.9)]),
                    (17.2, [("D4", 0.5), ("F4", 0.5), ("G4", 0.9)]),
                    (25.2, [("A4", 0.5), ("G4", 0.5), ("D4", 0.9)])):
        at2 = at
        for note, ln in seq:
            add(b, flute(n(note), ln, 0.12), at2)
            at2 += ln * 0.85
    return reverb(b, 0.2, 2.8, 1.0)


def warehouse_theme():
    dur = 28.0
    b = loop_buf(dur)
    add(b, drone(n("D2"), dur, 0.13), 0)
    add(b, drone(n("F3"), dur, 0.035), 0)
    add(b, wind(dur, 0.055), 0)
    # gotas / cuerdas tensas
    for at, note in ((1.0, "D3"), (5.6, "F3"), (9.4, "A2"), (13.2, "D3"),
                     (17.0, "C3"), (21.4, "A2"), (25.2, "D3")):
        add(b, pluck(n(note), 2.6, 0.24, 3.6, 0.42), at)
    # golpes lejanos
    for at in (0.2, 13.8):
        add(b, taiko(0.8, 0.22, 70, 38), at)
    add(b, bell(n("D3"), 6.0, 0.08), 7.0)
    return reverb(b, 0.42, 2.0, 2.0)


def castle_theme():
    """Tensión de amanecer: tambor lento, zumbido grave y campana rota."""
    dur = 32.0
    b = loop_buf(dur)
    add(b, drone(n("D2"), dur, 0.15), 0)
    add(b, drone(n("C3"), dur, 0.04), 0)
    add(b, wind(dur, 0.05), 0)
    # pulso de taiko lento y pesado (una negra cada dos tiempos)
    beat = 1.9
    t = 0.0
    i = 0
    while t < dur:
        add(b, taiko(0.9, 0.40 if i % 4 == 0 else 0.20, 78, 40), t)
        t += beat
        i += 1
    # campana grave al principio de cada frase
    for at in (0.6, 8.8, 17.2, 25.6):
        add(b, bell(n("D3"), 7.0, 0.13), at)
    add(b, bell(n("F3"), 6.0, 0.06), 4.4)
    # motivo de flauta corto, casi un lamento
    for at, note, ln in ((3.4, "A3", 2.4), (11.6, "F3", 2.8),
                         (20.2, "C4", 2.4), (28.0, "A3", 2.6)):
        add(b, flute(n(note), ln, 0.13), at)
    # cuerdas pulsadas graves
    for at, note in ((2.2, "D3"), (6.6, "A2"), (14.8, "C3"), (23.4, "D3")):
        add(b, pluck(n(note), 3.4, 0.18, 3.2, 0.40), at)
    return reverb(b, 0.45, 1.9, 2.2)


def epilogue_theme():
    dur = 28.0
    b = loop_buf(dur)
    add(b, drone(n("D3"), dur, 0.08), 0)
    add(b, drone(n("A2"), dur, 0.05), 0)
    add(b, bell(n("D4"), 6.0, 0.10), 0.3)
    add(b, bell(n("A3"), 6.0, 0.07), 20.5)
    melody = [(0.0, "D4", 3.4), (3.8, "C4", 3.0), (7.0, "A3", 3.6),
              (11.0, "F3", 3.2), (14.4, "G3", 3.0), (17.6, "A3", 3.4),
              (21.2, "C4", 3.0), (24.6, "D4", 3.2)]
    for at, note, ln in melody:
        add(b, flute(n(note), ln, 0.15), at)
    for at, note in ((2.0, "D4"), (6.2, "A3"), (10.4, "F4"), (14.8, "G3"),
                     (19.0, "C4"), (23.4, "A3")):
        add(b, pluck(n(note), 2.8, 0.16, 3.6, 0.45), at)
    return reverb(b, 0.34, 2.2, 1.6)


# ---------------------------------------------------------------------------
def main():
    global FFMPEG
    FFMPEG = shutil.which("ffmpeg")
    if not FFMPEG:
        raise SystemExit("ffmpeg no está en el PATH")
    os.makedirs(OUT, exist_ok=True)
    print("Música ->", OUT)
    for name, fn in (("menu", menu_theme), ("market", market_theme),
                     ("warehouse", warehouse_theme), ("castle", castle_theme),
                     ("epilogue", epilogue_theme)):
        write_ogg(name, fn())


if __name__ == "__main__":
    main()
