# Backend Code Guide for Java Developers

This guide walks through the Python/FastAPI backend **file by file**, mapping each concept to Java/Spring equivalents.

---

## File 1: `config.py` — Configuration (like application.properties + @ConfigurationProperties)

### What it does
- Loads all app and DB settings from environment variables or a `.env` file.
- Exposes a single **singleton** `settings` object used everywhere (e.g. `from config import settings`).

### Java mapping

| Python | Java / Spring |
|--------|----------------|
| `pydantic_settings.BaseSettings` | `@ConfigurationProperties` class (or `application.yml` + a `@Configuration` bean) |
| `Settings` class with `APP_NAME: str = "..."` | A `@ConfigurationProperties(prefix = "...")` class with fields and defaults |
| `model_config = SettingsConfigDict(env_file=...)` | Loading from `application.properties` / `.env`; `env_file` ≈ externalized config source |
| `settings = Settings()` at module load | A single `@Bean` or static holder like `ApplicationConfig.getInstance()` |
| `@property def database_url(self)` | A getter that computes a value from other config (e.g. building JDBC URL from host/port/user) |
| `str \| None` | `String` or `Optional<String>` / `@Nullable String` |

### Syntax / concepts

1. **Class with type hints and defaults**
   ```python
   APP_NAME: str = "Tutor App (NCERT Tracker)"
   DB_PORT: int = 5432
   ```
   Like a Java class with fields and default values (or defaults in `application.yml`).

2. **`model_config`**
   - Special attribute used by **Pydantic** (the library behind `BaseSettings`).
   - Roughly like annotations that tell the framework how to load and validate (e.g. which `.env` file, ignore extra keys).

3. **`@property`**
   ```python
   @property
   def database_url(self) -> str:
   ```
   - A getter that you call as `settings.database_url` (no `()`).
   - In Java: a getter method `getDatabaseUrl()` or a computed field.

4. **`Path(__file__).resolve().parent.parent`**
   - `__file__` = path of the current file (like `this.getClass().getResource(".")`).
   - `.parent` = parent directory; `.parent.parent` = repo root.
   - Used to point to the monorepo `.env` file.

5. **Single instance at bottom**
   ```python
   settings = Settings()
   ```
   - When any module does `from config import settings`, Python loads `config.py` once and reuses this instance.
   - Same idea as a singleton or a single `@ConfigurationProperties` bean injected everywhere.

### Flow in one line
**config.py** = “Load env/.env into a `Settings` object; expose `settings` and computed URLs (async vs sync) for the rest of the app.”

---

*Next: **File 2 — `main.py`** (app entry point, lifespan, middleware).*
