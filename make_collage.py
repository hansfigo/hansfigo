"""Bikin collage layout (kayak momo.gif) dari gambar statis di folder phos/.

Pakai:  python3 make_collage.py            -> hasil: phos-collage.png
Taruh 10 gambar di phos/ (urut nama file: 01.png, 02.jpg, ...).
Kalau kurang dari 12, sisanya diulang dari awal.
"""
import glob, os
from PIL import Image, ImageOps

W, GAP, BG = 790, 8, (13, 17, 23)  # BG = warna dark GitHub
# (tinggi baris, bobot lebar tiap kotak) -- meniru layout referensi
ROWS = [
    (210, [1]),                  # banner atas
    (145, [1, 2.1, 1]),
    (185, [1.5, 1.25, 1.2]),
    (180, [1, 1.3]),
    (190, [1]),                  # banner bawah
]

CENTER = {0: (0.5, 0.1)}  # index gambar -> titik fokus crop (x, y); banner atas naik biar kepala ga kepotong

def cover(img, w, h, c=(0.5, 0.5)):
    return ImageOps.fit(img.convert("RGB"), (w, h), Image.LANCZOS, centering=c)

files = sorted(sum((glob.glob(f"phos/*.{e}") for e in ("png", "jpg", "jpeg", "webp")), []))
if not files:
    raise SystemExit("Folder phos/ kosong. Taruh gambarnya dulu.")
need = sum(len(r[1]) for r in ROWS)
files = [files[i % len(files)] for i in range(need)]

H = sum(r[0] for r in ROWS) + GAP * (len(ROWS) + 1)
canvas = Image.new("RGB", (W + 2 * GAP, H), BG)
y, k = GAP, 0
for h, weights in ROWS:
    avail = W - GAP * (len(weights) - 1)
    ws = [round(avail * w / sum(weights)) for w in weights]
    ws[-1] = avail - sum(ws[:-1])
    x = GAP
    for w in ws:
        tile = cover(Image.open(files[k]), w, h, CENTER.get(k, (0.5, 0.5)))
        canvas.paste(tile, (x, y))
        x += w + GAP
        k += 1
    y += h + GAP
canvas.save("phos-collage.png", optimize=True)
print("OK ->", "phos-collage.png", canvas.size)
