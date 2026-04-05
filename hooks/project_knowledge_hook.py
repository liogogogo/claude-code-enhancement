#!/usr/bin/env python3
"""
项目知识 Hook - 在代码生成时注入项目风格指南

触发时机：
- PreToolUse (Edit/Write)

功能：
1. 加载项目知识
2. 生成风格指南
3. 注入到上下文中
"""

import json
import os
import sys
from pathlib import Path

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.durable_knowledge import DurableKnowledgeLayer


def get_project_knowledge_context(project_path: Path) -> str:
    """
    获取项目知识的上下文提示

    Args:
        project_path: 项目路径

    Returns:
        上下文字符串，用于注入到 Claude 的提示中
    """
    layer = DurableKnowledgeLayer.for_project_knowledge_only(project_path)
    if not layer.project_learner:
        return ""
    knowledge = layer.project_learner.load_knowledge()

    if not knowledge:
        return ""

    lines = ["\n# 项目风格指南（请遵循）\n"]

    # 命名规范
    if knowledge.naming:
        n = knowledge.naming
        lines.append("## 命名规范")
        lines.append(f"- 变量使用 `{n.variable_style}`")
        lines.append(f"- 函数使用 `{n.function_style}`")
        lines.append(f"- 类使用 `{n.class_style}`")
        lines.append(f"- 常量使用 `{n.constant_style}`")
        lines.append(f"- 私有成员前缀: `{n.private_prefix}`")
        lines.append("")

    # 代码风格
    if knowledge.style:
        s = knowledge.style
        lines.append("## 代码风格")
        lines.append(f"- 缩进: {s.indent_size} 空格")
        lines.append(f"- 引号: 使用 {s.quote_style} 引号")
        lines.append(f"- Docstring: {s.docstring_style} 风格")
        if s.max_line_length:
            lines.append(f"- 最大行长度: {s.max_line_length}")
        lines.append("")

    # 项目结构
    if knowledge.structure:
        s = knowledge.structure
        lines.append("## 项目结构")
        lines.append(f"- 类型: {s.type}")
        if s.framework:
            lines.append(f"- 框架: {s.framework}")
        lines.append(f"- 源码目录: {s.source_dir}")
        lines.append("")

    # 自定义规则
    if knowledge.custom_rules:
        lines.append("## 自定义规则")
        for rule in knowledge.custom_rules:
            lines.append(f"- {rule}")
        lines.append("")

    lines.append("---\n")

    return '\n'.join(lines)


def main():
    """主函数"""
    try:
        # 读取输入
        raw_input = sys.stdin.read()
        if not raw_input:
            sys.exit(0)

        input_data = json.loads(raw_input)
    except json.JSONDecodeError:
        sys.exit(0)

    # 获取项目路径
    cwd = input_data.get("cwd", os.getcwd())
    project_path = Path(cwd)

    # 获取工具名称
    tool_name = input_data.get("tool_name", "")

    # 只在编辑/写入文件时注入
    if tool_name not in ["Edit", "Write"]:
        sys.exit(0)

    # 获取项目知识上下文
    context = get_project_knowledge_context(project_path)

    if context:
        # 输出附加上下文
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "additionalContext": context,
            }
        }
        print(json.dumps(output))

    sys.exit(0)


if __name__ == "__main__":
    main()