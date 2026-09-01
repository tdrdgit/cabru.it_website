#!/usr/bin/env python3
"""Controlla una volta al mese che il certificato ISO 9001 sia ancora valido
e ancora pubblicato, e avvisa su Telegram quando c'e' qualcosa da fare.

Guarda tre cose:
  1. quanto manca alla scadenza del certificato;
  2. che le due pagine online mostrino ancora il numero di certificato;
  3. che il PDF del certificato sia scaricabile.

Avvisa quando manca meno di sei mesi alla scadenza, quando qualcosa non
risponde, e comunque ogni sei mesi anche se va tutto bene — quest'ultima e' la
sola difesa contro il caso peggiore, cioe' uno scheduler fermo che tace
esattamente come un mese tranquillo.

    python3 sorveglia_certificato.py            # il giro normale
    python3 sorveglia_certificato.py --sempre   # avvisa comunque, per provarlo
"""
import sys, os, json, datetime, urllib.request, urllib.error

sys.path.insert(0, os.path.expanduser("~/.claude/scripts"))

NUMERO   = "ICIM-9001-001683-08"
SCADENZA = datetime.date(2027, 10, 15)
PREAVVISO_GIORNI = 180      # da qui in poi si avvisa a ogni giro
BATTITO_GIORNI   = 180      # e comunque non si tace piu' a lungo di cosi'

# Il dominio vero prima, la preview dopo: si usa il primo che risponde.
BASI = ["https://www.cabru.it", "https://tdrdgit.github.io/cabru.it_website"]
PAGINE = ["/qualita/", "/en/quality/"]
PDF    = "/docs/certificato-iso-9001-cabru.pdf"

STATO = os.path.expanduser("~/Library/Application Support/potential/cabru_certificato_iso.json")


def scarica(url, testo=True):
    req = urllib.request.Request(url, headers={"User-Agent": "CABRU-monitor/1.0"})
    with urllib.request.urlopen(req, timeout=25) as r:
        return (r.read().decode("utf-8", "replace") if testo else b""), r.status


def base_viva():
    """La prima base che serve davvero la pagina qualita' con dentro il certificato.

    Il dominio non basta che risponda: oggi www.cabru.it risponde ma rimanda al
    sito vecchio, che il certificato non ce l'ha. Quindi si guarda il contenuto.
    """
    ultimo = None
    for b in BASI:
        try:
            corpo, _ = scarica(b + PAGINE[0])
            if NUMERO in corpo:
                return b, None
            ultimo = f"{b} risponde ma la pagina qualita' non contiene {NUMERO}"
        except Exception as e:
            ultimo = f"{b} non risponde ({e})"
    return None, ultimo


def main():
    sempre = "--sempre" in sys.argv
    oggi = datetime.date.today()
    giorni = (SCADENZA - oggi).days
    problemi = []

    base, perche = base_viva()
    if base is None:
        problemi.append(perche or "nessuna delle due basi risponde")
    else:
        for p in PAGINE[1:]:
            try:
                corpo, _ = scarica(base + p)
                if NUMERO not in corpo:
                    problemi.append(f"{p} non mostra piu' il numero di certificato")
            except Exception as e:
                problemi.append(f"{p} non risponde ({e})")
        try:
            _, stato = scarica(base + PDF, testo=False)
            if stato != 200:
                problemi.append(f"il PDF del certificato risponde {stato}")
        except Exception as e:
            problemi.append(f"il PDF del certificato non si scarica ({e})")

    print(f"[{oggi:%d.%m.%Y}] scadenza fra {giorni} giorni · base: {base or 'nessuna'} "
          f"· problemi: {len(problemi)}")

    try:
        stato = json.load(open(STATO, encoding="utf-8"))
        ultimo_avviso = datetime.date.fromisoformat(stato.get("ultimo_avviso", "2000-01-01"))
    except Exception:
        ultimo_avviso = datetime.date(2000, 1, 1)

    in_scadenza = giorni <= PREAVVISO_GIORNI
    battito = (oggi - ultimo_avviso).days >= BATTITO_GIORNI

    if problemi:
        riga = ("CABRU — la pagina del certificato ISO 9001 ha un problema:\n"
                + "\n".join("• " + p for p in problemi))
    elif giorni < 0:
        riga = (f"CABRU — il certificato ISO 9001 {NUMERO} e' SCADUTO il "
                f"{SCADENZA:%d.%m.%Y}. Il sito dichiara una certificazione non piu' valida: "
                f"va sostituito il PDF e aggiornate le due pagine qualita'.")
    elif in_scadenza:
        riga = (f"CABRU — il certificato ISO 9001 scade il {SCADENZA:%d.%m.%Y}, "
                f"fra {giorni} giorni. Al rinnovo vanno sostituiti il PDF in "
                f"sito/docs/ e gli estremi nelle pagine /qualita/ e /en/quality/.")
    elif battito or sempre:
        riga = (f"CABRU — certificato ISO 9001 in regola: online in italiano e in "
                f"inglese, PDF scaricabile, scade fra {giorni} giorni "
                f"({SCADENZA:%d.%m.%Y}).")
    else:
        riga = None

    if riga:
        try:
            import notifica_telegram
            notifica_telegram.notifica(riga, silenzioso=True)
            print("avviso Telegram mandato")
        except Exception as e:
            # un canale che tace quando si rompe e' il guasto da evitare
            print(f"Telegram non ha funzionato: {e}", file=sys.stderr)
        os.makedirs(os.path.dirname(STATO), exist_ok=True)
        json.dump({"ultimo_avviso": oggi.isoformat(), "ultimo_giro": oggi.isoformat(),
                   "giorni_alla_scadenza": giorni, "problemi": problemi},
                  open(STATO, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    else:
        os.makedirs(os.path.dirname(STATO), exist_ok=True)
        base_stato = {"ultimo_avviso": ultimo_avviso.isoformat()}
        base_stato.update({"ultimo_giro": oggi.isoformat(),
                           "giorni_alla_scadenza": giorni, "problemi": []})
        json.dump(base_stato, open(STATO, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)

    sys.exit(1 if problemi else 0)


if __name__ == "__main__":
    main()
