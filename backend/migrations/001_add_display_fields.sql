-- Migration: Add display/fallback and AI config fields to cameras
-- Run with psql: psql "$DATABASE_URL" -f 001_add_display_fields.sql

BEGIN;

ALTER TABLE cameras ADD COLUMN display_interval_seconds integer DEFAULT 5;
ALTER TABLE cameras ADD COLUMN fallback_seconds integer DEFAULT 5;
ALTER TABLE cameras ADD COLUMN ai_processing_fps integer DEFAULT 3;
ALTER TABLE cameras ADD COLUMN monitoring_interval_minutes integer DEFAULT 5;
ALTER TABLE cameras ADD COLUMN ai_region_json text;
ALTER TABLE cameras ADD COLUMN patrol_region_json text;

ALTER TABLE cameras ALTER COLUMN display_interval_seconds SET NOT NULL;
ALTER TABLE cameras ALTER COLUMN fallback_seconds SET NOT NULL;
ALTER TABLE cameras ALTER COLUMN ai_processing_fps SET NOT NULL;
ALTER TABLE cameras ALTER COLUMN monitoring_interval_minutes SET NOT NULL;

COMMIT;

-- Verify:
-- SELECT column_name, data_type, column_default FROM information_schema.columns
--   WHERE table_name='cameras' AND column_name IN ('display_interval_seconds','fallback_seconds','ai_region_json','patrol_region_json');
