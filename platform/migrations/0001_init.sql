-- OTVA v1 · migración 0001 (dialecto SQLite para el núcleo local de la Fase 1).
-- El DDL de PostgreSQL/PostGIS (Alembic) se deriva de este contrato cuando se decida el alojamiento (decisión A).
CREATE TABLE schema_migration (version TEXT PRIMARY KEY, applied_at TEXT NOT NULL);
CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);

CREATE TABLE event (
  event_id  TEXT PRIMARY KEY,
  legacy_id TEXT UNIQUE,
  seq       INTEGER NOT NULL            -- orden de la v0, para exportar idéntico
);

CREATE TABLE event_version (
  event_id TEXT NOT NULL REFERENCES event(event_id),
  version  INTEGER NOT NULL CHECK (version >= 1),
  status   TEXT NOT NULL CHECK (status IN ('CANDIDATO','PRELIMINAR','VERIFICADO_EQUIPO','VERIFICADO_INDEPENDIENTE','DESCARTADO','RETRACTADO')),
  event_type TEXT,                      -- NULL hasta mapeo revisado a mano (PENDIENTE)
  modus_raw  TEXT,
  t_start TEXT NOT NULL,
  t_precision TEXT NOT NULL CHECK (t_precision IN ('hora','día','semana','mes')),
  depto TEXT NOT NULL,
  mpio  TEXT NOT NULL,
  divipola_mpio TEXT,                   -- NULL hasta construir tabla DIVIPOLA (PENDIENTE)
  lat REAL, lon REAL,
  geo_precision TEXT NOT NULL CHECK (geo_precision IN ('exacta','vereda','centro_poblado','municipio','departamento')),
  reported_actor TEXT,
  actor_name TEXT,                      -- NULL = NO_ATRIBUIDO
  attribution_level TEXT NOT NULL CHECK (attribution_level IN ('A','B','C','D','E')),
  attribution_basis TEXT,
  casualties_civil_killed INTEGER CHECK (casualties_civil_killed IS NULL OR casualties_civil_killed >= 0),
  casualties_civil_injured INTEGER CHECK (casualties_civil_injured IS NULL OR casualties_civil_injured >= 0),
  casualties_public_force_killed INTEGER CHECK (casualties_public_force_killed IS NULL OR casualties_public_force_killed >= 0),
  casualties_public_force_injured INTEGER CHECK (casualties_public_force_injured IS NULL OR casualties_public_force_injured >= 0),
  kidnapped INTEGER CHECK (kidnapped IS NULL OR kidnapped >= 0),
  target_class TEXT,
  archive_status TEXT NOT NULL DEFAULT 'legacy_unarchived',
  claim_flags TEXT NOT NULL DEFAULT '[]',
  legacy_payload TEXT NOT NULL,         -- registro completo de la v0 (viaje de ida y vuelta)
  pipeline_version TEXT NOT NULL,
  prev_hash TEXT NOT NULL,
  row_hash  TEXT NOT NULL,
  PRIMARY KEY (event_id, version)
);

CREATE TABLE source_document (
  doc_id TEXT PRIMARY KEY,              -- SHA-256 de la URL canónica
  url TEXT NOT NULL,
  canonical_url TEXT NOT NULL,
  sha256 TEXT,                          -- hash del contenido capturado; NULL en históricos
  fetched_at TEXT,
  archive_status TEXT NOT NULL DEFAULT 'legacy_unarchived'
);

CREATE TABLE event_source (
  event_id TEXT NOT NULL, version INTEGER NOT NULL,
  doc_id TEXT NOT NULL REFERENCES source_document(doc_id),
  stance TEXT NOT NULL CHECK (stance IN ('supports','contradicts','context')),
  position INTEGER NOT NULL,
  PRIMARY KEY (event_id, version, doc_id),
  FOREIGN KEY (event_id, version) REFERENCES event_version(event_id, version)
);

CREATE TABLE excluded_record (seq INTEGER PRIMARY KEY, payload TEXT NOT NULL);
CREATE TABLE context_note   (seq INTEGER PRIMARY KEY, payload TEXT NOT NULL);

CREATE TABLE audit_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL,
  role TEXT NOT NULL,                   -- rol, no nombre de persona
  action TEXT NOT NULL,
  object TEXT NOT NULL,
  detail_hash TEXT NOT NULL,
  prev_hash TEXT NOT NULL,
  row_hash TEXT NOT NULL
);

-- Solo adición: se impide modificar o borrar historia y bitácora.
CREATE TRIGGER event_version_no_update BEFORE UPDATE ON event_version BEGIN SELECT RAISE(ABORT,'event_version es inmutable'); END;
CREATE TRIGGER event_version_no_delete BEFORE DELETE ON event_version BEGIN SELECT RAISE(ABORT,'event_version es inmutable'); END;
CREATE TRIGGER audit_log_no_update BEFORE UPDATE ON audit_log BEGIN SELECT RAISE(ABORT,'audit_log es de solo adición'); END;
CREATE TRIGGER audit_log_no_delete BEFORE DELETE ON audit_log BEGIN SELECT RAISE(ABORT,'audit_log es de solo adición'); END;
