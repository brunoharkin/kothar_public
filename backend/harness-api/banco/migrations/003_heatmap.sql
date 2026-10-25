CREATE TABLE IF NOT EXISTS heatmaps (
  id SERIAL PRIMARY KEY,
  project_id TEXT NOT NULL,
  url TEXT NOT NULL,
  x INTEGER NOT NULL,
  y INTEGER NOT NULL,
  type TEXT NOT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS heatmaps_project_url_idx ON heatmaps(project_id, url);
