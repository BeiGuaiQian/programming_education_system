"""Static analysis and feedback helpers for the browser EduIDE."""

from __future__ import annotations

import ast
import re
from typing import Any, Dict, List, Optional


def analyze_code(
    code: str,
    expected_function: str = "",
    requirements: Optional[List[str]] = None,
) -> Dict[str, Any]:
    requirements = requirements or []
    diagnostics: List[Dict[str, Any]] = []
    complexity_blocks: List[Dict[str, Any]] = []

    tree = None
    try:
        tree = ast.parse(code or "")
    except SyntaxError as exc:
        diagnostics.append(_syntax_error_to_diagnostic(exc))

    if tree is not None:
        diagnostics.extend(_teaching_warnings(tree, code, expected_function, requirements))
        complexity_blocks = _estimate_complexity_blocks(tree)

    summary = _build_summary(diagnostics, complexity_blocks)
    return {
        "success": True,
        "diagnostics": diagnostics,
        "complexity_blocks": complexity_blocks,
        "summary": summary,
    }


def detect_stuck(
    code: str,
    duration_seconds: float,
    submit_count: int = 0,
    failed_submit_count: int = 0,
    diagnostics: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    diagnostics = diagnostics or []
    has_error = any(item.get("severity") == "error" for item in diagnostics)
    code_is_empty = not code.strip() or code.strip().endswith("pass")

    level = "none"
    reasons: List[str] = []
    if duration_seconds >= 180 and code_is_empty:
        level = "light"
        reasons.append("停留超过 3 分钟，但代码还没有明显推进。")
    if duration_seconds >= 300 and has_error:
        level = "medium"
        reasons.append("停留超过 5 分钟，并且代码里还有语法错误。")
    if failed_submit_count >= 2:
        level = "medium"
        reasons.append("已经连续多次提交失败。")
    if failed_submit_count >= 3:
        level = "high"
        reasons.append("连续 3 次以上提交失败，建议先定位一个最小问题。")

    hints = {
        "none": "",
        "light": "先把函数头和 return 写出来，不急着一次完成所有细节。",
        "medium": "建议先看红线或黄线位置，优先修复第一个错误，再重新运行。",
        "high": "可以先只保留最小函数实现，用题目的第一个示例测试，确认通过后再扩展。",
    }
    return {
        "stuck": level != "none",
        "level": level,
        "reasons": reasons,
        "hint": hints[level],
    }


def build_submit_feedback(
    code: str,
    analysis: Dict[str, Any],
    grading: Dict[str, Any],
    title: str = "当前题目",
) -> Dict[str, Any]:
    diagnostics = analysis.get("diagnostics", [])
    errors = [item for item in diagnostics if item.get("severity") == "error"]
    warnings = [item for item in diagnostics if item.get("severity") == "warning"]
    complexity_blocks = analysis.get("complexity_blocks", [])
    structured = grading.get("structured_feedback") or {}
    hidden_result = grading.get("test_result") or grading.get("hidden_test_result") or {}

    error_locations = []
    for item in errors[:4]:
        error_locations.append(
            {
                "line": item.get("line"),
                "column": item.get("column"),
                "message": item.get("message"),
                "suggestion": item.get("suggestion", ""),
            }
        )
    for item in structured.get("error_locations", [])[:4]:
        if item not in error_locations:
            error_locations.append(item)

    failed_tests = [
        item
        for item in hidden_result.get("test_results", [])
        if not item.get("passed", False)
    ]
    fix_points: List[str] = []
    if errors:
        fix_points.append("先修复红线语法错误，否则代码无法正常执行。")
    if failed_tests:
        first = failed_tests[0]
        fix_points.append(
            f"优先检查用例 {first.get('call', '')}：期望 {first.get('expected')!r}，实际 {first.get('actual')!r}。"
        )
    fix_points.extend(structured.get("fix_points", [])[:4])
    if warnings:
        fix_points.append("再处理黄线 warning，它们通常会影响可读性或题意匹配。")

    style_suggestions = list(structured.get("style_suggestions", [])[:4])
    for block in complexity_blocks:
        if block.get("complexity") in {"O(n^2)", "O(n^3)"}:
            style_suggestions.append(
                f"第 {block['line_start']} 行附近复杂度估计为 {block['complexity']}，数据量变大时可以考虑减少嵌套循环。"
            )
            break
    if not style_suggestions:
        style_suggestions.append("保持函数名、参数名和题意一致，代码会更容易被检查和复用。")

    passed = bool(grading.get("passed"))
    summary = (
        f"{title} 已通过。下一步可以关注代码可读性和复杂度。"
        if passed
        else f"{title} 暂未通过。建议按“语法 -> 测试用例 -> 风格”的顺序排查。"
    )
    return {
        "summary": summary,
        "error_locations": error_locations,
        "fix_points": _dedupe(fix_points)[:6],
        "style_suggestions": _dedupe(style_suggestions)[:6],
        "next_hint": "改完后先用示例手动想一遍输入输出，再提交判题。",
    }


def _syntax_error_to_diagnostic(exc: SyntaxError) -> Dict[str, Any]:
    message = exc.msg or "语法错误"
    suggestion = "检查这一行附近的括号、引号、冒号和缩进。"
    if ":" in message or "expected ':'" in message:
        suggestion = "if、for、while、def、class 这类语句末尾通常需要冒号。"
    if "indent" in message.lower():
        suggestion = "检查缩进是否统一，函数体、if/for/while 内部需要缩进。"
    return {
        "severity": "error",
        "code": "SyntaxError",
        "line": exc.lineno or 1,
        "column": exc.offset or 1,
        "end_line": exc.end_lineno or exc.lineno or 1,
        "end_column": exc.end_offset or exc.offset or 1,
        "message": message,
        "suggestion": suggestion,
    }


def _teaching_warnings(
    tree: ast.AST,
    code: str,
    expected_function: str,
    requirements: List[str],
) -> List[Dict[str, Any]]:
    warnings: List[Dict[str, Any]] = []
    function_defs = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    function_names = {node.name for node in function_defs}

    if expected_function and expected_function not in function_names:
        warnings.append(
            {
                "severity": "warning",
                "code": "expected-function-missing",
                "line": 1,
                "column": 1,
                "message": f"题目通常要求定义函数 `{expected_function}`，当前没有找到。",
                "suggestion": f"先写出函数头：def {expected_function}(...):",
            }
        )

    for node in function_defs:
        returns_value = any(
            isinstance(child, ast.Return) and child.value is not None
            for child in ast.walk(node)
        )
        prints = [child for child in ast.walk(node) if _is_print_call(child)]
        if prints and not returns_value:
            first = prints[0]
            warnings.append(
                {
                    "severity": "warning",
                    "code": "print-without-return",
                    "line": getattr(first, "lineno", getattr(node, "lineno", 1)),
                    "column": getattr(first, "col_offset", 0) + 1,
                    "message": "函数里使用了 print，但没有 return 返回结果。",
                    "suggestion": "如果题目要求“返回”，请把 print 改成 return。",
                }
            )
        if any(isinstance(child, ast.Pass) for child in ast.walk(node)):
            warnings.append(
                {
                    "severity": "warning",
                    "code": "pass-left",
                    "line": getattr(node, "lineno", 1),
                    "column": 1,
                    "message": f"函数 `{node.name}` 里还保留了 pass。",
                    "suggestion": "把 pass 替换成真正的计算逻辑或 return。",
                }
            )

    assigned = {
        target.id: node
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        for target in node.targets
        if isinstance(target, ast.Name)
    }
    used = {
        node.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load)
    }
    for name, node in assigned.items():
        if name not in used and not name.startswith("_"):
            warnings.append(
                {
                    "severity": "warning",
                    "code": "unused-variable",
                    "line": getattr(node, "lineno", 1),
                    "column": getattr(node, "col_offset", 0) + 1,
                    "message": f"变量 `{name}` 被赋值后没有使用。",
                    "suggestion": "如果这是最终结果，检查是否应该 return 它。",
                }
            )
    return warnings[:12]


def _estimate_complexity_blocks(tree: ast.AST) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)):
            if _has_loop_ancestor(tree, node):
                continue
            depth = _loop_depth(node)
            complexity = "O(n)" if depth <= 1 else f"O(n^{depth})"
            if isinstance(node, ast.While) and _looks_logarithmic(node):
                complexity = "O(log n)"
            if _contains_sort_call(node) and complexity == "O(n)":
                complexity = "O(n log n)"
            blocks.append(
                {
                    "line_start": getattr(node, "lineno", 1),
                    "line_end": getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                    "complexity": complexity,
                    "confidence": "medium" if isinstance(node, ast.While) else "high",
                    "reason": "检测到一个完整循环代码块，已合并内部嵌套循环或排序操作。",
                }
            )
        if (
            isinstance(node, ast.Call)
            and _call_name(node.func) in {"sorted", "sort"}
            and not _has_loop_ancestor(tree, node)
        ):
            blocks.append(
                {
                    "line_start": getattr(node, "lineno", 1),
                    "line_end": getattr(node, "end_lineno", getattr(node, "lineno", 1)),
                    "complexity": "O(n log n)",
                    "confidence": "high",
                    "reason": "检测到排序操作，常见时间复杂度约为 O(n log n)。",
                }
            )
    return sorted(blocks, key=lambda item: (item["line_start"], item["line_end"]))[:10]


def _has_loop_ancestor(tree: ast.AST, target: ast.AST) -> bool:
    for node in ast.walk(tree):
        if node is target or not isinstance(node, (ast.For, ast.While)):
            continue
        for child in ast.walk(node):
            if child is target:
                return True
    return False


def _contains_sort_call(node: ast.AST) -> bool:
    return any(
        isinstance(child, ast.Call) and _call_name(child.func) in {"sorted", "sort"}
        for child in ast.walk(node)
    )


def _loop_depth(node: ast.AST) -> int:
    child_depths = [
        _loop_depth(child)
        for child in ast.iter_child_nodes(node)
        if child is not node
    ]
    nested = max(child_depths, default=0)
    return nested + (1 if isinstance(node, (ast.For, ast.While)) else 0)


def _looks_logarithmic(node: ast.While) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.AugAssign) and isinstance(child.op, (ast.FloorDiv, ast.Div)):
            return True
        if isinstance(child, ast.Assign) and isinstance(child.value, ast.BinOp) and isinstance(child.value.op, (ast.FloorDiv, ast.Div)):
            return True
    return False


def _is_print_call(node: ast.AST) -> bool:
    return isinstance(node, ast.Call) and _call_name(node.func) == "print"


def _call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        return func.attr
    return ""


def _build_summary(diagnostics: List[Dict[str, Any]], blocks: List[Dict[str, Any]]) -> str:
    errors = sum(1 for item in diagnostics if item.get("severity") == "error")
    warnings = sum(1 for item in diagnostics if item.get("severity") == "warning")
    if errors:
        return f"发现 {errors} 个语法错误，需要先修复红线位置。"
    if warnings:
        return f"代码可以运行，但有 {warnings} 个 warning 建议处理。"
    if blocks:
        return "代码结构基本可分析，复杂度提示已标注在编辑器中。"
    return "暂未发现明显问题。"


def _dedupe(items: List[str]) -> List[str]:
    seen = set()
    result = []
    for item in items:
        clean = str(item).strip()
        if clean and clean not in seen:
            seen.add(clean)
            result.append(clean)
    return result
