# src/programming_education_system/interactive_cli.py
"""
交互式命令行界面 - 简化版本
"""
import asyncio
import logging
import sys
import os
from typing import Dict, Any, List

# 添加src目录到路径
src_dir = os.path.join(os.path.dirname(__file__), '..', '..')
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

from programming_education_system.main import get_system


class InteractiveCLI:
    """交互式命令行界面 - 简化版本"""

    def __init__(self):
        self.system = get_system()
        self.user_id = "interactive_user"
        self.session_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("CLI")

    async def start_session(self):
        """开始交互会话"""
        print("\n" + "=" * 60)
        print("  编程教育智能体系统 - 交互式终端")
        print("=" * 60)
        print("\n🎯 系统特点：")
        print("  • 智能输入优化 - 自动优化您的输入")
        print("  • 智能意图识别 - 自动理解您的需求")
        print("  • 多场景支持 - 答疑、练习、代码评价、个性化建议")
        print("\n💡 提示：直接输入您的问题或需求")
        print("输入 'help' 查看帮助，输入 'exit' 退出系统。")
        print("-" * 60)

        while True:
            try:
                user_input = input("\n👤 您: ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit', '退出']:
                    await self._handle_exit()
                    break

                elif user_input.lower() in ['help', '帮助']:
                    self._show_help()

                elif user_input.lower() in ['history', '历史']:
                    self._show_history()

                elif user_input.lower() in ['clear', '清空']:
                    self._clear_history()

                else:
                    await self._process_user_input(user_input)

            except KeyboardInterrupt:
                await self._handle_exit()
                break
            except Exception as e:
                print(f"❌ 系统错误: {e}")
                self.logger.error(f"CLI错误: {e}")

    async def _process_user_input(self, user_input: str):
        """处理用户输入"""
        print("🔧 正在处理您的请求...")

        try:
            # 使用 "auto" 类型，让系统自动处理
            result = await self.system.process_user_request(
                "auto", user_input, self.user_id
            )

            # 记录会话历史
            self.session_history.append({
                "request": user_input,
                "response": result.get("response", ""),
                "type": result.get("request_type", "unknown"),
                "enhancement_applied": result.get("processing_info", {}).get("input_enhanced", False),
                "timestamp": asyncio.get_event_loop().time()
            })

            # 显示结果
            self._display_result(result)

        except Exception as e:
            error_msg = f"处理请求时出错: {e}"
            print(f"❌ {error_msg}")
            self.session_history.append({
                "request": user_input,
                "response": error_msg,
                "type": "error",
                "enhancement_applied": False,
                "timestamp": asyncio.get_event_loop().time()
            })

    def _display_result(self, result: Dict[str, Any]):
        """显示处理结果"""
        print("\n" + "🤖 智能体: " + "=" * 50)

        if result.get("success", False):
            response = result.get("response", "")
            details = result.get("details", {})
            request_type = result.get("request_type", "unknown")
            processing_info = result.get("processing_info", {})

            # 显示优化信息
            if processing_info.get("input_enhanced", False):
                print("✨ 输入已优化")

            # 显示处理类型
            intent_info = self._get_intent_display_info(request_type)
            print(f"{intent_info['emoji']} {intent_info['name']}")

            # 显示主要响应
            print(f"\n💡 {response}")

            # 显示详细信息
            if details:
                print("\n📋 详细信息:")

                # 显示练习题目
                if "exercises" in details:
                    for i, exercise in enumerate(details["exercises"], 1):
                        print(f"  {i}. {exercise.get('content', '')}")

                # 显示学习建议
                if "suggestions" in details:
                    for i, suggestion in enumerate(details["suggestions"], 1):
                        print(f"  • {suggestion}")

        else:
            print(f"❌ 处理失败: {result.get('error', '未知错误')}")

        print("=" * 60)

    def _get_intent_display_info(self, intent: str) -> Dict[str, str]:
        """获取意图的显示信息"""
        intent_info = {
            "qa": {
                "emoji": "💬",
                "name": "智能答疑"
            },
            "exercise": {
                "emoji": "📝",
                "name": "练习生成"
            },
            "evaluation": {
                "emoji": "🔍",
                "name": "代码评价"
            },
            "personal": {
                "emoji": "🎯",
                "name": "个性化建议"
            }
        }
        return intent_info.get(intent, {
            "emoji": "❓",
            "name": "未知类型"
        })

    def _show_help(self):
        """显示帮助信息"""
        help_text = """
📖 可用命令:

💬 自由提问:
  直接输入您的问题或需求，系统会自动优化和理解：
  "Python中如何定义函数？"
  "生成一个Python练习"
  "检查这段代码：def add(a, b): return a + b"
  "给我学习建议"

🛠️ 系统命令:
  help / 帮助    - 显示此帮助信息
  history / 历史 - 显示会话历史
  clear / 清空   - 清空会话历史
  exit / 退出    - 退出系统
        """
        print(help_text)

    def _show_history(self):
        """显示会话历史"""
        if not self.session_history:
            print("📝 暂无会话历史")
            return

        print(f"\n📝 会话历史 (共{len(self.session_history)}条):")
        for i, item in enumerate(self.session_history[-10:], 1):
            intent_info = self._get_intent_display_info(item['type'])
            enhancement_indicator = "✨" if item.get('enhancement_applied', False) else ""
            print(f"\n{i}. {enhancement_indicator} {intent_info['emoji']} {item['request'][:50]}...")
            print(f"   响应: {item['response'][:80]}...")

    def _clear_history(self):
        """清空会话历史"""
        self.session_history.clear()
        print("🗑️ 会话历史已清空")

    async def _handle_exit(self):
        """处理退出"""
        print("\n👋 感谢使用编程教育智能体系统！")
        print("📊 本次会话统计:")
        print(f"  • 总交互次数: {len(self.session_history)}")

        # 统计各类型请求
        type_count = {}
        for item in self.session_history:
            req_type = item["type"]
            type_count[req_type] = type_count.get(req_type, 0) + 1

        for req_type, count in type_count.items():
            intent_info = self._get_intent_display_info(req_type)
            print(f"  • {intent_info['emoji']} {intent_info['name']}: {count}次")

        print("期待下次为您服务！🎓")


async def main():
    """主函数"""
    cli = InteractiveCLI()
    await cli.start_session()


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行交互式界面
    asyncio.run(main())