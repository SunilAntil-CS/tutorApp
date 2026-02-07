# Logging (Backend & Frontend)

## Backend (FastAPI)

- **Where:** Console (stdout) and, by default, **`backend/logs/backend.log`** (or a path you set).
- **What is logged:**
  - Startup/shutdown
  - Every HTTP request (method, path) and response (status, duration)
  - DB results from the service layer (e.g. `get_quick_notes -> N lessons`, `get_all_books -> N books`)

**Configuration (env or `.env`):**

| Variable   | Default              | Description |
|-----------|----------------------|-------------|
| `LOG_LEVEL` | `INFO`             | Log level: `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FILE`  | `logs/backend.log` | Log file path (relative to `backend/` or absolute). Set to empty string for console only. |

**When running in Docker:** Use a **relative** path (e.g. `logs/backend.log`). An absolute host path (e.g. `/Users/.../backend.log`) does not exist inside the container; the code will fall back to `backend/logs/backend.log` inside the container if creating the configured path fails.

Example `.env` (works locally and in Docker):

```env
LOG_LEVEL=DEBUG
LOG_FILE=logs/backend.log
```

Or console only:

```env
LOG_FILE=
```

---

## Frontend (Flutter)

- **Where:** Console (print) always; on **mobile/desktop** also a **log file** (configurable).
- **What is logged:**
  - Every API request (method, URL)
  - Every API response (status, short body preview, e.g. "5 items")
  - API errors (message)

**Configuration:**

- **Log file path (mobile/desktop only):**
  - Default: app documents directory, file `tutor_app_log.txt`.
  - Override with compile-time define:
    ```bash
    flutter run --dart-define=LOG_FILE=/path/to/app_log.txt
    ```
- **Web:** Only console; no file (browser cannot write to disk).

Example (Android with custom log path):

```bash
flutter run --dart-define=API_BASE_URL=http://192.168.1.2:8000 --dart-define=LOG_FILE=/sdcard/Download/tutor_app_log.txt
```
