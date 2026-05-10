"""Interactive CLI for the programming education system."""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import Any, Dict, List

SRC_DIR = os.path.join(os.path.dirname(__file__), "..", "..")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

from programming_education_system.main_final import get_system


class FinalInteractiveCLI:
    """Simple terminal interface for interacting with the system."""

    def __init__(self) -> None:
        self.system = get_system()
        self.user_id = "interactive_user"
        self.session_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("CLI-Final")
        self.show_profile_insights = True

    async def start_session(self) -> None:
        print("\n" + "=" * 60)
        print("编程教育智能体系统 - 交互终端")
        print("=" * 60)
        print("直接输入你的问题、练习需求、代码评估请求或学习建议请求。")
        print("输入 `help` 查看命令，输入 `exit` 退出。")
        print("-" * 60)

        while True:
            try:
                user_input = input("\n你> ").strip()
                if not user_input:
                    continue
                lowered = user_input.lower()

                if lowered in {"exit", "quit", "退出"}:
                    await self._handle_exit()
                    break
                if lowered in {"help", "帮助"}:
                    self._show_help()
                    continue
                if lowered in {"history", "历史"}:
                    self._show_history()
                    continue
                if lowered in {"clear", "清空"}:
                    self._clear_history()
                    continue
                if lowered in {"profile", "画像"}:
                    await self._toggle_profile_mode()
                    continue
                if lowered in {"status", "状态"}:
                    await self._show_system_status()
                    continue
                if lowered in {"report", "报告"}:
                    await self._show_profile_report()
                    continue

                await self._process_user_input(user_input)
            except KeyboardInterrupt:
                await self._handle_exit()
                break
            except Exception as exc:
                print(f"系统错误: {exc}")
                self.logger.error("CLI error: %s", exc)

    async def _process_user_input(self, user_input: str) -> None:
        print("正在处理你的请求...")
        try:
            result = await self.system.process_user_request("auto", user_input, self.user_id)
            self.session_history.append(
                {
                    "request": user_input,
                    "response": result.get("response", ""),
                    "type": result.get("request_type", "unknown"),
                    "success": result.get("success", False),
                    "timestamp": asyncio.get_event_loop().time(),
                    "profile_insights": result.get("details", {}).get("profile_insights", {}),
                }
            )
            self._display_final_result(result)
        except Exception as exc:
            error_msg = f"处理请求时出错: {exc}"
            print(error_msg)
            self.session_history.append(
                {
                    "request": user_input,
                    "response": error_msg,
                    "type": "error",
                    "success": False,
                    "timestamp": asyncio.get_event_loop().time(),
                    "profile_insights": {},
                }
            )

    def _display_final_result(self, result: Dict[str, Any]) -> None:
        print("\n" + "系统回答 " + "=" * 52)
        if not result.get("success", False):
            print(f"处理失败: {result.get('error', '未知错误')}")
            print("=" * 60)
            return

        request_type = result.get("request_type", "unknown")
        details = result.get("details", {})
        intent_info = self._get_intent_display_info(request_type)
        print(f"{intent_info['label']}")
        print(f"\n{result.get('response', '')}")

        if details:
            print("\n补充信息:")
            if details.get("examples"):
                print("示例:")
                for example in details["examples"][:3]:
                    print(f"- {example}")
            if details.get("suggestions"):
                print("建议:")
                for suggestion in details["suggestions"][:5]:
                    print(f"- {suggestion}")
            if details.get("learning_tips"):
                print("学习提示:")
                for tip in details["learning_tips"][:5]:
                    print(f"- {tip}")

        if self.show_profile_insights:
            self._display_profile_insights(details.get("profile_insights", {}))
        print("=" * 60)

    def _display_profile_insights(self, insights: Dict[str, Any]) -> None:
        if not insights:
            return

        print("\n画像洞察:")
        print(f"- 用户类型: {insights.get('user_type', 'unknown')}")
        print(f"- 主题掌握度: {float(insights.get('topic_mastery', 0.5)):.2f}")
        print(f"- 推荐难度: {insights.get('recommended_difficulty', 'intermediate')}")
        focus_areas = insights.get("focus_areas", [])
        if focus_areas:
            print(f"- 建议聚焦: {', '.join(map(str, focus_areas))}")

    def _get_intent_display_info(self, intent: str) -> Dict[str, str]:
        intent_info = {
            "qa": {"label": "问答模式"},
            "exercise": {"label": "练习生成模式"},
            "evaluation": {"label": "代码评估模式"},
            "personal": {"label": "个性化建议模式"},
            "unknown": {"label": "自动路由模式"},
        }
        return intent_info.get(intent, intent_info["unknown"])

    async def _toggle_profile_mode(self) -> None:
        self.show_profile_insights = not self.show_profile_insights
        print(f"画像洞察显示已{'开启' if self.show_profile_insights else '关闭'}。")

    async def _show_system_status(self) -> None:
        status = await self.system.get_system_status()
        print("\n系统状态:")
        for key, value in status.items():
            if key == "timestamp":
                continue
            print(f"- {key}: {value}")

    async def _show_profile_report(self) -> None:
        report = await self.system.get_user_profile_report(self.user_id)
        if "error" in report:
            print(f"获取用户画像失败: {report['error']}")
            return

        print("\n用户画像报告:")
        user_profile = report.get("user_profile", {})
        print(f"- 用户: {report.get('user_id', self.user_id)}")
        print(f"- 画像来源: {report.get('profile_source', 'personalized_learning_agent')}")
        print(f"- 当前水平: {user_profile.get('programming_level', 'unknown')}")
        print(f"- 学习风格: {user_profile.get('learning_style', 'unknown')}")
        weak_topics = user_profile.get("weak_topics", [])
        if weak_topics:
            print(f"- 薄弱主题: {', '.join(map(str, weak_topics[:3]))}")

    def _show_help(self) -> None:
        print(
            "\n可用命令:\n"
            "- help / 帮助: 查看帮助\n"
            "- history / 历史: 查看最近会话\n"
            "- clear / 清空: 清空会话记录\n"
            "- profile / 画像: 开关画像洞察显示\n"
            "- status / 状态: 查看系统状态\n"
            "- report / 报告: 查看用户画像报告\n"
            "- exit / 退出: 退出系统\n"
            "\n直接输入自然语言即可，系统会自动判断是问答、练习、评估还是学习建议。"
        )

    def _show_history(self) -> None:
        if not self.session_history:
            print("暂无会话历史。")
            return
        print(f"\n最近会话 ({len(self.session_history)} 条):")
        for index, item in enumerate(self.session_history[-10:], start=1):
            print(f"{index}. [{item['type']}] {item['request'][:50]}")
            print(f"   {item['response'][:100]}")

    def _clear_history(self) -> None:
        self.session_history.clear()
        print("会话历史已清空。")

    async def _handle_exit(self) -> None:
        print("\n感谢使用编程教育智能体系统。")
        print(f"本次会话交互次数: {len(self.session_history)}")


async def main() -> None:
    cli = FinalInteractiveCLI()
    await cli.start_session()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    asyncio.run(main())
