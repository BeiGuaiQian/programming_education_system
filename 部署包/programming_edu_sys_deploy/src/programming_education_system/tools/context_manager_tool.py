"""CLI helpers for managing stored conversation context."""

from __future__ import annotations

import argparse
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from programming_education_system.utils.context_manager import context_manager


def clear_user_context(user_id: str):
    """Clear all context data for a single user."""
    print(f"正在清除用户 {user_id} 的上下文数据...")
    success = context_manager.clear_user_data(user_id)
    if success:
        print(f"已成功清除用户 {user_id} 的上下文数据")
    else:
        print(f"清除用户 {user_id} 的上下文数据失败")


def clear_all_contexts():
    """Clear all stored context when the backend supports bulk listing."""
    confirm = input("确认要清除所有用户上下文吗？输入 'YES' 确认: ")
    if confirm != "YES":
        print("操作已取消")
        return

    redis_client = getattr(context_manager, "redis_client", None)
    if redis_client is None:
        print("当前上下文后端不支持批量删除，请改用 clear-user。")
        return

    keys = []
    for pattern in ["conversation:*", "dialog_history:*", "learning_progress:*"]:
        keys.extend(redis_client.keys(pattern))

    if not keys:
        print("没有找到需要清除的上下文数据")
        return

    deleted_count = redis_client.delete(*keys)
    print(f"已清除 {deleted_count} 个上下文键")


def show_user_context(user_id: str):
    """Display a summary of a user's stored context."""
    print(f"\n用户 {user_id} 的上下文信息:")

    conversation_context = context_manager.get_conversation_context(user_id)
    print(f"对话上下文: {conversation_context or '无'}")

    dialog_history = context_manager.get_dialog_history(user_id, limit=5)
    print(f"对话历史条数: {len(dialog_history)}")
    for index, dialog in enumerate(dialog_history[:3], start=1):
        print(f"  {index}. 用户: {dialog.get('user_input', '')[:50]}...")

    learning_progress = context_manager.get_learning_progress(user_id)
    print(f"学习进度: {learning_progress or '无'}")


def list_all_users():
    """List users only when the backend supports it."""
    redis_client = getattr(context_manager, "redis_client", None)
    if redis_client is None:
        print("当前上下文后端不支持批量列举用户。")
        return

    conversation_keys = redis_client.keys("conversation:*")
    users = [key.split(":")[1] for key in conversation_keys]
    if not users:
        print("暂无用户数据")
        return

    for user_id in users:
        context = context_manager.get_conversation_context(user_id) or {}
        interaction_count = context.get("interaction_count", 0)
        last_topic = context.get("last_topic", "未知")
        print(f"{user_id} - 交互次数: {interaction_count}, 最后主题: {last_topic}")


def main():
    parser = argparse.ArgumentParser(description="上下文管理工具")
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    clear_parser = subparsers.add_parser("clear-user", help="清除特定用户的上下文")
    clear_parser.add_argument("user_id", help="要清除的用户 ID")

    subparsers.add_parser("clear-all", help="清除所有用户的上下文")

    show_parser = subparsers.add_parser("show", help="显示用户上下文信息")
    show_parser.add_argument("user_id", help="要查看的用户 ID")

    subparsers.add_parser("list", help="列出所有有上下文数据的用户")

    args = parser.parse_args()
    if args.command == "clear-user":
        clear_user_context(args.user_id)
    elif args.command == "clear-all":
        clear_all_contexts()
    elif args.command == "show":
        show_user_context(args.user_id)
    elif args.command == "list":
        list_all_users()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
