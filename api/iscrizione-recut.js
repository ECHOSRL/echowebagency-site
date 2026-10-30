// Riceve il modulo di /scarica-recut e scrive una riga in iscrizioni_recut
// (database di Universe, Neon) con l'utente sito_recut, che puo' solo inserire.
// Usa l'endpoint HTTP di Neon: nessuna dipendenza da installare.

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

  const connessione = process.env.RECUT_DATABASE_URL;
  if (!connessione) {
    console.error('iscrizione-recut: RECUT_DATABASE_URL non impostata');
    return res.status(503).json({ ok: false });
  }

  try {
    const host = new URL(connessione).hostname;
    const risposta = await fetch(`https://${host}/sql`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'Neon-Connection-String': connessione },
      body: JSON.stringify({
        query: `INSERT INTO iscrizioni_recut
                  (nome, cognome, email, azienda, consenso_aggiornamenti, consenso_invito_efn,
                   versione_informativa, user_agent)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)`,
        params: [nome, cognome, email, azienda, aggiornamenti, invitoEfn,
                 VERSIONE_INFORMATIVA, pulisci(req.headers['user-agent'], 300)],
      }),
    });
    if (!risposta.ok) {
      console.error('iscrizione-recut: database', risposta.status, await risposta.text());
      return res.status(502).json({ ok: false });
    }
    return res.status(200).json({ ok: true });
  } catch (errore) {
    console.error('iscrizione-recut:', errore);
    return res.status(502).json({ ok: false });
  }
};
