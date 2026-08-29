#!/usr/bin/env python3
"""Genera favicon, icone e il logo senza payoff, dal logo ad alta risoluzione.

Sorgente: assets/Logo CABRU.jpg (6088x1574), fuori dal repo del sito.
Il logo viene ritagliato SENZA il payoff ("PRODOTTI per LABORATORIO...").

    python3 _tooling/build_immagini.py            # favicon: la griglia di quadratini
    python3 _tooling/build_immagini.py --logo     # favicon: il logo intero senza payoff
    python3 _tooling/build_immagini.py --simbolo  # favicon: la sola "C" del marchio

Produce anche img/logo-cabru-nopayoff.png, usato dalle email di conferma:
li' il payoff e' gia' scritto in testo sotto il logo, quindi nell'immagine
non ci va.

Il ritaglio e' misurato sul file: il marchio finisce a y=1182 e il payoff
riprende a y=1238. Tagliare piu' in basso si porta dietro la prima riga del
payoff, che nell'email compare sbiadita sotto il logo. Se il file sorgente
cambia, i due valori vanno rimisurati.
"""
import sys, os
from PIL import Image, ImageDraw, ImageFilter

QUI = os.path.dirname(os.path.abspath(__file__))
SITO = os.path.dirname(QUI)
SORGENTE = os.path.join(os.path.dirname(SITO), 'assets', 'Logo CABRU.jpg')
BLU = (13, 115, 151)   # #0d7397, l'accento del sito (css/style.css)

src = Image.open(SORGENTE).convert('RGB')
LOGO = src.crop((8, 134, 6085, 1183))        # marchio senza payoff, "s.a.s." incluso
C    = src.crop((861, 225, 1589, 1121))      # la sola lettera C

def con_logo(lato, margine=0.05):
    utile = int(lato * (1 - 2*margine))
    s = min(utile/LOGO.width, utile/LOGO.height)
    im = LOGO.resize((max(1,int(LOGO.width*s)), max(1,int(LOGO.height*s))), Image.LANCZOS)
    if lato <= 64:                            # alle misure piccole il downscale sfoca le aste
        im = im.filter(ImageFilter.UnsharpMask(radius=1.0, percent=140, threshold=2))
    base = Image.new('RGB', (lato, lato), (255, 255, 255))
    base.paste(im, ((lato-im.width)//2, (lato-im.height)//2))
    return base

def con_griglia(lato, sfondo=None):
    """La griglia 3x5 del logo, ridisegnata alla misura richiesta.

    Non si scala img/favicon.png: a 16 e 32 px il ridimensionamento sfoca i
    bordi. Celle e distacchi vengono calcolati in pixel interi, cosi' i
    quadrati restano netti a qualunque misura.
    """
    CH, ME, SC = (183,200,217), (118,158,180), (18,129,172)   # le tre tonalita' del logo
    RAPPORTO = 16/14                                          # cella: piu' larga che alta
    m = max(1, round(lato*0.05))
    g = max(1, round(lato*0.035))
    h = max(1, (lato - 2*m - 4*g)//5)
    w = max(1, round(h*RAPPORTO))
    bw, bh = 3*w + 2*g, 5*h + 4*g
    x0, y0 = (lato-bw)//2, (lato-bh)//2
    base = Image.new('RGBA', (lato, lato), (255,255,255,0) if sfondo is None else sfondo+(255,))
    d = ImageDraw.Draw(base)
    for c, col in enumerate((CH, ME, SC)):
        for r in range(5):
            x, y = x0 + c*(w+g), y0 + r*(h+g)
            d.rectangle([x, y, x+w-1, y+h-1], fill=col+(255,))
    return base

def con_simbolo(lato, margine=0.15):
    g = C.convert('L')
    alpha = g.point(lambda v: 0 if v <= 105 else (255 if v >= 250 else int(255*(v-105)/145)))
    lettera = Image.new('RGBA', C.size, (255,255,255,255)); lettera.putalpha(alpha)
    utile = int(lato * (1 - 2*margine))
    s = utile / C.height
    im = lettera.resize((max(1,int(C.width*s)), utile), Image.LANCZOS)
    base = Image.new('RGBA', (lato, lato), BLU + (255,))
    base.alpha_composite(im, ((lato-im.width)//2, (lato-im.height)//2))
    return base.convert('RGB')

gen = con_simbolo if '--simbolo' in sys.argv else (con_logo if '--logo' in sys.argv else con_griglia)

# Logo senza payoff per le email. Il file e' 3x rispetto alla misura con cui
# viene dichiarato nel template, per gli schermi ad alta densita'.
EMAIL_H = 40
EMAIL_W = round(EMAIL_H * LOGO.width / LOGO.height)
LOGO.resize((EMAIL_W*3, EMAIL_H*3), Image.LANCZOS)\
    .save(os.path.join(SITO, 'img', 'logo-cabru-nopayoff.png'))

# Logo grande per l'apertura della home. Il PNG dell'intestazione e' alto 96 px:
# ingrandirlo lo sgranerebbe, quindi il grande si taglia dal sorgente ad alta
# risoluzione. Anche questo e' il doppio della misura con cui viene mostrato.
HERO_H = 130
INTERO = src.crop((7, 133, 6086, 1550))      # marchio + payoff, come il logo dell'intestazione


def senza_fondo(im):
    """Toglie il bianco del sorgente, che altrimenti si vede come un rettangolo.

    Il logo dell'intestazione sta su fondo bianco e il problema non si pone; in
    apertura il fondo e' grigio chiaro, quindi il bianco va tolto davvero — non
    coperto. Il bianco diventa trasparente in proporzione a quanto e' chiaro il
    pixel, e il colore viene riportato al suo valore pieno: senza quest'ultimo
    passaggio i bordi delle lettere restano slavati.
    """
    im = im.convert('RGB')
    px = im.load(); W, H = im.size
    out = Image.new('RGBA', (W, H))
    op = out.load()
    for y in range(H):
        for x in range(W):
            r, g, b = px[x, y]
            # quanto il pixel e' lontano dal bianco lo dice il canale piu' scuro,
            # non la luminosita': un blu pieno e' scuro solo sul rosso, e usare la
            # luminosita' lo renderebbe semitrasparente, cioe' slavato
            a = 255 - min(r, g, b)
            if a < 6:
                op[x, y] = (255, 255, 255, 0); continue
            f = a / 255.0
            op[x, y] = (
                max(0, min(255, int((r - 255 * (1 - f)) / f))),
                max(0, min(255, int((g - 255 * (1 - f)) / f))),
                max(0, min(255, int((b - 255 * (1 - f)) / f))),
                int(a))
    return out


senza_fondo(INTERO.resize((round(HERO_H * 2 * INTERO.width / INTERO.height), HERO_H * 2), Image.LANCZOS))\
    .save(os.path.join(SITO, 'img', 'logo-cabru-hero.png'))


def opaca(im):
    fondo = Image.new('RGB', im.size, (255,255,255))
    fondo.paste(im, mask=im.split()[3] if im.mode == 'RGBA' else None)
    return fondo

gen(192).save(os.path.join(SITO, 'img', 'icon-192.png'))
opaca(gen(180).convert('RGBA')).save(os.path.join(SITO, 'img', 'apple-touch-icon.png'))
# l'ICO tiene tre misure vere, ognuna ridisegnata: scalarne una sola le sfocherebbe
misure = [gen(l).convert('RGBA') for l in (48, 32, 16)]
misure[0].save(os.path.join(SITO, 'favicon.ico'), format='ICO',
               sizes=[(48,48),(32,32),(16,16)], append_images=misure[1:])
print('favicon.ico (16/32/48), img/icon-192.png, img/apple-touch-icon.png —',
      {con_simbolo:'simbolo C', con_logo:'logo senza payoff', con_griglia:'griglia del logo'}[gen])
print('img/logo-cabru-hero.png per l\'apertura della home, alto %d px in pagina' % HERO_H)
print('img/logo-cabru-nopayoff.png per le email — dichiararlo a %dx%d '
      'in CABRU_backend_AppsScript.gs (LOGO_W, LOGO_H)' % (EMAIL_W, EMAIL_H))
