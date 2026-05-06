"""Code evaluation agent with static, runtime, and teaching diagnostics."""

from __future__ import annotations

import ast
import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List

from programming_education_system.agents.base_agent import BaseAgent
from programming_education_system.config.llm_config import Config
from programming_education_system.utils.llm_utils import llm_client

logger = logging.getLogger(__name__)


class AnswerEvaluationAgent(BaseAgent):
    """Evaluate user code and provide structured teaching feedback."""

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
    BLOCKED_CALLS = {"__import__", "breakpoint", "compile", "eval", "exec", "input", "open"}
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

    async def evaluate_code(self, code: str, user_id: str, question_context: Dict[str, Any]) -> Dict[str, Any]:
        syntax = self._syntax_check(code)
        style = self._style_check(code)
        security = self._security_check(code, syntax)
        diagnostics = self._diagnose_learning_issues(code, syntax, style, security, question_context)
        run_result = await self._run_code(code, syntax_valid=syntax["valid"], security=security)
        test_result = await self._run_example_tests(code, question_context, syntax, security)
        llm_feedback = await self._llm_feedback(
            code, question_context, syntax, style, run_result, diagnostics, test_result
        )
        overall_score = self._calculate_score(syntax, style, security, run_result)
        if diagnostics.get("issue_count"):
            overall_score = max(0.0, overall_score - min(20, diagnostics["issue_count"] * 5))
        if test_result.get("failed"):
            overall_score = max(0.0, overall_score - min(25, test_result["failed"] * 8))
        return {
            "success": True,
            "overall_score": overall_score,
            "feedback": llm_feedback,
            "detailed_analysis": {
                "syntax": syntax,
                "style": style,
                "security": security,
                "execution": run_result,
                "example_tests": test_result,
                "diagnostics": diagnostics,
            },
            "personalized": True,
        }

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        user_id = request["user_id"]
        code, question_info = self._parse_evaluation_request(request["content"])
        analysis = request.get("intent_analysis", {})
        if analysis.get("topic") and question_info.get("topic") == "general":
            question_info["topic"] = analysis["topic"]
        result = await self.evaluate_code(code, user_id, question_info)

        await self.personal_agent.track_user_behavior(
            {
                "user_id": user_id,
                "intent": "evaluation",
                "evaluation_score": result.get("overall_score", 0),
                "score": result.get("overall_score", 0) / 100,
                "correct": result.get("overall_score", 0) >= 70,
                "topic": question_info.get("topic", "general"),
                "difficulty": question_info.get("difficulty", "medium"),
                "code_length": len(code),
                "success": result.get("success", False),
                "error_patterns": [
                    issue["type"]
                    for issue in result["detailed_analysis"]["diagnostics"].get("issues", [])
                ],
            }
        )

        response = f"## 代码评估报告\n**综合得分**: {result['overall_score']}/100\n\n{result['feedback']}"
        return {"response": response, "details": result, "success": True}

    def _parse_evaluation_request(self, content: str) -> tuple[str, Dict[str, Any]]:
        stripped_content = content.strip()
        code = stripped_content
        question_info: Dict[str, Any] = {"topic": "general", "description": "代码评估请求", "difficulty": "medium"}
        fenced_match = re.search(r"```(?:python)?\s*(.*?)```", stripped_content, re.DOTALL | re.IGNORECASE)
        if fenced_match:
            code = fenced_match.group(1).strip()
            request_text = stripped_content.replace(fenced_match.group(0), "").strip()
        else:
            request_text = stripped_content
        if request_text:
            question_info["description"] = request_text[:300]

        topic_keywords = {
            "python_basics": ["def ", "print(", "input(", "for ", "while "],
            "data_structures": ["list", "dict", "set", "tuple", "[", "{"],
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
        return {"score": max(0, 100 - len(issues) * 5), "issues": issues[:20], "line_count": len(lines)}

    def _security_check(self, code: str, syntax: Dict[str, Any]) -> Dict[str, Any]:
        issues: List[str] = []
        if len(code) > Config.MAX_CODE_LENGTH:
            issues.append(f"Code exceeds the secure evaluation limit of {Config.MAX_CODE_LENGTH} characters.")
        if not syntax.get("valid", False):
            return {"safe_to_execute": False, "issues": issues, "execution_allowed": False}

        try:
            tree = ast.parse(code)
        except SyntaxError:
            return {"safe_to_execute": False, "issues": issues, "execution_allowed": False}

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
            elif isinstance(node, ast.Attribute) and node.attr in self.BLOCKED_ATTRIBUTES:
                issues.append(f"Blocked attribute access detected: {node.attr}")

        safe_to_execute = not issues
        return {
            "safe_to_execute": safe_to_execute,
            "issues": issues[:20],
            "execution_allowed": safe_to_execute and Config.ENABLE_UNTRUSTED_CODE_EXECUTION,
        }

    async def _run_code(self, code: str, syntax_valid: bool, security: Dict[str, Any]) -> Dict[str, Any]:
        if not syntax_valid:
            return {"skipped": True, "reason": "syntax_invalid"}
        if not security.get("safe_to_execute", False):
            return {"skipped": True, "reason": "security_blocked", "security_issues": security.get("issues", [])}
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
                    proc = subprocess.run(
                        [sys.executable, "-I", temp_path],
                        capture_output=True,
                        text=True,
                        timeout=Config.CODE_EXECUTION_TIMEOUT,
                        encoding="utf-8",
                        errors="replace",
                        cwd=tempfile.gettempdir(),
                        env={"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
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
                        "stderr": f"Execution timed out after {Config.CODE_EXECUTION_TIMEOUT} seconds.",
                        "duration_ms": float(Config.CODE_EXECUTION_TIMEOUT * 1000),
                        "timed_out": True,
                    }

            return await loop.run_in_executor(None, _run)
        finally:
            try:
                os.unlink(temp_path)
            except OSError:
                pass

    async def _run_example_tests(
        self,
        code: str,
        question_context: Dict[str, Any],
        syntax: Dict[str, Any],
        security: Dict[str, Any],
    ) -> Dict[str, Any]:
        examples = question_context.get("examples") or question_context.get("test_cases") or []
        if not examples:
            return {"skipped": True, "reason": "no_examples"}
        if not syntax.get("valid", False) or not security.get("safe_to_execute", False):
            return {"skipped": True, "reason": "not_safe_or_invalid"}
        if not Config.ENABLE_UNTRUSTED_CODE_EXECUTION:
            return {"skipped": True, "reason": "execution_disabled"}

        runnable_cases = []
        for example in examples[:5]:
            call = str(example.get("input") or example.get("call") or "").strip()
            expected = str(example.get("output") or example.get("expected") or "").strip()
            if call and expected:
                runnable_cases.append({"call": call, "expected": expected})
        if not runnable_cases:
            return {"skipped": True, "reason": "no_runnable_examples"}

        harness = (
            code
            + "\n\nimport json\ncases = "
            + repr(runnable_cases)
            + "\nfor case in cases:\n"
            + "    try:\n"
            + "        value = eval(case['call'])\n"
            + "        print(json.dumps({'call': case['call'], 'actual': str(value), 'expected': case['expected']}))\n"
            + "    except Exception as exc:\n"
            + "        print(json.dumps({'call': case['call'], 'error': type(exc).__name__ + ': ' + str(exc), 'expected': case['expected']}))\n"
        )
        result = await self._run_code(harness, syntax_valid=True, security=security)
        if result.get("skipped"):
            return result
        passed = 0
        failed = 0
        cases = []
        for line in str(result.get("stdout", "")).splitlines():
            try:
                item = json.loads(line)
            except Exception:
                continue
            actual = str(item.get("actual", "")).strip()
            expected = str(item.get("expected", "")).strip()
            ok = actual == expected
            passed += int(ok)
            failed += int(not ok)
            cases.append({**item, "passed": ok})
        return {"skipped": False, "passed": passed, "failed": failed, "cases": cases}

    def _diagnose_learning_issues(
        self,
        code: str,
        syntax: Dict[str, Any],
        style: Dict[str, Any],
        security: Dict[str, Any],
        question_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        issues: List[Dict[str, str]] = []
        hints: List[str] = []
        if not syntax.get("valid", False):
            error = (syntax.get("errors") or [{}])[0]
            issues.append(
                {
                    "type": "syntax",
                    "evidence": f"第 {error.get('lineno', '?')} 行附近: {error.get('message', '')}",
                    "teaching_hint": "先让代码能被 Python 解析，再讨论算法逻辑。",
                }
            )
            hints.append("检查冒号、缩进、括号是否成对。")
        if security.get("issues"):
            issues.append(
                {
                    "type": "unsafe_operation",
                    "evidence": "; ".join(security.get("issues", [])[:3]),
                    "teaching_hint": "练习题里尽量用纯函数和内存数据结构，避免文件、系统或网络操作。",
                }
            )
        if any("tabs" in item for item in style.get("issues", [])):
            issues.append({"type": "formatting", "evidence": "代码混用了 tab。", "teaching_hint": "统一使用 4 个空格缩进。"})
        if "return" not in code and question_context.get("topic") != "script":
            issues.append(
                {
                    "type": "missing_return",
                    "evidence": "代码里没有 return。",
                    "teaching_hint": "如果题目要求写函数，通常要返回结果，而不是只 print。",
                }
            )
            hints.append("确认题目是要输出到屏幕，还是要函数返回值。")
        if re.search(r"for\s+\w+\s+in\s+range\(len\(", code):
            issues.append(
                {
                    "type": "iteration_style",
                    "evidence": "使用了 range(len(...))。",
                    "teaching_hint": "很多情况下可以直接遍历元素，或用 enumerate 同时拿到下标和值。",
                }
            )
        if re.search(r"while\s+True\s*:", code) and "break" not in code:
            issues.append(
                {
                    "type": "possible_infinite_loop",
                    "evidence": "while True 没有明显 break。",
                    "teaching_hint": "写循环时先明确终止条件。",
                }
            )
            hints.append("用一个很小的输入手动走一遍循环。")

        if not hints:
            hints.append("下一步可以用 2 到 3 个边界输入测试代码。")
        return {
            "issue_count": len(issues),
            "issues": issues,
            "hint_levels": {
                "light": hints[0],
                "medium": "把题目的输入、处理、输出拆成三段检查。",
                "strong": "对照参考解法时，重点比较边界条件和返回值。",
            },
        }

    async def _llm_feedback(
        self,
        code: str,
        question_context: Dict[str, Any],
        syntax: Dict[str, Any],
        style: Dict[str, Any],
        run_result: Dict[str, Any],
        diagnostics: Dict[str, Any],
        test_result: Dict[str, Any],
    ) -> str:
        system_prompt = (
            "角色：你是严谨、耐心的编程助教。\n"
            "任务：基于给定的静态检查、运行结果和规则诊断，给学生可执行的反馈。\n"
            "约束：不得臆测不存在的运行结果；不得忽略安全问题；不得只给空泛鼓励。\n"
            "教学策略：先指出最可能阻塞程序正确性的 1-3 个问题，再给分级提示和最小修改建议。\n"
            "输出格式：中文 Markdown，包含「主要问题」「分级提示」「修改建议」「做得好的地方」「下一步练习」。"
        )
        user_message = f"""
题目上下文:
{question_context}

语法检查:
{syntax}

风格检查:
{style}

运行结果:
{run_result}

示例测试:
{test_result}

规则诊断:
{diagnostics}

学生代码:
```python
{code}
```
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
