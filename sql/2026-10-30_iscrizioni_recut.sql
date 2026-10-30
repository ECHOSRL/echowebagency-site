-- Iscrizioni dalla pagina www.echo.srl/scarica-recut
--
-- Una riga per ogni invio del modulo, mai aggiornata: e' la prova di cosa ha
-- accettato la persona, quando, e con quale testo davanti. I due consensi sono
-- separati perche' sono due scopi diversi (aggiornamenti ReCut, invito EFN).
-- Chi chiede di uscire si segna in revocato_il, la riga resta.
--
-- Da lanciare una volta sul database di Universe, da un utente proprietario.

BEGIN;

CREATE TABLE IF NOT EXISTS iscrizioni_recut (
  id                     BIGSERIAL PRIMARY KEY,
  nome                   TEXT NOT NULL,
  cognome                TEXT NOT NULL DEFAULT '',
  email                  TEXT NOT NULL,
  azienda                TEXT NOT NULL DEFAULT '',
  consenso_aggiornamenti BOOLEAN NOT NULL DEFAULT false,
  consenso_invito_efn    BOOLEAN NOT NULL DEFAULT false,
  versione_informativa   TEXT NOT NULL,
  pagina                 TEXT NOT NULL DEFAULT '/scarica-recut',
  user_agent             TEXT NOT NULL DEFAULT '',
  creato_il              TIMESTAMPTZ NOT NULL DEFAULT now(),
  revocato_il            TIMESTAMPTZ,
  CONSTRAINT almeno_un_consenso CHECK (consenso_aggiornamenti OR consenso_invito_efn)
);

CREATE INDEX IF NOT EXISTS idx_iscrizioni_recut_email ON iscrizioni_recut (lower(email));

-- Utente che usa il sito: puo' solo aggiungere righe, non leggerle ne' cambiarle.
-- La password la sceglie Silvia al posto di CAMBIAMI, e la stessa va nella
-- variabile RECUT_DATABASE_URL del progetto Vercel echowebagency-site.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sito_recut') THEN
    CREATE ROLE sito_recut LOGIN PASSWORD 'CAMBIAMI';
  END IF;
END $$;

GRANT USAGE ON SCHEMA public TO sito_recut;
GRANT INSERT ON iscrizioni_recut TO sito_recut;
GRANT USAGE ON SEQUENCE iscrizioni_recut_id_seq TO sito_recut;

COMMIT;
