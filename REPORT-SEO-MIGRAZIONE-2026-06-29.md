# Report SEO & Migrazione dominio — echo.srl

**Data:** 29 giugno 2026
**Contesto:** richiesta iniziale "il sito su analytics sta perdendo entrate, controlla e vediamo cosa ottimizzare"
**Dominio canonico:** `www.echo.srl` · **Vecchio dominio:** `echowebagency.it` (redirect 301 → echo.srl)
**Stack:** HTML statico su Vercel (progetto `echowebagency-site`, piano Hobby) · Analytics: Vercel Web Analytics

---

## 1. La diagnosi (la cosa più importante)

Il sito **non sta "perdendo" entrate**: è un **dominio nuovo a metà di una migrazione**.

- Il traffico (le "entrate") è ancora **tutto sul vecchio dominio** `echowebagency.it`.
- `echo.srl` è nato da pochi giorni per Google → **~0 traffico organico**, è normale.
- L'obiettivo ora non è "recuperare" ma **far ereditare a echo.srl il traffico del vecchio dominio** prima di perderlo.

---

## 2. I dati raccolti

### Vercel Analytics (echo.srl)
- **Prima:** 5 visite / 30 giorni (praticamente zero, e tutte dirette/di test).
- **Oggi (24h):** 54 visite / 99 pagine viste → **picco gonfiato dai test interni** della sessione, ma con **~10 referral reali**: Google (5), Bing (2), LinkedIn (2), Ecosia (1). Le visite da Google/Bing sono ricerche brand che passano dal redirect del vecchio dominio → **il redirect funziona**.

### Google Search Console — VECCHIO dominio (echowebagency.it, 3 mesi)
- **216 clic · 3.020 impression · CTR 7,2% · posizione media 17** — ancora attivo.
- Query #1: **"echo web agency" = 115 clic (53% del totale)** → traffico brand/navigazionale.
- Pagine con traffico: `/` (190 clic), `/chi-siamo` (23), `/web` (6), `/contattaci` (3), `/portfolio` (1), `/servizi` (0 clic ma 189 impression).

### Google Search Console — NUOVO dominio (www.echo.srl)
- **0 clic.** Proprietà verificata solo intorno al 27/06 → dati ancora "in elaborazione".
- **Causa radice dello 0 traffico:** ispezione della homepage = *"Pagina duplicata, Google ha scelto una canonica diversa"* → Google attribuisce ancora il contenuto al vecchio dominio. È esattamente ciò che il Change of Address + i redirect risolvono.

### Accessi Search Console
- Hai (login info@echowebagency.it) le proprietà **URL-prefix** `https://www.echo.srl/` e `https://echowebagency.it/`.
- **NON** hai accesso alla proprietà *Dominio* `sc-domain:echo.srl` (verificata da un altro account, probabilmente chi gestiva il DNS).

---

## 3. Interventi fatti (29/06)

| # | Intervento | Dettaglio | Stato |
|---|---|---|---|
| 1 | **Redirect 404 tappati** | `/servizi`, `/web`, `/metodo-echo-2` → `/#metodo`; `/portfolio` → `/#casi`. Erano vecchi URL WordPress con impression residue che finivano in 404. | ✅ in `vercel.json`, commit `9ec25b1`, deployato e verificato (catena vecchio→nuovo = HTTP 200) |
| 2 | **Sitemap risottomessa** | `/sitemap.xml` con 30 URL (era stata letta a 15). | ✅ Google ha riletto → 30 pagine rilevate |
| 3 | **Change of Address** | echowebagency.it → www.echo.srl in Search Console. | ✅ Confermato e attivo, data inizio 29/06/2026 (~180gg per il trasferimento) |
| 4 | **Richieste di indicizzazione** | `echo.srl/`, `/chi-siamo`, `/blog/` aggiunte alla coda prioritaria. | ✅ fatte (home, chi-siamo, blog) |
| 5 | **Verifica robots.txt** | L'allarme "errore critico" sul vecchio dominio era **stale**: il report dettagliato dice "Recuperato / nessun problema". Google segue il 301. | ✅ falso allarme, nessun intervento |

**Fondamenta già esistenti (lavoro precedente):** 17 articoli blog, pagina `/chi-siamo` con bio (E-E-A-T), 5 pagine servizio + 3 settore, schema JSON-LD, sitemap/RSS. È il motore di contenuti che deve ancora indicizzarsi.

---

## 4. Prossimi passi

### Priorità alta (account/strategia — richiedono la tua mano)
- [ ] **Tenere `echowebagency.it` rinnovato e redirezionante.** È il ponte che regge i 216 clic/3mesi finché echo.srl non eredita il ranking. **Non farlo scadere.**
- [ ] **Recuperare l'accesso alla proprietà `sc-domain:echo.srl`** (chiedere a chi l'ha verificata, o ri-verificarla via DNS) — serve per il controllo completo.
- [ ] **Decisione strategica sul brand:** quanto difendere la query **"echo web agency"** (53% del traffico) ora che il brand abbandona "web agency". Le ricerche brand si trasferiscono coi redirect, ma echo.srl non contiene più quella keyword. Valutare: Google Business Profile, coerenza "Echo" ovunque, eventuale `alternateName` nello schema.

### Priorità media (posso farle io / semi-automatiche)
- [ ] **Richiesta indicizzazione** per le pagine rimaste: `/governance-ai`, `/ai-readiness-audit`, e i 2-3 articoli principali (la sitemap le prende comunque, questo accelera).
- [ ] **Monitoraggio** tra qualche giorno: ricontrollare indicizzazione (passaggio della canonica a echo.srl) e primi clic reali su echo.srl, al netto del rumore dei test.
- [ ] **(Opzionale) robots.txt a 200** sul vecchio dominio invece del 301 — best practice di migrazione, ma oggi funziona già.

### Crescita vera (mesi)
- [ ] **Far indicizzare e posizionare i 17 articoli** — è il vero motore delle "entrate" future. Il calendario editoriale è già pronto (`EDITORIAL-CALENDAR.md`).
- [ ] Costruire qualche **backlink** e presenza (LinkedIn già porta visite) per dare autorità al dominio nuovo.

---

## 5. Cosa aspettarsi (timeline)

- **2-6 settimane:** Google sposta la canonica su echo.srl; il traffico brand inizia a comparire sul dominio nuovo nei report GSC.
- **Mesi:** gli articoli si posizionano e arriva la crescita organica oltre il brand.
- **Sempre:** echowebagency.it resta vivo e redirezionante come ponte.

---

## Riferimenti
- Repo: `echowebagency-site` · commit redirect: `9ec25b1`
- File chiave: `vercel.json` (redirect), `sitemap.xml` (30 URL), `EDITORIAL-CALENDAR.md`
- Search Console: proprietà `https://www.echo.srl/` (URL-prefix)
- Memoria di lavoro: `echo-seo-migration-state` (stato migrazione, aggiornato 29/06)
