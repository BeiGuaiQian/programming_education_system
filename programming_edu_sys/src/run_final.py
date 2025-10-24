# run_final.py (放在项目根目录)
"""
最终版系统启动脚本
使用LLM-UM框架，集成所有功能
"""
import sys
import os
import asyncio

# 添加src目录到Python路径
src_dir = os.path.join(os.path.dirname(__file__), 'src')
sys.path.insert(0, src_dir)

def main():
    """主函数"""
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
        print("  │           └── cognitive_api_llm_um.py")
        print("  └── run_final.py")
    except Exception as e:
        print(f"❌ 启动错误: {e}")

if __name__ == "__main__":
    main()