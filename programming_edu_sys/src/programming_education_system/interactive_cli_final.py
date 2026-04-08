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
        self.show_cognitive_insights = True

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
                if lowered in {"cognitive", "认知"}:
                    await self._toggle_cognitive_mode()
                    continue
                if lowered in {"status", "状态"}:
                    await self._show_system_status()
                    continue
                if lowered in {"report", "报告"}:
                    await self._show_cognitive_report()
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
                    "cognitive_insights": result.get("cognitive_insights", {}),
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
                    "cognitive_insights": {},
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

        if self.show_cognitive_insights:
            self._display_cognitive_insights(result.get("cognitive_insights", {}))
        print("=" * 60)

    def _display_cognitive_insights(self, insights: Dict[str, Any]) -> None:
        user_cognitive_state = insights.get("user_cognitive_state", {})
        if not user_cognitive_state:
            return

        print("\n认知洞察:")
        print(f"- 认知水平: {user_cognitive_state.get('overall_cognitive_level', 0.5):.2f}")
        print(f"- 学习趋势: {user_cognitive_state.get('learning_trend', 'stable')}")

        learning_chars = user_cognitive_state.get("learning_characteristics", {})
        if learning_chars:
            print(f"- 学习风格: {learning_chars.get('learning_style', 'balanced')}")
            print(f"- 学习节奏: {learning_chars.get('learning_pace', 'moderate')}")
            print(f"- 学习信心: {learning_chars.get('confidence_level', 0.5):.2f}")

        dimensions = user_cognitive_state.get("cognitive_dimensions", {})
        if dimensions:
            strongest = max(dimensions.items(), key=lambda item: item[1])
            weakest = min(dimensions.items(), key=lambda item: item[1])
            print(f"- 当前强项: {strongest[0]} ({strongest[1]:.2f})")
            print(f"- 当前待提升: {weakest[0]} ({weakest[1]:.2f})")

        recommendations = insights.get("learning_recommendations", {}).get("recommendations", {})
        if recommendations:
            focus_areas = recommendations.get("focus_areas", [])
            if focus_areas:
                print(f"- 建议聚焦: {', '.join(focus_areas)}")

    def _get_intent_display_info(self, intent: str) -> Dict[str, str]:
        intent_info = {
            "qa": {"label": "问答模式"},
            "exercise": {"label": "练习生成模式"},
            "evaluation": {"label": "代码评估模式"},
            "personal": {"label": "个性化建议模式"},
            "unknown": {"label": "自动路由模式"},
        }
        return intent_info.get(intent, intent_info["unknown"])

    async def _toggle_cognitive_mode(self) -> None:
        self.show_cognitive_insights = not self.show_cognitive_insights
        print(f"认知洞察显示已{'开启' if self.show_cognitive_insights else '关闭'}。")

    async def _show_system_status(self) -> None:
        status = await self.system.get_system_status()
        print("\n系统状态:")
        for key, value in status.items():
            if key == "timestamp":
                continue
            print(f"- {key}: {value}")

    async def _show_cognitive_report(self) -> None:
        report = await self.system.get_user_cognitive_report(self.user_id)
        if "error" in report:
            print(f"获取认知报告失败: {report['error']}")
            return

        print("\n认知报告:")
        cognitive_state = report.get("cognitive_state", {})
        print(f"- 用户: {report.get('user_id', self.user_id)}")
        print(f"- 认知水平: {cognitive_state.get('overall_cognitive_level', 0.5):.2f}")
        print(f"- 交互次数: {cognitive_state.get('interaction_count', 0)}")

        progression = report.get("progression_analysis", {}).get("progression_analysis", {})
        if progression:
            print(f"- 学习趋势: {progression.get('trend', 'stable')}")
            print(f"- 进步速率: {progression.get('progress_rate', 0.0):.3f}")

        strengths_weaknesses = report.get("strengths_weaknesses", {})
        strengths = strengths_weaknesses.get("cognitive_strengths", [])
        weaknesses = strengths_weaknesses.get("cognitive_weaknesses", [])
        if strengths:
            print(f"- 强项: {', '.join(item.get('display_name', item.get('dimension', '')) for item in strengths)}")
        if weaknesses:
            print(f"- 待提升: {', '.join(item.get('display_name', item.get('dimension', '')) for item in weaknesses)}")

    def _show_help(self) -> None:
        print(
            "\n可用命令:\n"
            "- help / 帮助: 查看帮助\n"
            "- history / 历史: 查看最近会话\n"
            "- clear / 清空: 清空会话记录\n"
            "- cognitive / 认知: 开关认知洞察显示\n"
            "- status / 状态: 查看系统状态\n"
            "- report / 报告: 查看认知报告\n"
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
