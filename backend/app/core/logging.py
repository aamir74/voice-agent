"""Structured (JSON) logging setup shared by the API and the agent worker.

Use `get_logger(__name__)` everywhere instead of the stdlib root logger so that
all output is consistently formatted and easy to grep/ship.
"""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

_CONFIGURED = False


class JsonFormatter(logging.Formatter):
    """Render log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        # Attach any structured "extra" fields the caller passed in.
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


# Standard LogRecord attributes we don't want to duplicate into the JSON payload.
_RESERVED = set(
    logging.LogRecord("", 0, "", 0, "", (), None).__dict__.keys()
) | {"message", "asctime"}


def configure_logging(level: int = logging.INFO) -> None:
    """Install the JSON handler on the root logger exactly once."""
    global _CONFIGURED
    if _CONFIGURED:
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)
    _CONFIGURED = True


class _StructuredLogger(logging.LoggerAdapter):
    """Logger that lets callers pass structured fields via `extra=` freely.

    stdlib logging forbids `extra` keys that collide with reserved LogRecord
    attributes (e.g. `filename`, `module`, `name`). This adapter renames any such
    key (prefixing it with `ctx_`) so logging structured context never crashes.
    """

    def process(self, msg, kwargs):
        extra = kwargs.get("extra")
        if extra:
            kwargs["extra"] = {
                (f"ctx_{k}" if k in _RESERVED else k): v for k, v in extra.items()
            }
        return msg, kwargs


def get_logger(name: str) -> _StructuredLogger:
    """Return a configured structured logger. Safe to call before configure_logging()."""
    configure_logging()
    return _StructuredLogger(logging.getLogger(name), {})
