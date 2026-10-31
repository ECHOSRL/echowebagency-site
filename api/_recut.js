// Pezzi in comune tra iscrizione-recut e conferma-recut.
// Il trattino basso davanti al nome dice a Vercel di non farne un indirizzo.
//
// Le iscrizioni stanno nel foglio Google "Iscrizioni ReCut" del Drive di Echo.
// Lo scrive l'Apps Script in apps-script/iscrizioni-recut.gs, pubblicato come
// app web, che manda anche la mail di conferma da Gmail.

const crypto = require('crypto');

const SITO = 'https://www.echo.srl';

function configurato() {
  return Boolean(process.env.RECUT_SCRIPT_URL && process.env.RECUT_SCRIPT_SECRET);
}

async function chiamaScript(azione, dati) {
  const risposta = await fetch(process.env.RECUT_SCRIPT_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ ...dati, azione, segreto: process.env.RECUT_SCRIPT_SECRET }),
    redirect: 'follow',
  });
  if (!risposta.ok) throw new Error(`foglio ${risposta.status}: ${(await risposta.text()).slice(0, 300)}`);
  const esito = await risposta.json();
  if (!esito.ok && esito.errore !== 'scaduto') throw new Error(`foglio: ${esito.errore}`);
  return esito;
}

// Firma di un link: senza il segreto nessuno puo' fabbricare il link di un altro.
// La chiave e' ricavata dal segreto dello script, cosi' basta una variabile sola.
function firma(azione, id) {
  const chiave = crypto.createHmac('sha256', process.env.RECUT_SCRIPT_SECRET).update('firma-link-recut').digest();
  return crypto.createHmac('sha256', chiave).update(`${azione}:${id}`).digest('base64url');
}

function firmaValida(azione, id, data) {
  const attesa = Buffer.from(firma(azione, id));
  const ricevuta = Buffer.from(String(data || ''));
  return attesa.length === ricevuta.length && crypto.timingSafeEqual(attesa, ricevuta);
}

function link(azione, id) {
  return `${SITO}/conferma-recut?azione=${azione}&amp;id=${id}&amp;firma=${firma(azione, id)}`;
}

function escape(testo) {
  return String(testo).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

// Testo della mail di conferma, in HTML e in testo semplice.
function mailConferma({ id, nome, aggiornamenti, invitoEfn }) {
  const scelte = [];
  if (aggiornamenti) scelte.push('le novità di ReCut');
  if (invitoEfn) scelte.push('l’invito a Echo Fashion Network');
  const cosa = scelte.join(' e ');
  const confermaUrl = link('conferma', id);
  const revocaUrl = link('revoca', id);

  const html =
    '<div style="font-family:system-ui,sans-serif;max-width:520px;margin:auto;color:#111;line-height:1.5">' +
    `<p>Ciao ${escape(nome)},</p>` +
    `<p>qualcuno, speriamo tu, ha lasciato questo indirizzo sulla pagina di ReCut per ricevere ${escape(cosa)}.</p>` +
    '<p>Se sei stata o stato tu, conferma qui. Senza conferma non ti scriviamo altro.</p>' +
    `<p style="margin:24px 0"><a href="${confermaUrl}" style="background:#111;color:#fff;padding:12px 22px;border-radius:999px;text-decoration:none;display:inline-block;font-weight:600">Confermo il mio indirizzo</a></p>` +
    '<p style="font-size:14px;color:#555">Non sei stato tu, o hai cambiato idea? Puoi ignorare questa mail: se non confermi entro trenta giorni cancelliamo la richiesta. ' +
    `Oppure <a href="${revocaUrl}">annullala subito</a>.</p>` +
    '<hr style="border:none;border-top:1px solid #eee;margin:24px 0"/>' +
    `<p style="font-size:12px;color:#888">Echo S.r.l. &middot; <a href="${SITO}/privacy#recut" style="color:#888">Come trattiamo i tuoi dati</a></p>` +
    '</div>';

  const testo =
    `Ciao ${nome},\n\n` +
    `qualcuno, speriamo tu, ha lasciato questo indirizzo sulla pagina di ReCut per ricevere ${cosa}.\n\n` +
    `Se sei stata o stato tu, conferma qui:\n${confermaUrl.replace(/&amp;/g, '&')}\n\n` +
    'Senza conferma non ti scriviamo altro. Se non confermi entro trenta giorni cancelliamo la richiesta.\n' +
    `Per annullarla subito: ${revocaUrl.replace(/&amp;/g, '&')}\n\n` +
    `Echo S.r.l. · ${SITO}/privacy#recut\n`;

  return { html, testo };
}

module.exports = { configurato, chiamaScript, firmaValida, mailConferma };
