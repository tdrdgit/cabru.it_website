#!/usr/bin/env python3
"""Collega le pagine istituzionali nuove (Chi siamo, Contatti) al menu e al footer.

Perche' esiste: /contatti/ e /chi-siamo/ sono state scritte come pagine vere e
indicizzabili, ma nessuna pagina del sito le linkava — e una pagina che nessuno
linka, per Google, e' orfana. Lo script tocca tutte le pagine di entrambe le
lingue calcolando da se' il prefisso relativo giusto per la profondita' di
ciascuna, perche' il sito gira anche da sottocartella in anteprima e i path
root-relative si romperebbero.

Fa tre cose:
  1. il CTA "Contattaci" del menu smette di essere un mailto: e punta alla
     pagina contatti. Il modale continua ad aprirsi al clic (lo fa site.js),
     ma ora il link ha una destinazione vera per i crawler, per chi apre in
     una scheda nuova e per chi ha JavaScript disattivato;
  2. il footer legale guadagna "Chi siamo" e "Contatti";
  3. "Qualita'" nel footer viene uniformata: era presente solo sulle due home.

Idempotente: rieseguirlo non duplica nulla.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

L = {
    "it": {"contatti": "contatti/", "chisiamo": "chi-siamo/", "qualita": "qualita/",
           "t_chisiamo": "Chi siamo", "t_contatti": "Contatti", "t_qualita": "Qualità"},
    "en": {"contatti": "contact/", "chisiamo": "about/", "qualita": "quality/",
           "t_chisiamo": "About us", "t_contatti": "Contact", "t_qualita": "Quality"},
}


def prefix_for(path: Path) -> tuple[str, str]:
    """Prefisso relativo alla radice della lingua, e la lingua."""
    rel = path.relative_to(ROOT).parts
    if rel and rel[0] == "en":
        return "../" * (len(rel) - 2), "en"
    return "../" * (len(rel) - 1), "it"


def patch(html: str, pre: str, lang: str) -> tuple[str, list[str]]:
    t = L[lang]
    done = []

    # 1. CTA del menu: da mailto: alla pagina contatti
    new_cta = 'href="%s%s" class="nav-cta js-contact"' % (pre, t["contatti"])
    html, n = re.subn(r'href="mailto:info@cabru\.it" class="nav-cta js-contact"', new_cta, html)
    if n:
        done.append("cta")

    # 2+3. footer legale
    m = re.search(r'<div class="foot-legal">(.*?)</div>', html, re.S)
    if m and t["chisiamo"] not in m.group(1):
        links = []
        if t["qualita"] not in m.group(1):
            links.append('<a href="%s%s">%s</a>' % (pre, t["qualita"], t["t_qualita"]))
        links.append('<a href="%s%s">%s</a>' % (pre, t["chisiamo"], t["t_chisiamo"]))
        links.append('<a href="%s%s">%s</a>' % (pre, t["contatti"], t["t_contatti"]))
        html = html[:m.start(1)] + " · ".join(links) + " · " + m.group(1) + html[m.end(1):]
        done.append("footer")

    return html, done


def main() -> int:
    pages = sorted(p for p in ROOT.rglob("*.html") if "_tooling" not in p.parts)
    touched = cta = foot = 0
    for p in pages:
        pre, lang = prefix_for(p)
        src = p.read_text(encoding="utf-8")
        out, done = patch(src, pre, lang)
        if out != src:
            p.write_text(out, encoding="utf-8")
            touched += 1
            cta += "cta" in done
            foot += "footer" in done
    print(f"pagine lette: {len(pages)} · modificate: {touched} · CTA: {cta} · footer: {foot}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
