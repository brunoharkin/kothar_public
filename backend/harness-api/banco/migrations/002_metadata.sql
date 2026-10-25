-- Migration 002: adicionar campos metadata e tokens específicos (PostgreSQL)
ALTER TABLE traces ADD COLUMN IF NOT EXISTS metadata JSONB DEFAULT '{}'::jsonb;
ALTER TABLE traces ADD COLUMN IF NOT EXISTS content TEXT;
ALTER TABLE traces ADD COLUMN IF NOT EXISTS event_type TEXT;
ALTER TABLE traces ADD COLUMN IF NOT EXISTS agent_name TEXT;
ALTER TABLE traces ADD COLUMN IF NOT EXISTS sequence INTEGER;
ALTER TABLE traces ADD COLUMN IF NOT EXISTS error_message TEXT;
