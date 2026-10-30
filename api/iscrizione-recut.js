// Riceve il modulo di /scarica-recut, scrive una riga in iscrizioni_recut
// (database di Universe, Neon) e manda la mail per confermare l'indirizzo.
// Nessuna dipendenza da installare: Neon e Resend si chiamano via HTTP.

const { query, inviaConferma } = require('./_recut');

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

  if (!process.env.RECUT_DATABASE_URL || !process.env.RESEND_API_KEY || !process.env.RECUT_LINK_SECRET) {
    console.error('iscrizione-recut: manca RECUT_DATABASE_URL, RESEND_API_KEY o RECUT_LINK_SECRET');
    return res.status(503).json({ ok: false });
  }

  try {
    // Una sola mail di conferma al giorno per indirizzo: il modulo e' pubblico
    // e non deve diventare un modo per tempestare di mail qualcun altro.
    const recenti = await query(
      `SELECT 1 FROM iscrizioni_recut
        WHERE lower(email) = $1 AND creato_il > now() - interval '1 day' LIMIT 1`,
      [email],
    );

    const righe = await query(
      `INSERT INTO iscrizioni_recut
         (nome, cognome, email, azienda, consenso_aggiornamenti, consenso_invito_efn,
          versione_informativa, user_agent)
       VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
       RETURNING id`,
      [nome, cognome, email, azienda, aggiornamenti, invitoEfn,
       VERSIONE_INFORMATIVA, pulisci(req.headers['user-agent'], 300)],
    );

    if (recenti.length === 0) {
      await inviaConferma({ id: righe[0].id, nome, email, aggiornamenti, invitoEfn });
    }
    return res.status(200).json({ ok: true });
  } catch (errore) {
    console.error('iscrizione-recut:', errore.message);
    return res.status(502).json({ ok: false });
  }
};
