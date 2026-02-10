# Database migrations (Alembic)

Schema is managed by **Alembic**. The app does not create tables at startup.

**Docker:** The backend container runs `alembic upgrade head` on startup (see `scripts/docker-entrypoint.sh`), so tables are created when the container starts. View logs with: `docker compose logs -f backend`.

## Fresh setup (empty DB)

From the **backend** directory (with `.env` or `DB_*` set). Ensure the venv has deps: `pip install -r requirements.txt`. Then use `alembic` or `python -m alembic`:

```bash
cd backend
source .venv/bin/activate   # if using venv
pip install -r requirements.txt   # if alembic not found
alembic upgrade head
# or: python -m alembic upgrade head
```

Then run the seed for default tenant + sample content:

```bash
DB_HOST=localhost python -m scripts.seed_content
```

## Incremental changes (new migration)

1. Change the SQLModel classes in `models/content.py` (or add new ones).
2. Generate a migration:
   ```bash
   cd backend
   alembic revision --autogenerate -m "add_foo_column"
   ```
3. Review the new file under `alembic/versions/` and fix if needed.
4. Apply:
   ```bash
   alembic upgrade head
   ```

## Commands

| Command | Purpose |
|--------|--------|
| `alembic upgrade head` | Apply all pending migrations (fresh or incremental). |
| `alembic revision --autogenerate -m "message"` | Create a new migration from model diff. |
| `alembic downgrade -1` | Roll back one revision. |
| `alembic current` | Show current revision. |
| `alembic history` | List revisions. |

## Test that migrations run (after a schema change)

A small change was added so you can confirm the flow: **Book.updated_at** (optional column) and migration **002_add_book_updated_at**.

**1. See current revision (before applying):**
```bash
cd backend
alembic current
```
Example: `001_initial` (or empty if no DB yet).

**2. Apply pending migrations:**
```bash
alembic upgrade head
```
You should see: `Running upgrade 001_initial -> 002_updated_at, Add books.updated_at`.

**3. Confirm:**
```bash
alembic current
```
Should show: `002_updated_at`. In the DB, table `books` now has an `updated_at` column (nullable).

**4. (Optional) Roll back one step:**
```bash
alembic downgrade -1
```
Then `alembic current` shows `001_initial` again. Re-apply with `alembic upgrade head`.

**With Docker:** Rebuild and start the backend; the entrypoint runs `alembic upgrade head`, so 002 will apply on startup if the DB was already at 001.

## Environment

Alembic uses the same config as the app: **`.env`** (or `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`). Run from `backend/` so `config` and `models` resolve.

**If your `.env` has `DB_HOST=host.docker.internal`** (for Docker containers), that hostname does not resolve when you run Alembic **on your Mac**. Override it:

```bash
DB_HOST=localhost alembic current
DB_HOST=localhost alembic upgrade head
```
