# src/programming_education_system/interactive_cli.py
"""
交互式命令行界面 - 让用户可以与智能体系统对话
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
    """交互式命令行界面"""
    
    def __init__(self):
        self.system = get_system()
        self.user_id = "interactive_user"
        self.session_history: List[Dict[str, Any]] = []
        self.logger = logging.getLogger("CLI")
        
    async def start_session(self):
        """开始交互会话"""
        print("\n" + "="*60)
        print("  编程教育智能体系统 - 交互式终端")
        print("="*60)
        print("\n欢迎使用编程教育智能体系统！")
        print("您可以向我提问编程问题、请求练习、获取学习建议等。")
        print("输入 'help' 查看可用命令，输入 'exit' 退出系统。")
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
                    
                elif user_input.lower() in ['profile', '画像']:
                    await self._show_profile()
                    
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
        print("🤔 正在处理您的请求...")
        
        # 自动判断请求类型
        request_type = self._detect_request_type(user_input)
        
        try:
            # 调用系统处理请求
            result = await self.system.process_user_request(
                request_type, user_input, self.user_id
            )
            
            # 记录会话历史
            self.session_history.append({
                "request": user_input,
                "response": result.get("response", ""),
                "type": request_type,
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
                "timestamp": asyncio.get_event_loop().time()
            })
    
    def _detect_request_type(self, user_input: str) -> str:
        """自动检测请求类型"""
        input_lower = user_input.lower()
        
        # 练习相关
        if any(word in input_lower for word in ["练习", "题目", "习题", "exercise", "problem"]):
            return "exercise"
        
        # 评价相关
        elif any(word in input_lower for word in ["评价", "检查", "review", "evaluate", "代码"]):
            return "evaluation"
        
        # 个性化建议
        elif any(word in input_lower for word in ["建议", "推荐", "应该学", "学习路径", "suggestion"]):
            return "personal"
        
        # 默认为答疑
        else:
            return "qa"
    
    def _display_result(self, result: Dict[str, Any]):
        """显示处理结果"""
        print("\n" + "🤖 智能体: " + "="*50)
        
        if result.get("success", False):
            response = result.get("response", "")
            details = result.get("details", {})
            
            # 显示主要响应
            print(f"💡 {response}")
            
            # 显示详细信息
            if details:
                print("\n📋 详细信息:")
                
                # 显示练习题目
                if "exercises" in details:
                    for i, exercise in enumerate(details["exercises"], 1):
                        print(f"  {i}. {exercise.get('content', '')[:100]}...")
                
                # 显示学习建议
                if "suggestions" in details:
                    for i, suggestion in enumerate(details["suggestions"], 1):
                        print(f"  • {suggestion}")
                
                # 显示学习路径
                if "learning_path" in details:
                    path_info = details["learning_path"]
                    print(f"  学习路径 ({path_info.get('level', '未知级别')}):")
                    for i, step in enumerate(path_info.get("path", []), 1):
                        print(f"    {i}. {step}")
                
                # 显示评价结果
                if "overall_score" in details:
                    score = details["overall_score"]
                    print(f"  评分: {score}/100")
                    if "feedback" in details:
                        print(f"  反馈: {details['feedback']}")
            
        else:
            print(f"❌ 处理失败: {result.get('error', '未知错误')}")
        
        print("="*60)
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
📖 可用命令:

💬 直接提问:
  输入任何编程相关问题，如：
  "Python中如何定义函数？"
  "什么是面向对象编程？"
  "解释一下递归算法"

📝 练习相关:
  包含以下关键词的提问会自动识别为练习请求：
  "生成一个Python练习"
  "给我一道算法题"
  "想要做数据结构的练习"

🔍 代码评价:
  包含以下关键词的提问会自动识别为评价请求：
  "评价这段代码"
  "检查我的代码"
  "代码评审"

🎯 个性化建议:
  包含以下关键词的提问会自动识别为个性化请求：
  "给我学习建议"
  "推荐学习路径"
  "我应该学什么"

🛠️ 系统命令:
  help / 帮助    - 显示此帮助信息
  history / 历史 - 显示会话历史
  clear / 清空   - 清空会话历史
  profile / 画像 - 查看学习画像
  exit / 退出    - 退出系统
        """
        print(help_text)
    
    def _show_history(self):
        """显示会话历史"""
        if not self.session_history:
            print("📝 暂无会话历史")
            return
            
        print(f"\n📝 会话历史 (共{len(self.session_history)}条):")
        for i, item in enumerate(self.session_history[-10:], 1):  # 只显示最近10条
            print(f"\n{i}. [{item['type']}] {item['request'][:50]}...")
            print(f"   响应: {item['response'][:80]}...")
    
    def _clear_history(self):
        """清空会话历史"""
        self.session_history.clear()
        print("🗑️ 会话历史已清空")
    
    async def _show_profile(self):
        """显示用户画像"""
        try:
            # 通过系统获取用户画像
            result = await self.system.process_user_request(
                "personal", "显示我的学习画像", self.user_id
            )
            
            if result.get("success", False) and "details" in result:
                profile = result["details"].get("user_profile", {})
                
                print("\n👤 您的学习画像:")
                print(f"  📊 编程水平: {profile.get('programming_level', '未知')}")
                print(f"  🎯 学习风格: {profile.get('learning_style', '未知')}")
                
                if "knowledge_mastery" in profile:
                    print("  📚 知识点掌握情况:")
                    for topic, mastery in list(profile["knowledge_mastery"].items())[:5]:
                        print(f"     • {topic}: {mastery*100:.1f}%")
                
                if "weak_topics" in profile and profile["weak_topics"]:
                    print(f"  ⚠️  需要加强: {', '.join(profile['weak_topics'][:3])}")
                    
            else:
                print("❌ 无法获取用户画像信息")
                
        except Exception as e:
            print(f"❌ 获取用户画像时出错: {e}")
    
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
            print(f"  • {req_type} 请求: {count}次")
        
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