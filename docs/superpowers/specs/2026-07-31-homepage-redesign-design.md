# Redesign della homepage — specifica

Data: 2026-07-31
Repo: `ECHOSRL/echowebagency-site` · branch di lavoro da creare da `main`

## Obiettivo

Riscrivere la homepage di www.echo.srl secondo il layout e il copy approvati, ispirati al prototipo Pomelli, senza perdere il posizionamento e il capitale SEO già costruiti.

## Premessa: cosa è emerso dall'esplorazione

Il brief partiva da tre assunti che il codice smentisce. Sono la ragione di metà delle decisioni qui sotto.

1. **Non è un sito Next.js.** È HTML statico scritto a mano. Vercel ha framework preset `Other`, output directory `.`. Nessun React, nessun npm, nessuno step di build per la home (esiste solo uno script Python che genera il blog dai Markdown). Quindi "componenti separati Hero / PillarsSection / ServicesGrid" non è realizzabile come componenti React senza convertire l'intero sito.

2. **La palette non è da confermare: esiste già.** I token sono in `:root` e coincidono quasi esattamente con le ipotesi del brief.

3. **`index.html` è l'unica pagina che non usa `styles.css`.** Ha tutto il CSS inline. `styles.css` è invece condiviso da **38 altre pagine**. Spostarci dentro gli stili della home le romperebbe tutte.

## Design system (già codificato, non si tocca)

| Token | Valore | Uso |
|---|---|---|
| `--bg` | `#F5F3EE` | crema, sfondo sezioni chiare |
| `--text` | `#111110` | quasi-nero, testo e sezioni scure |
| `--accent` | `#C8E63C` | verde lime, CTA e accenti |
| `--accent-soft` | `#DEE8C4` | verde salvia, sezione pilastri e Numeri |
| `--muted` | `#6B6B68` | testo secondario |
| `--border` | `#E0DDD6` | bordi |
| `--font-serif` | Playfair Display | titoli |
| `--font-sans` | Inter | body |

Le ipotesi del brief (`#c9d94a`, `#f2f1ea`, `#0a0a0a`) vanno scartate a favore dei valori reali.

## Architettura

Si resta su HTML statico. Nessun build step, nessun rischio di regressione SEO.

- `index.html` — riscritta, ogni sezione delimitata da un commento `<!-- ===== NOME SEZIONE ===== -->`
- `home.css` — **nuovo file**, stili specifici della home, linkato solo da `index.html`
- `styles.css` — modificato **solo** nelle regole dei pulsanti (`.nav-cta`, `.btn-primary`, `.btn-secondary`, `.calendly-cta`), per propagare il nuovo linguaggio visivo alle 38 pagine interne senza toccare il loro HTML

Il perimetro su `styles.css` è ristretto ai soli pulsanti, non a `nav` e `footer` come ipotizzato inizialmente: le 38 pagine condividono lo stesso markup piatto del footer (`.footer-logo`, `.footer-copy`, `.footer-links`), quindi cambiare la regola `footer` per farne un layout a colonne le romperebbe tutte. Il footer a colonne della home vive solo in `home.css`, che è isolato perché `index.html` non carica `styles.css`.

La "separazione in componenti" chiesta dal brief si realizza come sezioni delimitate e un foglio di stile dedicato, non come componenti React.

## Struttura della pagina

| # | Sezione | Sfondo | Stato |
|---|---|---|---|
| 1 | Nav | crema traslucido | riscritta |
| 2 | Hero | crema | riscritta, con foto |
| 3 | Ticker clienti | crema | conservata, +4 nomi, resa accessibile |
| 4 | Un approccio orientato ai processi | salvia | nuova |
| 5 | Il Metodo | crema | conservata |
| 6 | Competenze operative | crema | nuova |
| 7 | I Numeri | salvia | conservata |
| 8 | L'impatto misurabile | nero | riscritta |
| 9 | CTA finale | crema | nuova |
| 10 | Footer | crema | riscritto a colonne |

Sezione **Origine** rimossa come sezione autonoma: la sua lista di quattro servizi confluisce nella griglia Competenze operative, il passaggio su Reggio Emilia e il distretto manifatturiero diventa l'intro della sezione pilastri, che ne eredita anche l'`id="origine"`. Il radicamento territoriale, rilevante per la local SEO, non si perde.

## Ancore: vincolo non negoziabile

Le 38 pagine interne linkano ancore della home in massa. Rimuoverle o rinominarle romperebbe 68 link interni in silenzio: nessun 404, solo uno scroll a vuoto in cima alla pagina, su un sito il cui valore SEO sta proprio nell'internal linking.

| Ancora | Link entranti | Sezione che ne eredita l'ID |
|---|---|---|
| `#metodo` | 38 | 5 — Il Metodo |
| `#contatti` | 38 | 9 — CTA finale |
| `#origine` | 22 | 4 — Un approccio orientato ai processi |
| `#casi` | 8 | 8 — L'impatto misurabile |

Gli ID storici restano quelli primari anche dove il titolo della sezione cambia: gli ID non sono visibili all'utente, e riusarli costa nulla mentre cambiarli costa 68 link. La sezione Competenze operative, che non ha antenati, prende `id="servizi"`.

Serve inoltre `scroll-margin-top` su tutte le sezioni bersaglio: la nav è `position: fixed` e senza quella proprietà il titolo finisce sotto la barra. È un difetto già presente oggi e va corretto nella riscrittura.

### 1. Nav

Voci e destinazioni:

| Voce | Destinazione |
|---|---|
| `METODO` | `#metodo` |
| `SERVIZI` | `#servizi` |
| `RISULTATI` | `#casi` |
| `BLOG` | `/blog/` |
| `CHI SIAMO` | `/chi-siamo` |
| `CONTATTI` | `#contatti` |

Più CTA `PRENOTA AUDIT` in verde lime con testo nero, maiuscolo, rettangolare.

`CHI SIAMO` era stato eliminato dalla nav approvata e reintrodotto su richiesta dell'autrice. La pagina resta linkata da 17 altre pagine, quindi non sarebbe rimasta orfana, ma avrebbe perso il link dalla pagina più forte del sito: lo stesso motivo per cui era stato aggiunto `BLOG`.

`BLOG` è un'aggiunta rispetto al brief. Le ultime otto commit del repo sono tutte lavoro SEO: 25 articoli, cluster di link interni, schema FAQPage. La homepage è la sorgente di link interni più forte del sito; toglierle il link al blog vanifica parte di quel lavoro.

`METODO` punta a `#metodo`, che continua a esistere (vedi sezione 5). Nel brief l'ancora sarebbe stata rotta.

### 2. Hero

- Occhiello: `Consulenza AI per le PMI manifatturiere`
- H1 (serif, grande): `Radici manifatturiere, visione digitale.`
- Sottotitolo: `Portiamo l'intelligenza artificiale dove il lavoro accade realmente. Ottimizzazione dei processi, formazione dei team e governance strategica per le PMI italiane.`
- CTA primaria: `Prenota un appuntamento` → Calendly (stesso URL di oggi)
- Immagine a destra: foto della sessione di formazione
- Sopra la foto, come testo HTML: `Human first`

Layout a due colonne su desktop, impilato sotto i 900px con la foto sotto il testo.

**Nota SEO da valutare.** L'H1 attuale è "L'intelligenza artificiale integrata nei reparti, non solo nei discorsi" e contiene la keyword principale. Il nuovo H1 è un'affermazione di marca e non la contiene. L'occhiello proposto sopra serve proprio a mantenere "Consulenza AI" e "PMI manifatturiere" in alto nella pagina. È una scelta consapevole: identità di marca sopra densità di keyword.

### 3. Ticker clienti

Ai 14 nomi attuali si aggiungono: `STEFANO RICCI`, `AGV MAROSTICA`, `CLUST-ER CREATE`, `GOLDEN GROUP`. Diciotto in totale, senza forme societarie, coerenti con la resa maiuscola esistente.

**Correzione di accessibilità.** Oggi l'intera fascia ha `aria-hidden="true"`: nessuno screen reader legge un solo nome cliente. Nella riscrittura `aria-hidden` resta solo sulla seconda metà, quella duplicata per il loop continuo, così i nomi diventano contenuto leggibile.

### 4. Un approccio orientato ai processi

Sfondo `--accent-soft`. Intro dal brief, preceduta dal recupero del radicamento a Reggio Emilia.

Quattro card in riga, ciascuna con badge titolo su sfondo nero e testo lime, più descrizione: Pragmatismo · Manufacturing Heritage · Strategic Governance · Integrazione Human-centric. Testi dal brief, invariati.

Sotto i 900px: una colonna.

### 5. Il Metodo

Conservata invariata: quattro step (Discovery, Mappa, Implementazione, Consolidamento). Serve l'ancora `#metodo` della nav.

### 6. Competenze operative

Sfondo crema, otto card con bordi sottili, titolo serif più descrizione. Testi dal brief.

Cinque card diventano link a pagine che esistono già, rinforzando l'internal linking:

| Card | Destinazione |
|---|---|
| AI Readiness Audit | `/ai-readiness-audit` |
| Governance AI | `/governance-ai` |
| Formazione AI | `/formazione-ai` |
| Integrazione AI | `/integrazione-ai` |
| Digital Product Passport (DPP) | `/digital-product-passport` |
| Consulenza AI | nessuna pagina, resta testo |
| Automazione | nessuna pagina, resta testo |
| Strategia digitale | nessuna pagina, resta testo |

Il brief chiede una griglia 3x3 per otto card: sarebbe una griglia con un buco. Si usa 4x2 su desktop, 2x2 su tablet, una colonna su mobile.

### 7. I Numeri

Conservata invariata: 40+ aziende, 12 settori, 3x velocità, 98% rinnovo. Coincidono con quanto indicato nel brief.

### 8. L'impatto misurabile — `id="casi"`

Sfondo nero, testo bianco, accenti lime, bordo sinistro lime su ogni scheda. Tutti e **sei** i risultati, non quattro: si conservano anche "Formazione, 120 dipendenti, 87% adozione" e "Milano, reporting, −70% tempo analisi".

**I risultati non sono virgolettati.** Il brief li riformulava come citazioni dirette di clienti fra virgolette. Nessuno ha pronunciato quelle frasi. Pubblicare testimonianze inventate attribuite a clienti, anche anonimizzati, è una pratica commerciale scorretta sanzionabile (Codice del Consumo, artt. 20-23; AGCM). Si mantengono gli stessi numeri e lo stesso impatto visivo, formulati come esiti di progetto — esattamente come sono presentati oggi.

Se in futuro arrivano dichiarazioni reali e attribuibili, la sezione è pronta a ospitarle come virgolettati veri.

### 9. CTA finale — `id="contatti"`

Sfondo crema. Titolo `Pronto per l'integrazione?`, testo e pulsante `Prenota un appuntamento` dal brief.

Raccoglie l'ancora `#contatti`: chi arriva da una delle 38 pagine interne atterra sull'invito a prenotare, con i recapiti completi nel footer immediatamente sotto.

### 10. Footer

Riscritto a colonne: logo Echo · `SEDE & CONTATTI` (Via Lelio e Fausto Socini 32/B, 42122 Reggio Emilia RE, info@echowebagency.it, +39 351 702 7294) · `ORARI OPERATIVI` (Lun–Ven 9:00–18:00, Sab e Dom chiuso) · icone Instagram e LinkedIn · riga copyright con P.IVA 03135740359.

Orari allineati al JSON-LD già pubblicato, che dichiara chiusura alle 18:00. Il brief indicava 17:00: sarebbe stata una modifica all'orario pubblicato, cioè una decisione di business, non di layout.

## Pulsanti

Nuovo stile: rettangolari, spigoli vivi, testo maiuscolo, lime su testo nero. Sostituisce le pillole arrotondate nere attuali (`border-radius: 2rem`).

Applicato in `styles.css` alle regole di `nav`, `footer` e pulsanti, così le 38 pagine interne ereditano il nuovo look senza modifiche al loro HTML. Le voci di menu delle pagine interne restano quelle attuali.

**Header: nav crema, deciso.** Il brief indica un header nero. Si mantiene invece la **nav crema traslucida** attuale, cambiando solo il pulsante CTA in lime rettangolare.

L'argomento originale era che la pagina avesse già due sezioni a fondo nero. Con il Paradosso rimosso ne resta una sola, quindi quell'argomento non regge più. Resta valido il motivo principale: la nav crema è ereditata da tutte le 38 pagine interne tramite `styles.css`, quindi renderla nera è un cambiamento di identità su tutto il sito e non un ritocco alla home.

**Correzione a un errore di questa specifica.** Una versione precedente sosteneva che il pulsante lime contrastasse meglio su crema che su nero. È l'opposto, e i numeri sono netti:

| Contorno del pulsante lime contro | Rapporto | WCAG 1.4.11 richiede 3:1 |
|---|---|---|
| Nero `#111110` | 13.35 | conforme |
| Crema `#F5F3EE` | 1.28 | non conforme |
| Verde salvia `#DEE8C4` | 1.11 | non conforme |

Il testo dentro il pulsante è sempre a posto (13.35:1), ma su sfondo chiaro la **forma** del pulsante è quasi invisibile: si legge la scritta senza capire che è un elemento cliccabile. Il problema è più grave sulle 38 pagine interne, dove `.btn-primary` vive dentro `.cta-section`, che ha sfondo salvia.

Rimedio adottato: un bordo `1.5px solid var(--text)` su tutti i pulsanti lime, che porta il contorno a 14.80:1 su salvia e 17.04:1 su crema. Nessun pulsante lime si trova su fondo nero, quindi il bordo scuro non crea il problema inverso.

## Immagine hero

Sorgente: `03_Marketing_LinkedIn/HUMAN FIRST FORMAZIONE AI CHE PARTE DALLE PERSONE.jpg`, 5712×4284, 1.3 MB.

Lavorazione:
1. Ritaglio della sola fotografia, eliminando cornice bianca e didascalia impressa nei pixel. La cornice è bianco puro e stonerebbe contro il crema `#F5F3EE`; il testo nei pixel non è leggibile da screen reader né indicizzabile.
2. Due versioni: ~1600px di lato lungo per il default, ~2400px per `srcset` 2x. Obiettivo sotto i 200 KB per la versione base.
3. Salvate come `hero-formazione.jpg` e `hero-formazione@2x.jpg` nella root del repo, coerente con la collocazione degli altri asset.
4. `alt`: `Sessione di formazione AI di Echo con un team aziendale attorno al tavolo riunioni`.
5. `width`, `height` e `loading="eager"` espliciti per evitare layout shift sull'elemento più visibile della pagina.

La frase "Human first" torna come testo HTML, non come pixel.

La foto ritrae persone riconoscibili. È già un asset pubblicato su LinkedIn, ma la homepage è un uso più permanente: verificare che il consenso all'uso dell'immagine copra anche questo.

## SEO — cosa resta intatto

Si conservano senza modifiche: `<title>`, canonical, favicon, manifest, theme-color, robots, Open Graph, Twitter Card e i tre blocchi JSON-LD (Organization, ProfessionalService, WebSite).

Unica modifica: la meta description, aggiornata ai nuovi contenuti e mantenuta sotto i 155 caratteri.

`Consulenza AI per PMI manifatturiere: ottimizzazione dei processi, formazione dei team e governance. Radici manifatturiere, visione digitale. Reggio Emilia.`

La conservazione dei 68 link interni entranti è trattata sopra, in "Ancore: vincolo non negoziabile".

## Criteri di completamento

- La home rende correttamente a 375px, 768px, 1280px e 1920px
- Nessun scroll orizzontale a nessuna larghezza
- Tutte le ancore della nav puntano a sezioni esistenti
- I quattro ID storici `#metodo`, `#contatti`, `#origine`, `#casi` esistono nella pagina e atterrano sotto la nav fissa, non nascosti dietro di essa
- Contrasto testo/sfondo conforme WCAG AA su tutte le sezioni, incluse lime su nero e nero su lime
- Ogni immagine ha `alt` descrittivo
- Gerarchia dei titoli semantica: un solo `<h1>`, nessun livello saltato
- Le 38 pagine interne restano integre dopo la modifica a `styles.css`
- Nessuna testimonianza virgolettata non attribuibile
- Lighthouse: nessuna regressione rispetto alla home attuale

## Fuori perimetro

Nessuna modifica all'HTML di pagine diverse dalla home. Nessuna modifica a blog, sitemap, robots o script di build.
