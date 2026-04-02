#!/usr/bin/env python3
"""
上下文查询工具

用法:
    python3 context_query.py search "authentication flow"
    python3 context_query.py stats
    python3 context_query.py index
    python3 context_query.py context "fix bug"
    python3 context_query.py prepare "fix bug" --show-trace
    python3 context_query.py architecture
"""

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.context_manager import create_context_manager
from src.core.unified import create_enhancer


def get_project_path() -> Path:
    """获取当前项目路径"""
    import os

    if "PROJECT_PATH" in os.environ:
        return Path(os.environ["PROJECT_PATH"])
    return Path.cwd()


def cmd_search(args):
    """搜索相关代码"""
    project_path = get_project_path()
    cm = create_context_manager(project_path)

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

    for index, (chunk, score) in enumerate(results, 1):
        print(f"\n{index}. {chunk.file_path}:{chunk.start_line}-{chunk.end_line}")
        print(f"   相似度: {score:.2%}")
        print(f"   语言: {chunk.language}")
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
        print(f"摘要层级: {[summary.value for summary in stats['summaries']]}")


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
    enhancer = create_enhancer(project_path=project_path)
    prepared = enhancer.prepare_task_context(args.query, max_chars=args.max_chars)
    print(prepared["injection_text"] or prepared["knowledge_context"] or prepared["code_context"])


def cmd_prepare(args):
    """获取结构化增强上下文"""
    project_path = get_project_path()
    enhancer = create_enhancer(project_path=project_path)
    prepared = enhancer.prepare_task_context(args.query, max_chars=args.max_chars)

    output = {
        "query": prepared["query"],
        "budget": prepared["budget"],
        "selected_items": prepared["selected_items"],
        "user_preferences": prepared["user_preferences"],
        "past_fixes": prepared["past_fixes"],
        "knowledge_context": prepared["knowledge_context"],
        "code_context": prepared["code_context"],
        "project_knowledge": prepared["project_knowledge"],
    }
    if args.show_trace:
        output["retrieval_trace"] = prepared["retrieval_trace"]
    if args.show_architecture:
        output["architecture_overview"] = prepared["architecture_overview"]

    print(json.dumps(output, indent=2, ensure_ascii=False))


def cmd_architecture(args):
    """输出增强架构图"""
    project_path = get_project_path()
    enhancer = create_enhancer(project_path=project_path)
    print(enhancer.render_architecture_diagram())


def cmd_clear(args):
    """清空索引"""
    project_path = get_project_path()
    cm = create_context_manager(project_path)
    cm.clear_all()
    print("✅ 索引已清空")


def main():
    parser = argparse.ArgumentParser(description="上下文查询工具 - 搜索和准备增强上下文")
    subparsers = parser.add_subparsers(dest="command", help="命令")

    search_parser = subparsers.add_parser("search", help="搜索相关代码")
    search_parser.add_argument("query", help="搜索查询")
    search_parser.add_argument("-n", "--num", type=int, default=10, help="返回结果数")
    search_parser.add_argument("-p", "--preview", type=int, default=5, help="预览行数")
    search_parser.set_defaults(func=cmd_search)

    stats_parser = subparsers.add_parser("stats", help="查看索引统计")
    stats_parser.set_defaults(func=cmd_stats)

    index_parser = subparsers.add_parser("index", help="索引项目")
    index_parser.add_argument("--patterns", nargs="+", help="文件模式 (如 **/*.py)")
    index_parser.add_argument("--exclude", nargs="+", help="排除模式")
    index_parser.add_argument("--chunk-size", type=int, default=500, help="代码块大小")
    index_parser.set_defaults(func=cmd_index)

    context_parser = subparsers.add_parser("context", help="获取查询上下文")
    context_parser.add_argument("query", help="查询文本")
    context_parser.add_argument("--max-chars", type=int, default=2400, help="知识上下文字符预算")
    context_parser.set_defaults(func=cmd_context)

    prepare_parser = subparsers.add_parser("prepare", help="获取结构化增强上下文")
    prepare_parser.add_argument("query", help="查询文本")
    prepare_parser.add_argument("--max-chars", type=int, default=2400, help="知识上下文字符预算")
    prepare_parser.add_argument("--show-trace", action="store_true", help="显示检索 trace")
    prepare_parser.add_argument("--show-architecture", action="store_true", help="显示架构图")
    prepare_parser.set_defaults(func=cmd_prepare)

    architecture_parser = subparsers.add_parser("architecture", help="显示增强架构图")
    architecture_parser.set_defaults(func=cmd_architecture)

    clear_parser = subparsers.add_parser("clear", help="清空索引")
    clear_parser.set_defaults(func=cmd_clear)

    args = parser.parse_args()
    if args.command is None:
        if len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
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
