"""Structured logs for handoffs between agents."""

from __future__ import annotations

import json
import logging
import os
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

LOGGER_NAME = "agent.interaction"
_CONFIGURED = False


def _default_log_path() -> Path:
    project_root = Path(__file__).resolve().parents[3]
    return project_root / "server" / "runtime" / "agent_interactions.log"


def configure_agent_interaction_logging() -> logging.Logger:
    """Configure a JSONL interaction log file once and return the logger."""
    global _CONFIGURED
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(logging.INFO)
    logger.propagate = True
    if _CONFIGURED:
        return logger

    log_path = Path(os.getenv("AGENT_INTERACTION_LOG_FILE", str(_default_log_path())))
    log_path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(
        log_path,
        maxBytes=int(os.getenv("AGENT_INTERACTION_LOG_MAX_BYTES", str(5 * 1024 * 1024))),
        backupCount=int(os.getenv("AGENT_INTERACTION_LOG_BACKUPS", "3")),
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    _CONFIGURED = True
    logger.info(
        json.dumps(
            {
                "event": "agent_log_configured",
                "log_file": str(log_path),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            },
            ensure_ascii=False,
        )
    )
    return logger


def summarize_for_log(value: Any, max_text: int = 500, max_items: int = 8, depth: int = 3) -> Any:
    """Make payloads readable without dumping whole chat histories or code blobs."""
    if depth <= 0:
        if isinstance(value, (dict, list, tuple)):
            return f"<{type(value).__name__}>"
        return _summarize_scalar(value, max_text)
    if isinstance(value, dict):
        result: Dict[str, Any] = {}
        for index, (key, item) in enumerate(value.items()):
            if index >= max_items:
                result["..."] = f"{len(value) - max_items} more"
                break
            key_text = str(key)
            if _looks_sensitive(key_text):
                result[key_text] = "<redacted>"
            else:
                result[key_text] = summarize_for_log(item, max_text, max_items, depth - 1)
        return result
    if isinstance(value, (list, tuple)):
        items = [summarize_for_log(item, max_text, max_items, depth - 1) for item in value[:max_items]]
        if len(value) > max_items:
            items.append(f"... {len(value) - max_items} more")
        return items
    return _summarize_scalar(value, max_text)


def log_agent_interaction(
    event: str,
    source: str,
    target: str | None = None,
    request_id: str | None = None,
    user_id: str | None = None,
    payload: Dict[str, Any] | None = None,
) -> None:
    """Write one structured JSONL event for an agent handoff or decision."""
    logger = configure_agent_interaction_logging()
    record = {
        "event": event,
        "source": source,
        "target": target,
        "request_id": request_id,
        "user_id": user_id,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "payload": summarize_for_log(payload or {}),
    }
    logger.info(json.dumps(record, ensure_ascii=False, default=str))


def _summarize_scalar(value: Any, max_text: int) -> Any:
    if isinstance(value, str):
        text = value.replace("\r\n", "\n").strip()
        return text[:max_text] + ("..." if len(text) > max_text else "")
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:max_text]


def _looks_sensitive(key: str) -> bool:
    lowered = key.lower()
    return any(token in lowered for token in ["password", "token", "secret", "api_key", "authorization"])
