#!/usr/bin/env python3
"""Quanto sono uniformi i loghi, come vengono resi in pagina.

Stesso metro prima e dopo: si guarda quanta superficie scura copre ogni logo
una volta ridotto all'altezza con cui la home lo mostra.
"""
import glob, math, os, sys
from PIL import Image

CART = sys.argv[1] if len(sys.argv) > 1 else "img/partners"
H_RESA = 58.0     # altezza a cui la home rende un logo

def peso(f):
    im = Image.open(f).convert("RGBA")
    px = im.load(); W, H = im.size
    ink = 0.0; minx=W; miny=H; maxx=-1; maxy=-1
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if a < 8: continue
            d = 1 - (0.299*r + 0.587*g + 0.114*b) / 255
            if d > 0.06:
                ink += min(d, 1.0) * (a / 255)
                minx=min(minx,x); maxx=max(maxx,x); miny=min(miny,y); maxy=max(maxy,y)
    s = H_RESA / H
    bw, bh = (maxx-minx+1, maxy-miny+1) if maxx >= 0 else (0, 0)
    return math.sqrt(ink) * s, bw*s, bh*s

righe = [(os.path.basename(f),) + peso(f) for f in sorted(glob.glob(os.path.join(CART, "*.png")))]
righe.sort(key=lambda r: -r[1])
print(f"{'logo':28} {'peso':>6}  {'reso in pagina':>16}")
for n, p, bw, bh in righe:
    print(f"{n:28} {p:>6.1f}  {bw:>7.0f}x{bh:<8.0f}")
v = [r[1] for r in righe]
med = sorted(v)[len(v)//2]
scarto = math.sqrt(sum((x-med)**2 for x in v)/len(v)) / med
print(f"\nmediana {med:.1f} · piu' grande {max(v):.1f} · piu' piccolo {min(v):.1f}")
print(f"divario massimo {max(v)/min(v):.1f}x · scarto medio dalla mediana {scarto*100:.0f}%")
