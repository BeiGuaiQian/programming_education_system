"""Code evaluation agent with static and lightweight runtime checks."""

from __future__ import annotations

import ast
import asyncio
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List, Optional

from programming_education_system.agents.base_agent import BaseAgent
from programming_education_system.config.llm_config import Config
from programming_education_system.utils.llm_utils import llm_client

logger = logging.getLogger(__name__)


class AnswerEvaluationAgent(BaseAgent):
    """Evaluate user code and provide structured feedback."""

    BLOCKED_IMPORTS = {
        "ctypes",
        "multiprocessing",
        "os",
        "pathlib",
        "pickle",
        "shutil",
        "socket",
        "subprocess",
        "sys",
        "tempfile",
        "threading",
    }
    BLOCKED_CALLS = {
        "__import__",
        "breakpoint",
        "compile",
        "eval",
        "exec",
        "input",
        "open",
    }
    BLOCKED_ATTRIBUTES = {
        "chmod",
        "connect",
        "fork",
        "kill",
        "listen",
        "popen",
        "remove",
        "rename",
        "replace",
        "rmdir",
        "run",
        "spawn",
        "system",
        "unlink",
    }

    def __init__(self, personal_agent):
        super().__init__("AnswerEvaluationAgent")
        self.personal_agent = personal_agent

    async def evaluate_code(
        self, code: str, user_id: str, question_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        syntax = self._syntax_check(code)
        style = self._style_check(code)
        security = self._security_check(code, syntax)
        run_result = await self._run_code(
            code,
            syntax_valid=syntax["valid"],
            security=security,
        )
        llm_feedback = await self._llm_feedback(code, question_context, syntax, style, run_result)
        overall_score = self._calculate_score(syntax, style, security, run_result)
        return {
            "success": True,
            "overall_score": overall_score,
            "feedback": llm_feedback,
            "detailed_analysis": {
                "syntax": syntax,
                "style": style,
                "security": security,
                "execution": run_result,
            },
            "personalized": False,
        }

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        user_id = request["user_id"]
        content = request["content"]
        code, question_info = self._parse_evaluation_request(content)
        result = await self.evaluate_code(code, user_id, question_info)

        await self.personal_agent.track_user_behavior(
            {
                "user_id": user_id,
                "evaluation_score": result.get("overall_score", 0),
                "topic": question_info.get("topic", "general"),
                "code_length": len(code),
                "success": result.get("success", False),
            }
        )

        response = (
            f"## 代码评估报告\n**综合得分**: {result['overall_score']}/100\n\n{result['feedback']}"
        )
        return {"response": response, "details": result, "success": True}

    def _parse_evaluation_request(self, content: str) -> tuple:
        stripped_content = content.strip()
        code = stripped_content
        question_info = {"topic": "general", "description": "代码评估请求", "difficulty": "medium"}
        fenced_match = re.search(r"```(?:python)?\s*(.*?)```", stripped_content, re.DOTALL | re.IGNORECASE)
        if fenced_match:
            code = fenced_match.group(1).strip()
            request_text = stripped_content.replace(fenced_match.group(0), "").strip()
        else:
            request_text = stripped_content
        if request_text:
            question_info["description"] = request_text[:200]

        topic_keywords = {
            "python_basics": ["def ", "print(", "input(", "for ", "while "],
            "data_structures": ["list", "dict", "set", "tuple"],
            "algorithms": ["sort", "search", "recursive", "algorithm", "binary_search"],
            "oop": ["class ", "self.", "__init__"],
        }
        lowered_code = code.lower()
        for topic, keywords in topic_keywords.items():
            if any(keyword.lower() in lowered_code for keyword in keywords):
                question_info["topic"] = topic
                break
        return code, question_info

    def _syntax_check(self, code: str) -> Dict[str, Any]:
        try:
            ast.parse(code)
            return {"valid": True, "errors": []}
        except SyntaxError as exc:
            return {
                "valid": False,
                "errors": [
                    {
                        "message": exc.msg or str(exc),
                        "lineno": getattr(exc, "lineno", None),
                        "offset": getattr(exc, "offset", None),
                        "text": (exc.text or "").rstrip() if getattr(exc, "text", None) else None,
                    }
                ],
            }

    def _style_check(self, code: str) -> Dict[str, Any]:
        issues: List[str] = []
        lines = code.splitlines()
        for index, line in enumerate(lines, start=1):
            if len(line) > 100:
                issues.append(f"Line {index} is longer than 100 characters.")
            if "\t" in line:
                issues.append(f"Line {index} contains tabs; prefer spaces.")
        score = max(0, 100 - len(issues) * 5)
        return {"score": score, "issues": issues[:20], "line_count": len(lines)}

    def _security_check(self, code: str, syntax: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[str] = []

        if len(code) > Config.MAX_CODE_LENGTH:
            issues.append(
                f"Code exceeds the secure evaluation limit of {Config.MAX_CODE_LENGTH} characters."
            )

        if not syntax.get("valid", False):
            return {
                "safe_to_execute": False,
                "issues": issues,
                "execution_allowed": False,
            }

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {
                "safe_to_execute": False,
                "issues": issues,
                "execution_allowed": False,
            }

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".", 1)[0]
                    if module_name in self.BLOCKED_IMPORTS:
                        issues.append(f"Blocked import detected: {module_name}")
            elif isinstance(node, ast.ImportFrom):
                module_name = (node.module or "").split(".", 1)[0]
                if module_name in self.BLOCKED_IMPORTS:
                    issues.append(f"Blocked import detected: {module_name}")
            elif isinstance(node, ast.Call):
                func_name = self._get_call_name(node.func)
                if func_name in self.BLOCKED_CALLS:
                    issues.append(f"Blocked function call detected: {func_name}")
            elif isinstance(node, ast.Attribute):
                if node.attr in self.BLOCKED_ATTRIBUTES:
                    issues.append(f"Blocked attribute access detected: {node.attr}")

        safe_to_execute = not issues
        return {
            "safe_to_execute": safe_to_execute,
            "issues": issues[:20],
            "execution_allowed": safe_to_execute and Config.ENABLE_UNTRUSTED_CODE_EXECUTION,
        }

    async def _run_code(
        self,
        code: str,
        syntax_valid: bool,
        security: Dict[str, Any],
    ) -> Dict[str, Any]:
        if not syntax_valid:
            return {"skipped": True, "reason": "syntax_invalid"}
        if not security.get("safe_to_execute", False):
            return {
                "skipped": True,
                "reason": "security_blocked",
                "security_issues": security.get("issues", []),
            }
        if not security.get("execution_allowed", False):
            return {
                "skipped": True,
                "reason": "execution_disabled",
                "message": "Runtime execution is disabled by default for safety.",
            }

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False, encoding="utf-8") as handle:
            handle.write(code)
            temp_path = handle.name

        try:
            loop = asyncio.get_running_loop()

            def _run():
                start = time.perf_counter()
                try:
                    safe_env = {
                        "PYTHONIOENCODING": "utf-8",
                        "PYTHONUTF8": "1",
                    }
                    proc = subprocess.run(
                        [sys.executable, "-I", temp_path],
                        capture_output=True,
                        text=True,
                        timeout=Config.CODE_EXECUTION_TIMEOUT,
                        encoding="utf-8",
                        errors="replace",
                        cwd=tempfile.gettempdir(),
                        env=safe_env,
                    )
                    return {
                        "returncode": proc.returncode,
                        "stdout": proc.stdout[:2000],
                        "stderr": proc.stderr[:2000],
                        "duration_ms": round((time.perf_counter() - start) * 1000, 2),
                        "timed_out": False,
                    }
                except subprocess.TimeoutExpired:
                    return {
                        "returncode": -1,
                        "stdout": "",
                        "stderr": (
                            f"Execution timed out after {Config.CODE_EXECUTION_TIMEOUT} seconds."
                        ),
                        "duration_ms": float(Config.CODE_EXECUTION_TIMEOUT * 1000),
                        "timed_out": True,
                    }

            return await loop.run_in_executor(None, _run)
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    async def _llm_feedback(
        self,
        code: str,
        question_context: Dict[str, Any],
        syntax: Dict[str, Any],
        style: Dict[str, Any],
        run_result: Dict[str, Any],
    ) -> str:
        system_prompt = "You are a patient programming reviewer. Give concise, actionable feedback."
        user_message = f"""
Question context: {question_context}
Syntax: {syntax}
Style: {style}
Execution: {run_result}

Code:
{code}

Please provide:
1. Main issues
2. Suggested fixes
3. What is already good
"""
        return await llm_client.generate_response(system_prompt, user_message, use_cache=False)

    @staticmethod
    def _get_call_name(func: ast.AST) -> str:
        if isinstance(func, ast.Name):
            return func.id
        if isinstance(func, ast.Attribute):
            return func.attr
        return ""

    @staticmethod
    def _calculate_score(
        syntax: Dict[str, Any],
        style: Dict[str, Any],
        security: Dict[str, Any],
        run_result: Dict[str, Any],
    ) -> float:
        score = 100.0
        if not syntax.get("valid", False):
            score -= 40
        score = min(score, float(style.get("score", 100)))
        if security.get("issues"):
            score -= min(30, len(security["issues"]) * 10)
        if run_result.get("timed_out"):
            score -= 20
        elif run_result.get("returncode", 0) != 0 and not run_result.get("skipped"):
            score -= 15
        return max(0.0, round(score, 1))
