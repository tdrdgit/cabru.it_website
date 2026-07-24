#!/usr/bin/env python3
# Generatore statico CABRU: content.json -> pagine HTML (IT + EN) nel sito.
import re, json, os, html, posixpath

def rel(cur, target):
    """Path relativo da 'cur' (url pagina, dir con / finale) a 'target' (root-absolute /...).
    Rende i link portabili: funzionano a root (cabru.it) e in sottopercorso (github.io)."""
    if not isinstance(target, str) or not target.startswith('/'):
        return target
    is_dir = target.endswith('/')
    r = posixpath.relpath(target, cur or '/')
    if is_dir and not r.endswith('/'):
        r += '/'
    if r in ('', '.'):
        r = './'
    return r

BASE = os.path.dirname(os.path.abspath(__file__))   # cartella _tooling (dentro sito/)
SITE = os.path.dirname(BASE)                          # la cartella sito/ = radice del sito pubblicato
data = json.load(open(os.path.join(BASE, "content.json"), encoding="utf-8"))

# ---- mappa slug brand -> file logo (differenze note) ----
LOGO = {"enzyme-research-laboratories": "enzyme-research"}
def logo_file(brand_slug):
    return LOGO.get(brand_slug, brand_slug) + ".png"

# ---- sito ufficiale del produttore (verificato via ricerca web, luglio 2026) ----
# Solo nelle pagine /aziende/<slug>/ il logo rimanda qui.
BRAND_SITE = {
    "a-a-biotechnology": "https://www.aabiot.com/",
    "affinity-biologicals": "https://affinitybiologicals.com/",
    "bioatlas": "https://www.bioatlas.com/",
    "biomedica-diagnostics": "https://biomedicadiagnostics.com/",
    "biovendor": "https://www.biovendor.com/",
    "candor-bioscience": "https://www.candor-bioscience.de/",
    "cayman-chemical": "https://www.caymanchem.com/",
    "condalab": "https://www.condalab.com/",
    "dia-pro": "https://www.diapro.it/",
    "enzyme-research-laboratories": "https://enzymeresearch.com/",
    "exbio": "https://www.exbio.cz/",
    "finetest": "https://www.fn-test.com/",
    "g-biosciences": "https://www.gbiosciences.com/",
    "immbiomed": "https://immbiomed.de/",
    "ldn": "https://www.ldn.de/",
    "magbio": "https://www.magbiogenomics.com/",
    "reliatech": "https://www.reliatech.de/",
    "rovalab": "http://www.rovalab.com/",
    "seqens": "https://www.seqens.com/",
    "smobio": "https://www.smobio.com/",
}

# ---- icone di categoria (stesse della home, in ordine CAT_SLUGS) ----
_ICO_OPEN = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
CAT_ICON = {
    "anticorpi": '<path d="M12 3v7"/><path d="M12 10 6 21"/><path d="M12 10l6 11"/><path d="M8 16h8"/>',
    "molecole-biochimiche": '<circle cx="12" cy="12" r="2.5"/><ellipse cx="12" cy="12" rx="10" ry="4.5"/><ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="10" ry="4.5" transform="rotate(120 12 12)"/>',
    "kit-elisa": '<rect x="3" y="3" width="18" height="18" rx="2"/><path d="M9 3v18M15 3v18M3 9h18M3 15h18"/>',
    "proteine": '<path d="M6 3c0 4 12 5 12 9s-12 5-12 9"/><path d="M18 3c0 4-12 5-12 9s12 5 12 9"/><path d="M8 6h8M8 18h8M9 9h6M9 15h6"/>',
    "acidi-nucleici": '<path d="M8 2c8 3 8 17 0 20M16 2c-8 3-8 17 0 20"/><path d="M9 5h6M8.4 9h7.2M8.4 15h7.2M9 19h6"/>',
    "elettroforesi-western-blot": '<rect x="4" y="3" width="6" height="18" rx="1"/><rect x="14" y="3" width="6" height="18" rx="1"/><path d="M4 8h6M4 13h6M14 7h6M14 12h6M14 17h6"/>',
    "terreni-microbiologia": '<path d="M4 12h16a8 8 0 0 1-16 0Z"/><path d="M3 12h18"/><path d="M12 4v3M9.5 5.5 12 7l2.5-1.5"/><circle cx="10" cy="15" r="1"/><circle cx="14" cy="16" r="1"/>',
    "soluzioni-polveri": '<path d="M9 3h6M10 3v6l-5 9a2 2 0 0 0 2 3h10a2 2 0 0 0 2-3l-5-9V3"/><path d="M7.5 15h9"/>',
    "plasmi": '<path d="M12 3s6 6.5 6 11a6 6 0 0 1-12 0c0-4.5 6-11 6-11Z"/>',
    "prodotti-diagnostici": '<rect x="5" y="3" width="14" height="18" rx="2"/><path d="M9 3v3h6V3"/><path d="M8 12.5l2.4 2.4L16 9.5"/>',
}
def cat_icon(slug):
    return f'<span class="cat-card__ico">{_ICO_OPEN}{CAT_ICON.get(slug, "")}</svg></span>'

# ---- mappa URL IT <-> EN ----
# IT: /prodotti/<s>/ /aziende/ /aziende/<s>/ /contatti/ /guide/eicosanoidi/ /applicazioni/tossicologia-forense/ /
# EN: /en/products/<s>/ /en/brands/ /en/brands/<s>/ /en/contact/ /en/guides/eicosanoids/ /en/applications/toxicology-forensics/ /en/
CAT_SLUGS = ["anticorpi","molecole-biochimiche","kit-elisa","proteine","acidi-nucleici",
             "elettroforesi-western-blot","terreni-microbiologia","soluzioni-polveri",
             "plasmi","prodotti-diagnostici"]
CAT_EN = {"anticorpi":"antibodies","molecole-biochimiche":"biochemicals","kit-elisa":"elisa-kits",
          "proteine":"proteins","acidi-nucleici":"nucleic-acids",
          "elettroforesi-western-blot":"electrophoresis-western-blot",
          "terreni-microbiologia":"microbiology-culture-media","soluzioni-polveri":"solutions-powders",
          "plasmi":"plasmas","prodotti-diagnostici":"diagnostic-products"}

def it_to_en_url(u):
    if u == "/": return "/en/"
    if u == "/aziende/": return "/en/brands/"
    if u == "/prodotti/": return "/en/products/"
    if u == "/contatti/": return "/en/contact/"
    if u == "/guide/eicosanoidi/": return "/en/guides/eicosanoids/"
    if u == "/applicazioni/tossicologia-forense/": return "/en/applications/toxicology-forensics/"
    m = re.match(r'^/prodotti/([^/]+)/$', u)
    if m: return f"/en/products/{CAT_EN.get(m.group(1), m.group(1))}/"
    m = re.match(r'^/aziende/([^/]+)/$', u)
    if m: return f"/en/brands/{m.group(1)}/"
    return u

# ---- raccolgo tutte le pagine in un modello unico ----
PAGES = []  # dict: it_url, en_url, lang blocks
def add(it_url, name, it, en, kind, brand_slug=None, jsonld_it=None, jsonld_en=None):
    PAGES.append({"it_url": it_url, "en_url": it_to_en_url(it_url), "name": name,
                  "it": it, "en": en, "kind": kind, "brand_slug": brand_slug})

for p in data["breadth"]:
    kind = "cat" if p["key"].startswith("/prodotti/") else ("hub" if p["key"]=="/aziende/" else "brand")
    bslug = p["key"].strip("/").split("/")[-1] if kind=="brand" else None
    add(p["key"], p["name"], p["it"], p["en"], kind, bslug)
for p in data["priority"]:
    bslug = p["key"].strip("/").split("/")[-1]
    add(p["key"], p["name"], p["it"], p["en"], "brand", bslug)

# ---- pagine extra (copy originale, IT+EN) ----
def block_page(title, meta, h1, blocks, faq=None):
    return {"title": title, "meta": meta, "h1": h1, "keywords":"", "blocks": blocks, "faq": faq or [], "jsonld": []}

# /prodotti/ hub
prod_it = block_page(
  "Prodotti per laboratorio | CABRU",
  "Le categorie di prodotto CABRU: anticorpi, molecole biochimiche, kit ELISA, proteine, acidi nucleici, elettroforesi, terreni e soluzioni.",
  "Categorie di prodotto",
  [("p","Reagenti, kit e materiali per la ricerca, la diagnostica e il controllo qualità, dai produttori internazionali rappresentati da CABRU in Italia. Le categorie di seguito organizzano l'offerta per ambito applicativo.")])
prod_en = block_page(
  "Laboratory products | CABRU",
  "CABRU product categories: antibodies, biochemicals, ELISA kits, proteins, nucleic acids, electrophoresis, culture media and solutions.",
  "Product categories",
  [("p","Reagents, kits and materials for research, diagnostics and quality control, from the international manufacturers represented by CABRU in Italy. The categories below organise the offering by application area.")])
add("/prodotti/", "Prodotti", prod_it, prod_en, "prodhub")

# NB: la pagina /contatti/ è stata rimossa: il contatto avviene tramite il form
# modale (js/site.js) richiamato dal pulsante "Contattaci" e dai link contatto.

# satellite: guida eicosanoidi
eico_it = block_page(
  "Eicosanoidi: cosa sono e come si dosano | CABRU",
  "Eicosanoidi: cosa sono prostaglandine, leucotrieni ed endocannabinoidi, il loro ruolo nell'infiammazione e come si studiano in laboratorio.",
  "Eicosanoidi: cosa sono e come si studiano",
  [("p","Gli eicosanoidi sono mediatori lipidici derivati dagli acidi grassi polinsaturi, in particolare dall'acido arachidonico. Comprendono prostaglandine, trombossani, leucotrieni e lipossine, ai quali si affiancano gli endocannabinoidi e altri lipidi bioattivi."),
   ("h3","Perché si studiano"),
   ("p","Regolano infiammazione, aggregazione piastrinica, tono vascolare e numerose vie di segnalazione cellulare. Sono bersagli e biomarcatori nella ricerca su infiammazione, dolore, oncologia e malattie cardiovascolari e metaboliche."),
   ("h3","Come si dosano in laboratorio"),
   ("p","Il dosaggio avviene tipicamente con saggi immunoenzimatici (kit ELISA/EIA) e con metodiche analitiche che impiegano standard di riferimento e traccianti. Servono reagenti a purezza elevata e standard analitici affidabili."),
   ("h3","Reagenti tramite CABRU"),
   ("p","Per lo studio degli eicosanoidi CABRU rappresenta [Cayman Chemical](/aziende/cayman-chemical/), storicamente specializzata nella chimica dei lipidi, con [molecole biochimiche](/prodotti/molecole-biochimiche/), standard e [kit ELISA](/prodotti/kit-elisa/) dedicati. Per approfondimenti o richieste è possibile rivolgersi a [CABRU](/contatti/).")])
eico_en = block_page(
  "Eicosanoids: what they are and how they are measured | CABRU",
  "Eicosanoids explained: prostaglandins, leukotrienes and endocannabinoids, their role in inflammation and how they are studied in the lab.",
  "Eicosanoids: what they are and how they are studied",
  [("p","Eicosanoids are lipid mediators derived from polyunsaturated fatty acids, mainly arachidonic acid. They include prostaglandins, thromboxanes, leukotrienes and lipoxins, alongside endocannabinoids and other bioactive lipids."),
   ("h3","Why they matter"),
   ("p","They regulate inflammation, platelet aggregation, vascular tone and many cell-signalling pathways, and act as targets and biomarkers in research on inflammation, pain, oncology and cardiovascular and metabolic disease."),
   ("h3","How they are measured"),
   ("p","They are typically quantified with enzyme immunoassays (ELISA/EIA kits) and analytical methods using reference standards and tracers, which require high-purity reagents and reliable analytical standards."),
   ("h3","Reagents via CABRU"),
   ("p","For eicosanoid research CABRU represents [Cayman Chemical](/en/brands/cayman-chemical/), long specialised in lipid chemistry, with [biochemicals](/en/products/biochemicals/), standards and dedicated [ELISA kits](/en/products/elisa-kits/). [Request information](/en/contact/).")])
add("/guide/eicosanoidi/", "Eicosanoidi", eico_it, eico_en, "guide")

# satellite: applicazione tossicologia forense
tox_it = block_page(
  "Tossicologia e scienze forensi: reagenti e standard | CABRU",
  "Reagenti, standard analitici e composti di riferimento per la tossicologia e le scienze forensi, dai produttori rappresentati da CABRU.",
  "Tossicologia e scienze forensi",
  [("p","La tossicologia analitica e le scienze forensi richiedono standard di riferimento e composti puri per l'identificazione e la quantificazione di sostanze, metaboliti e marcatori in matrici biologiche."),
   ("h3","Cosa serve"),
   ("p","Standard analitici certificati per metodica, traccianti, inibitori e molecole di riferimento, insieme a saggi per il dosaggio di metaboliti e mediatori. La qualità e la tracciabilità degli standard sono determinanti per l'affidabilità del dato."),
   ("h3","Reagenti tramite CABRU"),
   ("p","Per quest'area CABRU rappresenta [Cayman Chemical](/aziende/cayman-chemical/), con un'ampia offerta di [molecole biochimiche](/prodotti/molecole-biochimiche/), standard analitici e [kit ELISA](/prodotti/kit-elisa/). Per approfondimenti o richieste è possibile rivolgersi a [CABRU](/contatti/).")])
tox_en = block_page(
  "Toxicology and forensic science: reagents and standards | CABRU",
  "Reagents, analytical standards and reference compounds for toxicology and forensic science, from the manufacturers CABRU represents.",
  "Toxicology and forensic science",
  [("p","Analytical toxicology and forensic science rely on reference standards and pure compounds to identify and quantify substances, metabolites and markers in biological matrices."),
   ("h3","What is needed"),
   ("p","Method-specific certified analytical standards, tracers, inhibitors and reference molecules, together with assays for metabolites and mediators. Standard quality and traceability are decisive for reliable results."),
   ("h3","Reagents via CABRU"),
   ("p","For this area CABRU represents [Cayman Chemical](/en/brands/cayman-chemical/), with a broad range of [biochemicals](/en/products/biochemicals/), analytical standards and [ELISA kits](/en/products/elisa-kits/). [Request information](/en/contact/).")])
add("/applicazioni/tossicologia-forense/", "Tossicologia e scienze forensi", tox_it, tox_en, "application")

# categoria: Plasmi
plasmi_it = block_page(
  "Plasmi carenti e di controllo | CABRU",
  "Plasmi carenti e di controllo per lo studio dell'emostasi, della coagulazione e della trombosi, dai produttori rappresentati da CABRU in Italia.",
  "Plasmi carenti e di controllo",
  [("h2","Cosa comprende la categoria"),
   ("p","Plasmi carenti in singoli fattori e plasmi di controllo per lo studio dell'emostasi e della coagulazione, impiegati come matrici di riferimento nei saggi funzionali e nella validazione dei metodi."),
   ("h2","Applicazioni tipiche"),
   ("p","Studio di emostasi e trombosi, dosaggio dei fattori della coagulazione, controllo di qualità e taratura dei saggi funzionali."),
   ("h2","Aziende che li producono"),
   ("p","Plasmi dai produttori rappresentati da CABRU: [Affinity Biologicals](/aziende/affinity-biologicals/) e [BioMedica Diagnostics](/aziende/biomedica-diagnostics/)."),
   ("h2","Come richiedere un preventivo"),
   ("p","Per la referenza più adatta è sufficiente indicare il fattore o l'applicazione di interesse; CABRU individua il prodotto tra i produttori rappresentati e ne gestisce l'ordine con un unico referente.")],
  [["Che tipi di plasmi sono disponibili?","Plasmi carenti in singoli fattori e plasmi di controllo per lo studio dell'emostasi e della coagulazione."],
   ["Per quali applicazioni si utilizzano?","Studio di emostasi e trombosi, dosaggio dei fattori della coagulazione e controllo di qualità dei saggi funzionali."]])
plasmi_en = block_page(
  "Deficient and control plasmas | CABRU",
  "Deficient and control plasmas for the study of haemostasis, coagulation and thrombosis, from the manufacturers represented by CABRU in Italy.",
  "Deficient and control plasmas",
  [("h2","What this category covers"),
   ("p","Single-factor deficient plasmas and control plasmas for the study of haemostasis and coagulation, used as reference matrices in functional assays and method validation."),
   ("h2","Typical applications"),
   ("p","Study of haemostasis and thrombosis, coagulation-factor assays, quality control and calibration of functional assays."),
   ("h2","Who makes them"),
   ("p","Plasmas from the manufacturers represented by CABRU: [Affinity Biologicals](/en/brands/affinity-biologicals/) and [BioMedica Diagnostics](/en/brands/biomedica-diagnostics/)."),
   ("h2","How to request a quote"),
   ("p","To identify the most suitable reference it is sufficient to specify the factor or application of interest; CABRU sources the product among the manufacturers it represents and handles the order through a single point of contact.")],
  [["Which types of plasma are available?","Single-factor deficient plasmas and control plasmas for the study of haemostasis and coagulation."],
   ["What are they used for?","Study of haemostasis and thrombosis, coagulation-factor assays and quality control of functional assays."]])
add("/prodotti/plasmi/", "Plasmi carenti e di controllo", plasmi_it, plasmi_en, "cat")

# categoria: Prodotti diagnostici
diag_it = block_page(
  "Prodotti per la diagnostica | CABRU",
  "Kit e prodotti per la diagnostica dai produttori rappresentati da CABRU in Italia. Informazioni, disponibilità e preventivi.",
  "Prodotti per la diagnostica",
  [("h2","Cosa comprende la categoria"),
   ("p","Kit diagnostici e reagenti destinati all'ambito diagnostico, per la rilevazione e il dosaggio di marcatori e analiti di interesse clinico."),
   ("h2","Applicazioni tipiche"),
   ("p","Diagnostica di laboratorio, screening e dosaggi immunoenzimatici in ambito clinico."),
   ("h2","Aziende che li producono"),
   ("p","Prodotti diagnostici dai produttori rappresentati da CABRU: [DIA.PRO](/aziende/dia-pro/)."),
   ("h2","Come richiedere un preventivo"),
   ("p","Per la disponibilità e il preventivo di un kit è sufficiente indicare il prodotto o il marcatore di interesse; CABRU fornisce il riscontro con un unico referente.")],
  [["Chi produce i prodotti diagnostici distribuiti da CABRU?","I kit diagnostici provengono da DIA.PRO, produttore rappresentato da CABRU in Italia."],
   ["Qual è l'uso previsto dei prodotti?","L'uso previsto di ciascun prodotto è indicato nella documentazione del produttore."]])
diag_en = block_page(
  "Diagnostic products | CABRU",
  "Diagnostic kits and products from the manufacturers represented by CABRU in Italy. Information, availability and quotations.",
  "Diagnostic products",
  [("h2","What this category covers"),
   ("p","Diagnostic kits and reagents intended for the diagnostic field, for the detection and measurement of markers and analytes of clinical interest."),
   ("h2","Typical applications"),
   ("p","Laboratory diagnostics, screening and enzyme immunoassays in the clinical setting."),
   ("h2","Who makes them"),
   ("p","Diagnostic products from the manufacturers represented by CABRU: [DIA.PRO](/en/brands/dia-pro/)."),
   ("h2","How to request a quote"),
   ("p","To check availability and obtain a quotation for a kit it is sufficient to specify the product or marker of interest; CABRU provides the necessary feedback through a single point of contact.")],
  [["Who makes the diagnostic products distributed by CABRU?","The diagnostic kits are made by DIA.PRO, a manufacturer represented by CABRU in Italy."],
   ["What is the intended use of the products?","The intended use of each product is stated in the manufacturer's documentation."]])
add("/prodotti/prodotti-diagnostici/", "Prodotti per la diagnostica", diag_it, diag_en, "cat")

# ---- insieme URL esistenti (per risolvere i link interni) ----
EXISTING = set()
for pg in PAGES:
    EXISTING.add(pg["it_url"]); EXISTING.add(pg["en_url"])
EXISTING.add("/"); EXISTING.add("/en/")

# ---- inline markdown -> HTML (link + bold), con link-resolver ----
def render_inline(text, cur):
    text = text.strip()
    def linkrepl(m):
        t, u = m.group(1), m.group(2)
        if u in ("/contatti/","/en/contact/"):
            return f'<a href="mailto:info@cabru.it" class="js-contact">{t}</a>'
        if u.startswith(("http://","https://","mailto:","tel:","#")):
            attr = ' target="_blank" rel="noopener"' if u.startswith("http") else ""
            return f'<a href="{u}"{attr}>{t}</a>'
        if u in EXISTING:
            return f'<a href="{rel(cur, u)}">{t}</a>'
        return t  # link a pagina non esistente -> testo semplice (niente link rotti)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', linkrepl, text)
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    return text

def render_blocks(blocks, cur):
    out=[]
    for typ, val in blocks:
        if typ=="h2": out.append(f"<h2>{render_inline(val, cur)}</h2>")
        elif typ=="h3": out.append(f"<h3>{render_inline(val, cur)}</h3>")
        elif typ=="p": out.append(f"<p>{render_inline(val, cur)}</p>")
        elif typ=="ul":
            lis="".join(f"<li>{render_inline(x, cur)}</li>" for x in val)
            out.append(f"<ul class='mrk'>{lis}</ul>")
    return "\n".join(out)

def render_faq(faq, cur, en=False):
    if not faq: return ""
    title = "Frequently asked questions" if en else "Domande frequenti"
    items=[]
    for q,a in faq:
        items.append(f"<div class='faq-item'><h3 class='faq-q'>{render_inline(q, cur)}</h3><div class='faq-a'>{render_inline(a, cur)}</div></div>")
    return f"<section class='faq'><h2>{title}</h2>"+ "".join(items) +"</section>"

# ---- schema auto (breadcrumb + faqpage) quando non forniti ----
DOMAIN="https://www.cabru.it"
def auto_schema(pg, lang):
    b = pg[lang]
    url = pg["it_url"] if lang=="it" else pg["en_url"]
    crumbs=[{"@type":"ListItem","position":1,"name":"Home","item":DOMAIN+("/" if lang=="it" else "/en/")}]
    # add section + page
    crumbs.append({"@type":"ListItem","position":2,"name":b["h1"],"item":DOMAIN+url})
    out=[{"@context":"https://schema.org","@type":"BreadcrumbList","itemListElement":crumbs}]
    if b.get("faq"):
        out.append({"@context":"https://schema.org","@type":"FAQPage",
                    "inLanguage": "it-IT" if lang=="it" else "en-GB",
                    "mainEntity":[{"@type":"Question","name":re.sub('<[^>]+>','',q),
                                   "acceptedAnswer":{"@type":"Answer","text":re.sub(r'\[([^\]]+)\]\([^)]+\)',r'\1',re.sub(r'\*\*','',a))}} for q,a in b["faq"]]})
    return out

# ---- header / footer ----
NAV_IT=[("/prodotti/","Prodotti"),("/aziende/","Aziende"),("/catalogo/","Catalogo")]
NAV_EN=[("/en/products/","Products"),("/en/brands/","Brands"),("/en/catalog/","Catalogue")]

def header(lang, it_url, en_url, cur):
    home = "/" if lang=="it" else "/en/"
    nav = NAV_IT if lang=="it" else NAV_EN
    cta_txt = "Contattaci" if lang=="it" else "Contact us"
    navlinks="".join(f'<a href="{rel(cur,h)}">{t}</a>' for h,t in nav)
    lang_switch = (f'<a href="{rel(cur,it_url)}" class="lang {"on" if lang=="it" else ""}">IT</a>'
                   f'<a href="{rel(cur,en_url)}" class="lang {"on" if lang=="en" else ""}">EN</a>')
    return f'''<header class="site-header">
    <div class="wrap">
      <a class="brand" href="{rel(cur,home)}" aria-label="CABRU"><img src="{rel(cur,'/img/logo-cabru.png')}" alt="CABRU"></a>
      <input type="checkbox" id="navtoggle" class="nav-checkbox" aria-label="Menu">
      <label for="navtoggle" class="nav-burger" aria-label="Menu"><span></span><span></span><span></span></label>
      <nav class="nav">
        {navlinks}
        <a href="mailto:info@cabru.it" class="nav-cta js-contact">{cta_txt}</a>
        <span class="lang-switch">{lang_switch}</span>
      </nav>
    </div>
  </header>'''

def footer(lang):
    if lang=="it":
        return '''<footer class="site-footer"><div class="wrap">
      <div><span class="foot-brand">CABRU s.a.s.</span> · Via Enrico Forlanini 52, 20862 Arcore (MB) · <a href="tel:+390396013988">039 6013988</a> · <a href="mailto:info@cabru.it">info@cabru.it</a></div>
      <div>© <span id="y"></span> CABRU — Prodotti per laboratorio, industria e ricerca</div>
      </div></footer><script>document.getElementById('y').textContent=new Date().getFullYear()</script>'''
    return '''<footer class="site-footer"><div class="wrap">
      <div><span class="foot-brand">CABRU s.a.s.</span> · Via Enrico Forlanini 52, 20862 Arcore (MB), Italy · <a href="tel:+390396013988">+39 039 6013988</a> · <a href="mailto:info@cabru.it">info@cabru.it</a></div>
      <div>© <span id="y"></span> CABRU — Laboratory, industry and research products</div>
      </div></footer><script>document.getElementById('y').textContent=new Date().getFullYear()</script>'''

def breadcrumb(pg, lang, cur):
    home = "/" if lang=="it" else "/en/"
    parts=[f'<a href="{rel(cur,home)}">Home</a>']
    b=pg[lang]
    if pg["kind"]=="brand":
        hub = "/aziende/" if lang=="it" else "/en/brands/"
        parts.append(f'<a href="{rel(cur,hub)}">{"Aziende" if lang=="it" else "Brands"}</a>')
    elif pg["kind"]=="cat":
        hub = "/prodotti/" if lang=="it" else "/en/products/"
        parts.append(f'<a href="{rel(cur,hub)}">{"Prodotti" if lang=="it" else "Products"}</a>')
    parts.append(f'<span>{b["h1"]}</span>')
    return '<nav class="crumb">'+ " › ".join(parts) +'</nav>'

def brand_hero(pg, lang, cur):
    if pg["kind"]!="brand": return ""
    logo = rel(cur, "/img/partners/"+logo_file(pg["brand_slug"]))
    img = f'<img src="{logo}" alt="{pg["name"]}">'
    site = BRAND_SITE.get(pg["brand_slug"])
    if site:
        label = "Sito ufficiale di " if lang=="it" else "Official website of "
        return (f'<div class="brand-hero"><a class="brand-hero__link" href="{site}" '
                f'target="_blank" rel="noopener nofollow" title="{label}{pg["name"]}">{img}</a></div>')
    return f'<div class="brand-hero">{img}</div>'

def hub_grid(lang, cur):
    brands=[pg for pg in PAGES if pg["kind"]=="brand"]
    brands.sort(key=lambda x:x["name"].lower())
    cards=[]
    for pg in brands:
        url = rel(cur, pg["it_url"] if lang=="it" else pg["en_url"])
        logo=rel(cur, "/img/partners/"+logo_file(pg["brand_slug"]))
        cards.append(f'<a class="brand-card" href="{url}"><span class="brand-card__logo"><img src="{logo}" alt="{pg["name"]}" loading="lazy"></span><span class="brand-card__name">{pg["name"]}</span></a>')
    return '<div class="brand-grid">'+"".join(cards)+'</div>'

def prod_grid(lang, cur):
    cards=[]
    for s in CAT_SLUGS:
        pg=[p for p in PAGES if p["kind"]=="cat" and p["it_url"]==f"/prodotti/{s}/"][0]
        url=rel(cur, pg["it_url"] if lang=="it" else pg["en_url"])
        cards.append(f'<a class="cat-card" href="{url}">{cat_icon(s)}<span class="cat-card__name">{pg[lang]["h1"]}</span><span class="cat-card__meta">{pg[lang]["meta"][:90]}…</span></a>')
    return '<div class="cat-grid">'+"".join(cards)+'</div>'

def build_page(pg, lang):
    b=pg[lang]
    url = pg["it_url"] if lang=="it" else pg["en_url"]
    cur = url
    it_url, en_url = pg["it_url"], pg["en_url"]
    lang_attr = "it" if lang=="it" else "en"
    schema = b.get("jsonld") or auto_schema(pg, lang)
    schema_html = "\n".join(f'<script type="application/ld+json">{json.dumps(s, ensure_ascii=False)}</script>' for s in schema)
    body = render_blocks(b["blocks"], cur)
    extra=""
    if pg["kind"]=="hub": extra = hub_grid(lang, cur)
    if pg["kind"]=="prodhub": extra = prod_grid(lang, cur)
    faq_html = render_faq(b.get("faq"), cur, en=(lang=="en"))
    site_js = rel(cur, "/js/site.js")
    return f'''<!DOCTYPE html>
<html lang="{lang_attr}">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(b["title"])}</title>
<meta name="description" content="{html.escape(b["meta"])}">
<link rel="canonical" href="{DOMAIN+url}">
<link rel="alternate" hreflang="it" href="{DOMAIN+it_url}">
<link rel="alternate" hreflang="en" href="{DOMAIN+en_url}">
<link rel="alternate" hreflang="x-default" href="{DOMAIN+it_url}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="CABRU s.a.s.">
<meta property="og:locale" content="{'it_IT' if lang=='it' else 'en_US'}">
<meta property="og:title" content="{html.escape(b["title"])}">
<meta property="og:description" content="{html.escape(b["meta"] or b["title"])}">
<meta property="og:url" content="{DOMAIN+url}">
<meta property="og:image" content="{DOMAIN}/img/logo-cabru.png">
<meta name="twitter:card" content="summary">
<link rel="stylesheet" href="{rel(cur,'/css/style.css')}">
<link rel="stylesheet" href="{rel(cur,'/css/content.css')}">
{schema_html}
</head>
<body>
{header(lang, it_url, en_url, cur)}
<main class="page">
  <div class="wrap">
    {breadcrumb(pg, lang, cur)}
    <article class="doc">
      {brand_hero(pg, lang, cur)}
      <h1>{html.escape(b["h1"])}</h1>
      {body}
      {extra}
      {faq_html}
      <div class="cta-block">
        <a class="btn btn-primary js-contact" href="mailto:info@cabru.it">{'Richiedi informazioni' if lang=='it' else 'Request information'}</a>
      </div>
    </article>
  </div>
</main>
{footer(lang)}
<script src="{site_js}" defer></script>
</body>
</html>'''

def out_path(url):
    # url like /prodotti/anticorpi/  -> SITE/prodotti/anticorpi/index.html
    rel = url.strip("/")
    d = os.path.join(SITE, rel) if rel else SITE
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "index.html")

count=0
for pg in PAGES:
    for lang in ("it","en"):
        url = pg["it_url"] if lang=="it" else pg["en_url"]
        htmlout = build_page(pg, lang)
        open(out_path(url),"w",encoding="utf-8").write(htmlout)
        count+=1
print("Pagine generate:", count)
print("URL IT:", sorted(p["it_url"] for p in PAGES))
