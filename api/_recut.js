// Pezzi in comune tra iscrizione-recut e conferma-recut.
// Il trattino basso davanti al nome dice a Vercel di non farne un indirizzo.

const crypto = require('crypto');

const SITO = 'https://www.echo.srl';
const RESEND_API = 'https://api.resend.com/emails';
const MITTENTE = process.env.RECUT_EMAIL_FROM || 'ReCut di Echo <network@echowebagency.it>';

// Query sul database di Universe tramite l'endpoint HTTP di Neon.
async function query(sql, params) {
  const connessione = process.env.RECUT_DATABASE_URL;
  if (!connessione) throw new Error('RECUT_DATABASE_URL non impostata');
  const host = new URL(connessione).hostname;
  const risposta = await fetch(`https://${host}/sql`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', 'Neon-Connection-String': connessione },
    body: JSON.stringify({ query: sql, params }),
  });
  if (!risposta.ok) throw new Error(`database ${risposta.status}: ${(await risposta.text()).slice(0, 300)}`);
  return (await risposta.json()).rows || [];
}

// Firma di un link: senza il segreto nessuno puo' fabbricare il link di un altro.
function firma(azione, id) {
  const segreto = process.env.RECUT_LINK_SECRET;
  if (!segreto) throw new Error('RECUT_LINK_SECRET non impostata');
  return crypto.createHmac('sha256', segreto).update(`${azione}:${id}`).digest('base64url');
}

function firmaValida(azione, id, data) {
  const attesa = Buffer.from(firma(azione, id));
  const ricevuta = Buffer.from(String(data || ''));
  return attesa.length === ricevuta.length && crypto.timingSafeEqual(attesa, ricevuta);
}

function link(azione, id) {
  return `${SITO}/conferma-recut?azione=${azione}&id=${id}&firma=${firma(azione, id)}`;
}

function escape(testo) {
  return String(testo).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

async function inviaConferma({ id, nome, email, aggiornamenti, invitoEfn }) {
  const chiave = process.env.RESEND_API_KEY;
  if (!chiave) throw new Error('RESEND_API_KEY non impostata');

  const scelte = [];
  if (aggiornamenti) scelte.push('le novit&agrave; di ReCut');
  if (invitoEfn) scelte.push('l&rsquo;invito a Echo Fashion Network');

  const html =
    '<div style="font-family:system-ui,sans-serif;max-width:520px;margin:auto;color:#111;line-height:1.5">' +
    `<p>Ciao ${escape(nome)},</p>` +
    `<p>qualcuno, speriamo tu, ha lasciato questo indirizzo sulla pagina di ReCut per ricevere ${scelte.join(' e ')}.</p>` +
    '<p>Se sei stata o stato tu, conferma qui. Senza conferma non ti scriviamo altro.</p>' +
    `<p style="margin:24px 0"><a href="${link('conferma', id)}" style="background:#111;color:#fff;padding:12px 22px;border-radius:999px;text-decoration:none;display:inline-block;font-weight:600">Confermo il mio indirizzo</a></p>` +
    '<p style="font-size:14px;color:#555">Non sei stato tu, o hai cambiato idea? Puoi ignorare questa mail: se non confermi entro trenta giorni cancelliamo la richiesta. ' +
    `Oppure <a href="${link('revoca', id)}">annullala subito</a>.</p>` +
    '<hr style="border:none;border-top:1px solid #eee;margin:24px 0"/>' +
    `<p style="font-size:12px;color:#888">Echo S.r.l. &middot; <a href="${SITO}/privacy#recut" style="color:#888">Come trattiamo i tuoi dati</a></p>` +
    '</div>';

  const risposta = await fetch(RESEND_API, {
    method: 'POST',
    headers: { Authorization: `Bearer ${chiave}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ from: MITTENTE, to: email, subject: 'Conferma il tuo indirizzo per ReCut', html }),
  });
  if (!risposta.ok) throw new Error(`Resend ${risposta.status}: ${(await risposta.text()).slice(0, 300)}`);
}

module.exports = { query, firma, firmaValida, inviaConferma };
