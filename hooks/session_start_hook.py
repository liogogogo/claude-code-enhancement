#!/usr/bin/env python3
"""
Session Start Hook - 项目自动索引

在 Claude Code 会话开始时自动索引项目代码，为后续查询提供上下文。
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.context_manager import create_context_manager
from src.core.durable_knowledge import DurableKnowledgeLayer

DEBUG_LOG = os.path.expanduser("/tmp/session-start-debug.log")


def debug_log(message: str):
    """写入调试日志"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(DEBUG_LOG, "a") as file:
            file.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


def main():
    """主函数"""
    try:
        raw_input = sys.stdin.read()
        if raw_input:
            input_data = json.loads(raw_input)
            debug_log(f"Input: {json.dumps(input_data, ensure_ascii=False)[:200]}")
        else:
            input_data = {}
    except json.JSONDecodeError as error:
        debug_log(f"JSON decode error: {error}")
        input_data = {}

    cwd = input_data.get("cwd", os.getcwd())
    project_path = Path(cwd)
    debug_log(f"Project path: {project_path}")

    if not project_path.exists():
        debug_log(f"Project path does not exist: {project_path}")
        sys.exit(0)

    cm = None
    try:
        cm = create_context_manager(project_path)
        stats = cm.get_stats()
        debug_log(f"Current stats: {stats}")

        if stats["indexed_files"] == 0:
            debug_log("Auto-indexing project...")
            file_patterns = ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx", "**/*.go", "**/*.rs"]
            exclude_patterns = [
                "**/node_modules/**",
                "**/.venv/**",
                "**/venv/**",
                "**/__pycache__/**",
                "**/.git/**",
                "**/dist/**",
                "**/build/**",
            ]
            index_stats = cm.index_codebase(
                file_patterns=file_patterns,
                exclude_patterns=exclude_patterns,
            )
            debug_log(f"Index complete: {index_stats}")
            print("\n# 项目索引完成")
            print(f"- 文件数: {index_stats['indexed_files']}")
            print(f"- 代码块: {index_stats['total_chunks']}")
            print("- 可用查询: `python3 hooks/context_query.py prepare <query> --show-trace`")
        else:
            debug_log(f"Project already indexed: {stats['indexed_files']} files")
            print("\n# 项目索引状态")
            print(f"- 已索引文件: {stats['indexed_files']}")
            print(f"- 代码块: {stats['total_chunks']}")
            print(f"- 向量存储: {'启用' if stats['has_vector_store'] else '内存模式'}")
    except Exception as error:
        debug_log(f"Index error: {error}")
        print(f"\n# 项目索引失败: {error}")

    try:
        assets = DurableKnowledgeLayer.for_session_bootstrap(project_path)
        knowledge = None
        if assets.project_learner:
            knowledge = assets.project_learner.load_knowledge()
            if knowledge is None:
                debug_log("Learning project knowledge...")
                knowledge = assets.project_learner.learn()
                print("\n# 项目知识学习完成")
            else:
                print("\n# 项目知识已加载")

        if knowledge:
            if knowledge.structure:
                print(f"- 类型: {knowledge.structure.type}")
                if knowledge.structure.framework:
                    print(f"- 框架: {knowledge.structure.framework}")
            if knowledge.naming:
                print(f"- 命名风格: {knowledge.naming.function_style}")
            if knowledge.style:
                print(f"- 缩进: {knowledge.style.indent_size} 空格")

        print("\n# 增强系统")
        print("- 持久资产层已就绪（记忆 + 项目知识 + 检索注入）")
        print("- 架构图: `python3 hooks/context_query.py architecture`")
        print("- 结构化上下文: `python3 hooks/context_query.py prepare <query> --show-trace`")
        stats = assets.stats_dict()
        if cm is not None:
            stats["context_manager"] = cm.get_stats()
        debug_log(f"DurableKnowledgeLayer stats: {stats}")
    except Exception as error:
        debug_log(f"Knowledge/durable layer error: {error}")

    sys.exit(0)


if __name__ == "__main__":
    main()
