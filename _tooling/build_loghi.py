#!/usr/bin/env python3
"""Uniforma la dimensione PERCEPITA dei loghi dei produttori.

Il problema: i file arrivano dai produttori con proporzioni e margini diversi.
Vincolarli tutti alla stessa altezza in CSS non basta — un logo lungo e basso
copre molta piu' superficie di uno compatto, e a occhio sembra piu' grande.

Qui ogni logo viene ritagliato dal suo margine bianco, misurato in "inchiostro"
(quanta superficie scura copre davvero) e riscalato perche' quella superficie sia
uguale per tutti, dentro una tela identica per ogni logo. Cosi' l'uniformita'
vale ovunque il logo compaia, senza regole CSS per singolo file.

Gli originali stanno in _tooling/loghi_originali/ e non vengono mai toccati:
questo script li rilegge da capo a ogni esecuzione.
"""
import json, math, os, sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.dirname(HERE)
SRC  = os.path.join(HERE, "loghi_originali")
DST  = os.path.join(SITE, "img", "partners")
CONF = os.path.join(HERE, "loghi_taratura.json")

# La tela su cui ogni logo viene ricomposto, a doppia risoluzione rispetto a come
# la home lo mostra. Il suo rapporto decide l'equilibrio fra loghi lunghi e loghi
# compatti: piu' e' allungata, piu' i lunghi possono crescere e piu' i quadrati
# restano indietro, perche' l'altezza li ferma prima.
TELA_W, TELA_H = 400, 116
# Quanto il contenuto puo' occupare della tela, per lasciare aria ai lati.
MAX_W, MAX_H = 0.98, 0.94
# Un logo non deve nemmeno sparire: sotto questa altezza si smette di rimpicciolire.
MIN_H = 0.34
SOGLIA = 0.06          # sotto questo scuro il pixel e' considerato sfondo


def misura(im):
    """Ritaglio del contenuto e superficie di inchiostro, in pixel."""
    im = im.convert("RGBA")
    px = im.load(); W, H = im.size
    minx, miny, maxx, maxy = W, H, -1, -1
    ink = 0.0
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if a < 8:
                continue
            d = 1 - (0.299 * r + 0.587 * g + 0.114 * b) / 255
            if d > SOGLIA:
                ink += min(d, 1.0) * (a / 255)
                if x < minx: minx = x
                if x > maxx: maxx = x
                if y < miny: miny = y
                if y > maxy: maxy = y
    if maxx < 0:
        return None
    return (minx, miny, maxx + 1, maxy + 1), ink


def carica_taratura():
    """Correzioni a mano, per i casi che l'occhio giudica meglio del calcolo."""
    if os.path.exists(CONF):
        return json.load(open(CONF, encoding="utf-8"))
    return {}


def main():
    tara = carica_taratura()
    peso = tara.get("_peso_area", 1.0)      # 1 = uniforma l'area, 0 = uniforma l'altezza
    loghi = []
    for f in sorted(os.listdir(SRC)):
        if not f.lower().endswith(".png"):
            continue
        im = Image.open(os.path.join(SRC, f))
        m = misura(im)
        if not m:
            print("  saltato (vuoto):", f); continue
        box, ink = m
        ritaglio = im.convert("RGBA").crop(box)
        loghi.append({"file": f, "im": ritaglio, "ink": ink,
                      "w": box[2] - box[0], "h": box[3] - box[1]})

    # La misura del "quanto sembra grande".
    #
    # L'inchiostro da solo non basta: un logo con lettere sottili e molta aria
    # dentro (ExBio) ne ha poco e verrebbe ingrandito troppo, mentre uno fitto
    # verrebbe schiacciato. L'ingombro da solo sbaglia al contrario: premia chi
    # ha una firma lunga e sottile. La media dei due e' quella che l'occhio
    # conferma — il peso si regola in loghi_taratura.json.
    p_ink = tara.get("_peso_inchiostro", 0.5)
    for l in loghi:
        l["massa"] = (l["ink"] ** p_ink) * ((l["w"] * l["h"]) ** (1 - p_ink))
        l["k0"] = 1.0 / math.sqrt(l["massa"])

    # Il bersaglio si esprime come altezza: "il logo mediano e' alto il 62% della
    # fascia". E' l'unico modo di regolarlo guardando la pagina invece dei numeri.
    h_target = tara.get("_altezza_mediana", 0.62) * TELA_H

    # Tre passate: chi sfora i bordi viene limitato e il bersaglio si rilegge sui
    # rimasti, o i limitati tirerebbero giu' anche chi ci stava.
    liberi = list(loghi)
    for _ in range(3):
        alt = sorted(l["h"] * l["k0"] for l in liberi) or [1]
        C = h_target / alt[len(alt) // 2]
        limitati = []
        for l in loghi:
            k = l["k0"] * C
            kw = TELA_W * MAX_W / l["w"]
            kh = TELA_H * MAX_H / l["h"]
            kmin = TELA_H * MIN_H / l["h"]
            l["k"] = max(min(k, kw, kh), min(kmin, kw))
            l["limitato"] = abs(l["k"] - k) > 1e-6
            if l["limitato"]:
                limitati.append(l)
        nuovi_liberi = [l for l in loghi if not l["limitato"]]
        if len(nuovi_liberi) == len(liberi):
            break
        liberi = nuovi_liberi or loghi

    tela = Image.new("RGBA", (TELA_W, TELA_H), (255, 255, 255, 255))
    print(f"{'logo':28} {'scala':>7} {'contenuto sulla tela':>22}  nota")
    for l in loghi:
        k = l["k"] * tara.get(l["file"], 1.0)
        w, h = max(1, round(l["w"] * k)), max(1, round(l["h"] * k))
        w, h = min(w, TELA_W), min(h, TELA_H)
        img = l["im"].resize((w, h), Image.LANCZOS)
        out = tela.copy()
        out.paste(img, ((TELA_W - w) // 2, (TELA_H - h) // 2), img)
        out.convert("RGB").save(os.path.join(DST, l["file"]), optimize=True)
        note = []
        if l["limitato"]: note.append("al limite della tela")
        if k > 1.6: note.append(f"ingrandito {k:.1f}x — sorgente a bassa risoluzione")
        if l["file"] in tara: note.append(f"ritocco a mano x{tara[l['file']]}")
        print(f"{l['file']:28} {k:>7.2f} {w:>10}x{h:<10} {' · '.join(note)}")
    print(f"\n{len(loghi)} loghi riscritti in img/partners/ — tela {TELA_W}x{TELA_H}")


if __name__ == "__main__":
    main()
