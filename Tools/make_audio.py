"""Synteza zvuku pro Galerii o pulnoci: dest, hrom, kroky po mramoru, zvonky. Dozvuk haly je zapecen konvoluci."""
import os, wave, numpy as np
from scipy.signal import butter, sosfilt, fftconvolve
SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'SourceAssets', 'Audio')
os.makedirs(OUT, exist_ok=True)
rng = np.random.default_rng(7)
def bp(x, lo, hi, order=2):
    if lo and hi: sos = butter(order, [lo, hi], 'bandpass', fs=SR, output='sos')
    elif lo: sos = butter(order, lo, 'highpass', fs=SR, output='sos')
    else: sos = butter(order, hi, 'lowpass', fs=SR, output='sos')
    return sosfilt(sos, x, axis=0)
def norm(x, peak=0.89): return x * (peak / (np.max(np.abs(x)) + 1e-9))
def write(name, x):
    x = np.clip(x, -1, 1)
    if x.ndim == 1: x = x[:, None]
    w = wave.open(os.path.join(OUT, name + '.wav'), 'wb')
    w.setnchannels(x.shape[1]); w.setsampwidth(2); w.setframerate(SR)
    w.writeframes((x * 32767).astype('<i2').tobytes()); w.close(); print(name, round(len(x) / SR, 2), 's')
def hall_ir(t60=2.6, seed=1, bright=5200):
    r = np.random.default_rng(seed); n = int(SR * t60 * 1.15); t = np.arange(n) / SR
    ir = r.standard_normal(n) * np.exp(-6.9 * t / t60)
    ir = bp(ir, 110, bright)
    # hi frekvence dozniv. rychleji
    ir = ir * 0.6 + bp(ir, 0, 1400) * np.exp(-1.0 * t) * 1.2
    # rane odrazy od sten
    for d, g in ((0.011, .55), (0.019, .45), (0.031, .38), (0.047, .3), (0.071, .22)):
        k = int(d * SR); ir[k] += g * 6 * r.choice([-1, 1])
    ir[:int(0.004 * SR)] *= 0.0
    return ir / np.sqrt(np.sum(ir ** 2))
IRL, IRR = hall_ir(seed=1), hall_ir(seed=2)
def reverb(x, wet=0.35, ir=IRL, tail=2.8):
    x = np.concatenate([x, np.zeros(int(tail * SR))])
    w = fftconvolve(x, ir)[:len(x)]
    return x * (1 - wet * 0.3) + w * wet
def loopify(x, fade=2.0):
    n = int(fade * SR); body = x[n:-n].copy() if False else x.copy()
    a = x[:n]; b = x[-n:]; t = np.linspace(0, 1, n)
    if x.ndim == 2: t = t[:, None]
    head = b * np.cos(t * np.pi / 2) + a * np.sin(t * np.pi / 2)
    return np.concatenate([head, x[n:-n]])

# ---------- dest + ticho velke haly (stereo smycka) ----------
def rain(seconds=24.0):
    n = int(seconds * SR); ch = []
    for s in (11, 12):
        r = np.random.default_rng(s)
        w = r.standard_normal(n)
        hiss = bp(w, 1800, 9000) * 0.20                      # jemny sum deste venku
        body = bp(r.standard_normal(n), 300, 1500) * 0.16    # dest na strese
        rumble = bp(r.standard_normal(n), 30, 110) * 0.28    # vzduchotechnika / mistnost
        slow = 1 + 0.25 * np.sin(2 * np.pi * np.arange(n) / SR / 7.3 + s) + 0.12 * np.sin(2 * np.pi * np.arange(n) / SR / 2.9)
        x = (hiss + body) * slow + rumble
        # kapky na sklo: kratke rezonujici tiky
        drops = np.zeros(n)
        for _ in range(int(seconds * 26)):
            p = r.integers(0, n - 2000); f = r.uniform(1800, 6500); L = r.integers(120, 700)
            tt = np.arange(L) / SR
            drops[p:p + L] += r.uniform(0.05, 0.5) ** 2 * np.sin(2 * np.pi * f * tt) * np.exp(-tt * r.uniform(60, 240))
        # obcasne tezsi kapky z rimsy
        for _ in range(int(seconds * 2.2)):
            p = r.integers(0, n - 4000); f = r.uniform(380, 900); L = 3000; tt = np.arange(L) / SR
            drops[p:p + L] += 0.22 * np.sin(2 * np.pi * f * tt * (1 + 2.5 * tt)) * np.exp(-tt * 45)
        x = x + fftconvolve(drops, hall_ir(1.6, s + 20, 7000))[:n] * 0.5 + drops * 0.35
        ch.append(x)
    x = np.stack(ch, 1)
    # trocha korelace L/R
    x = x * 0.8 + x[:, ::-1] * 0.2
    return norm(loopify(x, 2.5), 0.55)
write('amb_rain', rain())

# ---------- hrom ----------
def thunder(seed, seconds=11.0):
    r = np.random.default_rng(seed); n = int(seconds * SR); t = np.arange(n) / SR
    x = np.zeros(n)
    for start, amp, dec in ((0.0, 1.0, 1.1), (0.35, 0.7, 1.6), (1.1, 0.8, 2.2), (2.4, 0.5, 3.0), (4.0, 0.35, 3.5)):
        k = int(start * SR); e = np.exp(-(t[:n - k]) / dec) * (1 - np.exp(-(t[:n - k]) * 40))
        x[k:] += amp * r.standard_normal(n - k) * e
    crack = bp(x, 400, 2500) * np.exp(-t * 2.2) * 0.5
    low = bp(x, 22, 140, 3) * 2.2
    mod = 1 + 0.5 * bp(r.standard_normal(n), 0, 6) * 30
    y = (low * np.clip(mod, 0.2, 2.5) + crack)
    yl = fftconvolve(y, hall_ir(3.2, seed + 1, 1800))[:n]; yr = fftconvolve(y, hall_ir(3.2, seed + 2, 1800))[:n]
    out = np.stack([y * 0.5 + yl, y * 0.5 + yr], 1)
    fade = np.minimum(1, (seconds - t) / 2.5)[:, None]
    return norm(bp(out, 0, 3000) * fade, 0.85)
write('thunder_1', thunder(31)); write('thunder_2', thunder(47, 9.0))

# ---------- kroky po lestenem mramoru ----------
def step(seed):
    r = np.random.default_rng(seed); n = int(0.30 * SR); t = np.arange(n) / SR
    heel = bp(r.standard_normal(n), 900, 4200) * np.exp(-t * r.uniform(140, 200))            # klapnuti podpatku
    thud = np.sin(2 * np.pi * r.uniform(95, 130) * t * (1 - 0.6 * t)) * np.exp(-t * 55) * 0.9  # telo kroku
    k = int(r.uniform(0.055, 0.08) * SR)
    toe = np.zeros(n); toe[k:] = (bp(r.standard_normal(n), 1500, 6000) * np.exp(-t * 260))[:n - k] * 0.45  # spicka
    scuff = bp(r.standard_normal(n), 2500, 8000) * np.exp(-((t - 0.05) / 0.03) ** 2) * 0.07
    dry = heel * 0.8 + thud + toe + scuff
    return norm(reverb(dry, wet=0.42, ir=hall_ir(2.4, seed + 100)), r.uniform(0.6, 0.75))
for i in range(6): write('step_%d' % (i + 1), step(60 + i))

# ---------- sebrani svetla: sklenene zvonky ----------
def bell(f0, dur=2.6, seed=0):
    t = np.arange(int(dur * SR)) / SR; x = np.zeros_like(t)
    for ratio, a, d in ((1, 1, 1.6), (2.76, .55, 1.0), (5.40, .32, .6), (8.93, .18, .35), (0.5, .25, 2.0), (13.3, .08, .2)):
        x += a * np.sin(2 * np.pi * f0 * ratio * t + seed * ratio) * np.exp(-t / d)
    return x * (1 - np.exp(-t * 900))
def pickup():
    n = int(3.4 * SR); x = np.zeros(n)
    for i, (f, dly) in enumerate(((880, 0), (1108.7, 0.09), (1318.5, 0.18), (1760, 0.30))):
        b = bell(f, 2.4, i) * (0.9 - i * 0.12); k = int(dly * SR); x[k:k + len(b)] += b[:n - k]
    sp = bp(rng.standard_normal(n), 6000, 14000) * np.exp(-np.arange(n) / SR * 6) * 0.08
    y = x + sp
    return norm(np.stack([reverb(y, .45, IRL)[:n], reverb(y, .45, IRR)[:n]], 1), 0.8)
write('pickup', pickup())

# ---------- hlas svetla: 3D smycka, podle ktere se da svetlo najit sluchem ----------
def orb_hum(seconds=6.0):
    n = int(seconds * SR); t = np.arange(n) / SR; x = np.zeros(n)
    for f, a, beat in ((220, .5, 1 / 3), (330, .35, 1 / 2), (440.5, .3, 2 / 3), (660, .22, 1 / 6), (1320, .1, 5 / 6), (1760.0, .06, 1 / 2)):
        f = round(f * seconds) / seconds   # cele pocty period => bezesva smycka
        x += a * np.sin(2 * np.pi * f * t) * (0.6 + 0.4 * np.sin(2 * np.pi * beat * t + f))
    air = bp(rng.standard_normal(n), 3000, 9000) * 0.03 * (1 + np.sin(2 * np.pi * t / 3))
    return norm(x + air, 0.5)
write('orb_hum', orb_hum())

# ---------- vyhra / prohra ----------
def win():
    n = int(6 * SR); x = np.zeros(n)
    for i, f in enumerate((261.6, 329.6, 392, 523.3, 659.3, 784, 1046.5)):
        b = bell(f, 4.5, i) * 0.6; k = int(i * 0.16 * SR); x[k:k + len(b)] += b[:n - k]
    return norm(np.stack([reverb(x, .5, IRL)[:n], reverb(x, .5, IRR)[:n]], 1), 0.8)
def lose():
    n = int(5 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 55 * t * (1 - 0.05 * t)) * np.exp(-t * 0.9) + 0.5 * np.sin(2 * np.pi * 82.4 * t) * np.exp(-t * 1.2)
    x += bp(rng.standard_normal(n), 60, 500) * np.exp(-t * 3) * 0.8      # zabouchnuti dveri
    lock = np.zeros(n); k = int(0.9 * SR); L = 2000; tt = np.arange(L) / SR
    lock[k:k + L] = np.sin(2 * np.pi * 2300 * tt) * np.exp(-tt * 300) * 0.5
    x += lock
    return norm(np.stack([reverb(x, .5, IRL)[:n], reverb(x, .5, IRR)[:n]], 1), 0.85)
write('win', win()); write('lose', lose())

# ---------- tikot hodin (poslednich 20 s) ----------
def tick():
    n = int(1.0 * SR); t = np.arange(n) / SR; x = np.zeros(n)
    c = bp(rng.standard_normal(n), 2500, 7000) * np.exp(-t * 500) + 0.5 * np.sin(2 * np.pi * 3100 * t) * np.exp(-t * 400)
    x += c; k = int(0.5 * SR); x[k:] += 0.7 * c[:n - k]
    return norm(reverb(x, .3, hall_ir(1.5, 9))[:n], 0.5)
write('tick', tick())
