"""In-memory context backend used as the final fallback."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from typing import Any, Dict, List, Optional


class MemoryContextManager:
    """Simple in-process storage for conversation state."""

    def __init__(self) -> None:
        self._conversation_contexts: Dict[str, Dict[str, Any]] = {}
        self._dialog_histories: Dict[str, List[Dict[str, Any]]] = {}
        self._learning_progress: Dict[str, Dict[str, Any]] = {}

    def save_conversation_context(self, user_id: str, context: Dict[str, Any]) -> bool:
        existing = self._conversation_contexts.get(user_id, {})
        merged = {**existing, **deepcopy(context)}
        merged["last_updated"] = datetime.now().isoformat()
        self._conversation_contexts[user_id] = merged
        return True

    def get_conversation_context(self, user_id: str) -> Optional[Dict[str, Any]]:
        context = self._conversation_contexts.get(user_id)
        return deepcopy(context) if context is not None else None

    def save_dialog_history(self, user_id: str, dialog: Dict[str, Any]) -> bool:
        history = self._dialog_histories.setdefault(user_id, [])
        item = deepcopy(dialog)
        item.setdefault("timestamp", datetime.now().isoformat())
        history.append(item)
        self._dialog_histories[user_id] = history[-100:]
        return True

    def get_dialog_history(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        history = self._dialog_histories.get(user_id, [])
        return deepcopy(history[-limit:])

    def save_learning_progress(self, user_id: str, progress: Dict[str, Any]) -> bool:
        existing = self._learning_progress.get(user_id, {})
        merged = {**existing, **deepcopy(progress)}
        merged["last_updated"] = datetime.now().isoformat()
        self._learning_progress[user_id] = merged
        return True

    def get_learning_progress(self, user_id: str) -> Optional[Dict[str, Any]]:
        progress = self._learning_progress.get(user_id)
        return deepcopy(progress) if progress is not None else None

    def clear_user_data(self, user_id: str) -> bool:
        self._conversation_contexts.pop(user_id, None)
        self._dialog_histories.pop(user_id, None)
        self._learning_progress.pop(user_id, None)
        return True
