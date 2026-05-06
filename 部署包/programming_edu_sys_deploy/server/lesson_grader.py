"""Lesson submission grading helpers."""

from __future__ import annotations

import ast
import asyncio
import json
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict, List, Optional

from programming_education_system.main_final import get_system


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

BLOCKED_CALLS = {"eval", "exec", "__import__", "open", "input", "compile", "breakpoint"}


def _make_diagnostic(
    message: str,
    suggestion: str,
    line: Optional[int] = None,
    column: Optional[int] = None,
    severity: str = "error",
) -> Dict[str, Any]:
    return {
        "line": line,
        "column": column,
        "severity": severity,
        "message": message,
        "suggestion": suggestion,
    }


def _find_function_names(tree: ast.AST) -> set[str]:
    return {node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}


def _get_call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def validate_lesson_code(code: str, required_function: str) -> List[str]:
    """Return blocking validation errors before hidden tests are run."""
    errors: List[str] = []
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return [f"语法错误: {exc.msg}"]

    function_names = _find_function_names(tree)
    if required_function not in function_names:
        errors.append(f"未找到必需函数 `{required_function}`。")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split(".", 1)[0]
                if module_name in BLOCKED_IMPORTS:
                    errors.append(f"检测到不允许的导入: {module_name}")
        elif isinstance(node, ast.ImportFrom):
            module_name = (node.module or "").split(".", 1)[0]
            if module_name in BLOCKED_IMPORTS:
                errors.append(f"检测到不允许的导入: {module_name}")
        elif isinstance(node, ast.Call):
            call_name = _get_call_name(node.func)
            if call_name in BLOCKED_CALLS:
                errors.append(f"检测到不允许的调用: {call_name}")

    return errors[:20]


def analyze_lesson_code(
    code: str,
    lesson: Dict[str, Any],
    hidden_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build student-facing diagnostics for a lesson submission."""
    exercise = lesson["exercise"]
    required_function = exercise.get("expected_function", "")
    diagnostics: List[Dict[str, Any]] = []
    fix_points: List[str] = []
    style_suggestions: List[str] = []
    positive_notes: List[str] = []

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        diagnostics.append(
            _make_diagnostic(
                message=f"这里有语法错误：{exc.msg}",
                suggestion="先修正这一行附近的括号、冒号、引号或缩进，再重新提交。",
                line=getattr(exc, "lineno", None),
                column=getattr(exc, "offset", None),
            )
        )
        return {
            "summary": "代码还没有通过基础语法检查。先把语法错误修掉，后面的测试才能继续运行。",
            "error_locations": diagnostics,
            "fix_points": ["优先处理标出的语法错误。", "确认函数头末尾有冒号，并且函数体有正确缩进。"],
            "style_suggestions": ["语法稳定后，再考虑命名、简洁度和可读性。"],
            "positive_notes": ["已经开始动手写代码了，这是最重要的一步。"],
        }

    function_nodes = {
        node.name: node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    }
    target_func = function_nodes.get(required_function)

    if required_function and target_func is None:
        diagnostics.append(
            _make_diagnostic(
                message=f"没有找到题目要求的函数 `{required_function}`。",
                suggestion=f"请确认函数名写成 `def {required_function}(...):`，不要改成其他名字。",
            )
        )
        fix_points.append(f"补上函数 `{required_function}`，函数名要和题目要求完全一致。")
    elif target_func is not None:
        positive_notes.append(f"函数 `{required_function}` 已经定义出来了。")
        expected_arg_count = 1 if required_function == "greet" else None
        if expected_arg_count is not None and len(target_func.args.args) != expected_arg_count:
            diagnostics.append(
                _make_diagnostic(
                    message=f"`{required_function}` 的参数数量不符合题目要求。",
                    suggestion="这一题只需要一个参数 `name`，可以写成 `def greet(name):`。",
                    line=target_func.lineno,
                    column=target_func.col_offset + 1,
                )
            )
            fix_points.append("检查函数参数列表，确保只接收题目要求的参数。")

        returns = [node for node in ast.walk(target_func) if isinstance(node, ast.Return)]
        if not returns:
            diagnostics.append(
                _make_diagnostic(
                    message=f"`{required_function}` 里面没有 `return`。",
                    suggestion="题目要求返回字符串，建议用 `return f\"Hello, {name}!\"`。",
                    line=target_func.lineno,
                    column=target_func.col_offset + 1,
                )
            )
            fix_points.append("把只显示结果的写法改成返回结果的写法，也就是使用 `return`。")
        else:
            positive_notes.append("函数里已经使用了 `return`，方向是对的。")

        for node in ast.walk(target_func):
            if isinstance(node, ast.Call) and _get_call_name(node.func) == "print":
                diagnostics.append(
                    _make_diagnostic(
                        message="函数里使用了 `print`，但这道题更关心返回值。",
                        suggestion="如果只是为了调试可以临时 print；正式答案里建议返回字符串。",
                        line=node.lineno,
                        column=node.col_offset + 1,
                        severity="warning",
                    )
                )
                style_suggestions.append("练习题要求“返回”时，优先写 `return`，不要用 `print` 代替结果。")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                module_name = alias.name.split(".", 1)[0]
                if module_name in BLOCKED_IMPORTS:
                    diagnostics.append(
                        _make_diagnostic(
                            message=f"检测到不允许的导入 `{module_name}`。",
                            suggestion="这类基础题不需要导入系统或文件相关模块，直接使用函数和字符串即可。",
                            line=node.lineno,
                            column=node.col_offset + 1,
                        )
                    )
        elif isinstance(node, ast.ImportFrom):
            module_name = (node.module or "").split(".", 1)[0]
            if module_name in BLOCKED_IMPORTS:
                diagnostics.append(
                    _make_diagnostic(
                        message=f"检测到不允许的导入 `{module_name}`。",
                        suggestion="请去掉这个导入，本题只需要普通 Python 表达式。",
                        line=node.lineno,
                        column=node.col_offset + 1,
                    )
                )
        elif isinstance(node, ast.Call):
            call_name = _get_call_name(node.func)
            if call_name in BLOCKED_CALLS:
                diagnostics.append(
                    _make_diagnostic(
                        message=f"检测到不允许的调用 `{call_name}`。",
                        suggestion="为了安全和可控判题，请不要在答案里使用这类动态执行或输入输出函数。",
                        line=node.lineno,
                        column=node.col_offset + 1,
                    )
                )

    hidden_result = hidden_result or {}
    failed_tests = [
        item for item in hidden_result.get("test_results", []) if not item.get("passed")
    ]
    for item in failed_tests[:3]:
        diagnostics.append(
            _make_diagnostic(
                message=(
                    f"测试 `{item.get('call')}` 没有通过：期望 `{item.get('expected')}`，"
                    f"实际得到 `{item.get('actual')}`。"
                ),
                suggestion="对照期望输出检查字符串内容、空格、标点和是否真正返回了结果。",
                severity="error",
            )
        )
    if failed_tests:
        fix_points.append("根据未通过的测试，逐字检查返回字符串，尤其是逗号、空格和感叹号。")
    elif hidden_result.get("test_results"):
        positive_notes.append("隐藏测试已经全部通过，说明核心功能正确。")

    lines = code.splitlines()
    for index, line in enumerate(lines, start=1):
        if "\t" in line:
            style_suggestions.append(f"第 {index} 行包含 Tab，建议统一使用 4 个空格缩进。")
        if len(line) > 88:
            style_suggestions.append(f"第 {index} 行偏长，可以适当拆分，让代码更容易阅读。")

    if target_func is not None and not style_suggestions:
        style_suggestions.append("当前代码比较短，保持清晰命名和稳定缩进就很好。")
    if not positive_notes:
        positive_notes.append("你已经提交了可分析的代码，下一步就是按反馈逐项修正。")

    if hidden_result.get("passed"):
        summary = "功能测试已经通过。下面的建议主要帮助你把代码写得更清楚、更像正式答案。"
    elif diagnostics:
        summary = "代码还没有完全通过。先看“错误位置”，再按“修改要点”逐项处理。"
    else:
        summary = "代码结构基本可读，但还需要结合题目要求再确认返回值是否完全一致。"

    return {
        "summary": summary,
        "error_locations": diagnostics[:10],
        "fix_points": fix_points[:8] or ["对照题目要求，确认函数名、参数和返回值三件事都一致。"],
        "style_suggestions": style_suggestions[:8],
        "positive_notes": positive_notes[:5],
    }


def format_structured_feedback(structured: Dict[str, Any]) -> str:
    """Convert structured diagnostics into a compact text summary for storage."""
    sections = [structured.get("summary", "")]
    section_map = [
        ("错误位置", structured.get("error_locations", [])),
        ("修改要点", structured.get("fix_points", [])),
        ("代码风格建议", structured.get("style_suggestions", [])),
        ("做得不错", structured.get("positive_notes", [])),
    ]
    for title, items in section_map:
        if not items:
            continue
        sections.append(f"\n{title}:")
        for item in items:
            if isinstance(item, dict):
                line = item.get("line")
                prefix = f"第 {line} 行：" if line else ""
                sections.append(f"- {prefix}{item.get('message')} 建议：{item.get('suggestion')}")
            else:
                sections.append(f"- {item}")
    return "\n".join(part for part in sections if part)


async def run_hidden_tests(code: str, lesson: Dict[str, Any]) -> Dict[str, Any]:
    """Execute hidden tests in a separate isolated Python process."""
    hidden_tests = lesson["exercise"]["hidden_tests"]
    required_function = lesson["exercise"].get("expected_function", "")
    validation_errors = validate_lesson_code(code, required_function) if required_function else []
    if validation_errors:
        return {
            "passed": False,
            "score": 0.0,
            "test_results": [],
            "validation_errors": validation_errors,
        }

    script = "\n".join(
        [
            "import contextlib",
            "import io",
            "import json",
            "",
            f"submitted_code = {json.dumps(code, ensure_ascii=False)}",
            f"test_cases = {json.dumps(hidden_tests, ensure_ascii=False)}",
            "namespace = {}",
            "setup_stdout = io.StringIO()",
            "try:",
            "    with contextlib.redirect_stdout(setup_stdout):",
            "        exec(submitted_code, namespace)",
            "except Exception as exc:",
            "    print(json.dumps({",
            "        'passed': False,",
            "        'score': 0.0,",
            "        'test_results': [],",
            "        'validation_errors': [f'代码准备阶段运行失败: {exc}'],",
            "        'stdout': setup_stdout.getvalue()",
            "    }, ensure_ascii=False, default=str))",
            "    raise SystemExit(0)",
            "results = []",
            "passed = 0",
            "",
            "for case in test_cases:",
            "    expr = case['call']",
            "    expected = case['expected']",
            "    try:",
            "        captured_stdout = io.StringIO()",
            "        with contextlib.redirect_stdout(captured_stdout):",
            "            actual = eval(expr, namespace)",
            "        ok = actual == expected",
            "        if ok:",
            "            passed += 1",
            "        results.append({",
            "            'call': expr,",
            "            'expected': expected,",
            "            'actual': actual,",
            "            'stdout': captured_stdout.getvalue(),",
            "            'passed': ok",
            "        })",
            "    except Exception as exc:",
            "        results.append({",
            "            'call': expr,",
            "            'expected': expected,",
            "            'actual': f'ERROR: {exc}',",
            "            'stdout': captured_stdout.getvalue() if 'captured_stdout' in locals() else '',",
            "            'passed': False",
            "        })",
            "",
            "total = len(test_cases)",
            "score = round((passed / total) * 100, 1) if total else 0.0",
            "print(json.dumps({",
            "    'passed': passed == total,",
            "    'score': score,",
            "    'test_results': results",
            "}, ensure_ascii=False, default=str))",
            "",
        ]
    )

    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as handle:
        handle.write(script)
        temp_path = handle.name

    try:
        def _run() -> Dict[str, Any]:
            proc = subprocess.run(
                [sys.executable, "-I", temp_path],
                capture_output=True,
                text=True,
                timeout=5,
                encoding="utf-8",
                errors="replace",
                cwd=tempfile.gettempdir(),
                env={"PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"},
            )
            if proc.returncode != 0:
                return {
                    "passed": False,
                    "score": 0.0,
                    "test_results": [],
                    "validation_errors": [proc.stderr[:500] or "代码运行失败"],
                }
            try:
                return json.loads(proc.stdout.strip())
            except json.JSONDecodeError:
                return {
                    "passed": False,
                    "score": 0.0,
                    "test_results": [],
                    "validation_errors": ["判题结果解析失败，请检查代码是否在函数外直接输出内容。"],
                }

        return await asyncio.to_thread(_run)
    except subprocess.TimeoutExpired:
        return {
            "passed": False,
            "score": 0.0,
            "test_results": [],
            "validation_errors": ["代码运行超时，请检查是否存在死循环。"],
        }
    finally:
        try:
            os.unlink(temp_path)
        except OSError:
            pass


async def grade_lesson_submission(code: str, lesson: Dict[str, Any], user_id: str) -> Dict[str, Any]:
    """Combine hidden tests with agent evaluation feedback."""
    hidden_result = await run_hidden_tests(code, lesson)
    structured_feedback = analyze_lesson_code(code, lesson, hidden_result)
    validation_errors = hidden_result.get("validation_errors", [])
    if validation_errors:
        feedback = format_structured_feedback(structured_feedback)
        return {
            "passed": False,
            "score": float(hidden_result.get("score", 0.0)),
            "feedback": feedback,
            "structured_feedback": structured_feedback,
            "hidden_test_result": hidden_result,
            "agent_evaluation": {
                "success": False,
                "response": feedback,
                "details": {"reason": "validation_failed"},
            },
        }

    system = get_system()
    exercise = lesson.get("exercise", {})
    evaluation_prompt = (
        f"请评价下面这份 Python 练习答案。\n"
        f"题目：{exercise.get('title', '')}\n"
        f"要求：{exercise.get('description', '')}\n"
        f"隐藏测试结果：{json.dumps(hidden_result, ensure_ascii=False)}\n\n"
        "请用中文反馈，重点包含：代码中错误的地方、需要修改的要点、代码风格提升建议。"
        "如果已经通过，也请说明可以继续优化的地方。\n\n"
        f"```python\n{code}\n```"
    )
    evaluation = await system.process_user_request(
        "evaluation",
        evaluation_prompt,
        user_id=user_id,
    )

    evaluation_text = str(evaluation.get("response", ""))
    passed = bool(hidden_result.get("passed", False))
    score = float(hidden_result.get("score", 0.0))
    feedback = format_structured_feedback(structured_feedback)
    if evaluation_text:
        feedback = f"{feedback}\n\n智能体补充建议:\n{evaluation_text}"

    return {
        "passed": passed,
        "score": score,
        "feedback": feedback,
        "structured_feedback": structured_feedback,
        "hidden_test_result": hidden_result,
        "agent_evaluation": evaluation,
    }
