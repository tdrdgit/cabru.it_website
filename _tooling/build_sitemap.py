#!/usr/bin/env python3
"""Rigenera sitemap.xml con lastmod reali.

Da eseguire dalla root del sito, prima di ogni deploy:

    python3 _tooling/build_sitemap.py

Il lastmod di ogni URL viene preso dalla data dell'ultimo commit git che ha
toccato il file. Se il file ha modifiche non ancora committate, si usa la data
di modifica sul filesystem: e' il dato piu' vicino alla verita' al momento del
deploy. Cosi' il lastmod non va mai aggiornato a mano, che e' il modo con cui
diventa un segnale falso.

changefreq e priority non vengono scritti: Google li ignora da anni.

Dal 05.10.2026 scrive anche il dateModified nel JSON-LD di ogni pagina, sul nodo
che rappresenta la pagina (FAQPage, AboutPage, ContactPage, TechArticle...), con
la stessa data del lastmod: due date diverse per la stessa pagina sono un
segnale che si contraddice. Se la data va cambiata, si scrive quella di oggi,
perche' il file cambia e verra' committato oggi. Le pagine senza un nodo pagina
(privacy, termini, catalogo, qualita', hub prodotti) restano senza.
"""

import datetime
import json
import os
import re
import subprocess
import sys

BASE = "https://www.cabru.it"
SITEMAP = "sitemap.xml"
PAGINA = {"WebPage", "FAQPage", "AboutPage", "ContactPage", "CollectionPage",
          "TechArticle", "Article"}
LD = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)


def scrivi_data(path, d):
    """Allinea il dateModified del nodo pagina a d; ritorna la data che vale per la pagina."""
    testo = open(path, encoding="utf-8").read()
    oggi = datetime.date.today().isoformat()
    esito = {"data": d, "trovato": False}

    def sostituisci(m):
        if esito["trovato"]:
            return m.group(0)
        blocco = m.group(2)
        nodo = json.loads(blocco)
        if not isinstance(nodo, dict) or nodo.get("@type") not in PAGINA:
            return m.group(0)
        esito["trovato"] = True
        if nodo.get("dateModified") == d:
            return m.group(0)
        # si rispetta la forma del blocco: compatto se era compatto
        compatto = json.dumps(nodo, ensure_ascii=False, separators=(",", ":")) == blocco
        nodo["dateModified"] = esito["data"] = oggi
        sep = (",", ":") if compatto else None
        return m.group(1) + json.dumps(nodo, ensure_ascii=False, separators=sep) + m.group(3)

    nuovo = LD.sub(sostituisci, testo)
    if nuovo != testo:
        open(path, "w", encoding="utf-8").write(nuovo)
    return esito["data"]


def is_dirty(path):
    """True se il file ha modifiche non committate (o non e' tracciato)."""
    r = subprocess.run(
        ["git", "status", "--porcelain", "--", path],
        capture_output=True, text=True,
    )
    return bool(r.stdout.strip())


def last_modified(path):
    """Data ISO dell'ultima modifica reale del file."""
    if not os.path.exists(path):
        return None
    if not is_dirty(path):
        r = subprocess.run(
            ["git", "log", "-1", "--format=%ad", "--date=short", "--", path],
            capture_output=True, text=True,
        )
        d = r.stdout.strip()
        if d:
            return d
    return datetime.date.fromtimestamp(os.path.getmtime(path)).isoformat()


def path_for(loc):
    p = loc.replace(BASE, "").strip("/")
    return (p + "/index.html") if p else "index.html"


def discover():
    """Tutte le pagine pubblicabili, lette dal filesystem.

    Fino al 2026-08-04 questa lista veniva riletta dalla sitemap gia' esistente:
    i lastmod si aggiornavano, ma una pagina nuova non ci entrava mai — e non ci
    sarebbe entrata nemmeno dopo il commit. Le pagine si scoprono dal disco, che
    e' l'unica fonte che sa cosa esiste davvero.
    """
    found = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in ("_tooling", ".git") and not d.startswith(".")]
        for f in files:
            if f != "index.html":
                continue
            fp = os.path.normpath(os.path.join(root, f))
            # una pagina esclusa dall'indice non va annunciata in sitemap
            head = open(fp, encoding="utf-8").read(4000)
            if re.search(r'<meta[^>]+name="robots"[^>]+noindex', head, re.I):
                continue
            rel = os.path.dirname(fp).replace(os.sep, "/").lstrip(".").strip("/")
            found.append((f"{BASE}/{rel}/" if rel else f"{BASE}/", fp))
    return sorted(found)


def main():
    if not os.path.exists(SITEMAP):
        sys.exit(f"{SITEMAP} non trovato: esegui lo script dalla root del sito.")

    pages = discover()
    if not pages:
        sys.exit("Nessuna pagina trovata: esegui lo script dalla root del sito.")

    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    uncommitted = []
    for loc, fp in pages:
        d = scrivi_data(fp, last_modified(fp))
        if is_dirty(fp):
            uncommitted.append(loc)
        out += ["  <url>", f"    <loc>{loc}</loc>", f"    <lastmod>{d}</lastmod>", "  </url>"]
    out += ["</urlset>", ""]

    open(SITEMAP, "w", encoding="utf-8").write("\n".join(out))
    print(f"sitemap.xml rigenerata: {len(pages)} URL")
    if uncommitted:
        print(f"ATTENZIONE - {len(uncommitted)} pagine non ancora committate: il loro")
        print("lastmod viene dalla data del file, non da git. Committa e rilancia")
        print("questo script prima del deploy, altrimenti la data cambia a ogni salvataggio.")


if __name__ == "__main__":
    main()
