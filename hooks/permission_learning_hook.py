#!/usr/bin/env python3
"""
Permission Learning Hook for Claude Code

功能：
1. 记录用户允许的权限模式
2. 智能归纳通用权限规则
3. 提供权限建议

用法：
- 配置为 Notification hook，监听 permission_prompt 事件
- 调用 PersonalMemory API 存储权限决策
- 定期分析并生成权限建议

作者: claude-code-enhancement
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径以导入 src 模块
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.memory.personal_memory import PersonalMemory

# 配置
DEBUG_LOG = os.path.expanduser("/tmp/permission-learning-debug.log")


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
        if not raw_input:
            debug_log("No input received")
            sys.exit(0)

        input_data = json.loads(raw_input)
    except json.JSONDecodeError as e:
        debug_log(f"JSON decode error: {e}")
        sys.exit(0)

    debug_log(f"Input: {json.dumps(input_data, ensure_ascii=False)[:500]}")

    # 获取通知类型
    notification_type = input_data.get("notification_type", "")
    debug_log(f"Notification type: {notification_type}")

    # 只处理权限提示
    if notification_type != "permission_prompt":
        sys.exit(0)

    # 提取权限信息
    permission = input_data.get("permission", "")
    action = input_data.get("action", "")  # "allow" or "deny"

    if not permission:
        debug_log("No permission found in input")
        sys.exit(0)

    debug_log(f"Permission: {permission}, Action: {action}")

    # 使用 PersonalMemory 记录权限决策
    try:
        memory = PersonalMemory()
        memory.record_permission_decision(
            permission=permission,
            action=action,
            context={"source": "claude_code_hook"},
        )
        debug_log(f"Recorded permission decision via PersonalMemory")

        # 生成建议
        suggestions = memory.suggest_permissions(threshold=3)

        # 输出建议（如果有新的高频模式）
        if suggestions:
            report = format_suggestions_report(suggestions[:5])
            print(report, file=sys.stderr)

    except Exception as e:
        debug_log(f"Error using PersonalMemory: {e}")
        # 降级：不做任何操作，允许继续

    sys.exit(0)


def format_suggestions_report(suggestions: list) -> str:
    """格式化建议报告"""
    if not suggestions:
        return ""

    lines = ["\n# 权限学习建议\n"]
    lines.append("基于你的使用习惯，建议添加以下权限规则：\n")

    for i, s in enumerate(suggestions, 1):
        lines.append(f"## {i}. {s['description']}")
        lines.append(f"- 模式: `{s['pattern']}`")
        lines.append(f"- 使用次数: {s['count']}")
        if s.get('examples'):
            lines.append(f"- 示例: `{s['examples'][0]}`")
        lines.append("")

    lines.append("---")
    lines.append("将以上模式添加到 ~/.claude/settings.json 的 permissions.allow 中")

    return "\n".join(lines)


if __name__ == "__main__":
    main()
