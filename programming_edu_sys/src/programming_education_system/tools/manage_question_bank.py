# tools/manage_question_bank.py
"""
题库管理命令行工具
"""
import argparse
import json
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from programming_education_system.utils.question_bank_manager import question_bank_manager

def init_sample_data():
    """初始化示例数据"""
    print("正在初始化示例数据...")
    result = question_bank_manager.initialize_sample_data()
    print(f"初始化完成: {result}")

def show_stats():
    """显示统计信息"""
    stats = question_bank_manager.get_question_stats()
    print("\n📊 题库统计信息:")
    print(f"总题目数: {stats.get('total_questions', 0)}")
    
    print("\n按主题分布:")
    for topic, count in stats.get('questions_by_topic', {}).items():
        print(f"  {topic}: {count}")
    
    print("\n按难度分布:")
    for difficulty, count in stats.get('questions_by_difficulty', {}).items():
        print(f"  {difficulty}: {count}")
    
    print("\n按类型分布:")
    for q_type, count in stats.get('questions_by_type', {}).items():
        print(f"  {q_type}: {count}")
    
    print(f"\n平均使用次数: {stats.get('average_usage_count', 0)}")
    print(f"平均成功率: {stats.get('average_success_rate', 0):.2%}")

def search_questions(args):
    """搜索题目"""
    questions = question_bank_manager.search_questions(
        keyword=args.keyword,
        topic=args.topic,
        difficulty=args.difficulty,
        limit=args.limit
    )
    
    print(f"\n🔍 找到 {len(questions)} 道题目:")
    for i, q in enumerate(questions, 1):
        print(f"\n{i}. [{q['difficulty']}] {q['topic']} - {q['content'][:50]}...")
        print(f"   类型: {q['question_type']}, 使用次数: {q['usage_count']}, 成功率: {q['success_rate']:.2%}")

def export_questions(args):
    """导出题目"""
    filters = {}
    if args.topic:
        filters['topic'] = args.topic
    if args.difficulty:
        filters['difficulty'] = args.difficulty
    
    question_bank_manager.export_to_json(args.output_file, filters)
    print(f"题目已导出到: {args.output_file}")

def import_questions(args):
    """导入题目"""
    result = question_bank_manager.import_from_json(args.input_file)
    print(f"导入完成: {result}")

def main():
    parser = argparse.ArgumentParser(description="题库管理工具")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # init命令
    subparsers.add_parser('init', help='初始化示例数据')
    
    # stats命令  
    subparsers.add_parser('stats', help='显示统计信息')
    
    # search命令
    search_parser = subparsers.add_parser('search', help='搜索题目')
    search_parser.add_argument('--keyword', help='搜索关键词')
    search_parser.add_argument('--topic', help='主题筛选')
    search_parser.add_argument('--difficulty', choices=['beginner', 'intermediate', 'advanced'], help='难度筛选')
    search_parser.add_argument('--limit', type=int, default=10, help='结果数量限制')
    
    # export命令
    export_parser = subparsers.add_parser('export', help='导出题目')
    export_parser.add_argument('output_file', help='输出文件路径')
    export_parser.add_argument('--topic', help='按主题筛选')
    export_parser.add_argument('--difficulty', choices=['beginner', 'intermediate', 'advanced'], help='按难度筛选')
    
    # import命令
    import_parser = subparsers.add_parser('import', help='导入题目')
    import_parser.add_argument('input_file', help='输入文件路径')
    
    args = parser.parse_args()
    
    if args.command == 'init':
        init_sample_data()
    elif args.command == 'stats':
        show_stats()
    elif args.command == 'search':
        search_questions(args)
    elif args.command == 'export':
        export_questions(args)
    elif args.command == 'import':
        import_questions(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()