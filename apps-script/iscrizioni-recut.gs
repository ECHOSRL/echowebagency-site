/**
 * Iscrizioni dalla pagina www.echo.srl/scarica-recut.
 *
 * Vive dentro il foglio Google "Iscrizioni ReCut" (Estensioni > Apps Script)
 * ed e' pubblicato come app web. Lo chiamano solo le funzioni del sito su
 * Vercel, con un segreto condiviso: chi non lo conosce non scrive niente.
 *
 * Una riga per ogni invio del modulo: e' la prova di cosa ha accettato la
 * persona, quando, e con quale testo davanti. I due consensi sono separati
 * perche' sono due scopi diversi (aggiornamenti ReCut, invito EFN).
 *
 * Il modulo e' pubblico: chiunque potrebbe scrivere l'indirizzo di un altro.
 * Per questo una riga NON e' ancora un consenso valido. Lo diventa solo con
 * confermato_il compilato, dopo che la persona ha premuto il pulsante nella
 * mail di conferma. Prima di quella data a quell'indirizzo parte una mail
 * sola: la richiesta di conferma. Chi chiede di uscire si segna in
 * revocato_il, la riga resta. Le richieste mai confermate si cancellano
 * da sole dopo trenta giorni (funzione pulizia, una volta al giorno).
 *
 * Installazione, una volta sola:
 *   1. Eseguire la funzione installa e autorizzare. Crea l'intestazione, la
 *      pulizia giornaliera e, se manca, il SEGRETO (Impostazioni progetto >
 *      Proprieta' script): il suo valore va in RECUT_SCRIPT_SECRET su Vercel.
 *   2. Esegui il deployment > Nuovo deployment > App web,
 *      Esegui come: me, Chi ha accesso: chiunque.
 *      L'URL che finisce in /exec va in RECUT_SCRIPT_URL su Vercel.
 */

const FOGLIO = 'Iscrizioni';
const COLONNE = [
  'id', 'creato_il', 'nome', 'cognome', 'email', 'azienda',
  'consenso_aggiornamenti', 'consenso_invito_efn', 'versione_informativa',
  'pagina', 'user_agent', 'mail_inviata_il', 'confermato_il', 'revocato_il',
];
const C = Object.fromEntries(COLONNE.map((nome, i) => [nome, i]));
const GIORNO = 24 * 60 * 60 * 1000;
const OGGETTO = 'Conferma il tuo indirizzo per ReCut';

function installa() {
  const proprieta = PropertiesService.getScriptProperties();
  if (!proprieta.getProperty('SEGRETO')) {
    proprieta.setProperty('SEGRETO', Utilities.getUuid() + Utilities.getUuid());
  }
  const foglio = prendiFoglio();
  if (foglio.getLastRow() === 0) {
    foglio.appendRow(COLONNE);
    foglio.setFrozenRows(1);
  }
  ScriptApp.getProjectTriggers()
    .filter((t) => t.getHandlerFunction() === 'pulizia')
    .forEach((t) => ScriptApp.deleteTrigger(t));
  ScriptApp.newTrigger('pulizia').timeBased().everyDays(1).atHour(3).create();
}

function doPost(e) {
  let dati;
  try {
    dati = JSON.parse(e.postData.contents);
  } catch (errore) {
    return risposta({ ok: false, errore: 'richiesta non valida' });
  }
  const segreto = PropertiesService.getScriptProperties().getProperty('SEGRETO');
  if (!segreto || dati.segreto !== segreto) return risposta({ ok: false, errore: 'non autorizzato' });

  const lucchetto = LockService.getScriptLock();
  lucchetto.waitLock(20000);
  try {
    if (dati.azione === 'iscrivi') return risposta(iscrivi(dati));
    if (dati.azione === 'conferma') return risposta(conferma(dati.id));
    if (dati.azione === 'revoca') return risposta(revoca(dati.id));
    return risposta({ ok: false, errore: 'azione sconosciuta' });
  } finally {
    lucchetto.releaseLock();
  }
}

function iscrivi(dati) {
  const foglio = prendiFoglio();
  const ora = new Date();
  const email = String(dati.email).toLowerCase();

  // Una sola mail di conferma al giorno per indirizzo: il modulo non deve
  // diventare un modo per tempestare di mail qualcun altro.
  const recente = righe(foglio).some((r) =>
    String(r.valori[C.email]).toLowerCase() === email &&
    ora - new Date(r.valori[C.creato_il]) < GIORNO);

  const riga = [];
  riga[C.id] = testo(dati.id);
  riga[C.creato_il] = ora;
  riga[C.nome] = testo(dati.nome);
  riga[C.cognome] = testo(dati.cognome);
  riga[C.email] = testo(email);
  riga[C.azienda] = testo(dati.azienda);
  riga[C.consenso_aggiornamenti] = dati.consenso_aggiornamenti === true;
  riga[C.consenso_invito_efn] = dati.consenso_invito_efn === true;
  riga[C.versione_informativa] = testo(dati.versione_informativa);
  riga[C.pagina] = '/scarica-recut';
  riga[C.user_agent] = testo(dati.user_agent);
  riga[C.mail_inviata_il] = '';
  riga[C.confermato_il] = '';
  riga[C.revocato_il] = '';
  foglio.appendRow(riga);

  if (!recente) {
    GmailApp.sendEmail(email, OGGETTO, dati.testo, { htmlBody: dati.html, name: 'ReCut di Echo' });
    foglio.getRange(foglio.getLastRow(), C.mail_inviata_il + 1).setValue(new Date());
  }
  return { ok: true };
}

function conferma(id) {
  const foglio = prendiFoglio();
  const r = trova(foglio, id);
  if (!r || r.valori[C.revocato_il]) return { ok: false, errore: 'scaduto' };
  if (!r.valori[C.confermato_il]) {
    if (new Date() - new Date(r.valori[C.creato_il]) > 30 * GIORNO) return { ok: false, errore: 'scaduto' };
    foglio.getRange(r.numero, C.confermato_il + 1).setValue(new Date());
  }
  return { ok: true };
}

function revoca(id) {
  const foglio = prendiFoglio();
  const r = trova(foglio, id);
  if (r && !r.valori[C.revocato_il]) foglio.getRange(r.numero, C.revocato_il + 1).setValue(new Date());
  return { ok: true };
}

// Cancella le richieste mai confermate dopo trenta giorni, come dice la privacy.
function pulizia() {
  const foglio = prendiFoglio();
  const ora = new Date();
  righe(foglio).reverse().forEach((r) => {
    if (!r.valori[C.confermato_il] && ora - new Date(r.valori[C.creato_il]) > 30 * GIORNO) {
      foglio.deleteRow(r.numero);
    }
  });
}

function prendiFoglio() {
  const file = SpreadsheetApp.getActiveSpreadsheet();
  return file.getSheetByName(FOGLIO) || file.insertSheet(FOGLIO);
}

function righe(foglio) {
  if (foglio.getLastRow() < 2) return [];
  return foglio.getRange(2, 1, foglio.getLastRow() - 1, COLONNE.length).getValues()
    .map((valori, i) => ({ numero: i + 2, valori }));
}

function trova(foglio, id) {
  return righe(foglio).find((r) => r.valori[C.id] === String(id)) || null;
}

// Un testo che comincia con = + - @ il foglio lo leggerebbe come formula:
// l'apostrofo davanti lo tiene testo.
function testo(valore) {
  const s = String(valore || '');
  return /^[=+\-@]/.test(s) ? "'" + s : s;
}

function risposta(oggetto) {
  return ContentService.createTextOutput(JSON.stringify(oggetto)).setMimeType(ContentService.MimeType.JSON);
}
