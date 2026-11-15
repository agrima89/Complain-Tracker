-- Baseline for Netlify Database. The app creates and migrates its own tables at startup
-- (see netlify/functions/utils/db.mjs, CREATE TABLE IF NOT EXISTS), so this only records the baseline.
CREATE TABLE IF NOT EXISTS app_meta (
  key TEXT PRIMARY KEY,
  value TEXT
);
