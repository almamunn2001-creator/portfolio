"""Procedural flat-illustration scenes (silhouette style) for faceless videos.

Each scene function draws onto a supersampled RGBA canvas and returns a PIL image.
"""
import math
import random

from PIL import Image, ImageDraw, ImageFilter

SS = 2  # supersampling factor for smooth edges


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(len(a)))


def gradient(w, h, stops):
    """Vertical gradient. stops: list of (pos 0..1, (r,g,b))."""
    img = Image.new("RGB", (w, h))
    px = img.load()
    col = []
    for y in range(h):
        t = y / (h - 1)
        for i in range(len(stops) - 1):
            p0, c0 = stops[i]
            p1, c1 = stops[i + 1]
            if p0 <= t <= p1:
                col.append(lerp(c0, c1, (t - p0) / max(p1 - p0, 1e-6)))
                break
        else:
            col.append(stops[-1][1])
    row = Image.new("RGB", (1, h))
    row.putdata(col)
    return row.resize((w, h)).convert("RGBA")


def glow(img, xy, r, color, strength=1.0):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = xy
    for i in range(12, 0, -1):
        rr = r * i / 4
        a = int(255 * strength * (1 - i / 13) ** 2 * 0.5)
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=color + (a,))
    layer = layer.filter(ImageFilter.GaussianBlur(r / 2))
    return Image.alpha_composite(img, layer)


def stars(d, w, h, n, seed=1, ymax=0.6):
    rnd = random.Random(seed)
    for _ in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h * ymax)
        r = rnd.uniform(1, 3.2) * SS
        a = rnd.randint(90, 255)
        d.ellipse([x - r, y - r, x + r, y + r], fill=(255, 255, 240, a))


def hills(d, w, h, base, amp, color, seed=0, freq=2.0):
    rnd = random.Random(seed)
    ph = [rnd.uniform(0, 6.28) for _ in range(3)]
    pts = [(0, h)]
    for x in range(0, w + 20, 20):
        t = x / w
        y = base + amp * (math.sin(t * freq * 3.14 + ph[0]) * 0.6
                          + math.sin(t * freq * 7.1 + ph[1]) * 0.3
                          + math.sin(t * freq * 13.3 + ph[2]) * 0.1)
        pts.append((x, y))
    pts.append((w, h))
    d.polygon(pts, fill=color)


# ---------------------------------------------------------------- figures

def person(d, x, feet, h, color, pose="stand", facing=1, hair=False):
    """Draw a simple silhouette. h = full standing height in px."""
    u = h / 8.0  # head unit
    f = facing

    def P(dx, dy):
        return (x + dx * u * f, feet - dy * u)

    if pose == "stand":
        d.ellipse([x - 0.5 * u, feet - 8 * u, x + 0.5 * u, feet - 6.9 * u], fill=color)
        d.polygon([P(-0.25, 6.95), P(0.25, 6.95), P(0.3, 6.6)], fill=color)
        d.polygon([P(-0.95, 6.6), P(0.95, 6.6), P(0.75, 3.9), P(-0.75, 3.9)], fill=color)
        d.polygon([P(-0.75, 4.1), P(0.75, 4.1), P(0.5, 0), P(0.1, 0), P(0, 3.4), P(-0.1, 0), P(-0.5, 0)], fill=color)
        d.polygon([P(-0.95, 6.5), P(-0.7, 6.5), P(-0.85, 3.6), P(-1.15, 3.7)], fill=color)
        d.polygon([P(0.95, 6.5), P(0.7, 6.5), P(0.85, 3.6), P(1.15, 3.7)], fill=color)
        if hair:
            d.polygon([P(-0.55, 7.6), P(0.55, 7.6), P(0.75, 5.6), P(-0.75, 5.6)], fill=color)
    elif pose == "child":
        d.ellipse([x - 0.6 * u, feet - 5.4 * u, x + 0.6 * u, feet - 4.1 * u], fill=color)
        d.polygon([P(-0.7, 4.1), P(0.7, 4.1), P(0.6, 2.0), P(-0.6, 2.0)], fill=color)
        d.polygon([P(-0.55, 2.1), P(0.55, 2.1), P(0.4, 0), P(0.08, 0), P(0, 1.6), P(-0.08, 0), P(-0.4, 0)], fill=color)
        # arm reaching up
        d.polygon([P(0.55, 3.9), P(0.75, 3.9), P(1.2, 6.0), P(0.95, 6.1)], fill=color)
        d.polygon([P(-0.7, 3.9), P(-0.5, 3.9), P(-0.7, 2.2), P(-0.9, 2.3)], fill=color)
    elif pose == "sit_ground":  # hugging knees
        d.ellipse([x - 0.5 * u, feet - 4.6 * u, x + 0.5 * u, feet - 3.5 * u], fill=color)
        d.polygon([P(-0.9, 3.6), P(0.5, 3.6), P(0.7, 0.4), P(-1.2, 0.2), P(-1.3, 1.2)], fill=color)
        d.polygon([P(0.3, 3.0), P(1.9, 2.2), P(1.9, 0), P(1.5, 0), P(1.4, 1.6), P(0.4, 0.8)], fill=color)
        d.polygon([P(-1.4, 0.3), P(1.9, 0.3), P(1.9, 0), P(-1.4, 0)], fill=color)
    elif pose == "bench":  # sitting on something at height ~2.2u
        d.ellipse([x - 0.5 * u, feet - 6.6 * u, x + 0.5 * u, feet - 5.5 * u], fill=color)
        d.polygon([P(-0.85, 5.55), P(0.75, 5.55), P(0.7, 2.4), P(-0.75, 2.2)], fill=color)
        d.polygon([P(-0.75, 2.8), P(0.6, 2.8), P(1.9, 2.6), P(1.9, 2.0), P(-0.75, 1.9)], fill=color)
        d.polygon([P(1.5, 2.4), P(1.95, 2.4), P(1.85, 0), P(1.5, 0)], fill=color)
        d.polygon([P(0.6, 5.3), P(0.8, 5.2), P(1.4, 3.0), P(1.1, 2.8)], fill=color)
    elif pose == "old":  # bent with cane
        d.ellipse([x + 0.3 * u * f - 0.5 * u, feet - 7.2 * u, x + 0.3 * u * f + 0.5 * u, feet - 6.1 * u], fill=color)
        d.polygon([P(-0.9, 6.2), P(0.6, 6.4), P(0.7, 3.7), P(-0.8, 3.7)], fill=color)
        d.polygon([P(-0.7, 3.9), P(0.7, 3.9), P(0.5, 0), P(0.12, 0), P(0, 3.0), P(-0.12, 0), P(-0.5, 0)], fill=color)
        d.polygon([P(0.5, 6.0), P(0.75, 5.9), P(1.6, 4.2), P(1.35, 4.0)], fill=color)
        d.line([P(1.5, 4.3), P(1.75, 0)], fill=color, width=int(0.18 * u))
        d.arc([P(1.25, 4.6)[0] - 0.3 * u, feet - 4.6 * u, P(1.25, 4.6)[0] + 0.3 * u, feet - 4.0 * u],
              180, 360, fill=color, width=int(0.15 * u))
    elif pose == "kneel":
        d.ellipse([x + 0.4 * u * f - 0.5 * u, feet - 5.4 * u, x + 0.4 * u * f + 0.5 * u, feet - 4.3 * u], fill=color)
        d.polygon([P(-0.9, 4.4), P(0.9, 4.6), P(0.6, 2.0), P(-0.8, 1.9)], fill=color)
        d.polygon([P(-0.8, 2.2), P(0.7, 2.2), P(1.6, 0), P(-1.6, 0), P(-1.2, 1.2)], fill=color)
        d.polygon([P(0.7, 4.3), P(0.95, 4.2), P(1.05, 1.3), P(0.75, 1.3)], fill=color)
        d.polygon([P(-0.85, 4.2), P(-0.6, 4.2), P(-0.6, 1.4), P(-0.9, 1.4)], fill=color)


def tree(d, x, base, h, color, seed=3):
    rnd = random.Random(seed)
    d.polygon([(x - h * 0.03, base), (x + h * 0.03, base), (x + h * 0.015, base - h * 0.55), (x - h * 0.015, base - h * 0.55)], fill=color)
    for _ in range(26):
        cx = x + rnd.uniform(-0.28, 0.28) * h
        cy = base - h * 0.62 + rnd.uniform(-0.2, 0.15) * h
        r = rnd.uniform(0.09, 0.17) * h
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)


def bird(d, x, y, s, color):
    d.line([(x - s, y - s * 0.4), (x, y), (x + s, y - s * 0.4)], fill=color, width=max(2, int(s * 0.18)), joint="curve")


def heart(d, cx, cy, s, color):
    pts = []
    for i in range(80):
        t = i / 80 * 2 * math.pi
        hx = 16 * math.sin(t) ** 3
        hy = 13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)
        pts.append((cx + hx * s / 16, cy - hy * s / 16))
    d.polygon(pts, fill=color)


def skyline(d, w, base, color, seed=5, hmin=0.12, hmax=0.4, h=None, windows=None):
    rnd = random.Random(seed)
    x = -20
    while x < w:
        bw = rnd.uniform(0.06, 0.13) * w
        bh = rnd.uniform(hmin, hmax) * h
        d.rectangle([x, base - bh, x + bw, base], fill=color)
        if windows:
            for wy in range(int(base - bh + 20 * SS), int(base - 10 * SS), int(26 * SS)):
                for wx in range(int(x + 10 * SS), int(x + bw - 14 * SS), int(22 * SS)):
                    if rnd.random() < 0.35:
                        d.rectangle([wx, wy, wx + 8 * SS, wy + 12 * SS], fill=windows)
        x += bw + rnd.uniform(2, 14) * SS


def rain(img, n, seed=9, color=(200, 210, 230, 70)):
    layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(seed)
    w, h = img.size
    for _ in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(0, h)
        L = rnd.uniform(30, 70) * SS
        d.line([(x, y), (x - L * 0.15, y + L)], fill=color, width=SS)
    return Image.alpha_composite(img, layer)


# ---------------------------------------------------------------- scenes

def s_poor(w, h):
    img = gradient(w, h, [(0, (12, 16, 34)), (0.6, (34, 40, 66)), (1, (18, 18, 28))])
    d = ImageDraw.Draw(img)
    skyline(d, w, h * 0.7, (22, 26, 44), seed=2, h=h, windows=(70, 66, 50))
    d.rectangle([0, h * 0.7, w, h], fill=(14, 14, 22))
    # street lamp
    lx = w * 0.72
    d.rectangle([lx - 6 * SS, h * 0.3, lx + 6 * SS, h * 0.78], fill=(8, 8, 12))
    d.rectangle([lx - 60 * SS, h * 0.3, lx + 6 * SS, h * 0.3 + 10 * SS], fill=(8, 8, 12))
    img = glow(img, (lx - 55 * SS, h * 0.315), 70 * SS, (255, 190, 110), 1.2)
    cone = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(cone).polygon([(lx - 70 * SS, h * 0.32), (lx - 40 * SS, h * 0.32), (w * 0.85, h * 0.8), (w * 0.3, h * 0.8)], fill=(255, 190, 110, 40))
    img = Image.alpha_composite(img, cone.filter(ImageFilter.GaussianBlur(20 * SS)))
    d = ImageDraw.Draw(img)
    d.rectangle([w * 0.2, h * 0.52, w * 0.24, h * 0.8], fill=(10, 10, 16))  # wall edge
    person(d, w * 0.45, h * 0.8, h * 0.22, (6, 6, 10), "sit_ground")
    # empty cup with a coin
    d.rectangle([w * 0.62, h * 0.775, w * 0.66, h * 0.8], fill=(6, 6, 10))
    d.ellipse([w * 0.67, h * 0.792, w * 0.69, h * 0.8], fill=(230, 190, 90))
    return rain(img, 500)


def s_rich(w, h):
    img = gradient(w, h, [(0, (8, 10, 30)), (0.55, (40, 30, 80)), (0.75, (120, 60, 90)), (1, (20, 14, 30))])
    d = ImageDraw.Draw(img)
    stars(d, w, h, 160, seed=4, ymax=0.45)
    img = glow(img, (w * 0.25, h * 0.2), 40 * SS, (250, 245, 220), 1.4)
    d = ImageDraw.Draw(img)
    d.ellipse([w * 0.25 - 40 * SS, h * 0.2 - 40 * SS, w * 0.25 + 40 * SS, h * 0.2 + 40 * SS], fill=(250, 245, 225))
    skyline(d, w, h * 0.8, (30, 22, 50), seed=7, h=h, hmin=0.1, hmax=0.3, windows=(255, 210, 120))
    skyline(d, w, h * 0.85, (16, 12, 28), seed=8, h=h, hmin=0.05, hmax=0.18, windows=(255, 200, 110))
    # penthouse balcony
    d.rectangle([0, h * 0.72, w, h], fill=(6, 5, 12))
    for i in range(10):
        bx = w * 0.04 + i * w * 0.07
        d.rectangle([bx, h * 0.64, bx + 5 * SS, h * 0.72], fill=(6, 5, 12))
    d.rectangle([0, h * 0.635, w * 0.7, h * 0.645], fill=(6, 5, 12))
    person(d, w * 0.42, h * 0.72, h * 0.24, (6, 5, 12), "stand", hair=False)
    # wine glass on rail
    gx = w * 0.6
    d.polygon([(gx - 12 * SS, h * 0.6), (gx + 12 * SS, h * 0.6), (gx, h * 0.62)], fill=(6, 5, 12))
    d.line([(gx, h * 0.62), (gx, h * 0.635)], fill=(6, 5, 12), width=3 * SS)
    return img


def s_young(w, h):
    img = gradient(w, h, [(0, (255, 170, 110)), (0.55, (255, 120, 120)), (0.8, (180, 80, 120)), (1, (70, 30, 70))])
    img = glow(img, (w * 0.5, h * 0.62), 110 * SS, (255, 230, 170), 1.3)
    d = ImageDraw.Draw(img)
    d.ellipse([w * 0.5 - 110 * SS, h * 0.62 - 110 * SS, w * 0.5 + 110 * SS, h * 0.62 + 110 * SS], fill=(255, 235, 190))
    hills(d, w, h, h * 0.72, h * 0.02, (120, 50, 90), seed=1)
    hills(d, w, h, h * 0.78, h * 0.015, (40, 16, 40), seed=2)
    tree(d, w * 0.18, h * 0.79, h * 0.38, (40, 16, 40), seed=11)
    # height marks on tree trunk
    for i in range(4):
        y = h * 0.79 - h * (0.05 + i * 0.03)
        d.line([(w * 0.19, y), (w * 0.215, y)], fill=(255, 220, 180), width=2 * SS)
    person(d, w * 0.33, h * 0.79, h * 0.2, (40, 16, 40), "child")
    # big adult shadow ahead
    person(d, w * 0.72, h * 0.79, h * 0.28, (40, 16, 40, 140), "stand")
    for i in range(5):
        bird(d, w * (0.55 + i * 0.07), h * (0.3 + (i % 2) * 0.03), (14 - i) * SS, (90, 40, 70))
    return img


def s_old(w, h):
    img = gradient(w, h, [(0, (60, 70, 110)), (0.5, (200, 140, 120)), (0.75, (240, 180, 130)), (1, (60, 40, 50))])
    img = glow(img, (w * 0.7, h * 0.66), 80 * SS, (255, 220, 160), 1.0)
    d = ImageDraw.Draw(img)
    hills(d, w, h, h * 0.75, h * 0.015, (90, 60, 70), seed=3)
    d.rectangle([0, h * 0.8, w, h], fill=(30, 20, 28))
    tree(d, w * 0.85, h * 0.8, h * 0.45, (30, 20, 28), seed=21)
    person(d, w * 0.4, h * 0.8, h * 0.24, (30, 20, 28), "old")
    # faded memory: child running with kite, translucent
    ghost = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(ghost)
    person(gd, w * 0.66, h * 0.8, h * 0.17, (255, 240, 220, 110), "child")
    kx, ky = w * 0.62, h * 0.3
    gd.polygon([(kx, ky - 40 * SS), (kx + 30 * SS, ky), (kx, ky + 50 * SS), (kx - 30 * SS, ky)], fill=(255, 240, 220, 130))
    gd.line([(kx, ky + 50 * SS), (w * 0.69, h * 0.68)], fill=(255, 240, 220, 110), width=2 * SS)
    img = Image.alpha_composite(img, ghost.filter(ImageFilter.GaussianBlur(2 * SS)))
    # falling leaves
    d = ImageDraw.Draw(img)
    rnd = random.Random(5)
    for _ in range(30):
        x, y = rnd.uniform(0, w), rnd.uniform(h * 0.2, h * 0.8)
        s = rnd.uniform(6, 12) * SS
        d.ellipse([x - s, y - s / 2, x + s, y + s / 2], fill=(150, 70, 40, 200))
    return img


def s_married(w, h):
    img = gradient(w, h, [(0, (20, 24, 36)), (1, (40, 36, 44))])
    d = ImageDraw.Draw(img)
    # window opening onto bright sky
    wx0, wy0, wx1, wy1 = w * 0.22, h * 0.18, w * 0.78, h * 0.62
    sky = gradient(int(wx1 - wx0), int(wy1 - wy0), [(0, (120, 180, 230)), (1, (230, 220, 200))])
    img.paste(sky, (int(wx0), int(wy0)))
    d = ImageDraw.Draw(img)
    for i in range(7):
        bird(d, w * (0.32 + i * 0.065), h * (0.27 + math.sin(i) * 0.03), (16 - i) * SS, (40, 50, 70))
    d.rectangle([w * 0.495, wy0, w * 0.505, wy1], fill=(14, 16, 24))
    d.rectangle([wx0, h * 0.4, wx1, h * 0.405], fill=(14, 16, 24))
    # bars hint of a cage on the window
    for i in range(1, 8):
        bx = wx0 + (wx1 - wx0) * i / 8
        d.line([(bx, wy0), (bx, wy1)], fill=(14, 16, 24, 160), width=3 * SS)
    d.rectangle([wx0 - 20 * SS, wy1, wx1 + 20 * SS, wy1 + 18 * SS], fill=(10, 10, 16))
    img = glow(img, (w * 0.5, h * 0.4), 140 * SS, (200, 220, 255), 0.5)
    d = ImageDraw.Draw(img)
    d.rectangle([0, h * 0.86, w, h], fill=(10, 10, 16))
    person(d, w * 0.5, h * 0.86, h * 0.3, (10, 10, 16), "stand")
    # ring glint
    img = glow(img, (w * 0.5 + h * 0.3 / 8 * 1.0, h * 0.86 - h * 0.3 / 8 * 3.7), 8 * SS, (255, 220, 120), 2.0)
    return img


def s_single(w, h):
    img = gradient(w, h, [(0, (30, 30, 60)), (0.6, (90, 70, 110)), (1, (30, 24, 40))])
    d = ImageDraw.Draw(img)
    stars(d, w, h, 80, seed=6, ymax=0.4)
    skyline(d, w, h * 0.78, (50, 40, 70), seed=12, h=h, hmin=0.06, hmax=0.2, windows=(255, 200, 140))
    d.rectangle([0, h * 0.78, w, h], fill=(16, 14, 24))
    # bench
    d.rectangle([w * 0.18, h * 0.745, w * 0.58, h * 0.755], fill=(10, 8, 16))
    d.rectangle([w * 0.2, h * 0.755, w * 0.215, h * 0.78], fill=(10, 8, 16))
    d.rectangle([w * 0.545, h * 0.755, w * 0.56, h * 0.78], fill=(10, 8, 16))
    d.rectangle([w * 0.18, h * 0.69, w * 0.58, h * 0.7], fill=(10, 8, 16))
    person(d, w * 0.28, h * 0.78, h * 0.21, (10, 8, 16), "bench")
    # empty side of bench + floating heart balloon
    img = glow(img, (w * 0.7, h * 0.33), 60 * SS, (255, 90, 120), 1.0)
    d = ImageDraw.Draw(img)
    heart(d, w * 0.7, h * 0.33, 60 * SS, (230, 60, 90))
    d.line([(w * 0.7, h * 0.33 + 55 * SS), (w * 0.66, h * 0.5), (w * 0.68, h * 0.6)], fill=(230, 200, 210, 150), width=2 * SS)
    # lamp
    lx = w * 0.85
    d.rectangle([lx - 5 * SS, h * 0.45, lx + 5 * SS, h * 0.78], fill=(10, 8, 16))
    img = glow(img, (lx, h * 0.45), 50 * SS, (255, 200, 140), 1.0)
    return img


def s_broken(w, h):
    img = gradient(w, h, [(0, (10, 12, 22)), (0.7, (28, 30, 48)), (1, (10, 10, 18))])
    img = glow(img, (w * 0.5, h * 0.45), 160 * SS, (120, 140, 220), 0.5)
    d = ImageDraw.Draw(img)
    d.rectangle([0, h * 0.8, w, h], fill=(8, 8, 14))
    person(d, w * 0.42, h * 0.8, h * 0.28, (6, 6, 10), "kneel")
    # cracked glowing heart held in front
    hx, hy, s = w * 0.62, h * 0.48, 90 * SS
    img = glow(img, (hx, hy), 90 * SS, (255, 90, 110), 1.3)
    d = ImageDraw.Draw(img)
    heart(d, hx, hy, s, (220, 50, 80))
    crack = [(hx - 10 * SS, hy - 70 * SS), (hx + 12 * SS, hy - 35 * SS), (hx - 14 * SS, hy - 5 * SS),
             (hx + 16 * SS, hy + 25 * SS), (hx - 4 * SS, hy + 60 * SS)]
    d.line(crack, fill=(10, 10, 18), width=7 * SS, joint="curve")
    # gold mending (kintsugi) on part of the crack - healing
    d.line(crack[2:], fill=(255, 200, 90), width=4 * SS, joint="curve")
    # shards falling
    rnd = random.Random(3)
    for _ in range(8):
        x, y = hx + rnd.uniform(-60, 60) * SS, hy + rnd.uniform(90, 300) * SS
        s2 = rnd.uniform(6, 14) * SS
        d.polygon([(x, y - s2), (x + s2 * 0.6, y), (x - s2 * 0.3, y + s2 * 0.7)], fill=(220, 50, 80, 200))
    return rain(img, 350, seed=4, color=(170, 180, 230, 60))


def s_truth(w, h):
    img = gradient(w, h, [(0, (6, 8, 24)), (0.6, (24, 30, 70)), (1, (8, 8, 20))])
    d = ImageDraw.Draw(img)
    stars(d, w, h, 260, seed=9, ymax=0.75)
    img = glow(img, (w * 0.5, h * 0.42), 220 * SS, (230, 230, 255), 0.9)
    d = ImageDraw.Draw(img)
    d.ellipse([w * 0.5 - 220 * SS, h * 0.42 - 220 * SS, w * 0.5 + 220 * SS, h * 0.42 + 220 * SS], fill=(235, 236, 250))
    for cx, cy, r in [(0.43, 0.38, 30), (0.56, 0.47, 45), (0.52, 0.34, 18)]:
        d.ellipse([w * cx - r * SS, h * cy - r * SS, w * cx + r * SS, h * cy + r * SS], fill=(215, 216, 235))
    # cliff
    d.polygon([(0, h * 0.7), (w * 0.35, h * 0.68), (w * 0.62, h * 0.7), (w * 0.66, h * 0.76), (w * 0.6, h), (0, h)], fill=(6, 6, 14))
    hills(d, w, h, h * 0.88, h * 0.01, (10, 10, 22), seed=8)
    person(d, w * 0.48, h * 0.69, h * 0.17, (6, 6, 14), "stand")
    return img


def s_happy(w, h):
    img = gradient(w, h, [(0, (90, 150, 220)), (0.45, (250, 200, 150)), (0.7, (255, 170, 110)), (1, (120, 90, 60))])
    img = glow(img, (w * 0.5, h * 0.66), 150 * SS, (255, 240, 190), 1.6)
    d = ImageDraw.Draw(img)
    d.ellipse([w * 0.5 - 90 * SS, h * 0.66 - 90 * SS, w * 0.5 + 90 * SS, h * 0.66 + 90 * SS], fill=(255, 245, 210))
    # sun rays
    rays = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(rays)
    for i in range(14):
        a = i / 14 * math.pi * 2
        rd.polygon([(w * 0.5, h * 0.66), (w * 0.5 + math.cos(a) * h, h * 0.66 + math.sin(a) * h),
                    (w * 0.5 + math.cos(a + 0.08) * h, h * 0.66 + math.sin(a + 0.08) * h)], fill=(255, 240, 200, 35))
    img = Image.alpha_composite(img, rays.filter(ImageFilter.GaussianBlur(8 * SS)))
    d = ImageDraw.Draw(img)
    hills(d, w, h, h * 0.73, h * 0.02, (150, 110, 90), seed=4)
    hills(d, w, h, h * 0.8, h * 0.03, (70, 60, 40), seed=5, freq=1.2)
    person(d, w * 0.35, h * 0.79, h * 0.2, (40, 32, 24), "sit_ground")
    # flowers
    rnd = random.Random(2)
    for _ in range(70):
        x, y = rnd.uniform(0, w), rnd.uniform(h * 0.81, h)
        r = rnd.uniform(5, 10) * SS
        c = rnd.choice([(255, 220, 120), (255, 160, 170), (255, 255, 240), (250, 130, 90)])
        d.line([(x, y), (x, y + 24 * SS)], fill=(50, 70, 30), width=2 * SS)
        d.ellipse([x - r, y - r, x + r, y + r], fill=c)
    for i in range(4):
        bird(d, w * (0.6 + i * 0.06), h * (0.42 - i * 0.02), 12 * SS, (90, 70, 60))
    return img


SCENES = {
    "poor": s_poor, "rich": s_rich, "young": s_young, "old": s_old,
    "married": s_married, "single": s_single, "broken": s_broken,
    "truth": s_truth, "happy": s_happy,
}


def render(name, w, h):
    img = SCENES[name](w * SS, h * SS)
    return img.convert("RGB").resize((w, h), Image.LANCZOS)
