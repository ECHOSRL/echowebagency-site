// Conferma o annulla un'iscrizione a ReCut dal link firmato nella mail.
// Risponde solo a POST: i programmi di posta aprono i link da soli per
// controllarli, e una semplice apertura non deve valere come conferma.
// La pagina /conferma-recut mostra il pulsante che manda questo POST.

const { configurato, chiamaScript, firmaValida } = require('./_recut');

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/;

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ ok: false });
  }
  if (!configurato()) {
    console.error('conferma-recut: manca RECUT_SCRIPT_URL o RECUT_SCRIPT_SECRET');
    return res.status(503).json({ ok: false });
  }

  const corpo = req.body || {};
  const azione = corpo.azione === 'revoca' ? 'revoca' : 'conferma';
  const id = String(corpo.id || '');
  if (!UUID.test(id) || !firmaValida(azione, id, corpo.firma)) {
    return res.status(400).json({ ok: false, errore: 'link non valido' });
  }

  try {
    // Il foglio rifiuta la conferma dopo trenta giorni o se e' gia' annullata.
    const esito = await chiamaScript(azione, { id });
    if (!esito.ok) return res.status(410).json({ ok: false, errore: 'scaduto' });
    return res.status(200).json({ ok: true, azione });
  } catch (errore) {
    console.error('conferma-recut:', errore.message);
    return res.status(502).json({ ok: false });
  }
};
