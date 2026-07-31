# Redesign della homepage — piano di implementazione

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Riscrivere la homepage di www.echo.srl secondo il layout approvato, senza rompere i 68 link interni entranti né il capitale SEO delle 38 pagine esistenti.

**Architecture:** Sito HTML statico, nessun build step. `index.html` viene riscritta con sezioni delimitate da commenti; gli stili vanno in un `home.css` dedicato, caricato solo dalla home. `styles.css`, condiviso da 38 pagine, viene toccato solo nelle regole dei pulsanti. Uno script Python di verifica (`scripts/check_home.py`, stdlib) presidia gli invarianti e fornisce il ciclo rosso/verde.

**Tech Stack:** HTML5, CSS3 (custom properties, grid, flexbox), Python 3.9 stdlib per la verifica, `sips` per le immagini, Vercel per il deploy.

## Global Constraints

- Il sito **non è Next.js**: nessun React, nessun npm, nessun build step per la home.
- `index.html` **non carica** `styles.css` e non deve iniziare a farlo. Carica solo `home.css`.
- `styles.css` è condiviso da **38 pagine**: modificarne solo le regole dei pulsanti `.nav-cta`, `.btn-primary`, `.btn-secondary`, `.calendly-cta`. Mai `nav`, `footer`, `:root`.
- I quattro ID storici `#metodo`, `#contatti`, `#origine`, `#casi` devono esistere nella pagina finale. Valgono 68 link interni.
- Token di colore e font già definiti, da riusare senza inventarne di nuovi: `--bg #F5F3EE`, `--text #111110`, `--accent #C8E63C`, `--accent-soft #DEE8C4`, `--muted #6B6B68`, `--border #E0DDD6`, Playfair Display, Inter.
- **Nessuna testimonianza virgolettata.** I risultati dei sei casi studio si formulano come esiti di progetto, mai come frasi attribuite a clienti.
- `<title>`, canonical, favicon, manifest, theme-color, robots, Open Graph, Twitter Card e i tre blocchi JSON-LD si conservano invariati. Cambia solo la meta description.
- Python è la 3.9.6 con la sola stdlib: niente Pillow, niente dipendenze esterne, coerente con gli script già presenti in `scripts/`.
- Testi delle sezioni: copiare **verbatim** dalla specifica `docs/superpowers/specs/2026-07-31-homepage-redesign-design.md`.
- Branch di lavoro: `homepage-redesign`. Non fare merge su `main` né deploy senza approvazione esplicita.

---

### Task 1: Script di verifica degli invarianti

Stabilisce il ciclo rosso/verde. Il repo non ha framework di test: questo script è il test.

**Files:**
- Create: `scripts/check_home.py`

**Interfaces:**
- Consumes: niente
- Produces: `python3 scripts/check_home.py` → exit 0 se tutti gli invarianti passano, exit 1 con elenco dei fallimenti. Usato come gate in tutti i task successivi.

- [ ] **Step 1: Scrivere lo script di verifica**

```python
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
```

- [ ] **Step 2: Eseguirlo per verificare che fallisca sulla home attuale**

Run: `cd /Users/silviarinaldi/Desktop/echowebagency-site && python3 scripts/check_home.py`

Expected: FAIL. La home attuale non ha `#servizi`, non carica `home.css`, il ticker ha `aria-hidden`, e le immagini hero non esistono ancora. Almeno cinque problemi elencati.

Se invece passa, lo script non sta controllando nulla: rileggerlo prima di proseguire.

- [ ] **Step 3: Commit**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
git add scripts/check_home.py
git commit -m "Aggiunge lo script di verifica degli invarianti della home

Il repo non ha framework di test. Questo script presidia cio' che il
redesign rischia di rompere senza produrre errori visibili: le ancore
entranti dalle 38 pagine, la gerarchia dei titoli, gli alt, i tag SEO
e il peso delle immagini hero.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2: Asset della foto hero

**Files:**
- Create: `hero-formazione.jpg` (1200×945, ~197KB)
- Create: `hero-formazione@2x.jpg` (1800×1418, ~298KB)

**Interfaces:**
- Consumes: niente
- Produces: due file JPEG nella root del repo, referenziati dall'hero nel Task 4 via `srcset`.

Sorgente: `/Users/silviarinaldi/Desktop/03_Marketing_LinkedIn/HUMAN FIRST FORMAZIONE AI CHE PARTE DALLE PERSONE.jpg` (5712×4284).

Il ritaglio elimina la cornice bianca e la didascalia "HUMAN FIRST / FORMAZIONE AI CHE PARTE DALLE PERSONE" impressa nei pixel. La cornice è bianco puro e stonerebbe contro il crema `#F5F3EE`; il testo nei pixel non è leggibile dagli screen reader né indicizzabile.

Le coordinate sono state ricavate campionando i pixel del sorgente, non a occhio: la cornice non bianca sta in `x 526..5089`, la foto finisce a `y≈3816` e sotto ci sono una banda bianca e le due righe di didascalia. Il ritaglio prescritto sotto applica un margine di sicurezza di qualche pixel su ogni lato.

**Non verificare questo ritaglio guardandolo.** Una striscia bianca di 26px sul bordo destro è già sfuggita una volta a un'ispezione a occhio: contro lo sfondo chiaro di un visualizzatore di immagini è invisibile. Lo Step 3 la controlla campionando i pixel.

`sips` non sa scrivere WebP su questa macchina (lo legge soltanto), quindi si resta su JPEG.

- [ ] **Step 1: Ritagliare la fotografia**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
SRC="/Users/silviarinaldi/Desktop/03_Marketing_LinkedIn/HUMAN FIRST FORMAZIONE AI CHE PARTE DALLE PERSONE.jpg"
sips -c 3588 4553 --cropOffset 222 530 "$SRC" --out /tmp/hero-crop.jpg
sips -g pixelWidth -g pixelHeight /tmp/hero-crop.jpg | tail -2
```

Expected: `pixelWidth: 4553`, `pixelHeight: 3588`.

- [ ] **Step 2: Generare le due versioni per il web**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
sips -Z 1200 -s format jpeg -s formatOptions 65 /tmp/hero-crop.jpg --out hero-formazione.jpg
sips -Z 1800 -s format jpeg -s formatOptions 55 /tmp/hero-crop.jpg --out "hero-formazione@2x.jpg"
ls -lh hero-formazione.jpg "hero-formazione@2x.jpg"
```

Expected: `hero-formazione.jpg` circa 197KB a 1200×945, `hero-formazione@2x.jpg` circa 298KB a 1800×1418. Entrambi sotto i budget dello script di verifica (260KB e 340KB).

Annotare le altezze reali riportate da `sips`: servono al Task 4, che le scrive come attributo `height` dell'`<img>`. Se non corrispondono, il browser calcola un rapporto d'aspetto sbagliato.

- [ ] **Step 3: Verificare al pixel che non resti cornice**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
sips -s format bmp hero-formazione.jpg --out /tmp/hero-check.bmp >/dev/null
python3 - <<'PY'
import struct, pathlib
d = pathlib.Path("/tmp/hero-check.bmp").read_bytes()
off = struct.unpack_from("<I", d, 10)[0]
w, h = struct.unpack_from("<ii", d, 18)
bpp = struct.unpack_from("<H", d, 28)[0]
topdown = h < 0
h = abs(h)
row = (w * bpp // 8 + 3) // 4 * 4

def px(x, y):
    yy = y if topdown else h - 1 - y
    i = off + yy * row + x * (bpp // 8)
    return d[i + 2], d[i + 1], d[i]

def bianco(c):
    return c[0] > 246 and c[1] > 246 and c[2] > 246

print(f"{w}x{h}")
peggio = 0
for lato, punti in [
    ("destro",   [(w - 1 - k, y) for y in range(20, h - 20, 60) for k in range(40)]),
    ("sinistro", [(k, y)         for y in range(20, h - 20, 60) for k in range(40)]),
    ("alto",     [(x, k)         for x in range(20, w - 20, 60) for k in range(40)]),
    ("basso",    [(x, h - 1 - k) for x in range(20, w - 20, 60) for k in range(40)]),
]:
    cnt = sum(1 for p in punti if bianco(px(*p)))
    print(f"  bordo {lato}: {cnt} pixel bianchi su {len(punti)}")
    peggio = max(peggio, cnt)
print("ESITO:", "PULITO" if peggio == 0 else "RESIDUO DI CORNICE")
PY
```

Expected: `1200x945`, zero pixel bianchi su tutti e quattro i bordi, `ESITO: PULITO`.

Se un bordo riporta pixel bianchi, la cornice non è stata eliminata del tutto: stringere di 30px l'offset o la dimensione sul lato interessato e ripetere dallo Step 1. Non accettare il risultato perché "a occhio sembra a posto" — la striscia bianca è invisibile in un visualizzatore di immagini con sfondo chiaro.

- [ ] **Step 4: Commit**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
git add hero-formazione.jpg "hero-formazione@2x.jpg"
git commit -m "Aggiunge la foto hero della sessione di formazione

Ritagliata dall'originale LinkedIn per togliere cornice bianca e
didascalia impressa nei pixel: la cornice stonava contro il crema del
sito e il testo nei pixel non era indicizzabile ne' accessibile.
Due tagli per srcset, 204KB e 288KB.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3: `home.css` — fondamenta, nav, pulsanti

**Files:**
- Create: `home.css`

**Interfaces:**
- Consumes: niente
- Produces: le classi `.btn`, `.btn-lime`, `.site-nav`, `.nav-links`, `.nav-cta`, `.section`, `.section-label`, `.section-title`, `.section-body`, usate da tutti i task successivi. I token `:root` sono ricopiati qui perché `index.html` non carica `styles.css`.

- [ ] **Step 1: Creare `home.css` con fondamenta, nav e pulsanti**

```css
/* ============================================================
   home.css — stili della sola homepage.
   index.html non carica styles.css (condiviso da 38 pagine):
   questo file e' autosufficiente, token compresi.
   ============================================================ */

*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg: #F5F3EE;
  --text: #111110;
  --accent: #C8E63C;
  --accent-soft: #DEE8C4;
  --muted: #6B6B68;
  --border: #E0DDD6;
  --font-serif: 'Playfair Display', Georgia, serif;
  --font-sans: 'Inter', system-ui, sans-serif;
  --nav-h: 76px;
}

html { scroll-behavior: smooth; }
body {
  background: var(--bg);
  color: var(--text);
  font-family: var(--font-sans);
  line-height: 1.6;
  overflow-x: hidden;
}

/* La nav e' fissa: senza questo gli anchor target finiscono sotto la barra.
   Difetto presente anche nella home attuale. */
[id] { scroll-margin-top: calc(var(--nav-h) + 1rem); }

img { max-width: 100%; height: auto; }

/* ===== PULSANTI ===== */
/* Rettangolari, spigoli vivi, maiuscolo. Sostituiscono le pillole nere. */
.btn {
  display: inline-block;
  padding: 0.95rem 2.1rem;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  text-decoration: none;
  border: 1.5px solid transparent;
  border-radius: 0;
  transition: background .2s, color .2s, border-color .2s;
}
.btn-lime { background: var(--accent); color: var(--text); }
.btn-lime:hover { background: var(--text); color: var(--accent); }

/* ===== NAV ===== */
.site-nav {
  position: fixed;
  top: 0; left: 0; right: 0;
  z-index: 100;
  min-height: var(--nav-h);
  padding: 1.25rem 3rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1.5rem;
  background: rgba(245, 243, 238, 0.95);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--border);
}
.nav-logo img { height: 32px; display: block; }
.nav-links { display: flex; gap: 2rem; list-style: none; }
.nav-links a {
  text-decoration: none;
  color: var(--text);
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  transition: opacity .2s;
}
.nav-links a:hover { opacity: 0.6; }
.nav-cta { padding: 0.7rem 1.5rem; font-size: 0.72rem; }

/* ===== IMPALCATURA DELLE SEZIONI ===== */
.section { padding: 7rem 3rem; border-bottom: 1px solid var(--border); }
.section-sage { background: var(--accent-soft); }
.section-dark { background: var(--text); color: var(--bg); }

.section-label {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 2.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}
.section-label::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
  max-width: 60px;
}
.section-dark .section-label { color: rgba(245, 243, 238, 0.5); }
.section-dark .section-label::after { background: rgba(245, 243, 238, 0.2); }

.section-title {
  font-family: var(--font-serif);
  font-size: clamp(2rem, 4vw, 3.4rem);
  font-weight: 500;
  line-height: 1.15;
  margin-bottom: 1.5rem;
  max-width: 800px;
}
.section-title em { font-style: italic; color: var(--muted); }
.section-dark .section-title { color: var(--bg); }
.section-dark .section-title em { color: var(--accent); }

.section-body {
  font-size: 1.0625rem;
  color: var(--muted);
  max-width: 640px;
  line-height: 1.8;
}
.section-dark .section-body { color: rgba(245, 243, 238, 0.7); }

/* ===== RESPONSIVE — impalcatura ===== */
@media (max-width: 900px) {
  .site-nav { padding: 1rem 1.5rem; }
  .nav-links { display: none; }
  .section { padding: 4rem 1.5rem; }
}
```

- [ ] **Step 2: Verificare che il CSS sia sintatticamente valido**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
python3 -c "
s = open('home.css').read()
assert s.count('{') == s.count('}'), f'graffe sbilanciate: {s.count(\"{\")} aperte, {s.count(\"}\")} chiuse'
print('graffe bilanciate:', s.count('{'), 'blocchi')
"
```

Expected: nessun errore, stampa il numero di blocchi.

- [ ] **Step 3: Commit**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
git add home.css
git commit -m "Aggiunge home.css con fondamenta, nav e pulsanti

Foglio autosufficiente per la sola home: index.html non carica
styles.css, quindi i token sono ricopiati qui. Introduce i pulsanti
rettangolari lime e lo scroll-margin-top che oggi manca, per cui le
ancore finiscono sotto la nav fissa.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 4: `index.html` — nav e hero

Da qui `index.html` viene riscritta. Il `<head>` si conserva quasi per intero: cambia solo la meta description e si aggiunge il link a `home.css`, togliendo il blocco `<style>` inline.

**Files:**
- Modify: `index.html` (head, nav, hero)
- Modify: `home.css` (stili hero)

**Interfaces:**
- Consumes: `.btn`, `.btn-lime`, `.site-nav`, `.nav-links`, `.nav-cta` dal Task 3; `hero-formazione.jpg` e `hero-formazione@2x.jpg` dal Task 2
- Produces: `.hero`, `.hero-eyebrow`, `.hero-title`, `.hero-media`

- [ ] **Step 1: Sostituire il blocco `<style>` inline con il link a `home.css`**

In `index.html`, cancellare tutto il blocco da `<style>` (riga 11) fino a `</style>` compreso (riga 146), e metterci:

```html
<link rel="stylesheet" href="/home.css">
```

- [ ] **Step 2: Aggiornare la meta description**

Sostituire la riga 7:

```html
<meta name="description" content="Consulenza AI per PMI manifatturiere: ottimizzazione dei processi, formazione dei team e governance. Radici manifatturiere, visione digitale. Reggio Emilia.">
```

Sono 154 caratteri, sotto il limite di 155 che lo script verifica. Non toccare il `<title>` sopra.

- [ ] **Step 3: Sostituire la nav**

Sostituire l'intero blocco `<nav>...</nav>`:

```html
<!-- ===== NAV ===== -->
<nav class="site-nav">
  <a href="/" class="nav-logo" aria-label="Echo S.r.l., torna alla home">
    <img src="/logo-on-cream.png" alt="Echo S.r.l.">
  </a>
  <ul class="nav-links">
    <li><a href="#metodo">Metodo</a></li>
    <li><a href="#servizi">Servizi</a></li>
    <li><a href="#casi">Risultati</a></li>
    <li><a href="/blog/">Blog</a></li>
    <li><a href="#contatti">Contatti</a></li>
  </ul>
  <a href="https://calendly.com/echowebagency-info/formazione" target="_blank" rel="noopener" class="btn btn-lime nav-cta">Prenota audit</a>
</nav>
```

`RISULTATI` punta a `#casi`, non a un id nuovo: quell'ancora raccoglie 8 link interni esistenti.

- [ ] **Step 4: Sostituire l'hero**

Sostituire l'intero blocco `<section class="hero">...</section>`:

```html
<!-- ===== HERO ===== -->
<header class="hero">
  <div class="hero-text">
    <p class="hero-eyebrow">Consulenza AI per le PMI manifatturiere</p>
    <h1 class="hero-title">Radici manifatturiere,<br><em>visione digitale.</em></h1>
    <p class="hero-subtitle">Portiamo l'intelligenza artificiale dove il lavoro accade realmente. Ottimizzazione dei processi, formazione dei team e governance strategica per le PMI italiane.</p>
    <a href="https://calendly.com/echowebagency-info/formazione" target="_blank" rel="noopener" class="btn btn-lime">Prenota un appuntamento</a>
  </div>
  <figure class="hero-media">
    <img src="/hero-formazione.jpg"
         srcset="/hero-formazione.jpg 1200w, /hero-formazione@2x.jpg 1800w"
         sizes="(max-width: 900px) 100vw, 48vw"
         width="1200" height="945"
         loading="eager" fetchpriority="high"
         alt="Sessione di formazione AI di Echo con un team aziendale attorno al tavolo riunioni">
    <figcaption class="hero-caption">Human first</figcaption>
  </figure>
</header>
```

`width` e `height` espliciti evitano il layout shift sull'elemento LCP. La didascalia "Human first" è testo HTML, non pixel.

- [ ] **Step 5: Aggiungere gli stili dell'hero in coda a `home.css`, prima del blocco `@media`**

```css
/* ===== HERO ===== */
.hero {
  min-height: 100vh;
  padding: calc(var(--nav-h) + 5rem) 3rem 5rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
  border-bottom: 1px solid var(--border);
}
.hero-eyebrow {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 1.75rem;
}
.hero-title {
  font-family: var(--font-serif);
  font-size: clamp(2.6rem, 5.5vw, 5rem);
  font-weight: 500;
  line-height: 1.08;
  margin-bottom: 2rem;
}
.hero-title em { font-style: italic; color: var(--muted); }
.hero-subtitle {
  font-size: 1.0625rem;
  color: var(--muted);
  max-width: 520px;
  line-height: 1.75;
  margin-bottom: 2.5rem;
}
.hero-media { position: relative; }
.hero-media img { display: block; width: 100%; }
.hero-caption {
  position: absolute;
  left: 0;
  bottom: 0;
  background: var(--accent);
  color: var(--text);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  padding: 0.7rem 1.4rem;
}
```

E dentro il blocco `@media (max-width: 900px)` esistente aggiungere:

```css
  .hero {
    grid-template-columns: 1fr;
    gap: 2.5rem;
    padding: calc(var(--nav-h) + 3rem) 1.5rem 3rem;
    min-height: auto;
  }
```

- [ ] **Step 6: Eseguire lo script di verifica**

Run: `cd /Users/silviarinaldi/Desktop/echowebagency-site && python3 scripts/check_home.py`

Expected: FAIL, ma con meno problemi di prima. Devono essere spariti "home.css non e' collegata", "immagine hero mancante" e "meta description". Devono restare i fallimenti sulle ancore `#servizi`, `#casi`, `#contatti` e sul ticker, perché quelle sezioni non sono ancora state riscritte.

- [ ] **Step 7: Commit**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
git add index.html home.css
git commit -m "Riscrive nav e hero della home

Nav a cinque voci con Blog, che il brief eliminava: la home e' la
sorgente di link interni piu' forte verso i 25 articoli. RISULTATI
punta all'ancora storica #casi invece che a un id nuovo, per non
perdere 8 link entranti. La didascalia Human first torna testo HTML.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 5: Ticker clienti, sezione approccio, metodo

**Files:**
- Modify: `index.html`
- Modify: `home.css`

**Interfaces:**
- Consumes: `.section`, `.section-sage`, `.section-label`, `.section-title`, `.section-body` dal Task 3
- Produces: `#origine` e `#metodo`, le due ancore più linkate (22 e 38 link entranti)

- [ ] **Step 1: Sostituire il ticker**

Sostituire l'intero blocco `<div class="ticker-wrap">...</div>`. Quattro nomi nuovi, e `aria-hidden` solo sulla seconda metà:

```html
<!-- ===== TICKER CLIENTI ===== -->
<section class="ticker-wrap" aria-label="Aziende con cui lavoriamo">
  <div class="ticker-track">
    <span class="ticker-item">AERAE BEAUTY</span>
    <span class="ticker-item">ALPHA STUDIO</span>
    <span class="ticker-item">YUGG</span>
    <span class="ticker-item">FLORA AI</span>
    <span class="ticker-item">RE-FABRIC AI</span>
    <span class="ticker-item">FLYRT</span>
    <span class="ticker-item">TEDX ITALIA</span>
    <span class="ticker-item">AMMIA</span>
    <span class="ticker-item">ALFIERI SHOWROOM</span>
    <span class="ticker-item">DAVID &amp; SONS</span>
    <span class="ticker-item">MAGLIERIE SACCHETTI</span>
    <span class="ticker-item">BEST MODE</span>
    <span class="ticker-item">SIMONCINI</span>
    <span class="ticker-item">D.A.T.E. SNEAKERS</span>
    <span class="ticker-item">STEFANO RICCI</span>
    <span class="ticker-item">AGV MAROSTICA</span>
    <span class="ticker-item">CLUST-ER CREATE</span>
    <span class="ticker-item">GOLDEN GROUP</span>
  </div>
  <!-- Copia per il loop continuo: nascosta agli screen reader per non ripetere i nomi. -->
  <div class="ticker-track" aria-hidden="true">
    <span class="ticker-item">AERAE BEAUTY</span>
    <span class="ticker-item">ALPHA STUDIO</span>
    <span class="ticker-item">YUGG</span>
    <span class="ticker-item">FLORA AI</span>
    <span class="ticker-item">RE-FABRIC AI</span>
    <span class="ticker-item">FLYRT</span>
    <span class="ticker-item">TEDX ITALIA</span>
    <span class="ticker-item">AMMIA</span>
    <span class="ticker-item">ALFIERI SHOWROOM</span>
    <span class="ticker-item">DAVID &amp; SONS</span>
    <span class="ticker-item">MAGLIERIE SACCHETTI</span>
    <span class="ticker-item">BEST MODE</span>
    <span class="ticker-item">SIMONCINI</span>
    <span class="ticker-item">D.A.T.E. SNEAKERS</span>
    <span class="ticker-item">STEFANO RICCI</span>
    <span class="ticker-item">AGV MAROSTICA</span>
    <span class="ticker-item">CLUST-ER CREATE</span>
    <span class="ticker-item">GOLDEN GROUP</span>
  </div>
</section>
```

- [ ] **Step 2: Sostituire la sezione Origine con la sezione approccio**

Sostituire l'intero blocco `<section id="origine">...</section>`. Eredita l'id, che vale 22 link entranti:

```html
<!-- ===== UN APPROCCIO ORIENTATO AI PROCESSI ===== -->
<section class="section section-sage" id="origine">
  <p class="section-label">01 — L'approccio</p>
  <h2 class="section-title">Un approccio<br><em>orientato ai processi.</em></h2>
  <p class="section-body">Echo S.r.l. nasce a Reggio Emilia, nel cuore del distretto manifatturiero italiano, e si posiziona come consulenza B2B specializzata che colma il divario tra la manifattura tradizionale e la tecnologia digitale avanzata. Nessuna installazione software generica: solo risultati misurabili e conformità normativa.</p>
  <div class="pilastri">
    <article class="pilastro">
      <h3 class="pilastro-badge">Pragmatismo</h3>
      <p>Analizziamo flussi reali per implementare soluzioni dove generano un impatto immediato e concreto sui costi e sui tempi.</p>
    </article>
    <article class="pilastro">
      <h3 class="pilastro-badge">Manufacturing Heritage</h3>
      <p>Comprendiamo a fondo le logiche di produzione. La tecnologia deve adattarsi al processo, non viceversa.</p>
    </article>
    <article class="pilastro">
      <h3 class="pilastro-badge">Strategic Governance</h3>
      <p>Garantiamo che l'adozione dell'AI avvenga in modo strutturato, sicuro e conforme alle normative vigenti.</p>
    </article>
    <article class="pilastro">
      <h3 class="pilastro-badge">Integrazione Human-centric</h3>
      <p>Formiamo i team per rendere la tecnologia un'estensione delle capacità umane, non una sostituzione.</p>
    </article>
  </div>
</section>
```

- [ ] **Step 3: Cancellare la sezione Paradosso e adattare il Metodo**

Cancellare per intero il blocco `<section class="paradosso" id="paradosso">...</section>`.

Nel blocco `<section id="metodo">`, cambiare il tag di apertura in `<section class="section" id="metodo">` e l'etichetta da `03 — Il Metodo` a `02 — Il Metodo`.

**Correggere anche la gerarchia dei titoli.** I quattro step usano `<h4>` sotto un `<h2>`: salta il livello `h3` e lo script di verifica lo segnala. Sostituire i quattro `<h4>` con `<h3>` e i rispettivi `</h4>` con `</h3>`, lasciando il testo invariato:

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
python3 - <<'PY'
from pathlib import Path
p = Path("index.html")
s = p.read_text(encoding="utf-8")
inizio = s.index('<div class="metodo-steps">')
fine = s.index('</section>', inizio)
blocco = s[inizio:fine].replace("<h4>", "<h3>").replace("</h4>", "</h3>")
p.write_text(s[:inizio] + blocco + s[fine:], encoding="utf-8")
print("h4 sostituiti nel blocco metodo:", blocco.count("<h3>"))
PY
```

Expected: `h4 sostituiti nel blocco metodo: 4`

Il CSS al passo successivo usa già `.step-content h3`, coerente con questa correzione.

- [ ] **Step 4: Aggiungere gli stili in coda a `home.css`, prima del blocco `@media`**

```css
/* ===== TICKER ===== */
.ticker-wrap {
  overflow: hidden;
  display: flex;
  gap: 3rem;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  padding: 1rem 0;
}
.ticker-track {
  display: flex;
  gap: 3rem;
  padding-right: 3rem;
  flex-shrink: 0;
  animation: ticker 40s linear infinite;
}
.ticker-wrap:hover .ticker-track { animation-play-state: paused; }
.ticker-item {
  font-size: 0.75rem;
  font-weight: 600;
  letter-spacing: 0.2em;
  text-transform: uppercase;
  color: var(--muted);
  white-space: nowrap;
}
@keyframes ticker { from { transform: translateX(0); } to { transform: translateX(-100%); } }
@media (prefers-reduced-motion: reduce) {
  .ticker-track { animation: none; }
}

/* ===== PILASTRI ===== */
.pilastri {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  margin-top: 3.5rem;
}
.pilastro-badge {
  display: inline-block;
  background: var(--text);
  color: var(--accent);
  font-family: var(--font-sans);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  padding: 0.5rem 1rem;
  margin-bottom: 1rem;
}
.pilastro p { font-size: 0.9375rem; color: var(--text); line-height: 1.7; opacity: 0.75; }

/* ===== METODO ===== */
.metodo-steps { margin-top: 3rem; }
.metodo-step {
  display: grid;
  grid-template-columns: 80px 1fr;
  gap: 2rem;
  padding: 2rem 0;
  border-bottom: 1px solid var(--border);
  align-items: start;
}
.step-num { font-family: var(--font-serif); font-size: 2.5rem; color: var(--accent-soft); font-weight: 500; line-height: 1; }
.step-content h3 { font-family: var(--font-serif); font-size: 1.3rem; font-weight: 500; margin-bottom: 0.5rem; }
.step-content p { font-size: 0.9375rem; color: var(--muted); line-height: 1.7; }
.step-tag {
  display: inline-block;
  background: var(--accent-soft);
  color: var(--text);
  font-size: 0.68rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  padding: 0.25rem 0.75rem;
  margin-bottom: 0.6rem;
}
```

E dentro `@media (max-width: 900px)`:

```css
  .pilastri { grid-template-columns: 1fr; }
  .metodo-step { grid-template-columns: 48px 1fr; gap: 1rem; }
```

- [ ] **Step 5: Eseguire lo script di verifica**

Run: `cd /Users/silviarinaldi/Desktop/echowebagency-site && python3 scripts/check_home.py`

Expected: FAIL, ma devono essere spariti l'errore sul ticker (`aria-hidden`) e quelli su `#origine` e `#metodo`. Restano `#servizi`, `#casi`, `#contatti`.

- [ ] **Step 6: Commit**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
git add index.html home.css
git commit -m "Riscrive ticker, sezione approccio e metodo

Il ticker passa a 18 nomi e diventa leggibile dagli screen reader:
prima aveva aria-hidden sull'intera fascia, quindi nessun nome cliente
era accessibile. La sezione approccio eredita l'id #origine per non
perdere 22 link entranti. Paradosso rimosso su decisione dell'autrice.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 6: Competenze operative, Numeri, Impatto misurabile

**Files:**
- Modify: `index.html`
- Modify: `home.css`

**Interfaces:**
- Consumes: `.section`, `.section-sage`, `.section-dark` dal Task 3
- Produces: `#servizi` e `#casi`

- [ ] **Step 1: Inserire la sezione Competenze operative subito dopo il Metodo**

```html
<!-- ===== COMPETENZE OPERATIVE ===== -->
<section class="section" id="servizi">
  <p class="section-label">03 — Competenze operative</p>
  <h2 class="section-title">Dalla diagnosi<br><em>all'implementazione.</em></h2>
  <p class="section-body">Soluzioni per i settori Moda, Beauty e Manifattura.</p>
  <div class="servizi-grid">
    <a class="servizio" href="/ai-readiness-audit">
      <h3>AI Readiness Audit</h3>
      <p>Diagnosi strutturata dei processi per identificare in due settimane dove l'AI genera valore reale.</p>
    </a>
    <a class="servizio" href="/governance-ai">
      <h3>Governance AI</h3>
      <p>Definizione di policy interne, classificazione del rischio e framework operativi per un uso strutturato e conforme.</p>
    </a>
    <a class="servizio" href="/formazione-ai">
      <h3>Formazione AI</h3>
      <p>Percorsi pratici e affiancamento operativo per l'uso quotidiano di strumenti e processi basati sull'AI.</p>
    </a>
    <a class="servizio" href="/integrazione-ai">
      <h3>Integrazione AI</h3>
      <p>Implementazione di automazioni e workflow intelligenti nei sistemi già in uso.</p>
    </a>
    <a class="servizio" href="/digital-product-passport">
      <h3>Digital Product Passport</h3>
      <p>Preparazione operativa al regolamento ESPR tramite raccolta, strutturazione e integrazione dei dati di filiera.</p>
    </a>
    <div class="servizio">
      <h3>Consulenza AI</h3>
      <p>Supporto strategico per l'implementazione di strumenti AI nei flussi aziendali reali.</p>
    </div>
    <div class="servizio">
      <h3>Automazione</h3>
      <p>Creazione di workflow intelligenti per eliminare il lavoro ripetitivo.</p>
    </div>
    <div class="servizio">
      <h3>Strategia digitale</h3>
      <p>Roadmap su misura per l'innovazione digitale, senza soluzioni preconfezionate.</p>
    </div>
  </div>
</section>
```

Cinque card sono `<a>` verso pagine esistenti, tre sono `<div>` perché quelle pagine non esistono: non inventare URL.

- [ ] **Step 2: Adattare la sezione Numeri**

Nel blocco `<section class="numeri" id="numeri">`, cambiare solo il tag di apertura in `<section class="section section-sage" id="numeri">`. L'etichetta resta `04 — I Numeri` e i quattro valori restano invariati.

- [ ] **Step 3: Sostituire i Casi studio con L'impatto misurabile**

Sostituire l'intero blocco `<section id="casi">...</section>`. Mantiene l'id e tutti e sei i risultati:

```html
<!-- ===== L'IMPATTO MISURABILE ===== -->
<section class="section section-dark" id="casi">
  <p class="section-label">05 — L'impatto misurabile</p>
  <h2 class="section-title">Risultati reali,<br><em>contesti reali.</em></h2>
  <div class="impatto-grid">
    <article class="impatto-card">
      <p class="impatto-val">&#8595; 60%</p>
      <p class="impatto-desc">Tempi di verifica del controllo qualità in produzione, grazie a un sistema di analisi AI per il controllo visivo dei prodotti.</p>
      <p class="impatto-meta">Settore manifatturiero — Reggio Emilia</p>
    </article>
    <article class="impatto-card">
      <p class="impatto-val">&#8593; 3x</p>
      <p class="impatto-desc">Velocità di produzione dei briefing stagionali per l'ufficio stile, con maggiore coerenza narrativa.</p>
      <p class="impatto-meta">Settore moda — Bologna</p>
    </article>
    <article class="impatto-card">
      <p class="impatto-val">&#8593; 34%</p>
      <p class="impatto-desc">Conversioni email nel primo trimestre, dopo l'introduzione della segmentazione AI e dei contenuti personalizzati.</p>
      <p class="impatto-meta">Settore retail — Modena</p>
    </article>
    <article class="impatto-card">
      <p class="impatto-val">&#8595; 40%</p>
      <p class="impatto-desc">Errori di previsione degli ordini in sei mesi, con un modello predittivo per la gestione di ordini e scorte.</p>
      <p class="impatto-meta">Settore logistica — Parma</p>
    </article>
    <article class="impatto-card">
      <p class="impatto-val">87%</p>
      <p class="impatto-desc">Adozione attiva su 120 dipendenti, dopo un programma di formazione in tre fasi con affiancamento operativo.</p>
      <p class="impatto-meta">Formazione — Reggio Emilia</p>
    </article>
    <article class="impatto-card">
      <p class="impatto-val">&#8595; 70%</p>
      <p class="impatto-desc">Tempo dedicato alla produzione di report, con dashboard AI e sintesi automatica dei dati chiave.</p>
      <p class="impatto-meta">Servizi professionali — Milano</p>
    </article>
  </div>
</section>
```

Nessun virgolettato: sono esiti di progetto, non frasi attribuite a clienti.

- [ ] **Step 4: Aggiungere gli stili in coda a `home.css`, prima del blocco `@media`**

```css
/* ===== COMPETENZE OPERATIVE ===== */
.servizi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0;
  margin-top: 3.5rem;
  border-top: 1px solid var(--border);
  border-left: 1px solid var(--border);
}
.servizio {
  padding: 2rem 1.75rem;
  border-right: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  text-decoration: none;
  color: inherit;
  display: block;
  transition: background .2s;
}
a.servizio:hover { background: var(--accent-soft); }
.servizio h3 {
  font-family: var(--font-serif);
  font-size: 1.15rem;
  font-weight: 500;
  margin-bottom: 0.75rem;
  line-height: 1.3;
}
.servizio p { font-size: 0.875rem; color: var(--muted); line-height: 1.7; }

/* ===== NUMERI ===== */
.numeri-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2rem; margin-top: 3.5rem; }
.numero-card { padding: 2rem 0; border-top: 2px solid var(--text); }
.numero-val { font-family: var(--font-serif); font-size: 3.5rem; font-weight: 600; line-height: 1; margin-bottom: 0.5rem; }
.numero-label { font-size: 0.875rem; color: var(--muted); line-height: 1.5; }

/* ===== IMPATTO MISURABILE ===== */
.impatto-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 2rem; margin-top: 3.5rem; }
.impatto-card { border-left: 3px solid var(--accent); padding: 0.25rem 0 0.25rem 1.75rem; }
.impatto-val {
  font-family: var(--font-serif);
  font-size: 2.6rem;
  font-weight: 600;
  line-height: 1;
  color: var(--accent);
  margin-bottom: 0.9rem;
}
.impatto-desc { font-size: 1rem; color: rgba(245, 243, 238, 0.8); line-height: 1.7; margin-bottom: 0.9rem; }
.impatto-meta {
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: rgba(245, 243, 238, 0.45);
}
```

E dentro `@media (max-width: 900px)`:

```css
  .servizi-grid { grid-template-columns: 1fr; }
  .numeri-grid { grid-template-columns: repeat(2, 1fr); }
  .impatto-grid { grid-template-columns: 1fr; gap: 2.5rem; }
```

Aggiungere anche un breakpoint intermedio, in fondo al file:

```css
@media (min-width: 901px) and (max-width: 1200px) {
  .servizi-grid { grid-template-columns: repeat(2, 1fr); }
}
```

- [ ] **Step 5: Eseguire lo script di verifica**

Run: `cd /Users/silviarinaldi/Desktop/echowebagency-site && python3 scripts/check_home.py`

Expected: FAIL solo su `#contatti`, l'ultima ancora mancante.

- [ ] **Step 6: Commit**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
git add index.html home.css
git commit -m "Aggiunge competenze operative e riscrive i risultati

Cinque delle otto card linkano le pagine servizi esistenti, per
rinforzare l'internal linking. I sei risultati restano sei e restano
esiti di progetto: il brief li riformulava come virgolettati di
clienti, ma nessuno ha pronunciato quelle frasi.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 7: CTA finale e footer

**Files:**
- Modify: `index.html`
- Modify: `home.css`

**Interfaces:**
- Consumes: `.section`, `.btn`, `.btn-lime` dal Task 3
- Produces: `#contatti`, ultima ancora storica

- [ ] **Step 1: Sostituire la sezione Contatti con la CTA finale**

Sostituire l'intero blocco `<section class="contatti" id="contatti">...</section>`:

```html
<!-- ===== CTA FINALE ===== -->
<section class="section cta-finale" id="contatti">
  <h2 class="section-title">Pronto per<br><em>l'integrazione?</em></h2>
  <p class="section-body">Scopri come possiamo ottimizzare i tuoi processi aziendali con soluzioni AI basate sull'evidenza scientifica e l'efficienza operativa.</p>
  <a href="https://calendly.com/echowebagency-info/formazione" target="_blank" rel="noopener" class="btn btn-lime cta-finale-btn">Prenota un appuntamento</a>
</section>
```

- [ ] **Step 2: Sostituire il footer**

Sostituire l'intero blocco `<footer>...</footer>`. Usa una classe propria: il footer piatto delle altre 38 pagine non deve essere toccato.

```html
<!-- ===== FOOTER ===== -->
<footer class="site-footer">
  <div class="footer-cols">
    <div class="footer-col">
      <a href="/" class="footer-logo" aria-label="Echo S.r.l., torna alla home">
        <img src="/logo-on-cream.png" alt="Echo S.r.l.">
      </a>
    </div>
    <div class="footer-col">
      <h2 class="footer-head">Sede &amp; contatti</h2>
      <address class="footer-addr">
        Via Lelio e Fausto Socini 32/B<br>
        42122 Reggio Emilia (RE), IT<br>
        <a href="mailto:info@echowebagency.it">info@echowebagency.it</a><br>
        <a href="tel:+393517027294">+39 351 702 7294</a>
      </address>
    </div>
    <div class="footer-col">
      <h2 class="footer-head">Orari operativi</h2>
      <p class="footer-orari">Lunedì – Venerdì<br>9:00 – 18:00</p>
      <p class="footer-orari footer-chiuso">Sabato e Domenica chiuso</p>
    </div>
    <div class="footer-col">
      <h2 class="footer-head">Seguici</h2>
      <ul class="footer-social">
        <li><a href="https://www.linkedin.com/company/echo-srl-re" target="_blank" rel="noopener">LinkedIn</a></li>
        <li><a href="https://www.instagram.com/echowebagency/" target="_blank" rel="noopener">Instagram</a></li>
      </ul>
    </div>
  </div>
  <p class="footer-copy">&copy; Echo S.r.l. Tutti i diritti riservati. &mdash; P.IVA 03135740359</p>
</footer>
```

Gli orari sono 9:00–18:00, allineati al JSON-LD già pubblicato in questa stessa pagina. Non introdurre 17:00 senza cambiare anche lo schema.

- [ ] **Step 3: Aggiungere gli stili in coda a `home.css`, prima dei blocchi `@media`**

```css
/* ===== CTA FINALE ===== */
.cta-finale { text-align: center; }
.cta-finale .section-title { margin-left: auto; margin-right: auto; }
.cta-finale .section-body { margin: 0 auto 2.5rem; }

/* ===== FOOTER ===== */
.site-footer { padding: 4.5rem 3rem 2.5rem; }
.footer-cols {
  display: grid;
  grid-template-columns: 1.2fr 1.4fr 1fr 1fr;
  gap: 2.5rem;
  padding-bottom: 3rem;
  border-bottom: 1px solid var(--border);
}
.footer-logo img { height: 34px; display: block; }
.footer-head {
  font-family: var(--font-sans);
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: var(--muted);
  margin-bottom: 1.1rem;
}
.footer-addr, .footer-orari { font-style: normal; font-size: 0.9375rem; line-height: 1.9; }
.footer-addr a { color: var(--text); text-decoration: none; }
.footer-addr a:hover { text-decoration: underline; }
.footer-chiuso { color: var(--muted); margin-top: 0.6rem; }
.footer-social { list-style: none; }
.footer-social a { font-size: 0.9375rem; line-height: 1.9; color: var(--text); text-decoration: none; }
.footer-social a:hover { text-decoration: underline; }
.footer-copy { padding-top: 1.75rem; font-size: 0.8rem; color: var(--muted); }
```

E dentro `@media (max-width: 900px)`:

```css
  .site-footer { padding: 3rem 1.5rem 2rem; }
  .footer-cols { grid-template-columns: 1fr; gap: 2rem; }
```

- [ ] **Step 4: Eseguire lo script di verifica**

Run: `cd /Users/silviarinaldi/Desktop/echowebagency-site && python3 scripts/check_home.py`

Expected: **PASS** — `OK — tutti gli invarianti della homepage sono rispettati`.

Se fallisce, correggere prima di committare.

- [ ] **Step 5: Commit**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
git add index.html home.css
git commit -m "Aggiunge CTA finale e footer a colonne

Il footer usa la classe .site-footer invece del selettore footer nudo:
le altre 38 pagine condividono lo stesso markup piatto e sarebbero
state stravolte. Orari 9-18, allineati al JSON-LD gia' pubblicato:
il brief indicava 17, ma cambiarlo e' una decisione di business.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 8: Propagare i pulsanti alle 38 pagine interne

**Files:**
- Modify: `styles.css` (solo le regole dei pulsanti)

**Interfaces:**
- Consumes: il linguaggio visivo dei pulsanti definito in `home.css` al Task 3
- Produces: nessuna nuova interfaccia

Solo le regole dei pulsanti. Non toccare `nav`, `footer`, `:root`: le 38 pagine condividono markup piatto e cambiarne il layout le romperebbe.

- [ ] **Step 1: Fotografare lo stato attuale di una pagina interna**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
grep -n "nav-cta\|btn-primary\|btn-secondary\|calendly-cta" styles.css
```

Annotare i numeri di riga: sono le uniche righe che si possono modificare.

- [ ] **Step 2: Sostituire le quattro regole dei pulsanti in `styles.css`**

```css
.nav-cta {
  background: var(--accent);
  color: var(--text);
  padding: 0.7rem 1.5rem;
  border-radius: 0;
  font-size: 0.72rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  text-decoration: none;
  transition: background .2s, color .2s;
}
.nav-cta:hover { background: var(--text); color: var(--accent); }

.btn-primary {
  background: var(--accent);
  color: var(--text);
  padding: 0.95rem 2.1rem;
  border-radius: 0;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  text-decoration: none;
  transition: background .2s, color .2s;
}
.btn-primary:hover { background: var(--text); color: var(--accent); }

.btn-secondary {
  background: transparent;
  color: var(--text);
  padding: 0.95rem 2.1rem;
  border-radius: 0;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  text-decoration: none;
  border: 1.5px solid var(--text);
  transition: background .2s, color .2s;
}
.btn-secondary:hover { background: var(--text); color: var(--bg); }

.calendly-cta {
  background: var(--accent);
  color: var(--text);
  padding: 1rem 2.5rem;
  border-radius: 0;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  text-decoration: none;
  display: inline-block;
  margin-top: 1rem;
  transition: background .2s, color .2s;
}
.calendly-cta:hover { background: var(--text); color: var(--accent); }
```

- [ ] **Step 3: Verificare che nulla fuori dai pulsanti sia cambiato**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
git diff styles.css | grep "^[-+]" | grep -v "^[-+][-+]" | \
  grep -vE "nav-cta|btn-primary|btn-secondary|calendly-cta|background|color|padding|border|font|letter-spacing|text-transform|text-decoration|transition|display|margin-top|^\+\}|^-\}|^\+$|^-$"
```

Expected: **nessun output**. Qualunque riga stampata è una modifica fuori perimetro: annullarla.

- [ ] **Step 4: Verificare a vista una pagina interna**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
python3 -m http.server 8765 &
sleep 1
open http://localhost:8765/chi-siamo
```

Controllare: il pulsante in alto a destra è ora lime rettangolare, il resto della pagina è immutato (nav crema, footer piatto, tipografia invariata). Poi fermare il server con `kill %1`.

- [ ] **Step 5: Commit**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
git add styles.css
git commit -m "Porta i pulsanti lime rettangolari sulle 38 pagine interne

Modificate solo le quattro regole dei pulsanti. Nav, footer e :root
restano intatti: le pagine interne condividono lo stesso markup piatto
e un cambio di layout le romperebbe tutte insieme.

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 9: Verifica finale responsive, accessibilità e non regressione

**Files:**
- Nessuna modifica prevista. Se emergono difetti, si correggono `home.css` o `index.html`.

**Interfaces:**
- Consumes: tutto quanto sopra
- Produces: la conferma che i criteri di completamento della specifica sono soddisfatti

- [ ] **Step 1: Avviare il server locale**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
python3 -m http.server 8765
```

Lasciarlo in esecuzione per tutti gli step successivi.

- [ ] **Step 2: Verificare la resa a quattro larghezze**

Aprire `http://localhost:8765/` e controllare a 375px, 768px, 1280px, 1920px.

Per ciascuna: nessuno scroll orizzontale, nessun testo troncato, la foto hero non deformata, la griglia servizi con il numero giusto di colonne (1 / 2 / 4 / 4), il footer leggibile.

Verifica automatica dell'assenza di scroll orizzontale, da eseguire nella console del browser a ogni larghezza:

```js
document.documentElement.scrollWidth <= document.documentElement.clientWidth
```

Expected: `true` a tutte e quattro le larghezze.

- [ ] **Step 3: Verificare che le quattro ancore storiche atterrino correttamente**

Nella console del browser:

```js
['metodo','contatti','origine','casi','servizi'].forEach(id => {
  const el = document.getElementById(id);
  console.log(id, el ? 'ok' : 'MANCANTE');
});
```

Expected: cinque `ok`.

Poi provare a mano `http://localhost:8765/#metodo` e `http://localhost:8765/#contatti`: il titolo della sezione deve essere visibile sotto la nav, non coperto da essa.

- [ ] **Step 4: Verificare i contrasti sulle combinazioni critiche**

Le tre a rischio sono: lime `#C8E63C` su nero `#111110` (badge pilastri e valori impatto), nero su lime (pulsanti), e `rgba(245,243,238,0.45)` su nero (`.impatto-meta`).

```bash
python3 - <<'PY'
def lum(hex_color):
    r, g, b = (int(hex_color[i:i+2], 16) / 255 for i in (1, 3, 5))
    f = lambda c: c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = f(r), f(g), f(b)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b

def ratio(a, b):
    la, lb = lum(a), lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)

for nome, a, b in [
    ("lime su nero", "#C8E63C", "#111110"),
    ("nero su lime", "#111110", "#C8E63C"),
    ("muted su crema", "#6B6B68", "#F5F3EE"),
    ("impatto-meta su nero", "#6E6D68", "#111110"),
]:
    r = ratio(a, b)
    print(f"{nome}: {r:.2f}  {'OK AA' if r >= 4.5 else 'SOTTO AA (4.5)'}")
PY
```

Expected: le prime tre sopra 4.5. Se `impatto-meta` risulta sotto, alzare l'opacità da `0.45` a `0.6` in `home.css` e rieseguire.

- [ ] **Step 5: Verificare che le 38 pagine interne non siano regredite**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
git diff main --stat -- . ':!index.html' ':!home.css' ':!hero-formazione*' ':!scripts/check_home.py' ':!docs/'
```

Expected: solo `styles.css`. Qualsiasi altro file nell'elenco è fuori perimetro.

Poi aprire a campione `http://localhost:8765/chi-siamo`, `http://localhost:8765/governance-ai` e `http://localhost:8765/blog/` e confermare che sono integre.

- [ ] **Step 6: Eseguire un'ultima volta lo script di verifica**

Run: `cd /Users/silviarinaldi/Desktop/echowebagency-site && python3 scripts/check_home.py`

Expected: `OK — tutti gli invarianti della homepage sono rispettati`

- [ ] **Step 7: Fermare il server e committare eventuali correzioni**

```bash
cd /Users/silviarinaldi/Desktop/echowebagency-site
git add -A
git commit -m "Correzioni emerse dalla verifica responsive e di contrasto

Co-Authored-By: Claude <noreply@anthropic.com>"
```

Se non ci sono correzioni da fare, saltare il commit.

---

## Prima del deploy

Il deploy in produzione **non fa parte di questo piano** e richiede approvazione esplicita. Quando arriverà:

1. Aprire una PR da `homepage-redesign` verso `main` e guardare la preview Vercel, che si genera automaticamente.
2. Controllare la preview su mobile reale, non solo con il ridimensionamento del browser.
3. Verificare che `https://<preview>/#metodo` e `/#contatti` atterrino correttamente, perché è il percorso che seguono i visitatori arrivati dalle pagine interne.
4. Eseguire Lighthouse da Chrome DevTools (scheda Lighthouse, modalità mobile) sia sulla preview sia su `https://www.echo.srl/`, e confrontare i quattro punteggi. Il criterio della specifica è "nessuna regressione": l'unico punto realmente a rischio è Performance, per via della foto hero che oggi non esiste. Se Performance cala di più di 5 punti, ridurre la qualità JPEG da 65 a 55 nel Task 2 e rigenerare. Questa verifica va fatta qui e non in locale, perché `python3 -m http.server` non applica compressione né gli header di cache di `vercel.json`, quindi in locale i numeri sarebbero falsati.
5. Solo dopo il via libera, fare merge: Vercel pubblica in automatico su `main`.

## Fuori perimetro

Nessuna modifica all'HTML di pagine diverse dalla home. Nessuna modifica a `blog/`, `sitemap.xml`, `robots.txt`, `vercel.json` o agli script di build esistenti. Nessuna conversione a Next.js. Nessun deploy.
