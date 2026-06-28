#!/usr/bin/env python3
"""Generate the AI Act 2026 lead-magnet PDF."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak,
    Table, TableStyle, ListFlowable, ListItem
)
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "lead-magnets" / "ai-act-2026-5-step-pmi.pdf"
OUT.parent.mkdir(exist_ok=True)

ACCENT = HexColor("#C8E63C")
DARK = HexColor("#111110")
MUTED = HexColor("#6B6B68")
CREAM = HexColor("#F5F3EE")

styles = getSampleStyleSheet()
H1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=24, leading=30, textColor=DARK, spaceAfter=14, spaceBefore=8)
H2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=16, leading=22, textColor=DARK, spaceAfter=10, spaceBefore=14)
H3 = ParagraphStyle("H3", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=12, leading=16, textColor=DARK, spaceAfter=6, spaceBefore=10)
BODY = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=10.5, leading=15, textColor=DARK, spaceAfter=8, alignment=TA_JUSTIFY)
LEAD = ParagraphStyle("Lead", parent=BODY, fontSize=12, leading=17, textColor=MUTED, spaceAfter=14)
CALLOUT = ParagraphStyle("Callout", parent=BODY, fontSize=10.5, leading=15, textColor=DARK, backColor=CREAM, borderColor=ACCENT, borderWidth=0, leftIndent=10, rightIndent=10, spaceBefore=8, spaceAfter=12)
SMALL = ParagraphStyle("Small", parent=BODY, fontSize=9, leading=12, textColor=MUTED)
COVER_TITLE = ParagraphStyle("CoverTitle", parent=H1, fontSize=32, leading=38, alignment=TA_LEFT, spaceAfter=18)
COVER_SUB = ParagraphStyle("CoverSub", parent=LEAD, fontSize=14, leading=20, alignment=TA_LEFT, textColor=DARK)
FOOTER_TXT = ParagraphStyle("FooterTxt", parent=SMALL, fontSize=8, leading=10, alignment=TA_CENTER, textColor=MUTED)


def header_footer(canvas, doc):
    canvas.saveState()
    # Footer
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2 * cm, 1.2 * cm, "Echo S.r.l. — info@echowebagency.it — echo.srl")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Pag. {doc.page}")
    # Top accent line
    canvas.setStrokeColor(ACCENT)
    canvas.setLineWidth(3)
    canvas.line(2 * cm, A4[1] - 1.5 * cm, A4[0] - 2 * cm, A4[1] - 1.5 * cm)
    canvas.restoreState()


def cover_page(canvas, doc):
    canvas.saveState()
    # Big accent block at top
    canvas.setFillColor(ACCENT)
    canvas.rect(0, A4[1] - 4 * cm, A4[0], 4 * cm, fill=1, stroke=0)
    canvas.setFillColor(DARK)
    canvas.setFont("Helvetica-Bold", 11)
    canvas.drawString(2 * cm, A4[1] - 2 * cm, "ECHO • PUBBLICAZIONE GRATUITA")
    canvas.setFont("Helvetica", 10)
    canvas.drawString(2 * cm, A4[1] - 2.7 * cm, "AI Act & PMI italiane • Versione 1.0 • Giugno 2026")
    # Footer
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(2 * cm, 1.2 * cm, "Echo S.r.l. — Reggio Emilia — echo.srl")
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, "Versione 1.0")
    canvas.restoreState()


story = []

# COVER
story.append(Spacer(1, 4.5 * cm))
story.append(Paragraph("AI Act 2026", COVER_TITLE))
story.append(Paragraph("5 step concreti<br/>per una PMI italiana<br/><font color='#6B6B68'>(senza panico, senza consulenza legale costosa nelle prime settimane)</font>", COVER_SUB))
story.append(Spacer(1, 4 * cm))
story.append(Paragraph("<b>A chi serve questa guida</b>", H3))
story.append(Paragraph(
    "Imprenditori, CEO, IT manager e operations di PMI italiane (5–200 dipendenti) "
    "che usano già ChatGPT, automazioni, chatbot o sistemi predittivi — e si stanno chiedendo se "
    "stanno operando nel rispetto dell'AI Act, che è già in vigore.",
    BODY,
))
story.append(Spacer(1, 0.5 * cm))
story.append(Paragraph(
    "<b>Cosa NON è questa guida</b><br/>"
    "Non è consulenza legale. È un percorso operativo: i 5 passi che facciamo con i clienti "
    "<i>prima</i> di sentire un legale specializzato. Senza questa base, qualunque consulenza diventa generica.",
    BODY,
))
story.append(PageBreak())

# INDICE
story.append(Paragraph("Indice", H1))
story.append(Paragraph("1. &nbsp;&nbsp;Perché l'AI Act riguarda anche te (anche se non vendi AI)", BODY))
story.append(Paragraph("2. &nbsp;&nbsp;Step 1 — Mappa gli strumenti AI già in uso", BODY))
story.append(Paragraph("3. &nbsp;&nbsp;Step 2 — Classifica il livello di rischio", BODY))
story.append(Paragraph("4. &nbsp;&nbsp;Step 3 — Definisci una policy interna chiara", BODY))
story.append(Paragraph("5. &nbsp;&nbsp;Step 4 — Documenta chi decide e con quali dati", BODY))
story.append(Paragraph("6. &nbsp;&nbsp;Step 5 — Forma i referenti interni", BODY))
story.append(Paragraph("7. &nbsp;&nbsp;Checklist finale per fare l'audit in azienda in un'ora", BODY))
story.append(Paragraph("8. &nbsp;&nbsp;Prossimi passi", BODY))
story.append(PageBreak())

# INTRO
story.append(Paragraph("1. Perché l'AI Act riguarda anche te", H1))
story.append(Paragraph(
    "L'AI Act europeo è in vigore dal 2024 e le sue scadenze si applicano per fasi tra il 2025 e il 2027. "
    "Non riguarda solo chi <i>produce</i> sistemi AI, ma anche chi li <b>integra nei propri processi</b>. "
    "E questo include praticamente ogni azienda italiana che oggi usa ChatGPT, sistemi predittivi, "
    "chatbot, generative tools per il marketing, o AI in produzione.",
    BODY,
))
story.append(Paragraph(
    "Il rischio non è solo la sanzione (che può arrivare al 7% del fatturato globale per le violazioni più gravi). "
    "Il rischio reale per una PMI è duplice:",
    BODY,
))
story.append(Paragraph(
    "<b>1. Esposizione legale silenziosa.</b> Strumenti AI usati senza policy possono violare GDPR, "
    "riservatezza commerciale e specifici divieti dell'AI Act senza che nessuno in azienda se ne accorga.",
    BODY,
))
story.append(Paragraph(
    "<b>2. Perdita di valore in fase di audit/due diligence.</b> Sempre più committenti chiedono ai fornitori "
    "di dichiarare come usano l'AI. Senza una mappa documentata, l'azienda perde contratti.",
    BODY,
))
story.append(Paragraph(
    "La buona notizia: nei prossimi 5 step ti diamo l'ossatura per arrivare ad avere "
    "<b>una governance proporzionata alla tua dimensione</b>, in 3–4 settimane di lavoro interno.",
    CALLOUT,
))
story.append(PageBreak())

# STEP 1
story.append(Paragraph("2. Step 1 — Mappa gli strumenti AI già in uso", H1))
story.append(Paragraph("Cosa fare", H3))
story.append(Paragraph(
    "Mezzogiornata di interviste rapide con i responsabili di ogni reparto. Una domanda chiave: "
    "<b>“Quali strumenti che generano testo, immagini, previsioni o decisioni automatiche usate, "
    "anche solo saltuariamente?”</b>",
    BODY,
))
story.append(Paragraph("Cosa mappare per ogni strumento", H3))
items = [
    "Nome dello strumento (ChatGPT, Copilot, Claude, Midjourney, Notion AI, sistemi predittivi del gestionale, chatbot del sito, ecc.)",
    "Reparto e persona che lo usa",
    "Tipo di dato che viene inserito (commerciale, produttivo, anagrafiche clienti, fornitori, candidati)",
    "Frequenza (quotidiana, settimanale, sporadica)",
    "Se serve a prendere decisioni operative o solo a velocizzare task",
]
story.append(ListFlowable([ListItem(Paragraph(i, BODY)) for i in items], bulletType='bullet', leftIndent=14))
story.append(Paragraph("Output", H3))
story.append(Paragraph(
    "Un foglio di lavoro semplice (Excel o Google Sheet) con una riga per strumento. "
    "Nella nostra esperienza, una PMI da 30 persone scopre <b>tipicamente 8–15 strumenti AI attivi</b>, "
    "di cui solo 2–3 noti al management.",
    CALLOUT,
))
story.append(Paragraph("Tempo stimato", H3))
story.append(Paragraph("2–3 giorni di lavoro distribuito.", BODY))
story.append(PageBreak())

# STEP 2
story.append(Paragraph("3. Step 2 — Classifica il livello di rischio", H1))
story.append(Paragraph(
    "L'AI Act definisce 4 categorie di rischio per i sistemi AI. Per ciascuno strumento mappato nello Step 1, "
    "assegna una categoria.",
    BODY,
))
data = [
    ["Categoria", "Esempi tipici in PMI", "Cosa serve fare"],
    ["Rischio inaccettabile\n(vietato)",
     "Sistemi di social scoring, manipolazione subliminale, riconoscimento emozioni sul lavoro",
     "Dismettere immediatamente"],
    ["Alto rischio",
     "AI che screen-a candidati, valuta credito, prende decisioni produttive senza supervisione umana",
     "Documentazione completa, validazione umana, audit periodico"],
    ["Rischio limitato",
     "Chatbot customer-facing, generazione contenuti pubblicati senza supervisione",
     "Trasparenza obbligatoria: l'utente deve sapere che parla con un'AI"],
    ["Rischio minimo",
     "ChatGPT per email interne, Copilot per produttività, AI per moodboard interni",
     "Policy interna di base, formazione"],
]
t = Table(data, colWidths=[3.5 * cm, 7 * cm, 5.5 * cm])
t.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), DARK),
    ('TEXTCOLOR', (0, 0), (-1, 0), white),
    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
    ('FONTSIZE', (0, 0), (-1, 0), 10),
    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
    ('FONTSIZE', (0, 1), (-1, -1), 9),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('TEXTCOLOR', (0, 1), (-1, -1), DARK),
    ('GRID', (0, 0), (-1, -1), 0.5, MUTED),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 8),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
]))
story.append(t)
story.append(Spacer(1, 0.5 * cm))
story.append(Paragraph("Tempo stimato", H3))
story.append(Paragraph("1 giornata.", BODY))
story.append(PageBreak())

# STEP 3
story.append(Paragraph("4. Step 3 — Definisci una policy interna chiara", H1))
story.append(Paragraph(
    "La policy AI di una PMI non deve essere lunga 60 pagine. Deve essere lunga <b>4–6 pagine</b>, scritta in italiano comprensibile, "
    "approvata dal CEO in una riunione, e affissa (o condivisa) ovunque sia visibile.",
    BODY,
))
story.append(Paragraph("Sezioni minime", H3))
sections = [
    "<b>Scopo</b>: perché abbiamo una policy AI (1 paragrafo)",
    "<b>Strumenti approvati</b>: lista chiara di cosa il team può usare (con versione, se rilevante)",
    "<b>Dati che NON possono uscire</b>: dati personali clienti, dati commerciali sensibili, prezzi, listini fornitori, formule, design protetti",
    "<b>Chi decide</b>: per ogni reparto, chi firma l'introduzione di un nuovo strumento AI",
    "<b>Decisioni automatizzate</b>: lista chiara delle decisioni che devono restare umane (assunzioni, valutazioni, accettazione ordini sopra X)",
    "<b>Procedura di emergenza</b>: chi chiamare se sospetti un uso scorretto o un data leak",
]
story.append(ListFlowable([ListItem(Paragraph(i, BODY)) for i in sections], bulletType='bullet', leftIndent=14))
story.append(Paragraph(
    "<b>Suggerimento operativo:</b> non partire da template di multinazionali. "
    "Scrivila come scriveresti un'istruzione operativa per un nuovo assunto.",
    CALLOUT,
))
story.append(Paragraph("Tempo stimato", H3))
story.append(Paragraph("1 settimana, con 2–3 cicli di revisione.", BODY))
story.append(PageBreak())

# STEP 4
story.append(Paragraph("5. Step 4 — Documenta chi decide e con quali dati", H1))
story.append(Paragraph(
    "Per gli strumenti di <b>alto rischio</b> e <b>rischio limitato</b> emersi nello Step 2, "
    "serve una scheda di documentazione. Una sola pagina per strumento. "
    "Questa è la differenza tra essere preparati a un audit e prendere una sanzione.",
    BODY,
))
story.append(Paragraph("Scheda strumento — campi minimi", H3))
fields = [
    "Nome strumento, fornitore, versione",
    "Categoria di rischio (Step 2)",
    "Tipo di decisioni/output che produce",
    "Dataset di input: che dati vengono passati, di chi sono",
    "Validazione umana: chi controlla l'output prima dell'azione",
    "Trasparenza verso l'utente finale (se applicabile)",
    "Data di valutazione e data prossima revisione (annuale)",
]
story.append(ListFlowable([ListItem(Paragraph(i, BODY)) for i in fields], bulletType='bullet', leftIndent=14))
story.append(Paragraph("Tempo stimato", H3))
story.append(Paragraph("1 settimana per documentare 5–10 strumenti.", BODY))
story.append(PageBreak())

# STEP 5
story.append(Paragraph("6. Step 5 — Forma i referenti interni", H1))
story.append(Paragraph(
    "Una governance senza persone formate è un PDF morto in un drive. "
    "Identifica un <b>referente AI per reparto</b> (3–5 persone in totale per una PMI media). "
    "Non devi formarli per <i>usare</i> l'AI, ma per <b>governarla</b>: applicare la policy, validare nuove richieste, segnalare zone grigie.",
    BODY,
))
story.append(Paragraph("Cosa coprire nella formazione (4 ore in totale)", H3))
training = [
    "1 ora — Cos'è l'AI Act, perché ci riguarda, le 4 categorie di rischio",
    "1 ora — Come leggere la policy aziendale, casi pratici reparto per reparto",
    "1 ora — Come compilare la scheda strumento (Step 4)",
    "1 ora — Come reagire a richieste nuove (es. un fornitore propone un tool AI)",
]
story.append(ListFlowable([ListItem(Paragraph(i, BODY)) for i in training], bulletType='bullet', leftIndent=14))
story.append(Paragraph("Tempo stimato", H3))
story.append(Paragraph("2 mezze giornate distribuite su 2 settimane.", BODY))
story.append(PageBreak())

# CHECKLIST
story.append(Paragraph("7. Checklist finale", H1))
story.append(Paragraph("Per fare l'audit AI in azienda in un'ora", LEAD))
checklist = [
    "Esiste una lista degli strumenti AI usati in azienda?",
    "Ognuno di questi strumenti ha una categoria di rischio assegnata?",
    "Esiste una policy AI scritta, approvata dal CEO?",
    "I dati sensibili (clienti, prezzi, formule) sono chiaramente fuori da quello che può finire in un modello AI esterno?",
    "Le decisioni automatizzate ad alto rischio hanno sempre una validazione umana?",
    "C'è almeno un referente AI formato per ogni reparto principale?",
    "C'è una scheda di documentazione compilata per i sistemi ad alto rischio?",
    "È stata fissata una data di revisione annuale del sistema di governance?",
]
for i, q in enumerate(checklist, 1):
    story.append(Paragraph(f"&#9744; &nbsp;{i}. {q}", BODY))
story.append(Spacer(1, 0.4 * cm))
story.append(Paragraph(
    "Se hai meno di 5 sì su 8: hai un'esposizione significativa. È il momento di partire.<br/>"
    "Se hai 5–7 sì: sei in mezzo. Manca la documentazione o la formazione, in genere.<br/>"
    "Se hai 8 sì: complimenti, sei sopra la media.",
    CALLOUT,
))
story.append(PageBreak())

# NEXT STEPS
story.append(Paragraph("8. Prossimi passi", H1))
story.append(Paragraph(
    "Questi 5 step coprono il <b>fondamento operativo</b>. Sono ciò che fai prima di chiamare un legale. "
    "Senza questa base, qualunque consulenza legale produce raccomandazioni generiche.",
    BODY,
))
story.append(Paragraph("Se vuoi accelerare", H3))
story.append(Paragraph(
    "Echo accompagna le PMI italiane in questo percorso. Un AI Readiness Audit dura 2–3 settimane e "
    "produce: mappa strumenti, classificazione rischio, policy proporzionata, schede documentazione, "
    "formazione referenti. Poi se serve consulenza legale, sai esattamente dove chiamarla.",
    BODY,
))
story.append(Spacer(1, 0.5 * cm))
story.append(Paragraph("Contatti", H2))
story.append(Paragraph(
    "<b>Silvia Rinaldi</b> — Founder, Echo S.r.l.<br/>"
    "Email: info@echowebagency.it<br/>"
    "Sito: echo.srl<br/>"
    "Sede: Via Lelio e Fausto Socini 32/B, 42122 Reggio Emilia (RE)<br/>"
    "Tel: +39 351 7027294",
    BODY,
))
story.append(Spacer(1, 0.5 * cm))
story.append(Paragraph(
    "Trenta minuti di call gratuita: <b>https://calendly.com/echowebagency-info/formazione</b>",
    CALLOUT,
))
story.append(Spacer(1, 1 * cm))
story.append(Paragraph(
    "Approfondimenti correlati sul sito echo.srl:<br/>"
    "• Servizio Governance AI: echo.srl/governance-ai<br/>"
    "• AI Readiness Audit: echo.srl/ai-readiness-audit<br/>"
    "• Articolo \"Stai usando l'AI fuori legge\": echo.srl/blog/stai-usando-ai-fuori-legge-ai-act-pmi<br/>"
    "• Case study maison di alta maglieria: echo.srl/casi-studio/maison-knit-luxury",
    SMALL,
))
story.append(Spacer(1, 1 * cm))
story.append(Paragraph(
    "Questa pubblicazione è una guida operativa basata sull'esperienza diretta di Echo S.r.l. con PMI italiane manifatturiere, moda e beauty. "
    "Non sostituisce una consulenza legale qualificata. Tutte le informazioni sono aggiornate a giugno 2026.",
    FOOTER_TXT,
))

doc = SimpleDocTemplate(
    str(OUT), pagesize=A4,
    leftMargin=2 * cm, rightMargin=2 * cm,
    topMargin=2.5 * cm, bottomMargin=1.8 * cm,
    title="AI Act 2026 — 5 step per una PMI italiana",
    author="Silvia Rinaldi, Echo S.r.l.",
    subject="Guida operativa AI Act per PMI",
    keywords="AI Act, governance AI, PMI italiane, intelligenza artificiale, compliance",
)
# First page = cover (different style), rest = normal header/footer
doc.build(story, onFirstPage=cover_page, onLaterPages=header_footer)
print(f"✓ Generated {OUT.relative_to(Path.cwd())}: {OUT.stat().st_size//1024} KB")
