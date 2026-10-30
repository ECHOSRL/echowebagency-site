-- Iscrizioni dalla pagina www.echo.srl/scarica-recut
--
-- Una riga per ogni invio del modulo: e' la prova di cosa ha accettato la
-- persona, quando, e con quale testo davanti. Dopo l'inserimento il sito
-- tocca solo confermato_il e revocato_il, nient'altro. I due consensi sono
-- separati perche' sono due scopi diversi (aggiornamenti ReCut, invito EFN).
-- Chi chiede di uscire si segna in revocato_il, la riga resta.
--
-- Il modulo e' pubblico: chiunque potrebbe scrivere l'indirizzo di un altro.
-- Per questo una riga NON e' ancora un consenso valido. Lo diventa solo con
-- confermato_il compilato, dopo che la persona ha risposto alla mail di
-- conferma. Prima di quella data a quell'indirizzo parte una mail sola: la
-- richiesta di conferma. Niente aggiornamenti, niente inviti EFN.
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
  confermato_il          TIMESTAMPTZ,
  revocato_il            TIMESTAMPTZ,
  CONSTRAINT almeno_un_consenso CHECK (consenso_aggiornamenti OR consenso_invito_efn)
);

CREATE INDEX IF NOT EXISTS idx_iscrizioni_recut_email ON iscrizioni_recut (lower(email));

-- Utente che usa il sito: aggiunge righe, legge solo le colonne che servono
-- a confermare (mai nome, azienda o consensi) e scrive solo le due date.
-- Nessuna password in questo file. Prima di lanciarlo, Silvia crea l'utente
-- sito_recut dalla console di Neon (Roles > New role): la password la genera
-- Neon, e l'indirizzo di connessione di quell'utente va nella variabile
-- RECUT_DATABASE_URL del progetto Vercel echowebagency-site.
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'sito_recut') THEN
    RAISE EXCEPTION 'Manca l''utente sito_recut: crealo prima dalla console di Neon.';
  END IF;
END $$;

GRANT USAGE ON SCHEMA public TO sito_recut;
GRANT INSERT ON iscrizioni_recut TO sito_recut;
GRANT SELECT (id, email, creato_il, confermato_il, revocato_il) ON iscrizioni_recut TO sito_recut;
GRANT UPDATE (confermato_il, revocato_il) ON iscrizioni_recut TO sito_recut;
GRANT USAGE ON SEQUENCE iscrizioni_recut_id_seq TO sito_recut;

COMMIT;

-- Pulizia delle richieste mai confermate, da lanciare ogni tanto (o da un
-- lavoro programmato di Universe) con un utente proprietario:
--
--   DELETE FROM iscrizioni_recut
--    WHERE confermato_il IS NULL AND creato_il < now() - interval '30 days';
