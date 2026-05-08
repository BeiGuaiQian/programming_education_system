"""Canonical question shape shared by lessons, static questions, and agents."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Optional


CANONICAL_FIELDS = [
    "question_id",
    "source",
    "topic",
    "difficulty",
    "title",
    "description",
    "question_type",
    "starter_code",
    "expected_function",
    "hidden_tests",
    "hints",
    "answer",
    "examples",
    "tags",
    "estimated_minutes",
    "metadata",
]


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def _string(value: Any, default: str = "") -> str:
    if value is None:
        return default
    return str(value)


def normalize_question(
    raw_question: Dict[str, Any],
    *,
    source: Optional[str] = None,
    question_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Return a canonical question while keeping legacy keys for old callers.

    Canonical keys:
    question_id, source, topic, difficulty, title, description, question_type,
    starter_code, expected_function, hidden_tests, hints, answer, examples, tags.

    Legacy aliases such as id, content and type are intentionally preserved so
    existing pages and grading code keep working during the migration.
    """
    raw = deepcopy(raw_question or {})
    content = raw.get("content")
    content_payload = content if isinstance(content, dict) else {}
    metadata = raw.get("metadata") if isinstance(raw.get("metadata"), dict) else {}

    canonical_id = _string(
        question_id
        or raw.get("question_id")
        or raw.get("id")
        or metadata.get("question_id")
        or metadata.get("id"),
        "unknown-question",
    )
    canonical_source = _string(source or raw.get("source") or metadata.get("source"), "system")
    question_type = _string(
        raw.get("question_type")
        or raw.get("type")
        or content_payload.get("type")
        or metadata.get("question_type"),
        "coding",
    )
    title = _string(
        raw.get("title")
        or content_payload.get("title")
        or metadata.get("title"),
        f"{_string(raw.get('topic'), 'general')} 练习",
    )
    description = _string(
        raw.get("description")
        or content_payload.get("description")
        or (content if not isinstance(content, dict) else "")
        or raw.get("prompt"),
        "",
    )

    normalized = {
        **raw,
        "question_id": canonical_id,
        "source": canonical_source,
        "topic": _string(raw.get("topic") or metadata.get("topic"), "general"),
        "difficulty": _string(raw.get("difficulty") or metadata.get("difficulty"), "beginner"),
        "title": title,
        "description": description,
        "question_type": question_type,
        "starter_code": _string(
            raw.get("starter_code")
            or content_payload.get("starter_code")
            or metadata.get("starter_code"),
            "",
        ),
        "expected_function": _string(
            raw.get("expected_function")
            or content_payload.get("expected_function")
            or metadata.get("expected_function"),
            "",
        ),
        "hidden_tests": _as_list(
            raw.get("hidden_tests")
            or raw.get("test_cases")
            or content_payload.get("hidden_tests")
            or content_payload.get("test_cases")
            or metadata.get("hidden_tests")
        ),
        "hints": _as_list(raw.get("hints") or content_payload.get("hints") or metadata.get("hints")),
        "answer": _string(raw.get("answer") or content_payload.get("answer") or metadata.get("answer"), ""),
        "examples": _as_list(raw.get("examples") or content_payload.get("examples") or metadata.get("examples")),
        "tags": _as_list(raw.get("tags") or metadata.get("tags")),
        "estimated_minutes": int(raw.get("estimated_minutes") or metadata.get("estimated_minutes") or 10),
        "metadata": metadata,
    }

    # Legacy aliases used throughout current Web pages and older agents.
    normalized["id"] = raw.get("id") or canonical_id
    normalized["type"] = raw.get("type") or question_type
    normalized["content"] = raw.get("content") if not isinstance(raw.get("content"), dict) else description
    normalized["test_cases"] = normalized["hidden_tests"]
    normalized["content_payload"] = {
        "title": normalized["title"],
        "description": normalized["description"],
        "requirements": _as_list(raw.get("requirements") or content_payload.get("requirements")),
        "examples": normalized["examples"],
        "hints": normalized["hints"],
        "answer": normalized["answer"],
        "starter_code": normalized["starter_code"],
        "expected_function": normalized["expected_function"],
        "hidden_tests": normalized["hidden_tests"],
    }
    return normalized


def normalize_lesson(lesson: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize the embedded exercise of a lesson and preserve lesson fields."""
    normalized_lesson = deepcopy(lesson or {})
    exercise = normalized_lesson.get("exercise") or {}
    exercise_id = exercise.get("id") or normalized_lesson.get("id")
    exercise_payload = {
        **exercise,
        "topic": exercise.get("topic") or normalized_lesson.get("topic"),
        "difficulty": exercise.get("difficulty") or normalized_lesson.get("difficulty"),
        "source": "lesson",
    }
    normalized_exercise = normalize_question(
        exercise_payload,
        source="lesson",
        question_id=_string(exercise_id, "lesson-exercise"),
    )
    normalized_lesson["exercise"] = {
        **exercise,
        **normalized_exercise,
        "id": exercise_id,
        "requirements": _as_list(exercise.get("requirements")),
        "description": normalized_exercise["description"],
    }
    return normalized_lesson


def question_as_lesson(question: Dict[str, Any]) -> Dict[str, Any]:
    """Wrap any canonical/legacy question in the lesson shape used by graders."""
    normalized = normalize_question(question)
    return {
        "id": normalized["question_id"],
        "title": normalized["title"],
        "topic": normalized["topic"],
        "difficulty": normalized["difficulty"],
        "exercise": {
            "id": normalized["question_id"],
            "question_id": normalized["question_id"],
            "source": normalized["source"],
            "title": normalized["title"],
            "description": normalized["description"],
            "requirements": normalized["content_payload"].get("requirements", []),
            "starter_code": normalized["starter_code"],
            "expected_function": normalized["expected_function"],
            "hidden_tests": normalized["hidden_tests"],
            "hints": normalized["hints"],
            "answer": normalized["answer"],
            "examples": normalized["examples"],
        },
    }
