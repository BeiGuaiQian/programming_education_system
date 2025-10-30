# src/programming_education_system/agents/evaluation_agent.py
"""
答案评析代理 - 科学认知API版本
基于用户认知状态提供个性化代码评价和反馈
"""
from typing import Dict, Any, List
import ast
import subprocess
import tempfile
import os
import logging
import asyncio

from programming_education_system.utils.llm_utils import llm_client
from programming_education_system.agents.base_agent import BaseAgent

# 导入科学认知API
from programming_education_system.cognition_judger.cognitive_api_scientific import get_scientific_cognitive_api, \
    get_scientific_cognitive_api_sync

logger = logging.getLogger(__name__)


class CognitiveCodeAnalyzer:
    """基于认知科学的代码分析器"""

    def __init__(self):
        self.cognition_api = get_scientific_cognitive_api_sync()

    async def analyze_cognitive_performance(self, code: str, user_id: str, question_context: Dict[str, Any]) -> Dict[
        str, Any]:
        """分析代码中展示的认知表现"""

        try:
            # 获取用户认知状态
            cognitive_state = await self.cognition_api.get_cognitive_state(user_id)

            # 获取个性化参数
            learning_params = await self.cognition_api.get_personalized_learning_parameters(user_id, "feedback")

            # 深度认知分析
            cognitive_analysis = await self._perform_cognitive_analysis(code, question_context, cognitive_state)

            # 生成个性化反馈
            personalized_feedback = await self._generate_personalized_feedback(
                code, cognitive_analysis, cognitive_state, learning_params
            )

            return {
                "success": True,
                "cognitive_analysis": cognitive_analysis,
                "personalized_feedback": personalized_feedback,
                "learning_parameters": learning_params,
                "user_cognitive_state": cognitive_state
            }

        except Exception as e:
            logger.error("认知分析失败: {}".format(e))
            return {
                "success": False,
                "error": str(e),
                "cognitive_analysis": {},
                "personalized_feedback": "暂时无法提供详细认知分析。"
            }

    async def _perform_cognitive_analysis(self, code: str, question_context: Dict[str, Any],
                                          cognitive_state: Dict[str, Any]) -> Dict[str, Any]:
        """执行认知分析"""

        system_prompt = """你是一个认知科学和编程教育专家，请基于Bloom分类学分析学习者的代码中展示的认知能力表现。

请评估以下维度的表现：
1. 记忆能力：语法、概念、API使用的准确性
2. 理解能力：对问题需求、约束条件的理解深度  
3. 应用能力：知识应用、问题解决的熟练程度
4. 分析能力：代码结构、逻辑关系的分析质量
5. 评价能力：代码质量、最佳实践的关注程度
6. 创造能力：创新思维、独特解决方案的体现

请提供具体的分析依据和改进建议。"""

        user_message = """请分析以下代码的认知表现：

问题描述：{question_desc}
难度级别：{difficulty}

代码：
{code}

当前用户认知水平：{user_level}

请基于Bloom分类学给出详细分析：""".format(
            question_desc=question_context.get('description', '编程练习'),
            difficulty=question_context.get('difficulty', '中等'),
            code=code,
            user_level=cognitive_state.get('overall_cognitive_level', 0.5)
        )

        analysis_result = await llm_client.generate_response(system_prompt, user_message)

        # 提取认知维度评分
        dimension_scores = self._extract_dimension_scores(analysis_result, cognitive_state)

        # 识别改进领域
        improvement_areas = self._identify_improvement_areas(dimension_scores, cognitive_state)

        return {
            "analysis_text": analysis_result,
            "dimension_scores": dimension_scores,
            "improvement_areas": improvement_areas,
            "demonstrated_abilities": self._calculate_demonstrated_abilities(dimension_scores)
        }

    def _extract_dimension_scores(self, analysis_text: str, cognitive_state: Dict[str, Any]) -> Dict[str, float]:
        """从分析文本中提取认知维度评分"""

        # 基于关键词匹配的简化实现
        dimension_keywords = {
            'remember': ['语法', '概念', '记忆', '掌握', '准确', '正确'],
            'understand': ['理解', '需求', '问题', '含义', '明白', '清楚'],
            'apply': ['应用', '实现', '解决', '使用', '实践', '操作'],
            'analyze': ['结构', '逻辑', '分析', '分解', '组织', '模块'],
            'evaluate': ['质量', '最佳实践', '评价', '标准', '优化', '改进'],
            'create': ['创新', '独特', '创造', '设计', '新颖', '创意']
        }

        scores = {}
        for dim, keywords in dimension_keywords.items():
            # 计算关键词出现频率
            keyword_count = sum(1 for keyword in keywords if keyword in analysis_text)
            base_score = min(1.0, keyword_count * 0.15)  # 基础分数

            # 结合用户当前认知水平调整
            current_level = cognitive_state.get('cognitive_dimensions', {}).get(dim, 0.5)
            adjusted_score = (base_score + current_level) / 2

            scores[dim] = round(adjusted_score, 2)

        return scores

    def _identify_improvement_areas(self, dimension_scores: Dict[str, float],
                                    cognitive_state: Dict[str, Any]) -> List[str]:
        """识别改进领域"""

        improvement_areas = []
        current_dimensions = cognitive_state.get("cognitive_dimensions", {})

        # 找出得分较低的维度
        weak_threshold = 0.6
        for dim, score in dimension_scores.items():
            if score < weak_threshold:
                dim_name = self._get_dimension_display_name(dim)
                improvement_areas.append("{}（当前得分: {:.2f}）".format(dim_name, score))

        # 如果所有维度都较好，提供进阶建议
        if not improvement_areas and dimension_scores:
            best_dim = max(dimension_scores.items(), key=lambda x: x[1])
            dim_name = self._get_dimension_display_name(best_dim[0])
            improvement_areas.append("继续深化{}能力，向专家水平迈进".format(dim_name))

        return improvement_areas[:3]  # 最多返回3个改进领域

    def _calculate_demonstrated_abilities(self, dimension_scores: Dict[str, float]) -> Dict[str, str]:
        """计算展示的能力水平"""

        ability_levels = {}
        for dim, score in dimension_scores.items():
            if score >= 0.8:
                level = "优秀"
            elif score >= 0.6:
                level = "良好"
            elif score >= 0.4:
                level = "基础"
            else:
                level = "待提升"

            dim_name = self._get_dimension_display_name(dim)
            ability_levels[dim_name] = level

        return ability_levels

    async def _generate_personalized_feedback(self, code: str, cognitive_analysis: Dict[str, Any],
                                              cognitive_state: Dict[str, Any], learning_params: Dict[str, Any]) -> str:
        """生成个性化反馈"""

        user_level = cognitive_state["overall_cognitive_level"]
        parameters = learning_params.get("parameters", {})
        feedback_granularity = parameters.get("feedback_granularity", "balanced")

        system_prompt = """你是一个耐心、专业的编程教育专家，擅长根据学习者的认知水平调整反馈方式。

学习者认知水平：{user_level}
反馈粒度要求：{feedback_granularity}
认知分析结果：{analysis_text}

请根据学习者的水平和需求提供适当的代码反馈：""".format(
            user_level=user_level,
            feedback_granularity=feedback_granularity,
            analysis_text=cognitive_analysis.get('analysis_text', '')
        )

        user_message = """请对以下代码提供个性化反馈和改进建议：

需要重点改进的领域：{improvement_areas}
展示的能力：{demonstrated_abilities}

代码：
{code}

请提供：
1. 具体的代码改进建议
2. 针对薄弱认知维度的训练建议  
3. 适合当前水平的下一步学习方向
4. 鼓励性的话语""".format(
            improvement_areas=', '.join(cognitive_analysis.get('improvement_areas', [])),
            demonstrated_abilities=', '.join(
                ["{}: {}".format(k, v) for k, v in cognitive_analysis.get('demonstrated_abilities', {}).items()]),
            code=code
        )

        feedback = await llm_client.generate_response(system_prompt, user_message)
        return feedback

    def _get_dimension_display_name(self, dimension: str) -> str:
        """获取维度显示名称"""
        names = {
            'remember': '记忆能力',
            'understand': '理解能力',
            'apply': '应用能力',
            'analyze': '分析能力',
            'evaluate': '评价能力',
            'create': '创造能力'
        }
        return names.get(dimension, dimension)


class StaticCodeAnalyzer:
    """静态代码分析器"""

    def __init__(self):
        self.cognition_api = get_scientific_cognitive_api_sync()

    async def analyze_static(self, code: str, user_id: str) -> Dict[str, Any]:
        """静态代码分析"""

        issues = []
        score = 100  # 起始分数

        try:
            # 基础语法检查
            ast.parse(code)
        except SyntaxError as e:
            issues.append("语法错误: {}".format(e))
            score -= 30

        # 代码风格检查
        lines = code.split('\n')

        # 检查缩进一致性
        for i, line in enumerate(lines, 1):
            if line and line[0] == ' ' and len(line) - len(line.lstrip()) % 4 != 0:
                issues.append("第{}行: 缩进不一致".format(i))
                score -= 2

        # 检查行长度
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                issues.append("第{}行: 行过长 ({} 字符)".format(i, len(line)))
                score -= 1

        try:
            # 获取用户认知状态以调整严格度
            cognitive_state = await self.cognition_api.get_cognitive_state(user_id)
            user_level = cognitive_state["overall_cognitive_level"]

            # 基于认知水平调整评分
            if user_level < 0.4:
                # 初学者更宽容
                score = max(score, 70)  # 保证最低分数
                # 只保留关键问题
                issues = [issue for issue in issues if "语法错误" in issue]

            # 使用LLM进行深度分析
            system_prompt = "你是一个代码审查专家，请根据学习者的认知水平({:.2f}/1.0)分析以下Python代码的质量。".format(
                user_level)

            llm_analysis = await llm_client.generate_response(
                system_prompt,
                "请分析以下Python代码的质量，考虑学习者的当前水平：\n{}".format(code)
            )

            return {
                "success": True,
                "score": max(0, score),
                "issues": issues,
                "llm_analysis": llm_analysis,
                "syntax_valid": len(issues) == 0 or all("语法错误" not in issue for issue in issues),
                "adjusted_for_level": user_level < 0.4
            }

        except Exception as e:
            logger.error("静态分析失败: {}".format(e))
            return {
                "success": False,
                "score": max(0, score),
                "issues": issues,
                "llm_analysis": "分析过程中出现错误",
                "syntax_valid": len(issues) == 0,
                "adjusted_for_level": False
            }


class DynamicCodeTester:
    """动态代码测试器"""

    async def test_execution(self, code: str, test_cases: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """动态测试代码执行"""

        results = []
        passed_count = 0

        if not test_cases:
            # 基础功能测试
            test_cases = [{
                "name": "基本执行测试",
                "test_code": "True",  # 简单验证代码可执行
                "expected": "basic_execution"
            }]

        for i, test_case in enumerate(test_cases):
            try:
                # 创建临时文件
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    # 包装测试代码
                    f.write("# 测试用例 {}: {}\n".format(i + 1, test_case.get('name', '未知')))
                    f.write(code)

                    if "test_code" in test_case:
                        f.write("\n\n# 测试执行\nresult = {}\n".format(test_case['test_code']))
                        f.write("print('TEST_RESULT:{}'.format(result))\n")

                    temp_file = f.name

                # 执行测试
                result = subprocess.run(
                    ['python', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                # 清理临时文件
                os.unlink(temp_file)

                if result.returncode == 0:
                    test_passed = self._check_test_result(result.stdout, test_case)
                    if test_passed:
                        passed_count += 1
                        results.append({
                            "test_case": i + 1,
                            "name": test_case.get('name', '未知'),
                            "status": "passed",
                            "output": result.stdout[:200]  # 限制输出长度
                        })
                    else:
                        results.append({
                            "test_case": i + 1,
                            "name": test_case.get('name', '未知'),
                            "status": "failed",
                            "output": result.stdout[:200]
                        })
                else:
                    results.append({
                        "test_case": i + 1,
                        "name": test_case.get('name', '未知'),
                        "status": "error",
                        "error": result.stderr[:200]
                    })

            except subprocess.TimeoutExpired:
                results.append({
                    "test_case": i + 1,
                    "name": test_case.get('name', '未知'),
                    "status": "timeout"
                })
            except Exception as e:
                results.append({
                    "test_case": i + 1,
                    "name": test_case.get('name', '未知'),
                    "status": "error",
                    "error": str(e)[:200]
                })

        success_rate = passed_count / len(test_cases) if test_cases else 0

        return {
            "success": True,
            "passed": passed_count,
            "total": len(test_cases),
            "success_rate": success_rate,
            "details": results
        }

    def _check_test_result(self, output: str, test_case: Dict[str, Any]) -> bool:
        """检查测试结果"""
        # 简化实现，实际应该更复杂
        if "TEST_RESULT:" in output:
            return True
        elif "error" not in output.lower() and "exception" not in output.lower():
            return True
        return False


class AnswerEvaluationAgent(BaseAgent):
    """答案评析代理 - 科学认知API版本"""

    def __init__(self, personal_agent):
        super().__init__("AnswerEvaluationAgent")
        self.cognitive_analyzer = CognitiveCodeAnalyzer()
        self.static_analyzer = StaticCodeAnalyzer()
        self.dynamic_tester = DynamicCodeTester()
        self.personal_agent = personal_agent
        self.cognition_api = get_scientific_cognitive_api_sync()

    async def evaluate_code(self, code: str, user_id: str, question_context: Dict[str, Any]) -> Dict[str, Any]:
        """代码评析主入口"""

        self.log_activity("开始评析代码", {
            "code_length": len(code),
            "user_id": user_id
        })

        try:
            # 并行执行多种分析
            static_task = self.static_analyzer.analyze_static(code, user_id)
            cognitive_task = self.cognitive_analyzer.analyze_cognitive_performance(code, user_id, question_context)
            dynamic_task = self.dynamic_tester.test_execution(code, question_context.get("test_cases"))

            static_result, cognitive_result, dynamic_result = await asyncio.gather(
                static_task, cognitive_task, dynamic_task,
                return_exceptions=True
            )

            # 处理可能的异常
            if isinstance(static_result, Exception):
                static_result = {"success": False, "error": str(static_result), "score": 50}
            if isinstance(cognitive_result, Exception):
                cognitive_result = {"success": False, "error": str(cognitive_result)}
            if isinstance(dynamic_result, Exception):
                dynamic_result = {"success": False, "error": str(dynamic_result)}

            # 计算综合评分
            overall_score = self._calculate_overall_score(static_result, dynamic_result, cognitive_result)

            # 生成综合反馈
            feedback = self._generate_comprehensive_feedback(static_result, dynamic_result, cognitive_result)

            return {
                "success": True,
                "overall_score": overall_score,
                "feedback": feedback,
                "detailed_analysis": {
                    "static_analysis": static_result,
                    "dynamic_analysis": dynamic_result,
                    "cognitive_analysis": cognitive_result
                },
                "personalized": cognitive_result.get("success", False)
            }

        except Exception as e:
            logger.error("代码评析失败: {}".format(e))
            return {
                "success": False,
                "error": str(e),
                "overall_score": 0,
                "feedback": "评析过程中出现错误"
            }

    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理评析请求"""

        user_id = request["user_id"]
        content = request["content"]

        # 解析代码和问题信息
        code, question_info = self._parse_evaluation_request(content)

        # 执行评析
        result = await self.evaluate_code(code, user_id, question_info)

        # 记录科学认知数据
        await self._record_cognitive_data(user_id, content, result)

        # 记录用户行为
        behavior_data = {
            "user_id": user_id,
            "evaluation_score": result.get("overall_score", 0),
            "topic": question_info.get("topic", "general"),
            "code_length": len(code),
            "success": result.get("success", False)
        }
        await self.personal_agent.track_user_behavior(behavior_data)

        # 构建响应
        if result["success"]:
            score = result["overall_score"]
            response_msg = "代码评析完成，综合得分: {}/100".format(score)

            if score >= 80:
                response_msg += " 🎉 优秀！"
            elif score >= 60:
                response_msg += " 👍 良好！"
            else:
                response_msg += " 💪 继续加油！"
        else:
            response_msg = "评析失败: {}".format(result.get('error', '未知错误'))

        return {
            "response": response_msg,
            "details": result,
            "success": result["success"]
        }

    async def _record_cognitive_data(self, user_id: str, content: str, result: Dict[str, Any]):
        """记录科学认知数据"""

        try:
            interaction_data = {
                'type': 'code_evaluation',
                'content': content[:300],  # 限制长度
                'user_response': str(result.get('overall_score', 0)),
                'context': '代码评价交互',
                'metadata': {
                    'evaluation_score': result.get('overall_score', 0),
                    'code_quality': result.get('detailed_analysis', {}).get('static_analysis', {}).get('score',
                                                                                                       0) / 100,
                    'personalized': result.get('personalized', False),
                    'success': result.get('success', False)
                }
            }

            analysis_result = await self.cognition_api.analyze_learning_interaction(user_id, interaction_data)

            if analysis_result['success']:
                self.logger.info("代码评价认知分析完成")

        except Exception as e:
            self.logger.warning("记录认知数据失败: {}".format(e))

    def _parse_evaluation_request(self, content: str) -> tuple:
        """解析评析请求"""
        # 简化实现，假设整个内容都是代码
        # 实际应该更复杂，可能需要解析代码块和问题描述

        lines = content.split('\n')
        code = content  # 默认整个内容为代码

        # 简单的问题信息提取
        question_info = {
            "topic": "general",
            "description": "代码评价请求",
            "difficulty": "medium"
        }

        # 尝试提取主题信息
        topic_keywords = {
            "python_basics": ["def ", "print(", "input("],
            "data_structures": ["list", "dict", "set", "tuple"],
            "algorithms": ["sort", "search", "recursive", "algorithm"],
            "oop": ["class ", "self.", "__init__"]
        }

        for topic, keywords in topic_keywords.items():
            if any(keyword in content for keyword in keywords):
                question_info["topic"] = topic
                break

        return code, question_info

    def _calculate_overall_score(self, static_result: Dict[str, Any],
                                 dynamic_result: Dict[str, Any],
                                 cognitive_result: Dict[str, Any]) -> float:
        """计算综合评分"""

        # 静态分析权重
        static_score = static_result.get("score", 0) if static_result.get("success", False) else 50
        static_weight = 0.4

        # 动态测试权重
        if dynamic_result.get("success", False):
            dynamic_success_rate = dynamic_result.get("success_rate", 0)
            dynamic_score = dynamic_success_rate * 100
        else:
            dynamic_score = 50
        dynamic_weight = 0.3

        # 认知分析权重
        if cognitive_result.get("success", False):
            cognitive_score = self._calculate_cognitive_score(cognitive_result)
        else:
            cognitive_score = 50
        cognitive_weight = 0.3

        # 加权平均
        overall_score = (
                static_score * static_weight +
                dynamic_score * dynamic_weight +
                cognitive_score * cognitive_weight
        )

        return round(overall_score, 1)

    def _calculate_cognitive_score(self, cognitive_result: Dict[str, Any]) -> float:
        """计算认知分析得分"""
        cognitive_analysis = cognitive_result.get("cognitive_analysis", {})
        dimension_scores = cognitive_analysis.get("dimension_scores", {})

        if not dimension_scores:
            return 50

        # 计算平均维度得分
        avg_score = sum(dimension_scores.values()) / len(dimension_scores)
        return avg_score * 100

    def _generate_comprehensive_feedback(self, static_result: Dict[str, Any],
                                         dynamic_result: Dict[str, Any],
                                         cognitive_result: Dict[str, Any]) -> str:
        """生成综合反馈"""

        feedback_parts = []

        # 静态分析反馈
        if static_result.get("success", False):
            static_score = static_result.get("score", 0)
            if static_score >= 80:
                feedback_parts.append("✅ 代码风格优秀！")
            elif static_score >= 60:
                feedback_parts.append("✅ 代码风格良好")
            else:
                feedback_parts.append("📝 代码风格需要改进")

            issues = static_result.get("issues", [])
            if issues:
                feedback_parts.extend(issues[:3])  # 最多显示3个问题

        # 动态测试反馈
        if dynamic_result.get("success", False):
            success_rate = dynamic_result.get("success_rate", 0)
            if success_rate == 1.0:
                feedback_parts.append("🎯 所有测试通过！")
            elif success_rate >= 0.7:
                feedback_parts.append("🎯 大部分测试通过 ({:.0%})".format(success_rate))
            else:
                feedback_parts.append("🔧 需要修复测试问题 ({:.0%})".format(success_rate))

        # 认知分析反馈
        if cognitive_result.get("success", False):
            cognitive_feedback = cognitive_result.get("personalized_feedback", "")
            if cognitive_feedback:
                feedback_parts.append("\n🧠 个性化学习建议：")
                feedback_parts.append(cognitive_feedback)

        # 默认反馈
        if not feedback_parts:
            feedback_parts.append("请继续改进代码质量")

        return "\n".join(feedback_parts)