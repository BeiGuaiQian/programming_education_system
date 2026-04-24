"""FastAPI backend with persistent auth, refresh tokens, and chat history APIs."""

from __future__ import annotations

import asyncio
import os
import secrets
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.responses import FileResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
STATIC_DIR = Path(__file__).resolve().parent / "static"
RUNTIME_DIR = PROJECT_ROOT / "server" / "runtime"

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from programming_education_system.main_final import get_system
from server.ide.analyzer import analyze_code, build_submit_feedback, detect_stuck
from server.lesson_catalog import get_lesson, list_curriculum, list_lessons
from server.lesson_grader import analyze_lesson_code, format_structured_feedback, grade_lesson_submission, run_hidden_tests
from server.question_catalog import get_question, get_question_facets, list_questions
from server.store import AppStore


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=32)
    password: str = Field(min_length=6, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=16, max_length=256)


class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_at: str
    refresh_expires_at: str
    username: str


class AgentRequest(BaseModel):
    content: str = Field(min_length=1, max_length=5000)
    request_type: Literal["auto", "qa", "exercise", "evaluation", "personal"] = "auto"
    conversation_id: Optional[str] = None


class AgentResponse(BaseModel):
    success: bool
    request_type: str
    response: str
    details: dict
    suggestions: list
    user_id: str
    conversation_id: str


class LessonSubmissionRequest(BaseModel):
    lesson_id: str = Field(min_length=1, max_length=100)
    code: str = Field(min_length=1, max_length=12000)


class LearningSelectionAskRequest(BaseModel):
    lesson_id: str = Field(min_length=1, max_length=100)
    selected_text: str = Field(min_length=1, max_length=1200)
    question: str = Field(default="", max_length=1000)
    surrounding_context: Optional[str] = Field(default=None, max_length=2500)


class ProfileUpdateRequest(BaseModel):
    nickname: Optional[str] = Field(default=None, min_length=1, max_length=32)
    avatar_url: Optional[str] = Field(default=None, max_length=500)
    bio: Optional[str] = Field(default=None, max_length=160)


class LearningPreferencesUpdateRequest(BaseModel):
    learning_goal: Optional[str] = Field(default=None, max_length=120)
    learning_style: Optional[str] = Field(default=None, max_length=40)
    preferred_pace: Optional[str] = Field(default=None, max_length=20)


class LearningEventRequest(BaseModel):
    event_type: str = Field(min_length=1, max_length=80)
    target_type: str = Field(min_length=1, max_length=80)
    target_id: Optional[str] = Field(default=None, max_length=160)
    duration_seconds: Optional[float] = Field(default=None, ge=0, le=86400)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QuizGenerateRequest(BaseModel):
    topic: str = Field(default="auto", max_length=80)
    difficulty: str = Field(default="auto", max_length=40)
    count: int = Field(default=5, ge=1, le=10)
    requirement: str = Field(default="", max_length=500)


class QuestionSubmissionRequest(BaseModel):
    code: str = Field(min_length=1, max_length=12000)


class IDEAnalyzeRequest(BaseModel):
    code: str = Field(default="", max_length=12000)
    context_type: Literal["question", "lesson", "general"] = "general"
    target_id: Optional[str] = Field(default=None, max_length=120)
    expected_function: Optional[str] = Field(default="", max_length=120)
    requirements: List[str] = Field(default_factory=list, max_length=20)


class IDEStuckCheckRequest(BaseModel):
    code: str = Field(default="", max_length=12000)
    context_type: Literal["question", "lesson", "general"] = "general"
    target_id: Optional[str] = Field(default=None, max_length=120)
    duration_seconds: float = Field(default=0, ge=0, le=86400)
    submit_count: int = Field(default=0, ge=0, le=100)
    failed_submit_count: int = Field(default=0, ge=0, le=100)
    diagnostics: List[Dict[str, Any]] = Field(default_factory=list)


@dataclass
class SessionData:
    username: str
    access_token: str
    access_expires_at: str
    refresh_expires_at: str


APP_TITLE = "Programming Education System Backend"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("SERVER_TOKEN_EXPIRE_MINUTES", "120"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("SERVER_REFRESH_TOKEN_EXPIRE_DAYS", "14"))
DEFAULT_ADMIN_USERNAME = os.getenv("SERVER_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("SERVER_ADMIN_PASSWORD", "change_me_please")
APP_DB_PATH = os.getenv("SERVER_APP_DB", str(RUNTIME_DIR / "app.db"))
AGENT_CONCURRENCY = max(1, int(os.getenv("SERVER_AGENT_CONCURRENCY", "32")))
AGENT_QUEUE_TIMEOUT_SECONDS = max(1, int(os.getenv("SERVER_AGENT_QUEUE_TIMEOUT_SECONDS", "30")))

app = FastAPI(title=APP_TITLE, version="2.0.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
security = HTTPBearer(auto_error=False)
store = AppStore(APP_DB_PATH)
store.ensure_user(DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD)
agent_semaphore = asyncio.Semaphore(AGENT_CONCURRENCY)


def _unauthorized(message: str = "未认证或登录已过期") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=message,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _issue_tokens(username: str) -> AuthResponse:
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(48)
    now = datetime.now(timezone.utc)
    access_expires_at = (now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).isoformat()
    refresh_expires_at = (now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)).isoformat()
    await _run_store(
        store.create_session,
        username=username,
        access_token=access_token,
        refresh_token=refresh_token,
        access_expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at,
    )
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_at=access_expires_at,
        refresh_expires_at=refresh_expires_at,
        username=username,
    )


async def _session_from_credentials(
    credentials: HTTPAuthorizationCredentials | None,
) -> tuple[SessionData, str]:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise _unauthorized()

    access_token = credentials.credentials
    session = await _run_store(store.get_session_by_access_token, access_token)
    if session is None:
        raise _unauthorized()

    return (
        SessionData(
            username=str(session["username"]),
            access_token=access_token,
            access_expires_at=str(session["access_expires_at"]),
            refresh_expires_at=str(session["refresh_expires_at"]),
        ),
        access_token,
    )


async def get_current_session(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> SessionData:
    session, _ = await _session_from_credentials(credentials)
    return session


async def get_current_access_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    _, token = await _session_from_credentials(credentials)
    return token


def _ensure_conversation(username: str, conversation_id: str | None, content: str) -> str:
    if conversation_id:
        conversation = store.get_conversation(username, conversation_id)
        if conversation is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
        return conversation_id

    title = content.strip().replace("\n", " ")[:30] or "新对话"
    created = store.create_conversation(username, title)
    return str(created["id"])


def _is_generic_agent_fallback(response: str) -> bool:
    fallback_markers = [
        "目前无法调用大模型",
        "按系统内置逻辑继续处理",
        "fallback",
        "llm_unavailable",
    ]
    return not response.strip() or any(marker in response for marker in fallback_markers)


def _learning_style_label(value: str | None) -> str:
    return {
        "concept_first": "先讲概念，再看例子",
        "example_first": "先看例子，再反推概念",
        "practice_first": "边做边学",
        "debug_first": "通过纠错来学习",
    }.get(value or "", "暂未设置")


def _preferred_pace_label(value: str | None) -> str:
    return {
        "slow": "慢一点，拆细步骤",
        "normal": "正常节奏",
        "fast": "快节奏，直接抓重点",
    }.get(value or "", "暂未设置")


def _local_learning_explanation(
    selected_text: str,
    question: str,
    lesson: dict,
) -> str:
    """Provide a selection-specific explanation when the LLM fallback is too generic."""
    text = selected_text.strip()
    lowered = text.lower()
    lesson_title = str(lesson.get("title", "当前知识点"))

    explanations = [
        f"你选中的这段是：`{text}`。",
    ]

    if "return" in lowered:
        explanations.extend(
            [
                "`return` 的意思是把函数里的结果交还给调用它的地方。",
                "在这节“函数定义基础”里，它很关键，因为题目要求的是“返回字符串”，不是只在屏幕上显示。",
                "小例子：`result = greet('Alice')` 这一句里，`result` 能拿到函数 return 出来的值。",
            ]
        )
    elif "print" in lowered:
        explanations.extend(
            [
                "`print` 是把内容显示到屏幕上，主要方便人看。",
                "它和 `return` 不一样：`print` 显示了结果，但调用函数的代码通常拿不到这个结果。",
                "所以如果题目写“返回 Hello, Alice!”，答案里应该优先用 `return`。",
            ]
        )
    elif "def" in lowered:
        explanations.extend(
            [
                "`def` 是 Python 定义函数的关键字，可以理解为“我要开始写一个函数了”。",
                "它后面跟函数名、括号、参数和冒号，例如：`def greet(name):`。",
                "冒号下面缩进的代码，就是这个函数真正要执行的内容。",
            ]
        )
    elif "name" in lowered or "参数" in text:
        explanations.extend(
            [
                "`name` 在这里是参数，也就是函数从外面接收的一份数据。",
                "调用 `greet('Alice')` 时，`name` 临时代表 `Alice`；调用 `greet('Bob')` 时，它就代表 `Bob`。",
                "参数让同一个函数可以处理不同输入，而不是只能处理一个写死的值。",
            ]
        )
    elif "hello" in lowered or "f\"" in lowered or "f'" in lowered:
        explanations.extend(
            [
                "这段通常是在生成一个字符串，也就是最终要返回的问候语。",
                "如果写成 `f\"Hello, {name}!\"`，花括号里的 `name` 会被替换成真实传进来的名字。",
                "比如 `name` 是 `Alice`，结果就是 `Hello, Alice!`。",
            ]
        )
    elif "缩进" in text or "indent" in lowered:
        explanations.extend(
            [
                "Python 用缩进表示代码属于哪一块。",
                "在函数里，`def` 下一行开始缩进的内容都属于这个函数。",
                "如果缩进错了，Python 可能直接报语法错误，也可能让代码逻辑跑偏。",
            ]
        )
    else:
        explanations.extend(
            [
                f"这段内容属于“{lesson_title}”里的一个小概念。",
                "可以先把它放回当前学习目标里理解：我们正在学习如何把一段重复逻辑整理成函数。",
                "判断它的作用时，可以问三个问题：它是在定义函数、接收输入，还是返回结果？",
            ]
        )

    if question:
        explanations.append(f"结合你的问题“{question}”，建议先看它在代码里扮演的是“输入、处理、输出”中的哪一步。")

    return "\n".join(explanations)


def _build_learning_level(progress: Dict[str, Any], total_lessons: int) -> Dict[str, Any]:
    attempts = int(progress.get("total_attempts", 0))
    completed = int(progress.get("completed_lessons", 0))
    average_score = float(progress.get("average_best_score", 0.0))
    completion_rate = completed / total_lessons if total_lessons else 0.0

    if attempts == 0:
        level_name = "刚刚起步"
        level_score = 10
        description = "还没有学习记录。先完成第一道练习，系统就能开始理解你的学习情况。"
    elif completion_rate >= 0.9 and average_score >= 90:
        level_name = "熟练掌握"
        level_score = 90
        description = "当前知识点完成度和正确率都很好，可以尝试更综合的练习。"
    elif average_score >= 75 or completion_rate >= 0.5:
        level_name = "稳步提升"
        level_score = 68
        description = "已经有稳定练习记录，下一步适合补齐薄弱点并提高代码质量。"
    else:
        level_name = "基础建立中"
        level_score = 38
        description = "已经开始练习了，建议先把当前知识点中的核心题做通。"

    return {
        "name": level_name,
        "score": level_score,
        "description": description,
        "completion_rate": round(completion_rate * 100, 1),
        "average_score": average_score,
    }


def _build_learning_recommendations(
    progress: Dict[str, Any],
    lessons: List[Dict[str, Any]],
    behavior: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    progress_by_lesson = {
        item["lesson_id"]: item for item in progress.get("lessons", [])
    }
    recommendations: List[Dict[str, Any]] = []

    for lesson in lessons:
        lesson_id = lesson["id"]
        item = progress_by_lesson.get(lesson_id)
        if item is None:
            recommendations.append(
                {
                    "lesson_id": lesson_id,
                    "title": lesson["title"],
                    "reason": "你还没有开始这个知识点，适合作为下一步学习内容。",
                    "priority": "high",
                    "action": "开始学习",
                }
            )
        elif not item.get("passed"):
            recommendations.append(
                {
                    "lesson_id": lesson_id,
                    "title": lesson["title"],
                    "reason": "这个知识点已经尝试过，但还没有通过，建议回到讲解和示例再做一次。",
                    "priority": "high",
                    "action": "继续练习",
                }
            )
        elif float(item.get("best_score", 0.0)) < 90:
            recommendations.append(
                {
                    "lesson_id": lesson_id,
                    "title": lesson["title"],
                    "reason": "已经通过，但还有提升空间。可以重做一次，重点关注判题反馈里的风格建议。",
                    "priority": "medium",
                    "action": "巩固提升",
                }
            )

    for stuck in (behavior or {}).get("stuck_targets", []):
        if stuck.get("target_type") != "lesson":
            continue
        lesson = next((item for item in lessons if item["id"] == stuck.get("target_id")), None)
        if not lesson:
            continue
        recommendations.insert(
            0,
            {
                "lesson_id": lesson["id"],
                "title": lesson["title"],
                "reason": "你在这个知识点停留时间较长，系统判断这里可能值得回看示例或让智能体换一种说法讲。",
                "priority": "high",
                "action": "回到卡点",
            },
        )

    if not recommendations:
        recommendations.append(
            {
                "lesson_id": lessons[0]["id"] if lessons else "",
                "title": "综合复习",
                "reason": "当前已完成可用知识点。建议尝试让智能体生成变式题，检查是否真正掌握。",
                "priority": "medium",
                "action": "生成变式练习",
            }
        )

    return recommendations[:5]


def _difficulty_for_level(level: Dict[str, Any]) -> str:
    score = float(level.get("score", 10))
    if score >= 80:
        return "advanced"
    if score >= 55:
        return "intermediate"
    return "beginner"


def _topic_priority_from_progress(progress: Dict[str, Any]) -> List[str]:
    progress_by_lesson = {item["lesson_id"]: item for item in progress.get("lessons", [])}
    priorities: List[str] = []
    for lesson in list_lessons(language="python"):
        item = progress_by_lesson.get(lesson["id"])
        if item is None or not item.get("passed") or float(item.get("best_score", 0.0)) < 85:
            priorities.append(str(lesson.get("topic", "python_basics")))
    priorities.extend(["python_basics", "data_structures", "algorithms", "oop"])
    deduped: List[str] = []
    for topic in priorities:
        if topic not in deduped:
            deduped.append(topic)
    return deduped


def _personalize_questions(
    questions: List[Dict[str, Any]],
    progress: Dict[str, Any],
    level: Dict[str, Any],
    behavior: Optional[Dict[str, Any]] = None,
    limit: int = 8,
) -> List[Dict[str, Any]]:
    recommended_difficulty = _difficulty_for_level(level)
    topic_priority = _topic_priority_from_progress(progress)
    topic_rank = {topic: index for index, topic in enumerate(topic_priority)}
    stuck_question_ids = {
        str(item.get("target_id"))
        for item in (behavior or {}).get("stuck_targets", [])
        if item.get("target_type") == "question" and item.get("target_id")
    }

    def score(item: Dict[str, Any]) -> tuple:
        difficulty_score = 0 if item["difficulty"] == recommended_difficulty else 1
        stuck_score = -1 if item["id"] in stuck_question_ids else 0
        return (
            stuck_score,
            difficulty_score,
            topic_rank.get(item["topic"], 99),
            item.get("estimated_minutes", 10),
            item["id"],
        )

    ranked = sorted(questions, key=score)
    enriched = []
    for item in ranked[:limit]:
        reason_parts = []
        if item["difficulty"] == recommended_difficulty:
            reason_parts.append("难度匹配你当前学习水平")
        if item["topic"] in topic_priority[:2]:
            reason_parts.append("主题贴近你当前需要巩固的知识点")
        if item["id"] in stuck_question_ids:
            reason_parts.append("你最近在这道题停留较久，适合回头解决卡点")
        if not reason_parts:
            reason_parts.append("适合作为拓展练习")
        enriched.append(
            {
                **item,
                "recommend_reason": "，".join(reason_parts) + "。",
            }
        )
    return enriched


async def _build_question_bank_overview(username: str) -> Dict[str, Any]:
    progress = await _run_store(store.get_lesson_progress_summary, username)
    behavior = await _run_store(store.get_learning_behavior_summary, username)
    question_progress = await _run_store(store.get_question_progress_summary, username)
    lessons = list_lessons(language="python")
    level = _build_learning_level(progress, len(lessons))
    questions = list_questions()
    grouped_questions = _build_question_knowledge_groups(questions, question_progress, behavior)
    recommended = [
        _enrich_question_status(question, question_progress, behavior)
        for question in _personalize_questions(questions, progress, level, behavior=behavior, limit=6)
    ]
    return {
        "level": level,
        "stats": {
            "total_questions": len(questions),
            "completed_questions": int(question_progress.get("completed_questions", 0)),
            "question_attempts": int(question_progress.get("total_attempts", 0)),
            "recommended_difficulty": _difficulty_for_level(level),
            "topic_priority": _topic_priority_from_progress(progress),
            "total_study_minutes": round(float(behavior.get("total_duration_seconds", 0.0)) / 60, 1),
        },
        "facets": get_question_facets(),
        "recommended_questions": recommended,
        "knowledge_groups": grouped_questions,
        "question_progress": question_progress,
        "behavior": behavior,
    }


def _filter_questions_for_quiz(
    all_questions: List[Dict[str, Any]],
    topic: str,
    difficulty: str,
    requirement: str,
) -> List[Dict[str, Any]]:
    topic_value = None if topic in {"auto", "all", ""} else topic
    difficulty_value = None if difficulty in {"auto", "all", ""} else difficulty
    keyword = requirement.strip() or None
    filtered = list_questions(topic=topic_value, difficulty=difficulty_value, keyword=keyword)
    if filtered:
        return filtered

    filtered = all_questions
    if topic_value:
        filtered = [item for item in filtered if item["topic"] == topic_value] or filtered
    if difficulty_value:
        filtered = [item for item in filtered if item["difficulty"] == difficulty_value] or filtered
    return filtered


async def _generate_personalized_quiz(username: str, payload: QuizGenerateRequest) -> Dict[str, Any]:
    overview = await _build_question_bank_overview(username)
    progress = await _run_store(store.get_lesson_progress_summary, username)
    behavior = overview.get("behavior", {})
    level = overview["level"]
    all_questions = list_questions()
    topic = payload.topic
    difficulty = payload.difficulty
    if topic == "auto":
        topic = overview["stats"]["topic_priority"][0] if overview["stats"]["topic_priority"] else "python_basics"
    if difficulty == "auto":
        difficulty = overview["stats"]["recommended_difficulty"]

    candidates = _filter_questions_for_quiz(all_questions, topic, difficulty, payload.requirement)
    personalized = _personalize_questions(candidates, progress, level, behavior=behavior, limit=payload.count)
    if len(personalized) < payload.count:
        seen = {item["id"] for item in personalized}
        extra = [
            item
            for item in _personalize_questions(all_questions, progress, level, behavior=behavior, limit=20)
            if item["id"] not in seen
        ]
        personalized.extend(extra[: payload.count - len(personalized)])

    total_minutes = sum(int(item.get("estimated_minutes", 10)) for item in personalized)
    return {
        "title": "个性化小测",
        "topic": topic,
        "difficulty": difficulty,
        "requirement": payload.requirement,
        "estimated_minutes": total_minutes,
        "reason": (
            f"根据你的学习水平“{level['name']}”和当前进度，"
            f"本次小测优先选择 {topic} / {difficulty} 相关题目。"
        ),
        "questions": personalized,
    }


def _question_as_lesson(question: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": question["id"],
        "title": question["title"],
        "topic": question["topic"],
        "difficulty": question["difficulty"],
        "exercise": {
            "id": question["id"],
            "title": question["title"],
            "description": question["content"],
            "expected_function": question.get("expected_function", ""),
            "hidden_tests": question.get("hidden_tests", []),
        },
    }


def _lesson_expected_function(lesson: Dict[str, Any]) -> str:
    return str(lesson.get("exercise", {}).get("expected_function", ""))


def _lesson_requirements(lesson: Dict[str, Any]) -> List[str]:
    return [str(item) for item in lesson.get("exercise", {}).get("requirements", [])]


async def _grade_question_submission(
    code: str,
    question: Dict[str, Any],
) -> Dict[str, Any]:
    pseudo_lesson = _question_as_lesson(question)
    hidden_result = await run_hidden_tests(code, pseudo_lesson)
    structured = analyze_lesson_code(code, pseudo_lesson, hidden_result)
    ide_analysis = analyze_code(
        code,
        expected_function=str(question.get("expected_function", "")),
        requirements=[str(item) for item in question.get("hints", [])],
    )
    feedback = format_structured_feedback(structured)
    grading = {
        "passed": bool(hidden_result.get("passed", False)),
        "score": float(hidden_result.get("score", 0.0)),
        "feedback": feedback,
        "structured_feedback": structured,
        "test_result": hidden_result,
    }
    ide_feedback = build_submit_feedback(
        code,
        ide_analysis,
        grading,
        title=str(question.get("title", "当前题目")),
    )
    return {
        "passed": grading["passed"],
        "score": grading["score"],
        "feedback": feedback,
        "structured_feedback": structured,
        "test_result": hidden_result,
        "ide_analysis": ide_analysis,
        "ide_feedback": ide_feedback,
    }


SKILL_DIMENSIONS = [
    {
        "id": "environment",
        "name": "环境与工具",
        "chapters": {"environment-setup", "getting-started"},
        "topics": {"python_basics"},
        "description": "安装环境、运行脚本、读基础报错的能力。",
    },
    {
        "id": "syntax",
        "name": "语法基础",
        "chapters": {"basic-types"},
        "topics": {"python_basics"},
        "description": "变量、类型、运算符、字符串和基本表达式。",
    },
    {
        "id": "control_flow",
        "name": "流程控制",
        "chapters": {"control-flow"},
        "topics": {"python_basics", "algorithms"},
        "description": "条件判断、循环、计数、累计和分支整理。",
    },
    {
        "id": "collections",
        "name": "数据容器",
        "chapters": {"data-structures"},
        "topics": {"data_structures"},
        "description": "列表、字典、集合、遍历和基础数据整理。",
    },
    {
        "id": "functions",
        "name": "函数能力",
        "chapters": {"functions"},
        "topics": {"python_basics"},
        "description": "def、参数、return、作用域和函数式拆分。",
    },
    {
        "id": "files_errors",
        "name": "文件与调试",
        "chapters": {"modules-io-exceptions"},
        "topics": {"python_basics"},
        "description": "文件读写、模块、异常处理和调试意识。",
    },
    {
        "id": "oop",
        "name": "面向对象",
        "chapters": {"oop"},
        "topics": {"oop"},
        "description": "类、对象、属性、方法和 self。",
    },
]


def _completion_score(status: str, best_score: float, attempts: int) -> float:
    if status == "completed":
        return min(100.0, max(72.0, best_score))
    if status == "in_progress":
        return min(68.0, 28.0 + attempts * 8 + best_score * 0.25)
    return 0.0


def _build_curriculum_progress(
    progress: Dict[str, Any],
    behavior: Dict[str, Any],
) -> Dict[str, Any]:
    progress_by_lesson = {item["lesson_id"]: item for item in progress.get("lessons", [])}
    focus_map = {
        (str(item.get("target_type")), str(item.get("target_id"))): item
        for item in behavior.get("target_focus", [])
    }

    chapters = []
    total_sections = 0
    started_sections = 0
    completed_sections = 0
    ready_sections = 0

    for chapter in list_curriculum(language="python"):
        chapter_sections = []
        chapter_score_total = 0.0
        for section in chapter.get("sections", []):
            total_sections += 1
            lesson_id = section.get("lesson_id")
            matched = progress_by_lesson.get(str(lesson_id)) if lesson_id else None
            status_text = "planned"
            status_label = "待补内容"
            best_score = 0.0
            attempts = 0
            if lesson_id:
                ready_sections += 1
                if matched and matched.get("passed"):
                    status_text = "completed"
                    status_label = "已完成"
                    completed_sections += 1
                    started_sections += 1
                elif matched:
                    status_text = "in_progress"
                    status_label = "进行中"
                    started_sections += 1
                else:
                    status_text = "not_started"
                    status_label = "可学习"
                best_score = float(matched.get("best_score", 0.0)) if matched else 0.0
                attempts = int(matched.get("attempts", 0)) if matched else 0

            focus = focus_map.get(("lesson", str(lesson_id or section["id"])), {})
            duration_minutes = round(float(focus.get("duration_seconds", 0.0) or 0.0) / 60, 1)
            section_score = _completion_score(status_text, best_score, attempts)
            chapter_score_total += section_score
            chapter_sections.append(
                {
                    "id": section["id"],
                    "lesson_id": lesson_id,
                    "title": section["title"],
                    "summary": section["summary"],
                    "status": status_text,
                    "status_label": status_label,
                    "estimated_minutes": section.get("estimated_minutes", 0),
                    "attempts": attempts,
                    "best_score": best_score,
                    "duration_minutes": duration_minutes,
                    "score": round(section_score, 1),
                }
            )

        section_count = len(chapter_sections) or 1
        chapter_completed = sum(1 for item in chapter_sections if item["status"] == "completed")
        chapter_started = sum(1 for item in chapter_sections if item["status"] in {"completed", "in_progress"})
        chapters.append(
            {
                "id": chapter["id"],
                "order": chapter["order"],
                "title": chapter["title"],
                "description": chapter["description"],
                "source": chapter["source"],
                "total_sections": len(chapter_sections),
                "started_sections": chapter_started,
                "completed_sections": chapter_completed,
                "completion_rate": round(chapter_completed / section_count * 100, 1),
                "engagement_rate": round(chapter_started / section_count * 100, 1),
                "score": round(chapter_score_total / section_count, 1),
                "sections": chapter_sections,
            }
        )

    return {
        "total_sections": total_sections,
        "ready_sections": ready_sections,
        "started_sections": started_sections,
        "completed_sections": completed_sections,
        "completion_rate": round(completed_sections / total_sections * 100, 1) if total_sections else 0.0,
        "ready_completion_rate": round(completed_sections / ready_sections * 100, 1) if ready_sections else 0.0,
        "chapters": chapters,
    }


def _summarize_questions_by_topic(question_progress: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    questions = {item["id"]: item for item in list_questions()}
    topic_summary: Dict[str, Dict[str, Any]] = {}
    for item in question_progress.get("questions", []):
        question = questions.get(item["question_id"])
        if not question:
            continue
        topic = question["topic"]
        bucket = topic_summary.setdefault(
            topic,
            {
                "topic": topic,
                "topic_name": question.get("topic_name", topic),
                "attempts": 0,
                "completed": 0,
                "best_scores": [],
            },
        )
        bucket["attempts"] += int(item.get("attempts", 0))
        bucket["completed"] += 1 if item.get("passed") else 0
        bucket["best_scores"].append(float(item.get("best_score", 0.0)))

    for bucket in topic_summary.values():
        scores = bucket.pop("best_scores")
        bucket["average_best_score"] = round(sum(scores) / len(scores), 1) if scores else 0.0
    return topic_summary


def _build_skill_profile(
    curriculum: Dict[str, Any],
    question_progress: Dict[str, Any],
    behavior: Dict[str, Any],
) -> List[Dict[str, Any]]:
    chapter_scores = {chapter["id"]: chapter for chapter in curriculum.get("chapters", [])}
    question_topics = _summarize_questions_by_topic(question_progress)
    stuck_targets = behavior.get("stuck_targets", [])

    skills = []
    for skill in SKILL_DIMENSIONS:
        related_chapters = [chapter_scores[item] for item in skill["chapters"] if item in chapter_scores]
        chapter_score = (
            sum(float(item.get("score", 0.0)) for item in related_chapters) / len(related_chapters)
            if related_chapters
            else 0.0
        )
        related_topics = [question_topics[item] for item in skill["topics"] if item in question_topics]
        question_score = (
            sum(float(item.get("average_best_score", 0.0)) for item in related_topics) / len(related_topics)
            if related_topics
            else 0.0
        )
        behavior_bonus = min(8.0, sum(float(chapter.get("engagement_rate", 0.0)) for chapter in related_chapters) / 100 * 5)
        stuck_penalty = 0.0
        for stuck in stuck_targets:
            target_id = str(stuck.get("target_id", ""))
            if any(target_id == section.get("lesson_id") or target_id == section.get("id") for chapter in related_chapters for section in chapter.get("sections", [])):
                stuck_penalty += 8.0
        score = max(0.0, min(100.0, chapter_score * 0.55 + question_score * 0.35 + behavior_bonus - stuck_penalty))
        if score >= 80:
            level = "强项"
        elif score >= 55:
            level = "稳定"
        elif score >= 25:
            level = "起步"
        else:
            level = "待建立"
        skills.append(
            {
                "id": skill["id"],
                "name": skill["name"],
                "description": skill["description"],
                "score": round(score, 1),
                "level": level,
                "chapter_score": round(chapter_score, 1),
                "question_score": round(question_score, 1),
            }
        )
    return skills


def _build_behavior_insights(behavior: Dict[str, Any]) -> List[Dict[str, str]]:
    insights = []
    preferences = behavior.get("preferences", {})
    if preferences.get("learning_goal"):
        insights.append({"title": "学习目标", "content": preferences["learning_goal"]})
    if preferences.get("learning_style"):
        insights.append({"title": "学习方式", "content": _learning_style_label(preferences.get("learning_style"))})
    if preferences.get("preferred_pace"):
        insights.append({"title": "学习节奏", "content": _preferred_pace_label(preferences.get("preferred_pace"))})
    for stuck in behavior.get("stuck_targets", [])[:3]:
        target_name = stuck.get("target_id") or "某个学习点"
        minutes = round(float(stuck.get("duration_seconds", 0.0) or 0.0) / 60, 1)
        insights.append(
            {
                "title": "可能卡点",
                "content": f"{target_name} 停留约 {minutes} 分钟，建议回看示例或询问智能体。",
            }
        )
    if not insights:
        insights.append({"title": "数据积累中", "content": "多完成几次学习和提交后，系统会给出更准确的画像。"})
    return insights


def _build_learning_path_recommendations(
    curriculum: Dict[str, Any],
    behavior: Dict[str, Any],
    limit: int = 6,
) -> List[Dict[str, Any]]:
    stuck_ids = {str(item.get("target_id")) for item in behavior.get("stuck_targets", []) if item.get("target_id")}
    candidates = []
    for chapter in curriculum.get("chapters", []):
        for section in chapter.get("sections", []):
            section_key = str(section.get("lesson_id") or section["id"])
            if section["status"] == "completed":
                continue
            priority = 2
            reason = "按照学习中心顺序，这是适合继续推进的小节。"
            if section_key in stuck_ids:
                priority = 0
                reason = "你最近在这里停留较久，适合优先回到这个卡点。"
            elif section["status"] == "in_progress":
                priority = 1
                reason = "这个小节已经开始但还没通过，继续完成会最直接提升进度。"
            elif section["status"] == "not_started":
                priority = 2
                reason = "这是当前可学习的下一节内容。"
            else:
                priority = 3
                reason = "内容还在规划中，可以先预览目录，后续补齐讲解和练习。"
            candidates.append(
                {
                    "id": section["id"],
                    "lesson_id": section.get("lesson_id"),
                    "chapter_title": chapter["title"],
                    "title": section["title"],
                    "status": section["status"],
                    "status_label": section["status_label"],
                    "reason": reason,
                    "estimated_minutes": section.get("estimated_minutes", 0),
                    "priority": priority,
                    "action": "继续学习" if section.get("lesson_id") else "预览目录",
                    "url": "/learn",
                }
            )
    return sorted(candidates, key=lambda item: (item["priority"], item["estimated_minutes"]))[:limit]


def _build_profile_question_recommendations(
    question_progress: Dict[str, Any],
    progress: Dict[str, Any],
    level: Dict[str, Any],
    behavior: Dict[str, Any],
    limit: int = 5,
) -> List[Dict[str, Any]]:
    attempted = {item["question_id"]: item for item in question_progress.get("questions", [])}
    base = _personalize_questions(list_questions(), progress, level, behavior=behavior, limit=20)
    recommended = []
    for question in base:
        item = attempted.get(question["id"])
        reason = question.get("recommend_reason", "")
        if item and not item.get("passed"):
            reason = f"这道题已经尝试过但还没通过，适合回头解决。{reason}"
        elif not item:
            reason = f"你还没有做过这道题。{reason}"
        else:
            reason = f"已通过，可作为巩固题复刷。{reason}"
        recommended.append(
            {
                **question,
                "attempts": int(item.get("attempts", 0)) if item else 0,
                "passed": bool(item.get("passed", False)) if item else False,
                "best_score": float(item.get("best_score", 0.0)) if item else 0.0,
                "recommend_reason": reason,
                "url": f"/questions/{question['id']}",
            }
        )
        if len(recommended) >= limit:
            break
    return recommended


def _duration_for_question(behavior: Dict[str, Any], question_id: str) -> float:
    for item in behavior.get("target_focus", []):
        if item.get("target_type") == "question" and item.get("target_id") == question_id:
            return round(float(item.get("duration_seconds", 0.0) or 0.0) / 60, 1)
    return 0.0


def _enrich_question_status(
    question: Dict[str, Any],
    question_progress: Dict[str, Any],
    behavior: Dict[str, Any],
) -> Dict[str, Any]:
    progress_by_question = {
        item["question_id"]: item
        for item in question_progress.get("questions", [])
    }
    item = progress_by_question.get(question["id"])
    if item and item.get("passed"):
        status_text = "completed"
        status_label = "已完成"
    elif item:
        status_text = "attempted"
        status_label = "待突破"
    else:
        status_text = "not_started"
        status_label = "未开始"
    duration_minutes = _duration_for_question(behavior, question["id"])
    return {
        **question,
        "status": status_text,
        "status_label": status_label,
        "attempts": int(item.get("attempts", 0)) if item else 0,
        "passed": bool(item.get("passed", False)) if item else False,
        "best_score": float(item.get("best_score", 0.0)) if item else 0.0,
        "latest_score": float(item.get("latest_score", 0.0)) if item else 0.0,
        "last_submitted_at": item.get("last_submitted_at") if item else None,
        "duration_minutes": duration_minutes,
        "url": f"/questions/{question['id']}",
    }


QUESTION_SECTION_MAP = {
    "py-func-001": ["python-functions-basics", "function-parameters"],
    "py-func-002": ["if-statements", "operators"],
    "py-func-003": ["python-functions-basics", "function-return-vs-print"],
    "py-list-001": ["list-basics", "for-loop-basics", "loop-exercises-patterns"],
    "py-list-002": ["list-slicing", "list-methods"],
    "py-dict-001": ["dict-basics", "dict-looping"],
    "py-algo-001": ["loop-exercises-patterns", "for-loop-basics"],
    "py-oop-001": ["class-object-basics", "attributes-methods", "simple-class-practice"],
}


def _infer_question_sections(question: Dict[str, Any]) -> List[str]:
    mapped = QUESTION_SECTION_MAP.get(question["id"])
    if mapped:
        return mapped

    tags = {str(tag).lower() for tag in question.get("tags", [])}
    topic = question.get("topic")
    if topic == "python_basics":
        if "条件" in tags or "取模" in tags:
            return ["if-statements", "operators"]
        if "函数" in tags or "return" in tags:
            return ["python-functions-basics"]
        return ["variables-assignment"]
    if topic == "data_structures":
        if "字典" in tags:
            return ["dict-basics"]
        if "列表" in tags:
            return ["list-basics"]
        return ["data-structures"]
    if topic == "algorithms":
        return ["loop-exercises-patterns"]
    if topic == "oop":
        return ["class-object-basics"]
    return []


def _build_question_knowledge_groups(
    questions: List[Dict[str, Any]],
    question_progress: Dict[str, Any],
    behavior: Dict[str, Any],
) -> List[Dict[str, Any]]:
    enriched_by_id = {
        question["id"]: _enrich_question_status(question, question_progress, behavior)
        for question in questions
    }
    questions_by_section: Dict[str, List[Dict[str, Any]]] = {}
    assigned_question_ids = set()
    for question in questions:
        section_ids = _infer_question_sections(question)
        if not section_ids:
            continue
        assigned_question_ids.add(question["id"])
        for section_id in section_ids:
            questions_by_section.setdefault(section_id, []).append(enriched_by_id[question["id"]])

    groups = []
    for chapter in list_curriculum(language="python"):
        section_groups = []
        chapter_questions: List[Dict[str, Any]] = []
        for section in chapter.get("sections", []):
            section_questions = questions_by_section.get(section["id"], [])
            completed = sum(1 for item in section_questions if item["status"] == "completed")
            attempted = sum(1 for item in section_questions if item["status"] in {"completed", "attempted"})
            duration_minutes = round(sum(float(item.get("duration_minutes", 0.0)) for item in section_questions), 1)
            chapter_questions.extend(section_questions)
            section_groups.append(
                {
                    "id": section["id"],
                    "lesson_id": section.get("lesson_id"),
                    "title": section["title"],
                    "summary": section["summary"],
                    "status": "has_questions" if section_questions else "empty",
                    "total": len(section_questions),
                    "completed": completed,
                    "attempted": attempted,
                    "completion_rate": round(completed / len(section_questions) * 100, 1) if section_questions else 0.0,
                    "duration_minutes": duration_minutes,
                    "questions": section_questions,
                }
            )

        unique_question_ids = {item["id"] for item in chapter_questions}
        unique_questions = [enriched_by_id[item] for item in unique_question_ids if item in enriched_by_id]
        completed = sum(1 for item in unique_questions if item["status"] == "completed")
        attempted = sum(1 for item in unique_questions if item["status"] in {"completed", "attempted"})
        groups.append(
            {
                "id": chapter["id"],
                "title": chapter["title"],
                "description": chapter["description"],
                "total": len(unique_questions),
                "completed": completed,
                "attempted": attempted,
                "completion_rate": round(completed / len(unique_questions) * 100, 1) if unique_questions else 0.0,
                "duration_minutes": round(sum(float(item.get("duration_minutes", 0.0)) for item in unique_questions), 1),
                "sections": section_groups,
            }
        )

    unassigned = [
        enriched_by_id[question["id"]]
        for question in questions
        if question["id"] not in assigned_question_ids and question["id"] in enriched_by_id
    ]
    if unassigned:
        completed = sum(1 for item in unassigned if item["status"] == "completed")
        groups.append(
            {
                "id": "unassigned",
                "title": "未关联学习中心的题目",
                "description": "这些题目暂时还没有映射到学习中心小节，后续会补齐归属。",
                "total": len(unassigned),
                "completed": completed,
                "attempted": sum(1 for item in unassigned if item["status"] in {"completed", "attempted"}),
                "completion_rate": round(completed / len(unassigned) * 100, 1),
                "duration_minutes": round(sum(float(item.get("duration_minutes", 0.0)) for item in unassigned), 1),
                "sections": [
                    {
                        "id": "unassigned",
                        "title": "待归类题目",
                        "summary": "暂未绑定到学习中心知识点。",
                        "status": "has_questions",
                        "total": len(unassigned),
                        "completed": completed,
                        "attempted": sum(1 for item in unassigned if item["status"] in {"completed", "attempted"}),
                        "completion_rate": round(completed / len(unassigned) * 100, 1),
                        "duration_minutes": round(sum(float(item.get("duration_minutes", 0.0)) for item in unassigned), 1),
                        "questions": unassigned,
                    }
                ],
            }
        )
    return groups


async def _build_profile_overview(username: str) -> Dict[str, Any]:
    user = await _run_store(store.get_user, username)
    progress = await _run_store(store.get_lesson_progress_summary, username)
    behavior = await _run_store(store.get_learning_behavior_summary, username)
    question_progress = await _run_store(store.get_question_progress_summary, username)
    recent = await _run_store(store.list_recent_lesson_submissions, username, 8)
    lessons = list_lessons(language="python")
    lesson_map = {lesson["id"]: lesson for lesson in lessons}
    curriculum = _build_curriculum_progress(progress, behavior)

    lesson_progress = []
    for lesson in lessons:
        matched = next(
            (
                item
                for item in progress.get("lessons", [])
                if item["lesson_id"] == lesson["id"]
            ),
            None,
        )
        lesson_progress.append(
            {
                "lesson_id": lesson["id"],
                "title": lesson["title"],
                "difficulty": lesson["difficulty"],
                "status": (
                    "completed"
                    if matched and matched.get("passed")
                    else "in_progress"
                    if matched
                    else "not_started"
                ),
                "attempts": int(matched.get("attempts", 0)) if matched else 0,
                "best_score": float(matched.get("best_score", 0.0)) if matched else 0.0,
                "latest_score": float(matched.get("latest_score", 0.0)) if matched else 0.0,
                "last_submitted_at": matched.get("last_submitted_at") if matched else None,
            }
        )

    enriched_recent = [
        {
            **item,
            "lesson_title": lesson_map.get(item["lesson_id"], {}).get("title", item["lesson_id"]),
        }
        for item in recent
    ]

    level = _build_learning_level(progress, len(lessons))
    skill_profile = _build_skill_profile(curriculum, question_progress, behavior)
    learning_path = _build_learning_path_recommendations(curriculum, behavior)
    recommended_questions = _build_profile_question_recommendations(
        question_progress,
        progress,
        level,
        behavior,
    )
    return {
        "profile": user or {"username": username},
        "level": level,
        "stats": {
            "total_lessons": curriculum["total_sections"],
            "ready_lessons": curriculum["ready_sections"],
            "completed_lessons": int(progress.get("completed_lessons", 0)),
            "total_attempts": int(progress.get("total_attempts", 0)),
            "question_attempts": int(question_progress.get("total_attempts", 0)),
            "completed_questions": int(question_progress.get("completed_questions", 0)),
            "average_best_score": float(progress.get("average_best_score", 0.0)),
            "completion_rate": level["completion_rate"],
            "curriculum_completion_rate": curriculum["completion_rate"],
            "ready_completion_rate": curriculum["ready_completion_rate"],
            "total_study_minutes": round(float(behavior.get("total_duration_seconds", 0.0)) / 60, 1),
        },
        "behavior": behavior,
        "behavior_insights": _build_behavior_insights(behavior),
        "curriculum": curriculum,
        "skill_profile": skill_profile,
        "question_progress": question_progress,
        "learning_path": learning_path,
        "recommended_questions": recommended_questions,
        "lesson_progress": lesson_progress,
        "recent_submissions": enriched_recent,
        "recommendations": _build_learning_recommendations(progress, lessons, behavior),
    }


async def _build_agent_learning_context(username: str) -> Dict[str, Any]:
    user = await _run_store(store.get_user, username)
    progress = await _run_store(store.get_lesson_progress_summary, username)
    behavior = await _run_store(store.get_learning_behavior_summary, username)
    lessons = list_lessons(language="python")
    level = _build_learning_level(progress, len(lessons))
    preferences = behavior.get("preferences", {})
    return {
        "profile": {
            "username": username,
            "nickname": (user or {}).get("nickname") or username,
            "learning_goal": preferences.get("learning_goal") or "",
            "learning_style": preferences.get("learning_style") or "",
            "learning_style_label": _learning_style_label(preferences.get("learning_style")),
            "preferred_pace": preferences.get("preferred_pace") or "",
            "preferred_pace_label": _preferred_pace_label(preferences.get("preferred_pace")),
        },
        "level": level,
        "progress": {
            "total_attempts": progress.get("total_attempts", 0),
            "completed_lessons": progress.get("completed_lessons", 0),
            "average_best_score": progress.get("average_best_score", 0.0),
        },
        "behavior": {
            "total_events": behavior.get("total_events", 0),
            "total_study_minutes": round(float(behavior.get("total_duration_seconds", 0.0)) / 60, 1),
            "stuck_targets": behavior.get("stuck_targets", [])[:3],
            "recent_events": behavior.get("recent_events", [])[:5],
        },
    }


async def _run_store(func, *args, **kwargs):
    return await asyncio.to_thread(func, *args, **kwargs)


async def _acquire_agent_slot() -> None:
    try:
        await asyncio.wait_for(agent_semaphore.acquire(), timeout=AGENT_QUEUE_TIMEOUT_SECONDS)
    except TimeoutError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="当前请求较多，请稍后重试",
        ) from exc


@app.on_event("startup")
async def warmup_dependencies() -> None:
    await asyncio.to_thread(get_system)


@app.on_event("shutdown")
async def close_store_connection() -> None:
    await asyncio.to_thread(store.close)


@app.get("/", include_in_schema=False)
async def index_page() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "index.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/chat", include_in_schema=False)
async def chat_page() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "chat.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/learn", include_in_schema=False)
async def learn_page() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "learn.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/profile", include_in_schema=False)
async def profile_page() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "profile.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/questions", include_in_schema=False)
async def questions_page() -> FileResponse:
    return FileResponse(
        STATIC_DIR / "questions.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/questions/{question_id}", include_in_schema=False)
async def question_detail_page(question_id: str) -> FileResponse:
    return FileResponse(
        STATIC_DIR / "question_detail.html",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


@app.get("/health")
async def health_check() -> dict:
    return {
        "status": "ok",
        "service": APP_TITLE,
        "app_db": APP_DB_PATH,
    }


@app.get("/learning/lessons")
async def lessons_overview(session: SessionData = Depends(get_current_session)) -> dict:
    return {
        "items": list_lessons(language="python"),
        "chapters": list_curriculum(language="python"),
    }


@app.get("/learning/lessons/{lesson_id}")
async def lesson_detail(lesson_id: str, session: SessionData = Depends(get_current_session)) -> dict:
    lesson = get_lesson(lesson_id)
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识点不存在")

    latest_submission = await _run_store(store.get_latest_lesson_submission, session.username, lesson_id)
    return {
        "lesson": lesson,
        "latest_submission": latest_submission,
    }


@app.post("/learning/ask-selection")
async def ask_learning_selection(
    payload: LearningSelectionAskRequest,
    session: SessionData = Depends(get_current_session),
) -> dict:
    lesson = get_lesson(payload.lesson_id)
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识点不存在")

    selected_text = payload.selected_text.strip()
    question = payload.question.strip()
    if not selected_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请先选中一段要解释的文本")

    prompt = (
        "你是编程教育系统里的学习助手。用户正在学习一个 Python 知识点，"
        "现在选中了一段教材或示例文本，希望你解释它的含义。\n\n"
        f"当前知识点：{lesson.get('title', '')}\n"
        f"知识点概述：{lesson.get('summary', '')}\n"
        f"教材来源：{lesson.get('source', {}).get('title', '')}，"
        f"{lesson.get('source', {}).get('authority', '')}\n\n"
        f"用户选中的文本：\n{selected_text}\n\n"
    )
    if payload.surrounding_context:
        prompt += f"选中文本附近的页面上下文：\n{payload.surrounding_context.strip()}\n\n"
    prompt += (
        f"用户的问题：{question or '请解释这段文本是什么意思，并说明它在当前知识点里起什么作用。'}\n\n"
        "回答要求：\n"
        "1. 用中文回答，语气自然，像老师在旁边简短讲解。\n"
        "2. 先用一句话说清楚这段文本的意思。\n"
        "3. 再结合当前知识点解释它为什么重要。\n"
        "4. 如果涉及代码，请给一个很小的例子。\n"
        "5. 不要展开太长，优先让初学者能马上继续阅读。"
    )

    agent_context = await _build_agent_learning_context(session.username)
    await _acquire_agent_slot()
    try:
        system = get_system()
        result = await system.process_user_request(
            request_type="qa",
            content=prompt,
            user_id=session.username,
            external_context=agent_context,
        )
    finally:
        agent_semaphore.release()

    agent_response = str(result.get("response", ""))
    used_local_fallback = _is_generic_agent_fallback(agent_response)
    response_text = (
        _local_learning_explanation(selected_text, question, lesson)
        if used_local_fallback
        else agent_response
    )

    return {
        "success": bool(result.get("success", False)),
        "lesson_id": payload.lesson_id,
        "selected_text": selected_text,
        "question": question,
        "response": response_text,
        "agent_called": True,
        "used_local_fallback": used_local_fallback,
        "raw_agent_response": agent_response if used_local_fallback else "",
        "details": {
            **result.get("details", {}),
            "selection_explanation_source": "local_fallback" if used_local_fallback else "agent",
        },
        "suggestions": result.get("suggestions", []),
    }


@app.post("/auth/register")
async def register(payload: RegisterRequest) -> dict:
    try:
        user = await _run_store(store.create_user, payload.username, payload.password)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {
        "success": True,
        "username": user["username"],
        "created_at": user["created_at"],
    }


@app.post("/auth/login", response_model=AuthResponse)
async def login(payload: LoginRequest) -> AuthResponse:
    username = payload.username.strip()
    if not await _run_store(store.verify_user, username, payload.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    return await _issue_tokens(username)


@app.post("/auth/refresh", response_model=AuthResponse)
async def refresh_auth(payload: RefreshRequest) -> AuthResponse:
    session = await _run_store(store.get_session_by_refresh_token, payload.refresh_token)
    if session is None:
        raise _unauthorized("刷新令牌无效或已过期")

    username = str(session["username"])
    await _run_store(store.revoke_session_by_refresh_token, payload.refresh_token)
    return await _issue_tokens(username)


@app.post("/auth/logout")
async def logout(access_token: str = Depends(get_current_access_token)) -> dict:
    await _run_store(store.revoke_session_by_access_token, access_token)
    return {"success": True}


@app.get("/auth/me")
async def current_user(session: SessionData = Depends(get_current_session)) -> dict:
    user = await _run_store(store.get_user, session.username)
    return {
        "username": session.username,
        "expires_at": session.access_expires_at,
        "refresh_expires_at": session.refresh_expires_at,
        "profile": user or {},
    }


@app.get("/profile/overview")
async def profile_overview(session: SessionData = Depends(get_current_session)) -> dict:
    return await _build_profile_overview(session.username)


@app.patch("/profile")
async def update_profile(
    payload: ProfileUpdateRequest,
    session: SessionData = Depends(get_current_session),
) -> dict:
    try:
        profile = await _run_store(
            store.update_user_profile,
            session.username,
            payload.nickname,
            payload.avatar_url,
            payload.bio,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {
        "success": True,
        "profile": profile,
    }


@app.patch("/profile/preferences")
async def update_learning_preferences(
    payload: LearningPreferencesUpdateRequest,
    session: SessionData = Depends(get_current_session),
) -> dict:
    try:
        profile = await _run_store(
            store.update_learning_preferences,
            session.username,
            payload.learning_goal,
            payload.learning_style,
            payload.preferred_pace,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    await _run_store(
        store.record_learning_event,
        session.username,
        "preferences_updated",
        "profile",
        session.username,
        None,
        {
            "learning_goal": payload.learning_goal,
            "learning_style": payload.learning_style,
            "preferred_pace": payload.preferred_pace,
        },
    )
    return {
        "success": True,
        "profile": profile,
    }


@app.post("/analytics/events")
async def record_learning_event(
    payload: LearningEventRequest,
    session: SessionData = Depends(get_current_session),
) -> dict:
    try:
        event = await _run_store(
            store.record_learning_event,
            session.username,
            payload.event_type,
            payload.target_type,
            payload.target_id,
            payload.duration_seconds,
            payload.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return {
        "success": True,
        "event": event,
    }


@app.get("/analytics/summary")
async def learning_analytics_summary(session: SessionData = Depends(get_current_session)) -> dict:
    return await _run_store(store.get_learning_behavior_summary, session.username)


@app.post("/ide/analyze")
async def analyze_ide_code(
    payload: IDEAnalyzeRequest,
    session: SessionData = Depends(get_current_session),
) -> dict:
    expected_function = payload.expected_function or ""
    requirements = payload.requirements
    if payload.context_type == "question" and payload.target_id:
        question = get_question(payload.target_id)
        if question:
            expected_function = expected_function or str(question.get("expected_function", ""))
            requirements = requirements or [str(item) for item in question.get("hints", [])]
    elif payload.context_type == "lesson" and payload.target_id:
        lesson = get_lesson(payload.target_id)
        if lesson:
            expected_function = expected_function or _lesson_expected_function(lesson)
            requirements = requirements or _lesson_requirements(lesson)

    result = await _run_store(
        analyze_code,
        payload.code,
        expected_function,
        requirements,
    )
    return result


@app.post("/ide/stuck-check")
async def check_ide_stuck(
    payload: IDEStuckCheckRequest,
    session: SessionData = Depends(get_current_session),
) -> dict:
    result = detect_stuck(
        payload.code,
        payload.duration_seconds,
        payload.submit_count,
        payload.failed_submit_count,
        payload.diagnostics,
    )
    if result.get("stuck") and payload.target_id:
        await _run_store(
            store.record_learning_event,
            session.username,
            "ide_stuck",
            payload.context_type,
            payload.target_id,
            payload.duration_seconds,
            {
                "level": result.get("level"),
                "reasons": result.get("reasons", []),
            },
        )
    return result


@app.get("/question-bank/overview")
async def question_bank_overview(session: SessionData = Depends(get_current_session)) -> dict:
    return await _build_question_bank_overview(session.username)


@app.get("/question-bank/questions")
async def question_bank_questions(
    topic: str = "all",
    difficulty: str = "all",
    question_type: str = "all",
    keyword: str = "",
    session: SessionData = Depends(get_current_session),
) -> dict:
    progress = await _run_store(store.get_lesson_progress_summary, session.username)
    behavior = await _run_store(store.get_learning_behavior_summary, session.username)
    question_progress = await _run_store(store.get_question_progress_summary, session.username)
    level = _build_learning_level(progress, len(list_lessons(language="python")))
    items = list_questions(
        topic=topic,
        difficulty=difficulty,
        question_type=question_type,
        keyword=keyword.strip() or None,
    )
    return {
        "items": [
            _enrich_question_status(item, question_progress, behavior)
            for item in _personalize_questions(items, progress, level, behavior=behavior, limit=50)
        ],
        "total": len(items),
        "knowledge_groups": _build_question_knowledge_groups(items, question_progress, behavior),
    }


@app.get("/question-bank/questions/{question_id}")
async def question_bank_question_detail(
    question_id: str,
    session: SessionData = Depends(get_current_session),
) -> dict:
    question = get_question(question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")
    latest_submission = await _run_store(
        store.get_latest_question_submission,
        session.username,
        question_id,
    )
    return {
        "question": question,
        "latest_submission": latest_submission,
    }


@app.post("/question-bank/questions/{question_id}/submit")
async def submit_question_solution(
    question_id: str,
    payload: QuestionSubmissionRequest,
    session: SessionData = Depends(get_current_session),
) -> dict:
    question = get_question(question_id)
    if question is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="题目不存在")

    grading = await _grade_question_submission(payload.code, question)
    await _run_store(
        store.record_learning_event,
        session.username,
        "question_submit",
        "question",
        question_id,
        None,
        {
            "passed": grading["passed"],
            "score": grading["score"],
            "topic": question.get("topic"),
            "difficulty": question.get("difficulty"),
        },
    )
    saved = await _run_store(
        store.save_question_submission,
        session.username,
        question_id,
        payload.code,
        grading["passed"],
        grading["score"],
        grading["feedback"],
        grading["test_result"],
    )
    return {
        "success": True,
        "passed": grading["passed"],
        "score": grading["score"],
        "feedback": grading["feedback"],
        "structured_feedback": grading["structured_feedback"],
        "test_result": grading["test_result"],
        "ide_analysis": grading["ide_analysis"],
        "ide_feedback": grading["ide_feedback"],
        "submission": saved,
    }


@app.post("/question-bank/quiz")
async def generate_question_quiz(
    payload: QuizGenerateRequest,
    session: SessionData = Depends(get_current_session),
) -> dict:
    quiz = await _generate_personalized_quiz(session.username, payload)
    return {
        "success": True,
        "quiz": quiz,
    }


@app.get("/chat/conversations")
async def list_conversations(session: SessionData = Depends(get_current_session)) -> dict:
    return {
        "items": await _run_store(store.list_conversations, session.username),
    }


@app.get("/chat/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, session: SessionData = Depends(get_current_session)) -> dict:
    conversation = await _run_store(store.get_conversation, session.username, conversation_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="对话不存在")
    return {
        "conversation": conversation,
        "messages": await _run_store(store.list_messages, session.username, conversation_id),
    }


@app.post("/agent/request", response_model=AgentResponse)
async def request_agent(
    payload: AgentRequest,
    session: SessionData = Depends(get_current_session),
) -> AgentResponse:
    conversation_id = await _run_store(
        _ensure_conversation,
        session.username,
        payload.conversation_id,
        payload.content,
    )
    await _run_store(
        store.add_message,
        session.username,
        conversation_id,
        "user",
        payload.content,
        payload.request_type,
    )
    await _run_store(
        store.record_learning_event,
        session.username,
        "agent_request",
        "conversation",
        conversation_id,
        None,
        {"request_type": payload.request_type, "content_length": len(payload.content)},
    )

    agent_context = await _build_agent_learning_context(session.username)
    await _acquire_agent_slot()
    try:
        system = get_system()
        result = await system.process_user_request(
            request_type=payload.request_type,
            content=payload.content,
            user_id=session.username,
            external_context=agent_context,
        )

        await _run_store(
            store.add_message,
            session.username,
            conversation_id,
            "assistant",
            str(result.get("response", "")),
            str(result.get("request_type", payload.request_type)),
        )

        return AgentResponse(
            success=bool(result.get("success", False)),
            request_type=str(result.get("request_type", payload.request_type)),
            response=str(result.get("response", "")),
            details=result.get("details", {}),
            suggestions=result.get("suggestions", []),
            user_id=str(result.get("user_id", session.username)),
            conversation_id=conversation_id,
        )
    finally:
        agent_semaphore.release()


@app.post("/learning/submit")
async def submit_lesson(
    payload: LessonSubmissionRequest,
    session: SessionData = Depends(get_current_session),
) -> dict:
    lesson = get_lesson(payload.lesson_id)
    if lesson is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="知识点不存在")

    await _acquire_agent_slot()
    try:
        grading = await grade_lesson_submission(payload.code, lesson, session.username)
    finally:
        agent_semaphore.release()

    ide_analysis = analyze_code(
        payload.code,
        expected_function=_lesson_expected_function(lesson),
        requirements=_lesson_requirements(lesson),
    )
    grading["ide_analysis"] = ide_analysis
    grading["ide_feedback"] = build_submit_feedback(
        payload.code,
        ide_analysis,
        {
            "passed": grading["passed"],
            "score": grading["score"],
            "feedback": grading["feedback"],
            "structured_feedback": grading["structured_feedback"],
            "hidden_test_result": grading["hidden_test_result"],
        },
        title=str(lesson.get("title", "当前知识点练习")),
    )

    await _run_store(
        store.record_learning_event,
        session.username,
        "lesson_submit",
        "lesson",
        payload.lesson_id,
        None,
        {
            "passed": grading["passed"],
            "score": grading["score"],
            "topic": lesson.get("topic"),
            "difficulty": lesson.get("difficulty"),
        },
    )

    saved = await _run_store(
        store.save_lesson_submission,
        session.username,
        payload.lesson_id,
        payload.code,
        grading["passed"],
        grading["score"],
        grading["feedback"],
        grading["structured_feedback"],
    )

    return {
        "success": True,
        "passed": grading["passed"],
        "score": grading["score"],
        "feedback": grading["feedback"],
        "structured_feedback": grading["structured_feedback"],
        "hidden_test_result": grading["hidden_test_result"],
        "agent_evaluation": grading["agent_evaluation"],
        "ide_analysis": grading["ide_analysis"],
        "ide_feedback": grading["ide_feedback"],
        "submission": saved,
    }
