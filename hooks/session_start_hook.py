#!/usr/bin/env python3
"""
Session Start Hook - 项目自动索引

在 Claude Code 会话开始时自动索引项目代码，为后续查询提供上下文。

触发时机：SessionStart 事件

功能：
1. 检测项目路径
2. 自动索引代码（如果尚未索引）
3. 输出索引状态供 Claude 参考

作者: claude-code-enhancement
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.context_manager import create_context_manager

# 调试日志
DEBUG_LOG = os.path.expanduser("/tmp/session-start-debug.log")


def debug_log(message: str):
    """写入调试日志"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(DEBUG_LOG, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


def main():
    """主函数"""
    # 读取输入
    try:
        raw_input = sys.stdin.read()
        if raw_input:
            input_data = json.loads(raw_input)
            debug_log(f"Input: {json.dumps(input_data, ensure_ascii=False)[:200]}")
        else:
            input_data = {}
    except json.JSONDecodeError as e:
        debug_log(f"JSON decode error: {e}")
        input_data = {}

    # 获取项目路径
    cwd = input_data.get("cwd", os.getcwd())
    project_path = Path(cwd)

    debug_log(f"Project path: {project_path}")

    # 检查是否是有效项目（有代码文件）
    if not project_path.exists():
        debug_log(f"Project path does not exist: {project_path}")
        sys.exit(0)

    # 创建上下文管理器
    try:
        cm = create_context_manager(project_path)
        stats = cm.get_stats()

        debug_log(f"Current stats: {stats}")

        # 如果尚未索引，自动索引
        if stats["indexed_files"] == 0:
            debug_log("Auto-indexing project...")

            # 确定文件模式
            file_patterns = ["**/*.py", "**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx", "**/*.go", "**/*.rs"]

            # 排除常见不需要的目录
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

            # 输出索引信息供 Claude 参考
            print(f"\n# 项目索引完成")
            print(f"- 文件数: {index_stats['indexed_files']}")
            print(f"- 代码块: {index_stats['total_chunks']}")
            print(f"- 可用查询: `python3 hooks/context_query.py search <query>`")

        else:
            debug_log(f"Project already indexed: {stats['indexed_files']} files")
            # 输出已有索引信息
            print(f"\n# 项目索引状态")
            print(f"- 已索引文件: {stats['indexed_files']}")
            print(f"- 代码块: {stats['total_chunks']}")
            print(f"- 向量存储: {'启用' if stats['has_vector_store'] else '内存模式'}")

    except Exception as e:
        debug_log(f"Error: {e}")
        # 不阻塞会话启动
        print(f"\n# 项目索引失败: {e}")

    sys.exit(0)


if __name__ == "__main__":
    main()