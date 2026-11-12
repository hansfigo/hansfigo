"""Layout-nya yang beranimasi: tiap kotak = frame yang geser/resize ke susunan baru
(A -> B -> C -> kolom -> A), gambar tetap di kotaknya masing-masing.

Pakai:  python3 make_gif_morph.py  -> phos-collage-morph.gif
"""
import glob, math, os
from PIL import Image, ImageOps

SCALE = 0.6
W, GAP, BG = round(790 * SCALE), 6, (13, 17, 23)
HC = round(910 * SCALE)                    # tinggi isi (di luar gap)
CW, CH = W + 2 * GAP, HC + 6 * GAP
CENTER = {0: (0.5, 0.1)}
MORPH, STAGGER, HOLD_MS, FRAME_MS = 10, 1, 900, 60

# layout baris: [(bobot tinggi, [bobot lebar...]), ...]  |  layout kolom: ("cols", [(bobot lebar, [bobot tinggi...]), ...])
LAYOUTS = [
    [(210, [1]), (145, [1, 2.1, 1]), (185, [1.5, 1.25, 1.2]), (180, [1, 1.3]), (190, [1])],
    [(150, [1, 1]), (170, [1, 1.6, 1]), (230, [1]), (150, [1.3, 1, 1.4]), (180, [1])],
    [(160, [1, 1.5, 1]), (220, [1]), (150, [1.4, 1, 1.2]), (190, [1]), (140, [1, 1.3])],
    ("cols", [(1.1, [1, 1, 1]), (1.4, [1.3, 1, 1.3, 1]), (1, [1, 1.4, 1])]),
]

def solve(spec):
    ax, ay, aw, ah = GAP, GAP, W, CH - 2 * GAP
    out = []
    if spec[0] == "cols":
        cols = spec[1]; cw = aw - GAP * (len(cols) - 1); x = ax
        for wt, hs in cols:
            w = round(cw * wt / sum(c[0] for c in cols)); hh = ah - GAP * (len(hs) - 1); y = ay
            for i, h in enumerate(hs):
                hp = round(hh * h / sum(hs)) if i < len(hs) - 1 else ay + ah - y
                out.append((x, y, w, hp)); y += hp + GAP
            x += w + GAP
    else:
        rh = ah - GAP * (len(spec) - 1); y = ay
        for ri, (hw, ws_) in enumerate(spec):
            h = round(rh * hw / sum(r[0] for r in spec)) if ri < len(spec) - 1 else ay + ah - y
            avail = aw - GAP * (len(ws_) - 1); x = ax
            for i, w in enumerate(ws_):
                wp = round(avail * w / sum(ws_)) if i < len(ws_) - 1 else ax + aw - x
                out.append((x, y, wp, h)); x += wp + GAP
            y += h + GAP
    return sorted(out, key=lambda r: (r[1], r[0]))     # urut baca: atas->bawah, kiri->kanan

L = [solve(s) for s in LAYOUTS]
assert all(len(l) == 10 for l in L)

files = sorted(sum((glob.glob(f"phos/*.{e}") for e in ("png", "jpg", "jpeg", "webp")), []))
src = []
for f in files[:10]:
    im = Image.open(f).convert("RGB"); im.thumbnail((900, 900), Image.LANCZOS); src.append(im)

def back(t, c=1.5):     # ease-out dengan overshoot (mantul)
    t = min(1, max(0, t)); return 1 + (c + 1) * (t - 1) ** 3 + c * (t - 1) ** 2

def render(rects):
    canvas = Image.new("RGB", (CW, CH), BG)
    for i, (x, y, w, h) in enumerate(rects):
        w, h = max(8, round(w)), max(8, round(h))
        canvas.paste(ImageOps.fit(src[i], (w, h), Image.BICUBIC, centering=CENTER.get(i, (0.5, 0.5))), (round(x), round(y)))
    return canvas

frames, durs = [], []
def add(img, ms):
    q = img.quantize(colors=48, dither=Image.Dither.NONE)
    if frames and q.tobytes() == frames[-1].tobytes(): durs[-1] += ms
    else: frames.append(q); durs.append(ms)

for k in range(len(L)):
    a, b = L[k], L[(k + 1) % len(L)]
    add(render(a), HOLD_MS)
    for f in range(MORPH + STAGGER * 9):
        rects = []
        for i in range(10):
            e = back((f - STAGGER * i) / MORPH)
            rects.append(tuple(a[i][j] + (b[i][j] - a[i][j]) * e for j in range(4)))
        add(render(rects), FRAME_MS)

frames[0].save("phos-collage-morph.gif", save_all=True, append_images=frames[1:],
               duration=durs, loop=0, optimize=True, disposal=1)
print(len(frames), "frames,", round(os.path.getsize("phos-collage-morph.gif") / 1e6, 2), "MB", frames[0].size)
