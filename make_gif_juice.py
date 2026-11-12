"""Versi 'full juice': 4 beat, tiap beat semua kotak tukar gambar dengan efek beda
(slide, zoom-blink, glitch RGB), plus screen shake, flash, zoom napas, dan kerlip bintang.
Loop mulus: swap A, swap B, balik B, balik A.

Pakai:  python3 make_gif_juice.py  -> phos-collage-juice.gif
"""
import glob, math, os, random
from PIL import Image, ImageOps, ImageChops, ImageDraw

SCALE = 0.65
W, GAP, BG = round(790 * SCALE), 6, (13, 17, 23)
ROWS = [(210, [1]), (145, [1, 2.1, 1]), (185, [1.5, 1.25, 1.2]), (180, [1, 1.3]), (190, [1])]
CENTER = {0: (0.5, 0.1)}
SIG1 = [(0, 9), (1, 3), (4, 6), (7, 8), (2, 5)]
SIG2 = [(0, 2), (1, 4), (3, 6), (5, 8), (7, 9)]
BEATS = [SIG1, SIG2, SIG2, SIG1]       # involusi -> kembali ke awal
BEAT, DUR, FRAME_MS = 16, 9, 60        # frame per beat, lama transisi, ms per frame
SHAKE, FLASH = 6, 0.45

def cover(img, w, h, c=(0.5, 0.5)):
    return ImageOps.fit(img.convert("RGB"), (w, h), Image.LANCZOS, centering=c)

files = sorted(sum((glob.glob(f"phos/*.{e}") for e in ("png", "jpg", "jpeg", "webp")), []))
imgs = [Image.open(f) for f in files]
rects, y = [], GAP
for h, ws_ in ROWS:
    h = round(h * SCALE)
    avail = W - GAP * (len(ws_) - 1)
    ws = [round(avail * w / sum(ws_)) for w in ws_]
    ws[-1] = avail - sum(ws[:-1])
    x = GAP
    for w in ws:
        rects.append((x, y, w, h)); x += w + GAP
    y += h + GAP
H = y
N = len(rects)
assert len(imgs) >= N

cache = {}
def base(i, s):
    if (i, s) not in cache:
        cache[(i, s)] = cover(imgs[i], rects[s][2], rects[s][3], CENTER.get(i, (0.5, 0.5)))
    return cache[(i, s)]

def zoom(im, z):
    if abs(z - 1) < 0.003: return im
    w, h = im.size
    big = im.resize((round(w * z), round(h * z)), Image.BILINEAR)
    l, t = (big.width - w) // 2, (big.height - h) // 2
    return big.crop((l, t, l + w, t + h))

ease = lambda t: 0.5 - 0.5 * math.cos(math.pi * min(1, max(0, t)))
white = lambda im, a: Image.blend(im, Image.new("RGB", im.size, (255, 255, 255)), min(1, max(0, a)))

def glitch(im, m, rnd):
    r, g, b = im.split()
    r = ImageChops.offset(r, m, 0); b = ImageChops.offset(b, -m, 0)
    out = Image.merge("RGB", (r, g, b))
    w, h = out.size
    for _ in range(5):
        sy = rnd.randrange(h); sh = rnd.randrange(3, max(4, h // 6)); dx = rnd.randint(-3 * m, 3 * m)
        strip = out.crop((0, sy, w, min(h, sy + sh)))
        out.paste(ImageChops.offset(strip, dx, 0), (0, sy))
    return out

# state sebelum tiap beat
states = [list(range(N))]
for sig in BEATS:
    s = list(states[-1])
    for a, b in sig: s[a], s[b] = s[b], s[a]
    states.append(s)

random.seed(7)
stars = [(random.randrange(W), random.randrange(H), random.random(), random.randrange(6, 13)) for _ in range(16)]
total = BEAT * len(BEATS)

def star(d, cx, cy, r):
    k = r * 0.22
    d.polygon([(cx, cy - r), (cx + k, cy - k), (cx + r, cy), (cx + k, cy + k),
               (cx, cy + r), (cx - k, cy + k), (cx - r, cy), (cx - k, cy - k)], fill=(255, 255, 255))

frames = []
for f in range(total):
    b, fb = divmod(f, BEAT)
    before, after = states[b], states[b + 1]
    rnd = random.Random(f)
    canvas = Image.new("RGB", (W + 2 * GAP, H), BG)
    for s, (x, y, w, h) in enumerate(rects):
        z = 1.05 + 0.04 * math.sin(2 * math.pi * (f / total * 2 + s * 0.13))   # napas
        dl = int(s * 0.6); p = (fb - dl) / DUR if fb >= dl else 0
        if p <= 0 or p >= 1 or before[s] == after[s]:
            im = base(after[s] if p >= 1 or fb >= dl + DUR else before[s], s)
            canvas.paste(zoom(im, z), (x, y)); continue
        fx = (s + b) % 4
        old, new = zoom(base(before[s], s), z), zoom(base(after[s], s), z)
        if fx in (0, 1):                                    # slide horizontal / vertikal
            e = ease(p); d = 1 if s % 2 == 0 else -1
            t = Image.new("RGB", (w, h))
            if fx == 0:
                off = round(e * w) * d
                t.paste(old, (-off, 0)); t.paste(new, (w * d - off, 0))
            else:
                off = round(e * h) * d
                t.paste(old, (0, -off)); t.paste(new, (0, h * d - off))
        elif fx == 2:                                       # zoom-blink
            k = math.sin(math.pi * p)
            t = white(zoom(old if p < .5 else new, 1 + 0.6 * k), 0.7 * k)
        else:                                               # glitch
            t = glitch(old if p < .5 else new, max(1, round(10 * math.sin(math.pi * p))), rnd)
        canvas.paste(t, (x, y))
    if fb < 5: canvas = white(canvas, FLASH * (1 - fb / 5))  # flash di awal beat
    d = ImageDraw.Draw(canvas)                               # bintang berkedip (loop mulus)
    for sx, sy, ph, r in stars:
        k = max(0, math.sin(2 * math.pi * (f / total * 2 + ph))) ** 4
        if k > 0.15: star(d, sx, sy, r * k)
    if fb < 6:                                               # shake
        a = SHAKE * (1 - fb / 6); sh = Image.new("RGB", canvas.size, BG)
        sh.paste(canvas, (round(rnd.uniform(-a, a)), round(rnd.uniform(-a, a)))); canvas = sh
    frames.append(canvas.quantize(colors=48, dither=Image.Dither.NONE))

frames[0].save("phos-collage-juice.gif", save_all=True, append_images=frames[1:],
               duration=FRAME_MS, loop=0, optimize=True, disposal=1)
print(len(frames), "frames,", round(os.path.getsize("phos-collage-juice.gif") / 1e6, 2), "MB", frames[0].size)
