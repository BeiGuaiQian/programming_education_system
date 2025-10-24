# test_cognitive_framework.py
"""
编程教育系统认知框架测试脚本
模拟不同水平和学习状态的用户，测试认知维度的动态变化
包含噪声数据以测试系统对退步的检测能力
"""
import asyncio
import logging
import sys
import os
import random
from typing import Dict, List, Any, Tuple
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from programming_education_system.main_final import get_system


class CognitiveTestUser:
    """测试用户类，模拟不同认知水平的用户"""
    
    def __init__(self, user_id: str, initial_level: str, learning_trend: str = "stable"):
        self.user_id = user_id
        self.initial_level = initial_level  # beginner, intermediate, advanced
        self.learning_trend = learning_trend  # stable, improving, declining
        self.interaction_count = 0
        self.cognitive_history = []
        
        # 基于初始水平和趋势设置问题难度
        self._setup_question_pool()
        
    def _setup_question_pool(self):
        """设置问题池，基于用户水平和学习趋势"""
        self.question_pools = {
            "beginner": [
                ("qa", "Python中如何定义变量？"),
                ("qa", "什么是函数？"),
                ("qa", "如何打印Hello World？"),
                ("qa", "列表和元组有什么区别？"),
                ("exercise", "生成一个简单的Python练习"),
                ("qa", "如何写一个if语句？"),
                ("qa", "什么是for循环？"),
                ("exercise", "生成一个关于列表的简单练习")
            ],
            "intermediate": [
                ("qa", "Python中的装饰器是什么？"),
                ("qa", "解释一下面向对象编程的概念"),
                ("qa", "如何实现一个类？"),
                ("qa", "生成器和迭代器有什么区别？"),
                ("exercise", "生成一个关于函数的高级练习"),
                ("qa", "如何处理Python中的异常？"),
                ("qa", "什么是上下文管理器？"),
                ("exercise", "生成一个关于面向对象的练习")
            ],
            "advanced": [
                ("qa", "解释Python的GIL（全局解释器锁）"),
                ("qa", "如何优化Python代码的性能？"),
                ("qa", "异步编程在Python中是如何工作的？"),
                ("qa", "解释元编程的概念"),
                ("exercise", "生成一个关于算法设计的挑战"),
                ("qa", "Python中的内存管理机制是怎样的？"),
                ("qa", "如何设计可扩展的软件架构？"),
                ("exercise", "生成一个关于设计模式的练习")
            ]
        }
        
        # 退步用户的问题池 - 故意混合简单问题
        self.declining_pool = [
            ("qa", "如何定义变量？"),  # 简单问题
            ("qa", "什么是Python？"),  # 非常基础
            ("qa", "如何打印输出？"),  # 基础问题
            ("qa", "Python中的GIL是什么？"),  # 偶尔复杂问题
            ("qa", "什么是for循环？"),  # 简单问题
            ("qa", "解释异步编程"),  # 复杂问题
            ("qa", "如何写注释？"),  # 简单问题
            ("qa", "什么是装饰器？")  # 复杂问题
        ]
    
    def get_next_interaction(self) -> Tuple[str, str]:
        """获取下一个交互内容，基于用户的学习趋势"""
        self.interaction_count += 1
        
        if self.learning_trend == "declining":
            # 退步用户：随着交互次数增加，提出更多简单问题
            if self.interaction_count > 5:
                # 后期主要问简单问题
                pool = [q for q in self.declining_pool if "如何" in q[1] or "什么" in q[1] or "打印" in q[1]]
            else:
                pool = self.declining_pool
        else:
            # 正常或进步用户
            pool = self.question_pools[self.initial_level]
            
            if self.learning_trend == "improving" and self.interaction_count > 4:
                # 进步用户：后期尝试更高级的问题
                if self.initial_level == "beginner":
                    pool = self.question_pools["intermediate"]
                elif self.initial_level == "intermediate":
                    pool = self.question_pools["advanced"]
        
        return random.choice(pool)
    
    def record_cognitive_state(self, cognitive_insights: Dict[str, Any]):
        """记录认知状态"""
        if cognitive_insights and "user_cognitive_state" in cognitive_insights:
            state = cognitive_insights["user_cognitive_state"]
            snapshot = {
                "timestamp": datetime.now(),
                "overall_level": state.get("overall_cognitive_level", 0.5),
                "cognitive_dimensions": state.get("cognitive_dimensions", {}),
                "interaction_count": self.interaction_count
            }
            self.cognitive_history.append(snapshot)


class CognitiveFrameworkTester:
    """认知框架测试器"""
    
    def __init__(self):
        self.system = get_system()
        self.test_users = []
        self.results = {}
        self.logger = logging.getLogger("CognitiveTester")
        
    def setup_test_users(self):
        """设置测试用户"""
        # 稳定进步的初学者
        self.test_users.append(CognitiveTestUser("test_beginner_stable", "beginner", "stable"))
        
        # 快速进步的中级用户
        self.test_users.append(CognitiveTestUser("test_intermediate_improving", "intermediate", "improving"))
        
        # 退步的高级用户
        self.test_users.append(CognitiveTestUser("test_advanced_declining", "advanced", "declining"))
        
        # 波动用户（混合表现）
        self.test_users.append(CognitiveTestUser("test_mixed_fluctuating", "intermediate", "stable"))
        
        self.logger.info(f"设置了 {len(self.test_users)} 个测试用户")
    
    async def run_single_interaction(self, user: CognitiveTestUser) -> Dict[str, Any]:
        """运行单次交互"""
        request_type, content = user.get_next_interaction()
        
        try:
            result = await self.system.process_user_request(request_type, content, user.user_id)
            
            # 记录认知状态
            if "cognitive_insights" in result:
                user.record_cognitive_state(result["cognitive_insights"])
            
            return {
                "success": True,
                "user_id": user.user_id,
                "interaction_count": user.interaction_count,
                "request_type": request_type,
                "content": content,
                "cognitive_insights": result.get("cognitive_insights", {}),
                "response_length": len(result.get("response", ""))
            }
        except Exception as e:
            self.logger.error(f"用户 {user.user_id} 交互失败: {e}")
            return {
                "success": False,
                "user_id": user.user_id,
                "error": str(e)
            }
    
    async def run_test_sequence(self, interactions_per_user: int = 10):
        """运行测试序列"""
        self.logger.info(f"开始测试序列，每个用户 {interactions_per_user} 次交互")
        
        for i in range(interactions_per_user):
            self.logger.info(f"第 {i+1} 轮交互")
            
            for user in self.test_users:
                # 随机延迟模拟真实交互
                await asyncio.sleep(random.uniform(0.5, 2.0))
                
                result = await self.run_single_interaction(user)
                
                if result["success"]:
                    self._log_interaction_result(result)
                
            # 每轮交互后显示进度
            await self._show_progress(i + 1, interactions_per_user)
    
    def _log_interaction_result(self, result: Dict[str, Any]):
        """记录交互结果"""
        user_id = result["user_id"]
        if user_id not in self.results:
            self.results[user_id] = []
        
        self.results[user_id].append(result)
    
    async def _show_progress(self, current: int, total: int):
        """显示测试进度"""
        progress = (current / total) * 100
        print(f"测试进度: {current}/{total} ({progress:.1f}%)")
        
        # 显示当前认知状态快照
        if current % 3 == 0:  # 每3轮显示一次状态
            await self._display_cognitive_snapshot()
    
    async def _display_cognitive_snapshot(self):
        """显示认知状态快照"""
        print("\n" + "="*80)
        print("当前认知状态快照:")
        print("="*80)
        
        for user in self.test_users:
            if user.cognitive_history:
                latest = user.cognitive_history[-1]
                trend = self._calculate_trend(user.cognitive_history)
                
                print(f"\n👤 用户: {user.user_id}")
                print(f"   📊 总体水平: {latest['overall_level']:.3f}")
                print(f"   📈 趋势: {trend}")
                print(f"   🔢 交互次数: {user.interaction_count}")
                
                # 显示主要认知维度
                dimensions = latest.get('cognitive_dimensions', {})
                if dimensions:
                    print("   🧠 认知维度:")
                    for dim, score in list(dimensions.items())[:3]:
                        dim_name = self._get_dimension_display_name(dim)
                        print(f"      {dim_name}: {score:.3f}")
        
        print("="*80 + "\n")
    
    def _calculate_trend(self, history: List[Dict]) -> str:
        """计算学习趋势"""
        if len(history) < 3:
            return "数据不足"
        
        recent = history[-3:]
        levels = [item['overall_level'] for item in recent]
        
        if levels[-1] > levels[0] + 0.05:
            return "进步 ↗"
        elif levels[-1] < levels[0] - 0.05:
            return "退步 ↘"
        else:
            return "稳定 →"
    
    def _get_dimension_display_name(self, dimension: str) -> str:
        """获取维度显示名称"""
        names = {
            'remember': '记忆',
            'understand': '理解', 
            'apply': '应用',
            'analyze': '分析',
            'evaluate': '评价',
            'create': '创造'
        }
        return names.get(dimension, dimension)
    
    async def generate_detailed_report(self):
        """生成详细测试报告"""
        print("\n" + "="*100)
        print("🧠 编程教育系统认知框架测试报告")
        print("="*100)
        
        for user in self.test_users:
            print(f"\n{'='*60}")
            print(f"👤 用户分析: {user.user_id}")
            print(f"   初始水平: {user.initial_level}")
            print(f"   学习趋势: {user.learning_trend}")
            print(f"   总交互次数: {user.interaction_count}")
            print(f"{'='*60}")
            
            if not user.cognitive_history:
                print("   ❌ 无认知历史数据")
                continue
            
            # 计算认知变化
            initial_state = user.cognitive_history[0]
            final_state = user.cognitive_history[-1]
            
            level_change = final_state['overall_level'] - initial_state['overall_level']
            change_icon = "🟢" if level_change > 0.02 else "🔴" if level_change < -0.02 else "🟡"
            
            print(f"\n   📈 总体认知水平变化:")
            print(f"      初始: {initial_state['overall_level']:.3f}")
            print(f"      最终: {final_state['overall_level']:.3f}")
            print(f"      变化: {change_icon} {level_change:+.3f}")
            
            # 分析认知维度变化
            initial_dims = initial_state.get('cognitive_dimensions', {})
            final_dims = final_state.get('cognitive_dimensions', {})
            
            if initial_dims and final_dims:
                print(f"\n   🎯 认知维度变化分析:")
                for dim in ['remember', 'understand', 'apply', 'analyze', 'evaluate', 'create']:
                    if dim in initial_dims and dim in final_dims:
                        initial_score = initial_dims[dim]
                        final_score = final_dims[dim]
                        change = final_score - initial_score
                        
                        dim_name = self._get_dimension_display_name(dim)
                        change_icon = "🟢" if change > 0.02 else "🔴" if change < -0.02 else "🟡"
                        
                        print(f"      {dim_name}: {initial_score:.3f} → {final_score:.3f} ({change_icon} {change:+.3f})")
            
            # 检测退步模式
            if user.learning_trend == "declining":
                self._analyze_decline_pattern(user)
            
            # 显示学习轨迹
            self._plot_learning_trajectory(user)
    
    def _analyze_decline_pattern(self, user: CognitiveTestUser):
        """分析退步模式"""
        if len(user.cognitive_history) < 5:
            return
        
        print(f"\n   ⚠️  退步模式检测:")
        
        # 检测总体水平下降
        levels = [state['overall_level'] for state in user.cognitive_history]
        max_level = max(levels)
        min_level = min(levels)
        current_level = levels[-1]
        
        if current_level < max_level - 0.1:
            decline_amount = max_level - current_level
            print(f"      总体水平下降: {decline_amount:.3f}")
        
        # 检测具体维度退步
        latest_dims = user.cognitive_history[-1].get('cognitive_dimensions', {})
        if len(user.cognitive_history) > 1:
            previous_dims = user.cognitive_history[-2].get('cognitive_dimensions', {})
            
            declined_dims = []
            for dim in latest_dims:
                if dim in previous_dims:
                    change = latest_dims[dim] - previous_dims[dim]
                    if change < -0.05:  # 显著下降
                        dim_name = self._get_dimension_display_name(dim)
                        declined_dims.append(f"{dim_name}({change:+.3f})")
            
            if declined_dims:
                print(f"      退步维度: {', '.join(declined_dims)}")
    
    def _plot_learning_trajectory(self, user: CognitiveTestUser):
        """绘制学习轨迹（文本版）"""
        if len(user.cognitive_history) < 2:
            return
        
        print(f"\n   📊 学习轨迹:")
        
        levels = [state['overall_level'] for state in user.cognitive_history]
        min_level = min(levels)
        max_level = max(levels)
        range_size = max_level - min_level
        
        if range_size < 0.1:  # 范围太小，归一化到0.1范围
            range_size = 0.1
            min_level = max(0, min_level - 0.05)
        
        # 创建文本图表
        chart_width = 40
        print("      " + "低".ljust(chart_width//2) + "高".rjust(chart_width//2))
        
        for i, level in enumerate(levels):
            position = int(((level - min_level) / range_size) * chart_width)
            position = max(0, min(chart_width, position))
            
            bar = " " * position + "█"
            print(f"      {i+1:2d}: {bar}")
    
    async def run_system_health_check(self):
        """运行系统健康检查"""
        print("\n" + "="*60)
        print("🔧 系统健康检查")
        print("="*60)
        
        try:
            # 检查系统状态
            status = await self.system.get_system_status()
            print(f"✅ 系统状态: {status.get('system', '未知')}")
            print(f"✅ 认知框架: {status.get('cognitive_framework', '未知')}")
            print(f"✅ 智能体初始化: {status.get('agents_initialized', False)}")
            
            # 检查科学API
            print(f"✅ 科学API: {status.get('scientific_api', '未知')}")
            
            # 测试认知报告生成
            for user in self.test_users[:1]:  # 只测试第一个用户
                report = await self.system.get_user_cognitive_report(user.user_id)
                if "error" not in report:
                    print(f"✅ 认知报告生成: 正常")
                else:
                    print(f"❌ 认知报告生成: 失败 - {report.get('error')}")
            
            print("✅ 系统健康检查完成")
            
        except Exception as e:
            print(f"❌ 系统健康检查失败: {e}")


async def main():
    """主测试函数"""
    # 配置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("🚀 开始编程教育系统认知框架测试")
    print("本测试将模拟不同认知水平的用户，检测系统对认知变化的响应能力")
    print("包含退步用户以测试系统对负面变化的检测")
    
    tester = CognitiveFrameworkTester()
    
    # 设置测试用户
    tester.setup_test_users()
    
    # 运行系统健康检查
    await tester.run_system_health_check()
    
    # 运行测试序列
    print("\n🎯 开始模拟用户交互测试...")
    await tester.run_test_sequence(interactions_per_user=8)
    
    # 生成详细报告
    print("\n📊 生成测试报告...")
    await tester.generate_detailed_report()
    
    print("\n🎉 测试完成!")
    print("通过分析测试报告，您可以查看:")
    print("  • 不同用户的认知发展轨迹")
    print("  • 系统对退步用户的检测能力") 
    print("  • 各认知维度的动态变化")
    print("  • 学习趋势的识别准确性")


if __name__ == "__main__":
    # 运行测试
    asyncio.run(main())