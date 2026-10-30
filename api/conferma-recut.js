// Conferma o annulla un'iscrizione a ReCut dal link firmato nella mail.
// Risponde solo a POST: i programmi di posta aprono i link da soli per
// controllarli, e una semplice apertura non deve valere come conferma.
// La pagina /conferma-recut mostra il pulsante che manda questo POST.

const { query, firmaValida } = require('./_recut');

module.exports = async (req, res) => {
  if (req.method !== 'POST') {
    res.setHeader('Allow', 'POST');
    return res.status(405).json({ ok: false });
  }

  const corpo = req.body || {};
  const azione = corpo.azione === 'revoca' ? 'revoca' : 'conferma';
  const id = String(corpo.id || '');
  if (!/^\d{1,18}$/.test(id) || !process.env.RECUT_LINK_SECRET || !firmaValida(azione, id, corpo.firma)) {
    return res.status(400).json({ ok: false, errore: 'link non valido' });
  }

  try {
    if (azione === 'conferma') {
      // Il link vale trenta giorni, poi la richiesta viene cancellata.
      const righe = await query(
        `UPDATE iscrizioni_recut SET confermato_il = COALESCE(confermato_il, now())
          WHERE id = $1 AND revocato_il IS NULL
            AND creato_il > now() - interval '30 days'
          RETURNING confermato_il`,
        [id],
      );
      if (righe.length === 0) return res.status(410).json({ ok: false, errore: 'scaduto' });
    } else {
      await query(
        `UPDATE iscrizioni_recut SET revocato_il = now()
          WHERE id = $1 AND revocato_il IS NULL`,
        [id],
      );
    }
    return res.status(200).json({ ok: true, azione });
  } catch (errore) {
    console.error('conferma-recut:', errore.message);
    return res.status(502).json({ ok: false });
  }
};
