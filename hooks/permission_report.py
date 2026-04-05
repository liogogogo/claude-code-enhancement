#!/usr/bin/env python3
"""
权限学习报告工具

用法:
    python3 permission_report.py           # 查看完整报告
    python3 permission_report.py --suggest # 只显示建议
    python3 permission_report.py --stats   # 只显示统计
    python3 permission_report.py --export  # 导出建议
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 添加项目路径以导入 src 模块
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.core.durable_knowledge import DurableKnowledgeLayer


def _open_memory():
    """与个人记忆文件同一入口，经耐久资产层（不挂载项目学习）。"""
    layer = DurableKnowledgeLayer.for_hook_personal_memory(Path.cwd())
    return DurableKnowledgeLayer.require_personal_memory(layer)


def print_stats(memory: PersonalMemory):
    """打印统计信息"""
    stats = memory.get_stats()
    perm_stats = memory.get_permission_stats()

    print("=" * 50)
    print("📊 权限学习统计")
    print("=" * 50)

    print(f"\n✅ 允许的权限: {perm_stats['allowed']} 种")
    print(f"❌ 拒绝的权限: {perm_stats['denied']} 种")
    print(f"🔄 归纳的模式: {perm_stats['patterns_discovered']} 种")

    # 显示 Top 5 模式
    patterns = memory.get_permission_patterns()
    if patterns:
        print("\n📈 高频模式 Top 5:")
        for i, pp in enumerate(patterns[:5], 1):
            print(f"   {i}. {pp.pattern} ({pp.count} 次)")


def print_suggestions(memory: PersonalMemory):
    """打印建议"""
    suggestions = memory.suggest_permissions(threshold=3)

    if not suggestions:
        print("暂无权限建议（需要至少 3 次使用同一模式）")
        return

    print("=" * 50)
    print("💡 权限建议")
    print("=" * 50)

    print()
    for i, s in enumerate(suggestions[:10], 1):
        print(f"{i}. {s.get('description', s.get('pattern'))}")
        print(f"   模式: {s.get('pattern')}")
        print(f"   次数: {s.get('count')}")
        print()


def print_full_report(memory: PersonalMemory):
    """打印完整报告"""
    print("\n" + "=" * 60)
    print("📋 Claude Code 权限学习报告")
    print("=" * 60)

    print_stats(memory)
    print()
    print_suggestions(memory)

    print("=" * 60)
    print("\n💡 提示: 将建议的模式添加到 ~/.claude/settings.json")
    print("   格式: \"Bash(git push:*)\" 添加到 permissions.allow 数组")


def export_to_settings(memory: PersonalMemory):
    """导出建议到 settings.json 格式"""
    suggestions = memory.suggest_permissions(threshold=3)

    if not suggestions:
        print("暂无可导出的建议")
        return

    print("\n# 将以下内容添加到 ~/.claude/settings.json 的 permissions.allow 中:\n")
    print('"permissions": {')
    print('  "allow": [')

    existing = get_existing_permissions()

    for s in suggestions:
        pattern = s.get("pattern", "")
        if pattern and pattern not in existing:
            desc = s.get("description", "")
            count = s.get("count", 0)
            print(f'    "{pattern}",  # {desc} ({count}次)')

    print("  ]")
    print("}")


def get_existing_permissions():
    """获取现有权限"""
    settings_file = Path.home() / ".claude" / "settings.json"
    if settings_file.exists():
        try:
            with open(settings_file, "r") as f:
                settings = json.load(f)
            return set(settings.get("permissions", {}).get("allow", []))
        except Exception:
            pass
    return set()


def main():
    memory = _open_memory()

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--suggest":
            print_suggestions(memory)
        elif arg == "--stats":
            print_stats(memory)
        elif arg == "--export":
            export_to_settings(memory)
        else:
            print(f"用法: {sys.argv[0]} [--suggest|--stats|--export]")
    else:
        print_full_report(memory)


if __name__ == "__main__":
    main()
