"""Configurable logging: structured JSON to stdout (for container runtime/Coolify) and optional file."""
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from config import settings


class JsonFormatter(logging.Formatter):
    """Emit one JSON object per log record to stdout for log aggregators and Coolify."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj = {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, default=str)


def setup_logging() -> None:
    """Configure root logger: stdout (JSON or text) and optional file when LOG_FILE is set."""
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    root = logging.getLogger()
    root.setLevel(level)
    root.handlers.clear()

    console = logging.StreamHandler(sys.stdout)
    console.setLevel(level)
    if getattr(settings, "LOG_FORMAT", "json").lower() == "json":
        console.setFormatter(JsonFormatter())
    else:
        console.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    root.addHandler(console)

    if settings.LOG_FILE and settings.LOG_FILE.strip():
        log_path = Path(settings.LOG_FILE)
        if not log_path.is_absolute():
            log_path = Path(__file__).resolve().parent / log_path
        try:
            log_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError:
            fallback = Path(__file__).resolve().parent / "logs" / (log_path.name or "backend.log")
            try:
                fallback.parent.mkdir(parents=True, exist_ok=True)
            except OSError:
                fallback = Path("/tmp") / "tutor_backend.log"
            log_path = fallback
        try:
            fh = logging.FileHandler(log_path, encoding="utf-8")
            fh.setLevel(level)
            fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"))
            root.addHandler(fh)
        except OSError:
            pass


def get_logger(name: str) -> logging.Logger:
    """Return a logger for the given module/name."""
    return logging.getLogger(name)
