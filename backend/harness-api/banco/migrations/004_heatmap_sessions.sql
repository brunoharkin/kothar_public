-- Add session_id to heatmaps table
ALTER TABLE heatmaps ADD COLUMN IF NOT EXISTS session_id TEXT;
-- Create an index for faster querying by session
CREATE INDEX IF NOT EXISTS heatmaps_session_idx ON heatmaps(session_id);
