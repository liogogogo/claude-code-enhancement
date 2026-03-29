#!/usr/bin/env python3
"""
权限学习报告工具

用法:
    python3 permission_report.py           # 查看完整报告
    python3 permission_report.py --suggest # 只显示建议
    python3 permission_report.py --stats   # 只显示统计
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

PERMISSION_LEARNING_FILE = os.path.expanduser("~/.claude/permission_learning.json")
SUGGESTION_FILE = os.path.expanduser("~/.claude/permission_suggestions.json")


def load_data():
    """加载学习数据"""
    if os.path.exists(PERMISSION_LEARNING_FILE):
        with open(PERMISSION_LEARNING_FILE, "r") as f:
            return json.load(f)
    return None


def load_suggestions():
    """加载建议"""
    if os.path.exists(SUGGESTION_FILE):
        with open(SUGGESTION_FILE, "r") as f:
            return json.load(f)
    return None


def print_stats(data):
    """打印统计信息"""
    if not data:
        print("暂无学习数据")
        return

    print("=" * 50)
    print("📊 权限学习统计")
    print("=" * 50)

    allowed = data.get("allowed_permissions", {})
    denied = data.get("denied_permissions", {})
    patterns = data.get("pattern_usage", {})

    print(f"\n✅ 允许的权限: {len(allowed)} 种")
    total_allowed = sum(p.get("count", 0) for p in allowed.values())
    print(f"   总使用次数: {total_allowed}")

    print(f"\n❌ 拒绝的权限: {len(denied)} 种")

    print(f"\n🔄 归纳的模式: {len(patterns)} 种")

    # 显示 Top 5 模式
    if patterns:
        print("\n📈 高频模式 Top 5:")
        sorted_patterns = sorted(
            patterns.items(),
            key=lambda x: x[1].get("count", 0),
            reverse=True
        )[:5]
        for i, (pattern, info) in enumerate(sorted_patterns, 1):
            print(f"   {i}. {pattern} ({info.get('count', 0)} 次)")


def print_suggestions():
    """打印建议"""
    suggestions = load_suggestions()

    if not suggestions or not suggestions.get("suggestions"):
        print("暂无权限建议")
        return

    print("=" * 50)
    print("💡 权限建议")
    print("=" * 50)

    generated_at = suggestions.get("generated_at", "")
    if generated_at:
        print(f"\n生成时间: {generated_at}")

    print()
    for i, s in enumerate(suggestions.get("suggestions", [])[:10], 1):
        print(f"{i}. {s.get('description', s.get('pattern'))}")
        print(f"   模式: {s.get('pattern')}")
        print(f"   次数: {s.get('count')}")
        print()


def print_full_report():
    """打印完整报告"""
    data = load_data()

    print("\n" + "=" * 60)
    print("📋 Claude Code 权限学习报告")
    print("=" * 60)

    print_stats(data)
    print()
    print_suggestions()

    print("=" * 60)
    print("\n💡 提示: 将建议的模式添加到 ~/.claude/settings.json")
    print("   格式: \"Bash(git push:*)\" 添加到 permissions.allow 数组")


def export_to_settings():
    """导出建议到 settings.json 格式"""
    suggestions = load_suggestions()

    if not suggestions or not suggestions.get("suggestions"):
        print("暂无可导出的建议")
        return

    print("\n# 将以下内容添加到 ~/.claude/settings.json 的 permissions.allow 中:\n")
    print('"permissions": {')
    print('  "allow": [')

    existing = get_existing_permissions()

    for s in suggestions.get("suggestions", []):
        pattern = s.get("pattern", "")
        if pattern and pattern not in existing:
            print(f'    "{pattern}",  # {s.get("description", "")}')

    print("  ]")
    print("}")


def get_existing_permissions():
    """获取现有权限"""
    settings_file = os.path.expanduser("~/.claude/settings.json")
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r") as f:
                settings = json.load(f)
            return set(settings.get("permissions", {}).get("allow", []))
        except Exception:
            pass
    return set()


def main():
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--suggest":
            print_suggestions()
        elif arg == "--stats":
            data = load_data()
            print_stats(data)
        elif arg == "--export":
            export_to_settings()
        else:
            print(f"用法: {sys.argv[0]} [--suggest|--stats|--export]")
    else:
        print_full_report()


if __name__ == "__main__":
    main()
