# tools/context_manager_tool.py
"""
上下文管理工具 - 提供清除和管理功能
"""
import argparse
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from programming_education_system.utils.context_manager import context_manager

def clear_user_context(user_id: str):
    """清除用户上下文"""
    print(f"正在清除用户 {user_id} 的上下文数据...")
    
    success = context_manager.clear_user_data(user_id)
    if success:
        print(f"✅ 已成功清除用户 {user_id} 的所有上下文数据")
    else:
        print(f"❌ 清除用户 {user_id} 上下文数据失败")

def clear_all_contexts():
    """清除所有用户的上下文数据（谨慎使用）"""
    confirm = input("⚠️  确定要清除所有用户的上下文数据吗？这将不可恢复！(输入 'YES' 确认): ")
    if confirm != 'YES' :
        print("操作已取消")
        return
    
    # 获取所有相关的键
    keys = []
    for pattern in ["conversation:*", "dialog_history:*", "learning_progress:*"]:
        keys.extend(context_manager.redis_client.keys(pattern))
    
    if not keys:
        print("没有找到需要清除的上下文数据")
        return
    
    # 删除所有键
    deleted_count = context_manager.redis_client.delete(*keys)
    print(f"✅ 已清除 {deleted_count} 个上下文数据键")

def show_user_context(user_id: str):
    """显示用户上下文信息"""
    print(f"\n📊 用户 {user_id} 的上下文信息:")
    
    # 对话上下文
    conversation_context = context_manager.get_conversation_context(user_id)
    if conversation_context:
        print(f"🗣️  对话上下文: {conversation_context}")
    else:
        print("🗣️  对话上下文: 无")
    
    # 对话历史
    dialog_history = context_manager.get_dialog_history(user_id, limit=5)
    print(f"📝 对话历史记录数: {len(dialog_history)}")
    for i, dialog in enumerate(dialog_history[:3]):  # 显示最近3条
        print(f"  {i+1}. 用户: {dialog.get('user_input', '')[:50]}...")
    
    # 学习进度
    learning_progress = context_manager.get_learning_progress(user_id)
    if learning_progress:
        print(f"📚 学习进度: {learning_progress}")
    else:
        print("📚 学习进度: 无")

def list_all_users():
    """列出所有有上下文数据的用户"""
    print("👥 有上下文数据的用户列表:")
    
    # 获取所有对话上下文的键
    conversation_keys = context_manager.redis_client.keys("conversation:*")
    users = [key.split(":")[1] for key in conversation_keys]
    
    if not users:
        print("  暂无用户数据")
        return
    
    for user_id in users:
        # 获取用户的一些基本信息
        context = context_manager.get_conversation_context(user_id) or {}
        interaction_count = context.get('interaction_count', 0)
        last_topic = context.get('last_topic', '未知')
        print(f"  👤 {user_id} - 交互次数: {interaction_count}, 最后主题: {last_topic}")

def main():
    parser = argparse.ArgumentParser(description="上下文管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # clear-user 命令
    clear_parser = subparsers.add_parser('clear-user', help='清除特定用户的上下文')
    clear_parser.add_argument('user_id', help='要清除的用户ID')
    
    # clear-all 命令
    subparsers.add_parser('clear-all', help='清除所有用户的上下文（谨慎使用）')
    
    # show 命令
    show_parser = subparsers.add_parser('show', help='显示用户上下文信息')
    show_parser.add_argument('user_id', help='要查看的用户ID')
    
    # list 命令
    subparsers.add_parser('list', help='列出所有有上下文数据的用户')
    
    args = parser.parse_args()
    clear_all_contexts()
    if args.command == 'clear-user':
        clear_user_context(args.user_id)
    elif args.command == 'clear-all':
        clear_all_contexts()
    elif args.command == 'show':
        show_user_context(args.user_id)
    elif args.command == 'list':
        list_all_users()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()