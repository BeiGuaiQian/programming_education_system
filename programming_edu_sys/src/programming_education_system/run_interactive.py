# run_interactive.py (放在项目根目录)
"""
交互式系统启动脚本
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
        from programming_education_system.interactive_cli import main as cli_main
        print("🚀 启动编程教育智能体系统交互界面...")
        asyncio.run(cli_main())
    except ImportError as e:
        print(f"❌ 导入错误: {e}")
        print("请确保项目结构正确，且所有依赖已安装")
    except Exception as e:
        print(f"❌ 启动错误: {e}")

if __name__ == "__main__":
    main()