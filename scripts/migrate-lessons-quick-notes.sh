#!/usr/bin/env bash
# Add lessons.subject, lessons.is_quick_note and make chapter_id nullable (Quick Concepts).
# Run from repo root: ./scripts/migrate-lessons-quick-notes.sh

set -e
docker compose exec tutor_db_local psql -U postgres -d tutor_app_db -c "
  ALTER TABLE lessons ADD COLUMN IF NOT EXISTS subject VARCHAR;
  ALTER TABLE lessons ADD COLUMN IF NOT EXISTS is_quick_note BOOLEAN DEFAULT false;
  ALTER TABLE lessons ALTER COLUMN chapter_id DROP NOT NULL;
"
echo "Done: lessons.subject, lessons.is_quick_note added; chapter_id nullable."
