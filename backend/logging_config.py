"""Configurable file + console logging. Load from config (LOG_LEVEL, LOG_FILE)."""
import logging
import sys
from pathlib import Path

from config import settings


def setup_logging() -> None:
    """Configure root logger: console and optional file (when LOG_FILE is set)."""
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    fmt = "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    root = logging.getLogger()
    root.setLevel(level)
    # Avoid duplicate handlers when reloading
    root.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    console.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
    root.addHandler(console)

    if settings.LOG_FILE and settings.LOG_FILE.strip():
        log_path = Path(settings.LOG_FILE)
        if not log_path.is_absolute():
            log_path = Path(__file__).resolve().parent / log_path
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Host path in Docker or permission denied: use /app/logs (Dockerfile creates it) or /tmp.
            fallback = Path(__file__).resolve().parent / "logs" / (log_path.name or "backend.log")
            try:
                fallback.parent.mkdir(parents=True, exist_ok=True)
            except OSError:
                fallback = Path("/tmp") / "tutor_backend.log"
            log_path = fallback
        try:
            fh = logging.FileHandler(log_path, encoding="utf-8")
            fh.setLevel(level)
            fh.setFormatter(logging.Formatter(fmt, datefmt=date_fmt))
            root.addHandler(fh)
        except OSError:
            # Still unwritable; skip file logging, console only.
            pass


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module/name."""
    return logging.getLogger(name)
