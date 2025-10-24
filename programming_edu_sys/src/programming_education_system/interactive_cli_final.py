# src/programming_education_system/interactive_cli_final.py
"""
最终版交互式命令行界面
集成真正的LLM认知框架，保留所有功能
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

from programming_education_system.main_final import get_system


class FinalInteractiveCLI:
    """最终版交互式命令行界面 - 集成真正的LLM认知框架"""

    def __init__(self):
        self.system = get_system()
        self.user_id = "interactive_user"
        self.session_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("CLI-Final")

        # 功能开关
        self.show_cognitive_insights = True  # 显示认知洞察
        self.auto_enhance_input = True  # 自动优化输入
        self.llm_cognitive_enabled = True  # LLM认知框架启用

    async def start_session(self):
        """开始交互会话"""
        print("\n" + "=" * 60)
        print("  🤖 编程教育智能体系统 - 最终版交互终端")
        print("=" * 60)
        print("\n🎯 系统特点：")
        print("  • 智能输入优化 - 自动优化您的输入")
        print("  • 智能意图识别 - 自动理解您的需求")
        print("  • 多场景支持 - 答疑、练习、代码评价、个性化建议")
        print("  • 🧠 真正LLM认知建模 - 基于大模型的动态用户认知分析")
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

                elif user_input.lower() in ['cognitive', '认知']:
                    await self._toggle_cognitive_mode()

                elif user_input.lower() in ['status', '状态']:
                    await self._show_system_status()

                elif user_input.lower() in ['report', '报告']:
                    await self._show_cognitive_report()

                else:
                    await self._process_user_input(user_input)

            except KeyboardInterrupt:
                await self._handle_exit()
                break
            except Exception as e:
                print(f"❌ 系统错误: {e}")
                self.logger.error(f"CLI错误: {e}")

    async def _process_user_input(self, user_input: str):
        """处理用户输入 - 集成真正的LLM认知框架"""
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
                "success": result.get("success", False),
                "timestamp": asyncio.get_event_loop().time(),
                "cognitive_insights": result.get("cognitive_insights", {})
            })

            # 显示结果
            self._display_final_result(result)

        except Exception as e:
            error_msg = f"处理请求时出错: {e}"
            print(f"❌ {error_msg}")
            self.session_history.append({
                "request": user_input,
                "response": error_msg,
                "type": "error",
                "success": False,
                "timestamp": asyncio.get_event_loop().time(),
                "cognitive_insights": {}
            })

    def _display_final_result(self, result: Dict[str, Any]):
        """显示最终版处理结果 - 集成真正的LLM认知框架"""
        print("\n" + "🤖 智能体: " + "=" * 50)

        if result.get("success", False):
            response = result.get("response", "")
            details = result.get("details", {})
            request_type = result.get("request_type", "unknown")
            cognitive_insights = result.get("cognitive_insights", {})

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

                # 显示代码分析
                if "code_analysis" in details:
                    analysis = details["code_analysis"]
                    print(f"  🔍 代码分析: {analysis.get('feedback', '')}")

            # 🧠 显示真正的LLM认知洞察
            if cognitive_insights and self.show_cognitive_insights and self.llm_cognitive_enabled:
                self._display_llm_cognitive_insights(cognitive_insights, request_type)

        else:
            print(f"❌ 处理失败: {result.get('error', '未知错误')}")

        print("=" * 60)

    # 在 _display_llm_cognitive_insights 方法中更新：

    def _display_llm_cognitive_insights(self, insights: Dict[str, Any], request_type: str):
        """显示科学认知洞察信息"""
        print("\n🧠 科学认知洞察:")

        # 用户认知状态
        user_cognitive_state = insights.get("user_cognitive_state", {})
        if user_cognitive_state:
            overall_level = user_cognitive_state.get('overall_cognitive_level', 0.5)
            cognitive_dimensions = user_cognitive_state.get('cognitive_dimensions', {})
            knowledge_domains = user_cognitive_state.get('knowledge_domains', {})
            learning_chars = user_cognitive_state.get('learning_characteristics', {})
            metacognitive_skills = user_cognitive_state.get('metacognitive_skills', {})
            assessment_quality = user_cognitive_state.get('assessment_quality', {})

            # 显示总体认知水平
            level_emoji = self._get_cognitive_level_emoji(overall_level)
            print(f"  {level_emoji} 认知水平: {overall_level:.2f}/1.0")

            # 显示评估质量
            if assessment_quality:
                confidence = assessment_quality.get('confidence', 0)
                consistency = assessment_quality.get('consistency', 0)
                print(f"  📊 评估质量: 置信度{confidence:.2f} | 一致性{consistency:.2f}")

            # 显示认知维度（Bloom分类学）
            if cognitive_dimensions:
                print(f"  📈 Bloom认知维度:")
                bloom_order = ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']
                for dim in bloom_order:
                    if dim in cognitive_dimensions:
                        level = cognitive_dimensions[dim]
                        dim_emoji = self._get_cognitive_level_emoji(level)
                        dim_name = self._get_dimension_display_name(dim)
                        bar = "█" * int(level * 10) + "░" * (10 - int(level * 10))
                        print(f"    {dim_emoji} {dim_name}: {bar} {level:.2f}")

            # 显示知识领域
            if knowledge_domains:
                print(f"  📚 知识领域掌握:")
                for domain, mastery in list(knowledge_domains.items())[:4]:
                    if isinstance(mastery, (int, float)):
                        domain_emoji = self._get_domain_emoji(domain)
                        domain_name = self._get_domain_display_name(domain)
                        bar = "█" * int(mastery * 10) + "░" * (10 - int(mastery * 10))
                        print(f"    {domain_emoji} {domain_name}: {bar} {mastery:.2f}")

            # 显示学习特征
            if learning_chars:
                print(f"  🎓 学习特征:")
                if 'learning_style' in learning_chars:
                    style_emoji = self._get_learning_style_emoji(learning_chars['learning_style'])
                    print(f"    {style_emoji} 学习风格: {learning_chars['learning_style']}")
                if 'learning_pace' in learning_chars:
                    pace_emoji = self._get_pace_emoji(learning_chars['learning_pace'])
                    print(f"    {pace_emoji} 学习节奏: {learning_chars['learning_pace']}")
                if 'confidence_level' in learning_chars:
                    confidence = learning_chars['confidence_level']
                    confidence_emoji = "💪" if confidence > 0.7 else "🤔" if confidence > 0.4 else "🌱"
                    print(f"    {confidence_emoji} 学习信心: {confidence:.2f}")

        # 学习参数
        learning_parameters = insights.get("learning_parameters", {})
        if learning_parameters and 'parameters' in learning_parameters:
            params = learning_parameters['parameters']
            print(f"  ⚙️  科学学习参数:")

            key_params = {
                'explanation_depth': '解释深度',
                'example_complexity': '示例复杂度',
                'conceptual_scaffolding': '概念脚手架',
                'practice_intensity': '练习强度',
                'cognitive_challenge_level': '认知挑战'
            }

            for param_key, param_name in key_params.items():
                if param_key in params:
                    value = params[param_key]
                    if isinstance(value, (int, float)):
                        bar = "█" * int(value * 10) + "░" * (10 - int(value * 10))
                        print(f"    📏 {param_name}: {bar} {value:.1f}")
                    else:
                        print(f"    📏 {param_name}: {value}")

        # 认知强项弱项
        strengths_weaknesses = insights.get("strengths_weaknesses", {})
        if strengths_weaknesses:
            print(f"  🎯 认知分析:")

            strengths = strengths_weaknesses.get('cognitive_strengths', [])
            if strengths:
                print(f"    💪 强项: {', '.join([s.get('display_name', '') for s in strengths[:2]])}")

            weaknesses = strengths_weaknesses.get('cognitive_weaknesses', [])
            if weaknesses:
                print(f"    📚 待提升: {', '.join([w.get('display_name', '') for w in weaknesses[:2]])}")

        # 学习进展
        progression_analysis = insights.get("progression_analysis", {})
        if progression_analysis and progression_analysis.get('has_sufficient_history', False):
            progression = progression_analysis.get('progression_analysis', {})
            if progression:
                trend = progression.get('trend', 'stable')
                trend_emoji = {
                    'significant_improvement': '🚀',
                    'moderate_improvement': '📈',
                    'stable': '➡️',
                    'regression': '📉'
                }.get(trend, '📊')
                print(f"    {trend_emoji} 学习趋势: {trend}")
    def _get_dimension_display_name(self, dimension: str) -> str:
        """获取认知维度的显示名称"""
        dimension_names = {
            'remember': '记忆',
            'understand': '理解',
            'apply': '应用',
            'analyze': '分析',
            'evaluate': '评价',
            'create': '创造'
        }
        return dimension_names.get(dimension, dimension)

    def _get_domain_emoji(self, domain: str) -> str:
        """获取知识领域的emoji"""
        domain_emojis = {
            'python_basics': '🐍',
            'data_structures': '📊',
            'algorithms': '⚡',
            'oop': '🔄',
            'functional': 'λ',
            'concurrency': '⚙️'
        }
        return domain_emojis.get(domain, '📚')

    def _get_domain_display_name(self, domain: str) -> str:
        """获取知识领域的显示名称"""
        domain_names = {
            'python_basics': 'Python基础',
            'data_structures': '数据结构',
            'algorithms': '算法',
            'oop': '面向对象',
            'functional': '函数式编程',
            'concurrency': '并发编程'
        }
        return domain_names.get(domain, domain)

    def _get_learning_style_emoji(self, style: str) -> str:
        """获取学习风格的emoji"""
        style_emojis = {
            'visual': '👁️',
            'conceptual': '💭',
            'practical': '🔧',
            'theoretical': '📖',
            'balanced': '⚖️'
        }
        return style_emojis.get(style, '🎓')

    def _get_pace_emoji(self, pace: str) -> str:
        """获取学习节奏的emoji"""
        pace_emojis = {
            'slow': '🐢',
            'moderate': '🚶',
            'fast': '🏃'
        }
        return pace_emojis.get(pace, '📊')

    def _get_cognitive_level_emoji(self, level: float) -> str:
        """根据认知水平返回对应的emoji"""
        if level >= 0.8:
            return "🚀"  # 高级
        elif level >= 0.6:
            return "💪"  # 中级
        elif level >= 0.4:
            return "📚"  # 初级
        else:
            return "🌱"  # 新手

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

    async def _toggle_cognitive_mode(self):
        """切换认知模式显示"""
        self.show_cognitive_insights = not self.show_cognitive_insights
        status = "开启" if self.show_cognitive_insights else "关闭"
        print(f"🧠 认知洞察显示已{status}")

    async def _show_system_status(self):
        """显示系统状态"""
        status = await self.system.get_system_status()
        print("\n🔧 系统状态:")
        for key, value in status.items():
            if key == "timestamp":
                continue
            status_icon = "✅" if value else "❌"
            if isinstance(value, bool):
                value_str = "是" if value else "否"
            else:
                value_str = str(value)
            print(f"  {status_icon} {key}: {value_str}")

    async def _show_cognitive_report(self):
        """显示详细认知报告"""
        try:
            report = await self.system.get_user_cognitive_report(self.user_id)

            if "error" in report:
                print(f"❌ 获取认知报告失败: {report['error']}")
                return

            print("\n" + "🧠 详细认知报告 " + "=" * 40)

            cognitive_state = report.get("cognitive_state", {})
            learning_progress = report.get("learning_progress", {})

            # 显示认知状态
            if cognitive_state:
                print(f"\n📊 认知状态:")
                print(f"  👤 用户ID: {cognitive_state.get('user_id', '未知')}")
                print(f"  🎯 总体水平: {cognitive_state.get('overall_level', 0):.2f}/1.0")
                print(f"  📈 学习趋势: {cognitive_state.get('learning_trend', '未知')}")
                print(f"  🔍 数据点数: {cognitive_state.get('data_points', 0)}")
                print(f"  💪 交互次数: {cognitive_state.get('interaction_count', 0)}")
                print(f"  🎯 置信度: {cognitive_state.get('confidence', 0):.2f}")

                # 认知维度详情
                dimensions = cognitive_state.get('cognitive_dimensions', {})
                if dimensions:
                    print(f"\n  📈 认知维度详情:")
                    for dim, score in dimensions.items():
                        dim_name = self._get_dimension_display_name(dim)
                        bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
                        print(f"    {dim_name:8} {bar} {score:.2f}")

            # 显示学习进展
            if learning_progress and learning_progress.get('has_sufficient_data', False):
                print(f"\n📈 学习进展:")
                print(f"  🎯 当前水平: {learning_progress.get('current_level', 0):.2f}")
                print(f"  📊 进展趋势: {learning_progress.get('progress_trend', '未知')}")

                improvement_areas = learning_progress.get('improvement_areas', [])
                if improvement_areas:
                    print(f"  🎯 改进领域: {', '.join(improvement_areas)}")

                strengths = learning_progress.get('strengths', [])
                if strengths:
                    print(f"  💪 优势领域: {', '.join(strengths)}")

            print("=" * 50)

        except Exception as e:
            print(f"❌ 显示认知报告失败: {e}")

    def _show_help(self):
        """显示帮助信息"""
        help_text = f"""
📖 可用命令:

💬 自由提问:
  直接输入您的问题或需求，系统会自动优化和理解：
  "Python中如何定义函数？"
  "生成一个Python练习" 
  "检查这段代码：def add(a, b): return a + b"
  "给我学习建议"

🧠 LLM认知功能: {'✅ 已开启' if self.llm_cognitive_enabled else '❌ 已关闭'}
  系统使用真实大模型实时分析您的学习状态并提供个性化建议
  认知洞察显示: {'✅ 开启' if self.show_cognitive_insights else '❌ 关闭'}

🛠️ 系统命令:
  help / 帮助     - 显示此帮助信息
  history / 历史  - 显示会话历史
  clear / 清空    - 清空会话历史
  cognitive / 认知 - 切换认知洞察显示
  status / 状态   - 显示系统状态
  report / 报告   - 显示详细认知报告
  exit / 退出     - 退出系统
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

            # 显示认知水平（如果有）
            cognitive_info = ""
            cognitive_state = item.get('cognitive_insights', {}).get('user_cognitive_state', {})
            if cognitive_state and cognitive_state.get('overall_level'):
                level = cognitive_state['overall_level']
                cognitive_info = f" 🧠{level:.2f}"

            status_icon = "✅" if item.get('success', False) else "❌"
            print(f"\n{i}. {status_icon} {intent_info['emoji']} {item['request'][:50]}...{cognitive_info}")
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

        # LLM认知分析总结
        if self.session_history:
            cognitive_levels = []
            successful_interactions = [item for item in self.session_history if item.get('success', False)]

            for item in successful_interactions:
                cognitive_state = item.get('cognitive_insights', {}).get('user_cognitive_state', {})
                if cognitive_state and cognitive_state.get('overall_level'):
                    cognitive_levels.append(cognitive_state['overall_level'])

            if cognitive_levels:
                avg_level = sum(cognitive_levels) / len(cognitive_levels)
                level_emoji = self._get_cognitive_level_emoji(avg_level)
                print(f"  {level_emoji} 平均认知水平: {avg_level:.2f}/1.0")

                # 学习进度评估
                if avg_level > 0.7:
                    progress = "优秀"
                elif avg_level > 0.5:
                    progress = "良好"
                else:
                    progress = "入门"
                print(f"  📈 学习进度: {progress}")

        print("期待下次为您服务！🎓")


async def main():
    """主函数"""
    cli = FinalInteractiveCLI()
    await cli.start_session()


if __name__ == "__main__":
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # 运行最终版交互式界面
    asyncio.run(main())