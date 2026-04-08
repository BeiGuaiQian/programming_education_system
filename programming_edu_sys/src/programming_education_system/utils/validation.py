"""Input validation and sanitization helpers."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, Tuple

from programming_education_system.config.llm_config import Config

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when a request fails validation."""


def validate_user_input(content: str, user_id: str) -> Tuple[bool, str]:
    """Validate user input content and identifier."""
    if len(content) > Config.MAX_INPUT_LENGTH:
        return False, f"输入内容过长，最大允许 {Config.MAX_INPUT_LENGTH} 个字符"

    if not content.strip():
        return False, "输入内容不能为空"

    if not re.match(Config.USER_ID_PATTERN, user_id):
        return False, f"用户 ID 格式无效，需匹配: {Config.USER_ID_PATTERN}"

    dangerous_patterns = [r"\.\./", r"<\s*script", r"javascript:", r"on\w+\s*="]
    for pattern in dangerous_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            logger.warning("Potentially unsafe content detected for user %s: %s", user_id, pattern)
            return False, "输入包含不安全内容"

    return True, ""


def sanitize_content(content: str) -> str:
    """Remove control characters and escape basic HTML characters."""
    if not content:
        return content

    sanitized = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", content)
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#39;",
        ">": "&gt;",
        "<": "&lt;",
    }
    for char, escape in html_escape_table.items():
        sanitized = sanitized.replace(char, escape)
    sanitized = re.sub(r"\n{4,}", "\n\n\n", sanitized)
    return sanitized.strip()


def validate_request_structure(request: Dict[str, Any]) -> Tuple[bool, str]:
    """Validate basic request structure."""
    required_fields = ["type", "content", "user_id"]
    for field in required_fields:
        if field not in request:
            return False, f"缺少必要字段: {field}"

    valid_types = ["qa", "exercise", "evaluation", "personal", "auto"]
    if request["type"] not in valid_types:
        return False, f"无效的请求类型: {request['type']}，有效类型: {valid_types}"

    if not isinstance(request["content"], str):
        return False, "content 字段必须是字符串"
    if not isinstance(request["user_id"], str):
        return False, "user_id 字段必须是字符串"

    return True, ""


def validate_user_id(user_id: str) -> bool:
    """Validate the user identifier pattern."""
    return bool(re.match(Config.USER_ID_PATTERN, user_id))


def get_safe_user_id(user_id: str) -> str:
    """Return a sanitized user identifier."""
    if validate_user_id(user_id):
        return user_id

    logger.warning("Invalid user_id detected: %s; using sanitized fallback.", user_id)
    safe_id = re.sub(r"[^a-zA-Z0-9_-]", "_", user_id)[:50]
    return safe_id or "anonymous_user"


def validate_and_sanitize_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Validate request structure and return a sanitized copy."""
    is_valid, error_msg = validate_request_structure(request)
    if not is_valid:
        raise ValidationError(error_msg)

    safe_user_id = get_safe_user_id(request["user_id"])
    is_valid, error_msg = validate_user_input(request["content"], safe_user_id)
    if not is_valid:
        raise ValidationError(error_msg)

    safe_request = request.copy()
    safe_request["user_id"] = safe_user_id
    safe_request["content"] = sanitize_content(request["content"])
    return safe_request
