"""Launch script for the programming education system."""

from __future__ import annotations

import asyncio
import os
import sys

SRC_DIR = os.path.join(os.path.dirname(__file__), "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)


def _configure_console_encoding() -> None:
    """Prefer UTF-8 output to avoid garbled Chinese text on Windows terminals."""
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    os.environ.setdefault("PYTHONUTF8", "1")

    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass

    if os.name == "nt":
        try:
            os.system("chcp 65001 > nul")
        except Exception:
            pass


def main() -> None:
    """Start the interactive CLI."""
    try:
        _configure_console_encoding()
        from programming_education_system.interactive_cli_final import main as cli_main

        print("启动编程教育智能体系统")
        print("交互终端和核心代理已加载")
        print("=" * 50)
        asyncio.run(cli_main())
    except ImportError as exc:
        print(f"导入失败: {exc}")
        print("请确认项目目录下存在 `src/programming_education_system`。")
    except Exception as exc:
        print(f"启动失败: {exc}")


if __name__ == "__main__":
    main()
