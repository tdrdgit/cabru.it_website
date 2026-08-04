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
"""

import datetime
import os
import re
import subprocess
import sys

BASE = "https://www.cabru.it"
SITEMAP = "sitemap.xml"


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


def main():
    if not os.path.exists(SITEMAP):
        sys.exit(f"{SITEMAP} non trovato: esegui lo script dalla root del sito.")

    locs = re.findall(r"<loc>(.*?)</loc>", open(SITEMAP, encoding="utf-8").read())
    if not locs:
        sys.exit("Nessun <loc> trovato nella sitemap.")

    out = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    missing = []
    for loc in locs:
        fp = path_for(loc)
        d = last_modified(fp)
        if d is None:
            missing.append(loc)
            continue
        out += ["  <url>", f"    <loc>{loc}</loc>", f"    <lastmod>{d}</lastmod>", "  </url>"]
    out += ["</urlset>", ""]

    open(SITEMAP, "w", encoding="utf-8").write("\n".join(out))
    print(f"sitemap.xml rigenerata: {len(locs) - len(missing)} URL")
    if missing:
        print(f"ATTENZIONE - {len(missing)} URL in sitemap senza file corrispondente:")
        for m in missing:
            print("   ", m)


if __name__ == "__main__":
    main()
