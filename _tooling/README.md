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
- I percorsi degli script sono relativi alla posizione del file: `SITE` = la cartella
  `sito/` (padre di `_tooling/`); l'XLS viene scritto nella cartella padre del repo.
