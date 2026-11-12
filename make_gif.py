"""Collage animasi: pasangan kotak saling tukar gambar (slide), lalu balik lagi. Loop.

Pakai:  python3 make_gif.py   -> phos-collage.gif
Gambar diambil dari phos/ (urut nama), layout sama kayak make_collage.py.
"""
import glob, math
from PIL import Image, ImageOps

SCALE = 0.65                      # kecilin biar ukuran GIF ga bengkak
W, GAP, BG = round(790 * SCALE), 6, (13, 17, 23)
ROWS = [(210, [1]), (145, [1, 2.1, 1]), (185, [1.5, 1.25, 1.2]), (180, [1, 1.3]), (190, [1])]
CENTER = {0: (0.5, 0.1)}          # fokus crop per slot
PAIRS = [(0, 9), (1, 3), (4, 6), (7, 8), (2, 5)]   # slot yang saling tukar
FPS_MS = 70                       # durasi tiap frame transisi
MOVE, STAGGER, HOLD = 9, 6, 20   # frame: lama geser, jeda antar pasangan, diam di antara fase

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
assert len(imgs) >= len(rects), f"butuh {len(rects)} gambar"

# cache: gambar i di-crop sesuai ukuran slot s
cache = {}
def tile(i, s):
    if (i, s) not in cache:
        _, _, w, h = rects[s]
        cache[(i, s)] = cover(imgs[i], w, h, CENTER.get(i, (0.5, 0.5)))
    return cache[(i, s)]

ease = lambda t: 0.5 - 0.5 * math.cos(math.pi * t)

# timeline: tiap slot punya (mulai, dari-gambar, ke-gambar)
events = {}  # slot -> list of (start_frame, src_img, dst_img, dir)
for n, (a, b) in enumerate(PAIRS):
    t1 = HOLD // 2 + n * STAGGER
    for s, o, d in ((a, b, 1), (b, a, -1)):
        events.setdefault(s, []).append((t1, s, o, d))
        events[s].append((t1 + HOLD + len(PAIRS) * STAGGER + MOVE, o, s, -d))
total = max(e[0] for v in events.values() for e in v) + MOVE + HOLD // 2

frames, durs = [], []
for f in range(total):
    canvas = Image.new("RGB", (W + 2 * GAP, H), BG)
    for s, (x, y, w, h) in enumerate(rects):
        cur, nxt, p, d = s, s, 0.0, 1
        for st, src, dst, dr in events.get(s, []):
            if f >= st + MOVE: cur = nxt = dst
            elif f >= st: cur, nxt, p, d = src, dst, ease((f - st) / MOVE), dr
        if p == 0:
            canvas.paste(tile(cur, s), (x, y))
        else:
            off = round(p * w) * d
            t = Image.new("RGB", (w, h))
            t.paste(tile(cur, s), (-off, 0)); t.paste(tile(nxt, s), (w * d - off, 0))
            canvas.paste(t, (x, y))
    q = canvas.quantize(colors=64, dither=Image.Dither.NONE)
    if frames and q.tobytes() == frames[-1].tobytes():
        durs[-1] += FPS_MS
    else:
        frames.append(q); durs.append(FPS_MS)

frames[0].save("phos-collage.gif", save_all=True, append_images=frames[1:],
               duration=durs, loop=0, optimize=True, disposal=1)
import os
print(len(frames), "frames,", total, "ticks,", round(os.path.getsize("phos-collage.gif") / 1e6, 2), "MB")
