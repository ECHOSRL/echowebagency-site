// Riceve il modulo di /scarica-recut e lo passa al foglio Google delle
// iscrizioni, che salva la riga e manda la mail per confermare l'indirizzo.

const crypto = require('crypto');
const { configurato, chiamaScript, mailConferma } = require('./_recut');

const VERSIONE_INFORMATIVA = 'privacy-2026-10-30';
const EMAIL_VALIDA = /^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/;

function pulisci(valore, max) {
  return String(valore || '').replace(/\s+/g, ' ').trim().slice(0, max);
}

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ ok: false });
  }

  const corpo = req.body || {};
  // Campo trappola: le persone non lo vedono, i programmi automatici lo riempiono.
  if (corpo.sito) return res.status(200).json({ ok: true });

  const nome = pulisci(corpo.nome, 80);
  const cognome = pulisci(corpo.cognome, 80);
  const email = pulisci(corpo.email, 200).toLowerCase();
  const azienda = pulisci(corpo.azienda, 120);
  const aggiornamenti = corpo.consenso_aggiornamenti === true;
  const invitoEfn = corpo.consenso_invito_efn === true;

  if (!aggiornamenti && !invitoEfn) {
    return res.status(400).json({ ok: false, errore: 'nessun consenso' });
  }
  if (!nome || !EMAIL_VALIDA.test(email)) {
    return res.status(400).json({ ok: false, errore: 'nome o email mancanti' });
  }

  if (!configurato()) {
    console.error('iscrizione-recut: manca RECUT_SCRIPT_URL, RECUT_SCRIPT_SECRET o RECUT_LINK_SECRET');
    return res.status(503).json({ ok: false });
  }

  try {
    const id = crypto.randomUUID();
    await chiamaScript('iscrivi', {
      id, nome, cognome, email, azienda,
      consenso_aggiornamenti: aggiornamenti,
      consenso_invito_efn: invitoEfn,
      versione_informativa: VERSIONE_INFORMATIVA,
      user_agent: pulisci(req.headers['user-agent'], 300),
      ...mailConferma({ id, nome, aggiornamenti, invitoEfn }),
    });
    return res.status(200).json({ ok: true });
  } catch (errore) {
    console.error('iscrizione-recut:', errore.message);
    return res.status(502).json({ ok: false });
  }
};
