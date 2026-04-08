"""Project self-check utility."""

from __future__ import annotations

import asyncio
import importlib
import sys
from pathlib import Path
from typing import List, Tuple


PROJECT_SRC = Path(__file__).resolve().parents[2]


def run_import_checks() -> List[Tuple[str, bool, str]]:
    modules = [
        "programming_education_system",
        "programming_education_system.main_final",
        "programming_education_system.interactive_cli_final",
        "programming_education_system.agents.user_agent",
        "programming_education_system.agents.main_agent",
        "programming_education_system.agents.qa_agent",
        "programming_education_system.agents.exercise_agent",
        "programming_education_system.agents.evaluation_agent",
        "programming_education_system.agents.personal_agent",
    ]
    results: List[Tuple[str, bool, str]] = []
    for module in modules:
        try:
            importlib.import_module(module)
            results.append((module, True, "ok"))
        except Exception as exc:  # pragma: no cover - diagnostic path
            results.append((module, False, f"{type(exc).__name__}: {exc}"))
    return results


async def run_smoke_test() -> Tuple[bool, str]:
    from programming_education_system.main_final import get_system

    system = get_system()
    result = await system.process_user_request(
        "qa",
        "Python 中函数是什么？",
        user_id="self_check_user",
    )
    if result.get("success") and result.get("response"):
        return True, str(result["response"])[:120]
    return False, "Smoke test returned an empty or failed response."


def main() -> int:
    if str(PROJECT_SRC) not in sys.path:
        sys.path.insert(0, str(PROJECT_SRC))

    print("Running import checks...")
    import_results = run_import_checks()
    has_error = False
    for module, ok, detail in import_results:
        status = "OK" if ok else "FAIL"
        print(f"[{status}] {module}: {detail}")
        has_error = has_error or not ok

    print("\nRunning smoke test...")
    smoke_ok, smoke_detail = asyncio.run(run_smoke_test())
    print(f"[{'OK' if smoke_ok else 'FAIL'}] smoke_test: {smoke_detail}")
    has_error = has_error or not smoke_ok

    return 1 if has_error else 0


if __name__ == "__main__":
    raise SystemExit(main())
