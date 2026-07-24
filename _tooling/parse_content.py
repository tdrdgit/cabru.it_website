#!/usr/bin/env python3
# Parser dei due file di contenuto (breadth.md, priority-brands.md) -> content.json
import re, json, os

BASE = os.path.dirname(os.path.abspath(__file__))
CONTENT = os.path.join(BASE, "content")

def read(p): return open(p, encoding="utf-8").read()

def slug_from_header(line):
    m = re.search(r'`(/[^`]+/)`', line)
    return m.group(1) if m else None

def clean(s): return s.strip()

# ---------------- breadth.md ----------------
def parse_breadth():
    txt = read(os.path.join(CONTENT, "breadth.md"))
    pages = []
    # split on "## " page headers (level-2), keep only those with a slug in backticks
    chunks = re.split(r'\n## ', txt)
    for ch in chunks:
        header = ch.splitlines()[0]
        it_slug = slug_from_header("## " + header)
        if not it_slug:
            continue
        name = re.split(r'—|—', header)[0].strip().lstrip('#').strip()
        name = re.sub(r'^[AB]\d+\.\s*', '', name)
        # split IT / EN
        parts = re.split(r'\n### (ITALIANO|ENGLISH)\n', ch)
        # parts: [before, 'ITALIANO', itblock, 'ENGLISH', enblock]
        lang_blocks = {}
        for i in range(1, len(parts)-1, 2):
            lang_blocks[parts[i]] = parts[i+1]
        page = {"key": it_slug, "name": name, "it": None, "en": None}
        for lang, key in (("ITALIANO","it"), ("ENGLISH","en")):
            if lang not in lang_blocks: continue
            page[key] = parse_breadth_block(lang_blocks[lang])
        pages.append(page)
    # hub (livello 1: "# PARTE C — HUB AZIENDE `/aziende/`")
    hm = re.search(r'\n# PARTE C[^\n]*`(/aziende/)`\n(.+?)(?=\n## |\Z)', txt, re.S)
    if hm:
        block = hm.group(2)
        parts = re.split(r'\n### (ITALIANO|ENGLISH)\n', block)
        lb = {}
        for i in range(1, len(parts)-1, 2):
            lb[parts[i]] = parts[i+1]
        page = {"key": "/aziende/", "name": "Aziende rappresentate", "it": None, "en": None}
        for lang, key in (("ITALIANO","it"), ("ENGLISH","en")):
            if lang in lb:
                page[key] = parse_breadth_block(lb[lang])
        pages.append(page)
    return pages

def parse_breadth_block(block):
    d = {"title":"", "meta":"", "h1":"", "keywords":"", "blocks":[], "faq":[]}
    lines = block.split("\n")
    # meta bullets
    for ln in lines:
        m = re.match(r'\s*-\s*\*\*(Keyword target|Target keyword|Title|Meta|H1):\*\*\s*(.*)', ln)
        if m:
            k, v = m.group(1), clean(m.group(2))
            if k in ("Keyword target","Target keyword"): d["keywords"]=v
            elif k=="Title": d["title"]=v
            elif k=="Meta": d["meta"]=v
            elif k=="H1": d["h1"]=v
    # H2 sections: **H2 — Title** then paragraph(s)
    for m in re.finditer(r'\*\*H2 — (.+?)\*\*\n(.+?)(?=\n\*\*|\n### |\Z)', block, re.S):
        d["blocks"].append(("h2", clean(m.group(1))))
        para = clean(m.group(2))
        d["blocks"].append(("p", para))
    # FAQ
    fm = re.search(r'\*\*FAQ\*\*\n(.+?)(?=\n\*\*Link|\n\*\*Internal|\n### |\Z)', block, re.S)
    if fm:
        for q in re.finditer(r'\d+\.\s*\*(.+?)\*\s*(.+?)(?=\n\d+\.|\Z)', fm.group(1), re.S):
            d["faq"].append([clean(q.group(1)), clean(q.group(2))])
    return d

# ---------------- priority-brands.md ----------------
def parse_priority():
    txt = read(os.path.join(CONTENT, "priority-brands.md"))
    pages = []
    # brands split on "# n) NAME"
    chunks = re.split(r'\n# \d+\)\s*', txt)
    for ch in chunks[1:]:
        name = ch.splitlines()[0].strip()
        if name.startswith('"'):  # the tactical notes section
            continue
        # two sub-blocks: "## n.1 — Italiano · `/slug/`" and "## n.2 — English · `/slug/`"
        subs = re.split(r'\n## \d+\.\d+ — ', ch)
        page = {"key": None, "name": name.title() if name.isupper() else name, "it": None, "en": None}
        for sub in subs[1:]:
            head = sub.splitlines()[0]
            lang = "it" if head.lower().startswith("italiano") else "en"
            slug = slug_from_header(head)
            parsed = parse_priority_block(sub)
            parsed["slug"]=slug
            page[lang]=parsed
            if lang=="it": page["key"]=slug
        if page["key"]:            # scarta la sezione "note tattiche" (senza slug)
            pages.append(page)
    return pages

def bt(v):  # strip surrounding backticks
    v=clean(v);
    if v.startswith("`") and v.endswith("`"): v=v[1:-1]
    return clean(v)

def parse_priority_block(block):
    d = {"title":"", "meta":"", "h1":"", "keywords":"", "blocks":[], "faq":[], "jsonld":[]}
    # fields
    for pat,key in [
        (r'\*\*`?<title>`?\*\*[^:]*:\s*(.+)', "title"),
        (r'\*\*Meta description\*\*[^:]*:\s*(.+)', "meta"),
        (r'\*\*H1:\*\*\s*(.+)', "h1"),
        (r'\*\*Keyword target[^:]*:\*\*\s*(.+)', "keywords"),
        (r'\*\*Target:\*\*\s*(.+)', "keywords"),
    ]:
        m=re.search(pat, block)
        if m and not d[key]: d[key]=bt(m.group(1))
    # body
    bm = re.search(r'### Body\n(.+?)(?=\n### )', block, re.S)
    if bm:
        d["blocks"]=md_body_to_blocks(bm.group(1))
    # faq
    fm = re.search(r'### FAQ\n(.+?)(?=\n### )', block, re.S)
    if fm:
        for q in re.finditer(r'\*\*(.+?)\*\*\n(.+?)(?=\n\*\*|\Z)', fm.group(1), re.S):
            d["faq"].append([clean(q.group(1)), clean(q.group(2))])
    # jsonld blocks
    jm = re.search(r'### JSON-LD.*?\n(.+?)(?=\n### |\n## |\n---|\Z)', block, re.S)
    if jm:
        for jb in re.finditer(r'```json\n(.+?)\n```', jm.group(1), re.S):
            try:
                d["jsonld"].append(json.loads(jb.group(1)))
            except Exception as e:
                d["jsonld"].append({"_parse_error": str(e)})
    return d

def md_body_to_blocks(body):
    blocks=[]
    # split into logical lines/paragraphs
    for raw in re.split(r'\n\s*\n', body.strip()):
        seg=raw.strip()
        if not seg: continue
        # bullet list?
        if re.match(r'^[-*] ', seg):
            items=[clean(re.sub(r'^[-*]\s*','',l)) for l in seg.splitlines() if l.strip()]
            blocks.append(("ul", items))
            continue
        # standalone bold line = subheading
        m=re.match(r'^\*\*(.+?)\*\*\s*$', seg)
        if m:
            blocks.append(("h3", clean(m.group(1))))
            continue
        # bold-lead paragraph "**Head**\ntext"
        m2=re.match(r'^\*\*(.+?)\*\*\n(.+)', seg, re.S)
        if m2:
            blocks.append(("h3", clean(m2.group(1))))
            blocks.append(("p", clean(m2.group(2))))
            continue
        blocks.append(("p", seg))
    return blocks

if __name__=="__main__":
    breadth = parse_breadth()
    priority = parse_priority()
    data = {"breadth": breadth, "priority": priority}
    json.dump(data, open(os.path.join(BASE,"content.json"),"w",encoding="utf-8"), ensure_ascii=False, indent=1)
    # report
    print("BREADTH pagine:", len(breadth))
    cats=[p for p in breadth if p["key"].startswith("/prodotti/")]
    brands=[p for p in breadth if p["key"].startswith("/aziende/")]
    hub=[p for p in breadth if not p["key"].startswith(("/prodotti/","/aziende/"))]
    print("  categorie:", len(cats), "| brand:", len(brands), "| altro(hub):", len(hub), [h["key"] for h in hub])
    print("HUB:", [p["key"] for p in breadth if p["key"]=="/aziende/"])
    print("PRIORITY brand:", len(priority), [p["key"] for p in priority])
    # sanity: any missing fields?
    prob=[]
    for p in breadth+priority:
        for lang in ("it","en"):
            b=p.get(lang)
            if not b: prob.append((p["key"],lang,"MANCA BLOCCO LINGUA")); continue
            if not b["title"]: prob.append((p["key"],lang,"no title"))
            if not b["h1"]: prob.append((p["key"],lang,"no h1"))
            if not b["blocks"]: prob.append((p["key"],lang,"no body"))
    print("PROBLEMI:", len(prob))
    for x in prob[:30]: print("  ", x)
    # sample
    print("\n--- ESEMPIO categoria (it) ---")
    c=cats[0]["it"]; print("title:",c["title"][:70]); print("h1:",c["h1"]); print("blocks:",len(c["blocks"]),"faq:",len(c["faq"]))
    print("--- ESEMPIO priority Cayman (it) ---")
    cay=[p for p in priority if "cayman" in p["key"]][0]["it"]
    print("title:",cay["title"]); print("blocks:",len(cay["blocks"]),"faq:",len(cay["faq"]),"jsonld:",len(cay["jsonld"]))
