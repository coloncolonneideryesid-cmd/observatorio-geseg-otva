-- OTVA v1 · migración 0002: ciclo de vida de los casos (quién hizo qué y cuándo) y registro de exportaciones.
-- Las acciones NO entran al hash de la versión (la versión solo guarda datos); quedan ancladas en audit_log (encadenado).
CREATE TABLE event_action (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  event_id TEXT NOT NULL REFERENCES event(event_id),
  version INTEGER NOT NULL,
  ts TEXT NOT NULL,
  usuario TEXT NOT NULL,
  rol TEXT NOT NULL,
  accion TEXT NOT NULL,            -- crear | editar | transicion | sincronizar
  estado_de TEXT,
  estado_a TEXT,
  nota TEXT
);
CREATE INDEX event_action_evento ON event_action(event_id, id);
CREATE TABLE export_log (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts TEXT NOT NULL, usuario TEXT NOT NULL, ruta TEXT NOT NULL, sha256 TEXT NOT NULL, n_eventos INTEGER NOT NULL
);
CREATE TRIGGER event_action_no_update BEFORE UPDATE ON event_action BEGIN SELECT RAISE(ABORT,'event_action es de solo adición'); END;
CREATE TRIGGER event_action_no_delete BEFORE DELETE ON event_action BEGIN SELECT RAISE(ABORT,'event_action es de solo adición'); END;
