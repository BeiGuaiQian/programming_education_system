"""
Console entry for setuptools (`progedu`). Same behavior as project `run_final.py`.
"""

import asyncio
import os
import sys

# Ensure package import works when running as script or via console_scripts
_pkg_root = os.path.dirname(os.path.abspath(__file__))
_src_root = os.path.dirname(_pkg_root)
if _src_root not in sys.path:
    sys.path.insert(0, _src_root)


def main():
    """Start the interactive CLI (same as run_final.py)."""
    try:
        from programming_education_system.interactive_cli_final import main as cli_main

        print("🚀 启动编程教育智能体系统 - 最终版")
        print("🧠 LLM-UM框架已集成 | 📚 所有功能已整合")
        print("=" * 50)
        asyncio.run(cli_main())
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保项目结构正确:")
        print("  project_root/")
        print("  ├── src/")
        print("  │   └── programming_education_system/")
        print("  │       ├── main_final.py")
        print("  │       ├── interactive_cli_final.py")
        print("  │       └── cognition_judger/")
        print("  └── run_final.py")
    except Exception as e:
        print(f"❌ 启动错误: {e}")


if __name__ == "__main__":
    main()
