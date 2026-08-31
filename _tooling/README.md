# _tooling — generatori del sito CABRU (NON pubblicato)

Cartella di servizio DENTRO il repo (`sito/_tooling/`). Sta nel repo così viaggia
con GitHub, ma il nome inizia con `_` quindi GitHub Pages la ignora: non finisce
online. Da qui si rigenerano le pagine del sito e l'XLS dei testi da correggere.

## File
- `content.json`     — fonte dei contenuti (IT+EN) delle pagine generate
- `generate.py`      — `content.json` → pagine HTML in `../` (la cartella `sito/`, 68 pagine interne)
- `build_xls.py`     — estrae i testi IT dal sito → `../../CABRU_testi_IT_da_correggere.xlsx` (FUORI dal repo)
- `desc.json`        — nomi + descrizioni brevi delle aziende (usato da `build_xls.py`)
- `parse_content.py` — utility

## Comandi (dalla cartella `_tooling`)
    python3 generate.py     # rigenera le pagine interne del sito
    python3 build_xls.py    # rigenera l'XLS delle correzioni
    python3 build_loghi.py  # riscrive i loghi dei produttori in img/partners/
    python3 misura_loghi.py img/partners   # dice quanto sono uniformi

## Dipendenze
- `generate.py`: solo Python standard, nessuna dipendenza.
- `build_xls.py`: `beautifulsoup4` + `openpyxl`. Se mancano:
      pip3 install --target ./pylib beautifulsoup4 openpyxl
  Lo script aggiunge `./pylib` al path se la cartella esiste, altrimenti usa
  le librerie di sistema.

## Note
- Home, home EN e le due pagine catalogo sono scritte a mano in `../` (dentro `sito/`)
  (NON generate da `generate.py`): le modifiche lì vanno fatte a mano.
- Regola: dopo ogni modifica ai testi del sito, rigenerare l'XLS con `build_xls.py`.
  Vedi sotto: «Le correzioni dei testi» — l'XLS e' anche il canale con cui altri
  chiedono modifiche, quindi rigenerarlo a sproposito cancella le loro richieste.
- I percorsi degli script sono relativi alla posizione del file: `SITE` = la cartella
  `sito/` (padre di `_tooling/`); l'XLS viene scritto nella cartella padre del repo.

## I loghi dei produttori
I file in `../img/partners/` **sono generati**: si modificano da
`loghi_originali/` (gli originali dei produttori, mai toccati) rilanciando
`build_loghi.py`. Un ritocco fatto a mano sull'immagine pubblicata sparisce alla
prima rigenerazione, senza dire niente.

Lo script serve a un problema solo: i loghi arrivano con proporzioni e margini
diversi, e vincolarli alla stessa altezza in CSS non basta — un logo lungo copre
molta piu' superficie di uno compatto e sembra piu' grande. Qui ognuno viene
ritagliato dal margine bianco, misurato e riscalato perche' pesi come gli altri,
sopra una tela identica per tutti. Cosi' l'uniformita' vale su ogni pagina in cui
il logo compare, senza regole CSS per singolo file.

Le regolazioni stanno in `loghi_taratura.json`: il peso fra superficie scura e
ingombro, l'altezza del logo mediano, e un moltiplicatore per i casi che l'occhio
giudica fuori posto. `misura_loghi.py` dice a che punto si e': si e' passati da un
divario di 4,4 volte fra il logo piu' pesante e il piu' leggero a 1,8.

⚠️ Un logo aggiunto con un file a bassa risoluzione viene ingrandito e si vede:
lo script lo segnala da solo con "sorgente a bassa risoluzione".

## Le correzioni dei testi — come si lavora

L'XLS ha tre colonne: **A** il tipo di testo (non si tocca, serve a rimettere le
correzioni al posto giusto), **B** il testo che c'e' oggi online, **C** la colonna
gialla dove chi rilegge scrive la versione corretta.

Il giro e' sempre questo:

1. **Si integra la modifica nel sito**, in italiano **e in inglese**. L'inglese non
   sta nell'XLS: e' derivato dall'italiano, e va aggiornato nello stesso passaggio o
   le due lingue si disallineano senza che niente dia errore.
2. **Il testo corretto si sposta dalla colonna C alla colonna B** e li' resta
   **verde** (`#1B5E20`).
3. **La colonna C torna vuota.**
4. Il testo verde entra nel registro `verdi.json`.

I passi 2, 3 e 4 li fa `correzioni.py`:

    python3 correzioni.py elenca   # cosa e' stato chiesto, e dove
    python3 correzioni.py chiudi   # DOPO averlo messo nel sito

### Cosa vuol dire verde

🔑 **Verde = l'ha voluto un umano.** E' la convenzione globale: un valore verde non e'
solo «corretto una volta», e' una decisione che vale anche per le prossime.

🔴 **Quindi un testo verde non si riscrive in autonomia.** Se una modifica automatica
andrebbe a toccarlo — e a maggior ragione se e' una traduzione generata — **si segnala
a Carlo prima**, non dopo. Il controllo e' `correzioni.tocco_un_verde(testo)`, che
risponde con il foglio in cui quel testo era stato deciso.

### Due guasti silenziosi, gia' chiusi

- **Il verde spariva a ogni rigenerazione**: `build_xls.py` ricostruisce il file da
  zero e riscriveva tutti i testi in grigio. Ora rilegge `verdi.json` e ricolora.
  Il registro e' un file a parte apposta: sopravvive anche a un XLS cancellato.
- **Rigenerare cancellava le correzioni non ancora processate.** Ora `build_xls.py`
  si ferma e dice quali sono. Con `--forza` si sovrascrive lo stesso, ma solo
  sapendo di buttarle.
