#!/usr/bin/env python3
"""Verifica gli invarianti della homepage di echo.srl.

Il repo non ha un framework di test: questo script svolge quel ruolo.
Controlla cio' che il redesign della home rischia di rompere in silenzio:
ancore entranti, gerarchia dei titoli, accessibilita', tag SEO, peso immagini.

Run:  python3 scripts/check_home.py
Exit: 0 tutto ok, 1 almeno un fallimento
"""
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"

# Ancore storiche linkate dalle 38 pagine interne. Valgono 68 link.
ANCORE_STORICHE = ["metodo", "contatti", "origine", "casi"]
# Ancora nuova, introdotta dalla nav ridisegnata.
ANCORE_NUOVE = ["servizi"]

# Tag SEO che devono sopravvivere alla riscrittura.
SEO_ATTESI = [
    'rel="canonical"',
    'property="og:title"',
    'property="og:image"',
    'name="twitter:card"',
    'rel="icon"',
    'rel="manifest"',
]

IMMAGINI_HERO = [
    ("hero-formazione.jpg", 260),
    ("hero-formazione@2x.jpg", 340),
]


class Analisi(HTMLParser):
    """Raccoglie dalla pagina cio' che serve alle asserzioni."""

    def __init__(self):
        super().__init__()
        self.ids = set()
        self.titoli = []           # (livello, testo)
        self.immagini = []         # dict di attributi
        self.href_interni = []     # href che iniziano con '#'
        self.fogli_stile = []
        self._titolo_corrente = None
        self.ticker_wrap_nascosto = False
        self.ticker_prima_track_nascosta = None

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.add(a["id"])
        if tag == "img":
            self.immagini.append(a)
        if tag == "a" and a.get("href", "").startswith("#"):
            self.href_interni.append(a["href"][1:])
        if tag == "link" and a.get("rel") == "stylesheet":
            self.fogli_stile.append(a.get("href", ""))
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self._titolo_corrente = (int(tag[1]), "")
        # La prima meta' del ticker deve essere leggibile dagli screen reader.
        # Va controllato sia il contenitore sia la prima track: oggi
        # aria-hidden sta sul wrap, e controllare solo la track lo mancherebbe.
        classi = a.get("class", "")
        if "ticker-wrap" in classi and a.get("aria-hidden") == "true":
            self.ticker_wrap_nascosto = True
        if "ticker-track" in classi and self.ticker_prima_track_nascosta is None:
            self.ticker_prima_track_nascosta = a.get("aria-hidden") == "true"

    def handle_data(self, data):
        if self._titolo_corrente:
            liv, testo = self._titolo_corrente
            self._titolo_corrente = (liv, testo + data.strip())

    def handle_endtag(self, tag):
        if tag in ("h1", "h2", "h3", "h4", "h5", "h6") and self._titolo_corrente:
            self.titoli.append(self._titolo_corrente)
            self._titolo_corrente = None


def main():
    errori = []

    if not INDEX.exists():
        print("FAIL: index.html non trovata")
        return 1

    sorgente = INDEX.read_text(encoding="utf-8")
    p = Analisi()
    p.feed(sorgente)

    # 1. Ancore storiche: 68 link interni dipendono da queste.
    for ancora in ANCORE_STORICHE:
        if ancora not in p.ids:
            errori.append(
                f"ancora storica '#{ancora}' assente: rompe i link interni delle 38 pagine"
            )

    # 2. Ancore nuove introdotte dalla nav.
    for ancora in ANCORE_NUOVE:
        if ancora not in p.ids:
            errori.append(f"ancora '#{ancora}' assente ma referenziata dalla nav")

    # 3. Ogni href interno deve puntare a un id esistente.
    for href in p.href_interni:
        if href and href not in p.ids:
            errori.append(f"link '#{href}' non punta a nessun id della pagina")

    # 4. Un solo h1.
    h1 = [t for liv, t in p.titoli if liv == 1]
    if len(h1) != 1:
        errori.append(f"attesi 1 h1, trovati {len(h1)}")

    # 5. Gerarchia dei titoli senza salti di livello.
    precedente = 0
    for liv, testo in p.titoli:
        if precedente and liv > precedente + 1:
            errori.append(
                f"salto di livello nei titoli: h{precedente} -> h{liv} ('{testo[:40]}')"
            )
        precedente = liv

    # 6. Ogni immagine ha un alt descrittivo.
    for img in p.immagini:
        if not img.get("alt", "").strip():
            errori.append(f"img senza alt: {img.get('src', '?')}")

    # 7. Il ticker clienti deve essere leggibile dagli screen reader.
    if p.ticker_wrap_nascosto:
        errori.append(
            "il contenitore del ticker ha aria-hidden: nessun nome cliente e' leggibile dagli screen reader"
        )
    if p.ticker_prima_track_nascosta is True:
        errori.append(
            "la prima meta' del ticker ha aria-hidden: i nomi clienti sono invisibili agli screen reader"
        )

    # 8. La home carica home.css e non styles.css.
    if not any("home.css" in f for f in p.fogli_stile):
        errori.append("home.css non e' collegata")
    if any("styles.css" in f for f in p.fogli_stile):
        errori.append("index.html non deve caricare styles.css (condiviso da 38 pagine)")

    # 9. Tag SEO sopravvissuti.
    for tag in SEO_ATTESI:
        if tag not in sorgente:
            errori.append(f"tag SEO perduto: {tag}")

    if sorgente.count("application/ld+json") != 3:
        errori.append(
            f"attesi 3 blocchi JSON-LD, trovati {sorgente.count('application/ld+json')}"
        )

    # 10. Meta description entro i 155 caratteri.
    m = re.search(r'<meta name="description" content="([^"]*)"', sorgente)
    if not m:
        errori.append("meta description assente")
    elif len(m.group(1)) > 155:
        errori.append(f"meta description di {len(m.group(1))} caratteri, massimo 155")

    # 11. Titolo invariato.
    if "<title>Echo S.r.l. &mdash; Consulenza AI per le PMI | Reggio Emilia</title>" not in sorgente \
            and "<title>Echo S.r.l. — Consulenza AI per le PMI | Reggio Emilia</title>" not in sorgente:
        errori.append("il <title> e' cambiato: deve restare invariato")

    # 12. Immagini hero presenti e entro budget.
    for nome, budget_kb in IMMAGINI_HERO:
        f = ROOT / nome
        if not f.exists():
            errori.append(f"immagine hero mancante: {nome}")
        else:
            kb = f.stat().st_size // 1024
            if kb > budget_kb:
                errori.append(f"{nome} pesa {kb}KB, budget {budget_kb}KB")

    if errori:
        print(f"FAIL — {len(errori)} problemi:\n")
        for e in errori:
            print(f"  - {e}")
        return 1

    print("OK — tutti gli invarianti della homepage sono rispettati")
    return 0


if __name__ == "__main__":
    sys.exit(main())
