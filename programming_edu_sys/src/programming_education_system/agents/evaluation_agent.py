# programming_education_system/agents/evaluation_agent.py
"""
答案评析代理
"""
from typing import Dict, Any, List
import ast
import subprocess
import tempfile
import os
from programming_education_system.utils.llm_utils import llm_client
from programming_education_system.agents.base_agent import BaseAgent

class StaticEvaluationAgent:
    """静态分析子代理"""
    
    async def static_evaluate(self, code: str) -> Dict[str, Any]:
        """静态代码分析"""
        issues = []
        score = 100  # 起始分数
        
        try:
            # 语法检查
            ast.parse(code)
        except SyntaxError as e:
            issues.append(f"语法错误: {e}")
            score -= 30
        
        # 代码风格和结构检查（简化版）
        lines = code.split('\n')
        
        # 检查缩进
        for i, line in enumerate(lines, 1):
            if line and line[0] == ' ' and len(line) - len(line.lstrip()) % 4 != 0:
                issues.append(f"第{i}行: 缩进不一致")
                score -= 5
        
        # 检查行长度
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                issues.append(f"第{i}行: 行过长 ({len(line)} 字符)")
                score -= 2
        
        # 使用LLM进行更深入的分析
        system_prompt = """你是一个代码审查专家，请分析以下Python代码的代码风格、可读性和最佳实践使用情况。"""
        
        llm_analysis = await llm_client.generate_response(
            system_prompt, 
            f"请分析以下Python代码的质量：\n```python\n{code}\n```"
        )
        
        return {
            "score": max(0, score),
            "issues": issues,
            "llm_analysis": llm_analysis,
            "syntax_valid": len(issues) == 0 or all("缩进" in issue or "行过长" in issue for issue in issues)
        }

class DynamicEvaluationAgent:
    """动态分析子代理"""
    
    async def dynamic_evaluate(self, code: str, test_cases: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """动态代码分析"""
        results = []
        passed_count = 0
        
        if not test_cases:
            # 如果没有提供测试用例，运行基本测试
            test_cases = [{"input": "", "expected": "basic_execution"}]
        
        for i, test_case in enumerate(test_cases):
            try:
                # 创建临时文件执行代码
                with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                    # 包装用户代码以便测试
                    if "input" in test_case and test_case["input"]:
                        # 这里简化处理，实际需要更复杂的测试框架
                        f.write(f"# 测试用例 {i+1}\n")
                        f.write(code)
                        f.write(f"\n\n# 测试执行\nresult = {test_case.get('test_code', 'None')}\n")
                        f.write("print(f'TEST_RESULT:{result}')\n")
                    else:
                        f.write(code)
                    
                    temp_file = f.name
                
                # 执行代码
                result = subprocess.run(
                    ['python', temp_file],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                # 清理临时文件
                os.unlink(temp_file)
                
                if result.returncode == 0:
                    test_passed = self._check_test_output(result.stdout, test_case)
                    if test_passed:
                        passed_count += 1
                        results.append({"test_case": i+1, "status": "passed"})
                    else:
                        results.append({"test_case": i+1, "status": "failed", "output": result.stdout})
                else:
                    results.append({
                        "test_case": i+1, 
                        "status": "error", 
                        "error": result.stderr
                    })
                
            except subprocess.TimeoutExpired:
                results.append({"test_case": i+1, "status": "timeout"})
            except Exception as e:
                results.append({"test_case": i+1, "status": "error", "error": str(e)})
        
        return {
            "passed": passed_count,
            "total": len(test_cases),
            "success_rate": passed_count / len(test_cases) if test_cases else 0,
            "details": results
        }
    
    def _check_test_output(self, output: str, test_case: Dict[str, Any]) -> bool:
        """检查测试输出（简化版）"""
        # 实际实现需要根据具体测试用例来验证
        return "TEST_RESULT:" in output

class AnswerEvaluationAgent(BaseAgent):
    """答案评析代理"""
    
    def __init__(self, personal_agent):
        super().__init__("AnswerEvaluationAgent")
        self.static_agent = StaticEvaluationAgent()
        self.dynamic_agent = DynamicEvaluationAgent()
        self.personal_agent = personal_agent
    
    async def evaluate_answer(self, answer: str, question: Dict[str, Any]) -> Dict[str, Any]:
        """答案评析总入口"""
        self.log_activity("开始评析答案", {"answer_length": len(answer)})
        
        # 静态分析
        static_result = await self.static_agent.static_evaluate(answer)
        
        # 动态分析（如果有测试用例）
        dynamic_result = None
        if question.get("test_cases"):
            dynamic_result = await self.dynamic_agent.dynamic_evaluate(answer, question["test_cases"])
        
        # 综合评分
        overall_score = self._calculate_overall_score(static_result, dynamic_result)
        
        return {
            "overall_score": overall_score,
            "static_analysis": static_result,
            "dynamic_analysis": dynamic_result,
            "feedback": self._generate_feedback(static_result, dynamic_result)
        }
    
    async def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """处理评析请求"""
        user_id = request["user_id"]
        content = request["content"]
        
        # 解析代码和问题信息（简化）
        code, question_info = self._parse_evaluation_request(content)
        
        # 执行评析
        result = await self.evaluate_answer(code, question_info)
        
        # 更新用户画像
        if "topic" in question_info:
            behavior_data = {
                "user_id": user_id,
                "evaluation_score": result["overall_score"],
                "topic": question_info["topic"],
                "code_quality_issues": len(result["static_analysis"]["issues"])
            }
            await self.personal_agent.track_user_behavior(behavior_data)
        
        return {
            "response": f"代码评析完成，得分: {result['overall_score']}/100",
            "details": result
        }
    
    def _parse_evaluation_request(self, content: str) -> tuple:
        """解析评析请求"""
        # 简化解析，实际应该更复杂
        lines = content.split('\n')
        code = content  # 假设整个内容都是代码
        question_info = {"topic": "general"}  # 简化问题信息
        
        return code, question_info
    
    def _calculate_overall_score(self, static_result: Dict[str, Any], 
                               dynamic_result: Dict[str, Any]) -> float:
        """计算综合评分"""
        static_score = static_result.get("score", 0)
        
        if dynamic_result:
            dynamic_success_rate = dynamic_result.get("success_rate", 0)
            return (static_score * 0.4 + dynamic_success_rate * 100 * 0.6)
        else:
            return static_score
    
    def _generate_feedback(self, static_result: Dict[str, Any], 
                          dynamic_result: Dict[str, Any]) -> str:
        """生成反馈信息"""
        feedback_parts = []
        
        # 静态分析反馈
        if static_result["issues"]:
            feedback_parts.append("代码风格需要改进：")
            feedback_parts.extend(static_result["issues"])
        else:
            feedback_parts.append("代码风格良好！")
        
        # 动态分析反馈
        if dynamic_result:
            success_rate = dynamic_result["success_rate"]
            if success_rate == 1.0:
                feedback_parts.append("所有测试用例通过！")
            elif success_rate > 0.5:
                feedback_parts.append(f"部分测试用例通过 ({success_rate:.0%})")
            else:
                feedback_parts.append(f"多数测试用例失败 ({success_rate:.0%})")
        
        return "\n".join(feedback_parts)