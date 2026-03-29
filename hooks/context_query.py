#!/usr/bin/env python3
"""
上下文查询工具

用法:
    python3 context_query.py "authentication flow"     # 搜索相关代码
    python3 context_query.py --stats                   # 查看索引统计
    python3 context_query.py --index                   # 重新索引项目
    python3 context_query.py --context "fix bug"       # 获取查询上下文
"""

import argparse
import sys
from pathlib import Path

# 添加项目路径以导入 src 模块
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.context_manager import create_context_manager


def get_project_path() -> Path:
    """获取当前项目路径"""
    # 优先使用环境变量
    import os
    if "PROJECT_PATH" in os.environ:
        return Path(os.environ["PROJECT_PATH"])

    # 否则使用当前目录
    return Path.cwd()


def cmd_search(args):
    """搜索相关代码"""
    project_path = get_project_path()
    cm = create_context_manager(project_path)

    # 检查是否已索引
    stats = cm.get_stats()
    if stats["indexed_files"] == 0:
        print("项目尚未索引，正在索引...")
        cm.index_codebase()

    print(f"搜索: {args.query}")
    print("-" * 60)

    results = cm.search(args.query, n_results=args.num)

    if not results:
        print("未找到相关代码")
        return

    for i, (chunk, score) in enumerate(results, 1):
        print(f"\n{i}. {chunk.file_path}:{chunk.start_line}-{chunk.end_line}")
        print(f"   相似度: {score:.2%}")
        print(f"   语言: {chunk.language}")

        # 显示代码片段
        lines = chunk.content.split("\n")
        preview_lines = lines[:args.preview] if len(lines) > args.preview else lines
        print("   ```")
        for line in preview_lines:
            print(f"   {line}")
        if len(lines) > args.preview:
            print(f"   ... ({len(lines) - args.preview} more lines)")
        print("   ```")


def cmd_stats(args):
    """查看索引统计"""
    project_path = get_project_path()
    cm = create_context_manager(project_path)

    stats = cm.get_stats()

    print("=" * 50)
    print("📊 项目索引统计")
    print("=" * 50)
    print(f"已索引文件: {stats['indexed_files']}")
    print(f"预估代码块: {stats['total_chunks']}")
    print(f"对话轮次: {stats['conversation_turns']}")
    print(f"向量存储: {'已启用' if stats['has_vector_store'] else '内存模式'}")

    if stats["summaries"]:
        print(f"摘要层级: {[s.value for s in stats['summaries']]}")


def cmd_index(args):
    """索引项目"""
    project_path = get_project_path()
    cm = create_context_manager(project_path)

    print(f"索引项目: {project_path}")
    print("文件模式:", args.patterns or ["**/*.py", "**/*.ts", "**/*.js", "**/*.go"])
    print()

    stats = cm.index_codebase(
        file_patterns=args.patterns,
        exclude_patterns=args.exclude,
        chunk_size=args.chunk_size,
    )

    print("=" * 50)
    print("✅ 索引完成")
    print("=" * 50)
    print(f"处理文件: {stats['files_processed']}")
    print(f"代码块: {stats['total_chunks']}")
    print(f"索引文件: {stats['indexed_files']}")


def cmd_context(args):
    """获取查询上下文"""
    project_path = get_project_path()
    cm = create_context_manager(project_path)

    # 检查是否已索引
    stats = cm.get_stats()
    if stats["indexed_files"] == 0:
        print("项目尚未索引，正在索引...")
        cm.index_codebase()

    context = cm.get_context_for_query(
        args.query,
        max_tokens=args.max_tokens,
        include_summaries=not args.no_summary,
    )

    print(context)


def cmd_clear(args):
    """清空索引"""
    project_path = get_project_path()
    cm = create_context_manager(project_path)

    cm.clear_all()
    print("✅ 索引已清空")


def main():
    parser = argparse.ArgumentParser(
        description="上下文查询工具 - 搜索项目代码"
    )
    subparsers = parser.add_subparsers(dest="command", help="命令")

    # search 命令
    search_parser = subparsers.add_parser("search", help="搜索相关代码")
    search_parser.add_argument("query", help="搜索查询")
    search_parser.add_argument("-n", "--num", type=int, default=10, help="返回结果数")
    search_parser.add_argument("-p", "--preview", type=int, default=5, help="预览行数")
    search_parser.set_defaults(func=cmd_search)

    # stats 命令
    stats_parser = subparsers.add_parser("stats", help="查看索引统计")
    stats_parser.set_defaults(func=cmd_stats)

    # index 命令
    index_parser = subparsers.add_parser("index", help="索引项目")
    index_parser.add_argument(
        "--patterns", nargs="+", help="文件模式 (如 **/*.py)"
    )
    index_parser.add_argument(
        "--exclude", nargs="+", help="排除模式"
    )
    index_parser.add_argument(
        "--chunk-size", type=int, default=500, help="代码块大小"
    )
    index_parser.set_defaults(func=cmd_index)

    # context 命令
    context_parser = subparsers.add_parser("context", help="获取查询上下文")
    context_parser.add_argument("query", help="查询文本")
    context_parser.add_argument(
        "--max-tokens", type=int, default=100000, help="最大 token 数"
    )
    context_parser.add_argument(
        "--no-summary", action="store_true", help="不包含摘要"
    )
    context_parser.set_defaults(func=cmd_context)

    # clear 命令
    clear_parser = subparsers.add_parser("clear", help="清空索引")
    clear_parser.set_defaults(func=cmd_clear)

    args = parser.parse_args()

    # 默认命令：如果没有指定命令，把第一个参数当作搜索查询
    if args.command is None:
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
            # 创建一个简单的搜索
            class DefaultArgs:
                query = sys.argv[1]
                num = 10
                preview = 5
            args = DefaultArgs()
            cmd_search(args)
        else:
            parser.print_help()
    else:
        args.func(args)


if __name__ == "__main__":
    main()
