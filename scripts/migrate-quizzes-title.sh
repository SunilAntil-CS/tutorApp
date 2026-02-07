#!/usr/bin/env bash
# Add quizzes.title column (for DBs created with old Quiz schema).
# Run from repo root: ./scripts/migrate-quizzes-title.sh
# Or: bash scripts/migrate-quizzes-title.sh

set -e
docker compose exec tutor_db_local psql -U postgres -d tutor_app_db -c "
  ALTER TABLE quizzes ADD COLUMN IF NOT EXISTS title VARCHAR(255) DEFAULT 'Quiz';
  UPDATE quizzes SET title = 'Quiz' WHERE title IS NULL;
"
echo "Done: quizzes.title column added/updated."
