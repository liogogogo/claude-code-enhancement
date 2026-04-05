#!/usr/bin/env python3
"""
权限应用器 - 将学习到的权限应用到配置

解决的核心问题：
- personal_memory 存储了权限模式但没有应用
- 用户每次还要手动批准

工作流程：
1. 读取 ~/.claude/memory/permissions.json
2. 提取高频模式 (count >= threshold)
3. 生成 permissions.allow 配置
4. 写入 settings.json 或输出供用户确认
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .durable_knowledge import DurableKnowledgeLayer


class PermissionApplier:
    """
    权限应用器

    将学习到的权限模式应用到配置文件。
    """

    def __init__(
        self,
        memory_path: Optional[Path] = None,
        settings_path: Optional[Path] = None,
    ):
        self.memory_path = memory_path or DurableKnowledgeLayer.default_memory_root()
        self.settings_path = settings_path or Path.home() / ".claude" / "settings.json"

    def get_learned_permissions(self, min_count: int = 3) -> Dict[str, dict]:
        """
        获取学习到的权限模式

        Args:
            min_count: 最小出现次数阈值

        Returns:
            权限模式字典
        """
        perms_file = self.memory_path / "permissions.json"
        if not perms_file.exists():
            return {}

        try:
            data = json.loads(perms_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, IOError):
            return {}

        patterns = data.get("patterns", {})
        result = {}

        for pattern, info in patterns.items():
            count = info.get("count", 0)
            if count >= min_count:
                result[pattern] = {
                    "count": count,
                    "description": info.get("description", ""),
                    "last_seen": info.get("last_seen"),
                }

        return result

    def generate_allow_list(
        self,
        min_count: int = 3,
        include_patterns: Optional[List[str]] = None,
        exclude_patterns: Optional[List[str]] = None,
    ) -> List[str]:
        """
        生成 allow 列表

        Args:
            min_count: 最小出现次数
            include_patterns: 强制包含的模式
            exclude_patterns: 排除的模式

        Returns:
            权限 allow 列表
        """
        learned = self.get_learned_permissions(min_count)

        allow_list = []

        # 添加学习到的模式
        for pattern in sorted(learned.keys()):
            # 检查是否在排除列表
            if exclude_patterns:
                if any(ex in pattern for ex in exclude_patterns):
                    continue

            allow_list.append(pattern)

        # 添加强制包含的模式
        if include_patterns:
            for p in include_patterns:
                if p not in allow_list:
                    allow_list.append(p)

        return allow_list

    def apply_to_settings(
        self,
        min_count: int = 3,
        dry_run: bool = False,
        merge: bool = True,
    ) -> dict:
        """
        应用到 settings.json

        Args:
            min_count: 最小出现次数阈值
            dry_run: 仅预览不写入
            merge: 是否与现有配置合并

        Returns:
            结果信息
        """
        allow_list = self.generate_allow_list(min_count)

        if not allow_list:
            return {
                "success": False,
                "message": "没有学习到足够的权限模式",
                "patterns_found": 0,
            }

        # 读取现有配置
        existing = {}
        if self.settings_path.exists():
            try:
                existing = json.loads(self.settings_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                existing = {}

        # 准备新配置
        if merge and "permissions" in existing:
            existing_allow = existing.get("permissions", {}).get("allow", [])
            # 合并去重
            combined = list(set(existing_allow + allow_list))
            allow_list = sorted(combined)

        new_config = existing.copy()
        if "permissions" not in new_config:
            new_config["permissions"] = {}
        new_config["permissions"]["allow"] = allow_list

        # 添加元数据
        new_config["_learned_at"] = datetime.now().isoformat()
        new_config["_learned_count"] = len(allow_list)

        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "message": "预览模式，未写入",
                "patterns_found": len(allow_list),
                "config_preview": new_config,
                "new_permissions": allow_list,
            }

        # 备份现有配置
        if self.settings_path.exists():
            backup_path = self.settings_path.with_suffix(
                f".backup.{datetime.now().strftime('%Y%m%d%H%M%S')}"
            )
            backup_path.write_text(
                json.dumps(existing, indent=2, ensure_ascii=False),
                encoding="utf-8"
            )

        # 写入新配置
        self.settings_path.parent.mkdir(parents=True, exist_ok=True)
        self.settings_path.write_text(
            json.dumps(new_config, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

        return {
            "success": True,
            "message": f"已应用 {len(allow_list)} 个权限模式",
            "patterns_found": len(allow_list),
            "backup": str(backup_path) if self.settings_path.exists() else None,
            "applied_permissions": allow_list,
        }

    def generate_report(self) -> str:
        """生成权限学习报告"""
        learned = self.get_learned_permissions(min_count=1)

        lines = [
            "╔══════════════════════════════════════════════════════════╗",
            "║              权限学习报告                                 ║",
            "╚══════════════════════════════════════════════════════════╝",
            "",
        ]

        if not learned:
            lines.append("  暂无学习到的权限模式")
            return "\n".join(lines)

        # 按次数排序
        sorted_patterns = sorted(
            learned.items(),
            key=lambda x: x[1].get("count", 0),
            reverse=True
        )

        # 统计
        total_patterns = len(sorted_patterns)
        ready_patterns = sum(1 for p, i in sorted_patterns if i.get("count", 0) >= 3)

        lines.append(f"  总模式数: {total_patterns}")
        lines.append(f"  可应用 (>=3次): {ready_patterns}")
        lines.append("")

        # 列出模式
        lines.append("  模式列表:")
        lines.append("  ┌──────────────────────┬───────┬─────────────┐")
        lines.append("  │ 模式                 │ 次数  │ 状态        │")
        lines.append("  ├──────────────────────┼───────┼─────────────┤")

        for pattern, info in sorted_patterns[:15]:
            count = info.get("count", 0)
            status = "✅ 可用" if count >= 3 else "⏳ 待观察"
            # 截断模式名称
            display_pattern = pattern[:20] + "..." if len(pattern) > 20 else pattern
            lines.append(f"  │ {display_pattern:<20} │ {count:>5} │ {status:<11} │")

        lines.append("  └──────────────────────┴───────┴─────────────┘")
        lines.append("")

        # 建议的 allow 列表
        ready = [p for p, i in sorted_patterns if i.get("count", 0) >= 3]
        if ready:
            lines.append("  建议添加到 settings.json:")
            lines.append('  "permissions": {')
            lines.append('    "allow": [')
            for p in ready[:10]:
                lines.append(f'      "{p}",')
            lines.append('    ]')
            lines.append('  }')

        return "\n".join(lines)


def apply_learned_permissions(
    min_count: int = 3,
    dry_run: bool = False,
) -> dict:
    """
    便捷函数：应用学习到的权限

    Args:
        min_count: 最小出现次数
        dry_run: 预览模式

    Returns:
        结果信息
    """
    applier = PermissionApplier()
    return applier.apply_to_settings(min_count=min_count, dry_run=dry_run)


if __name__ == "__main__":
    import sys

    applier = PermissionApplier()

    # 默认显示报告
    if len(sys.argv) == 1:
        print(applier.generate_report())
        print()
        print("运行 'python permission_applier.py --apply' 应用权限")
        sys.exit(0)

    # 应用权限
    if "--apply" in sys.argv:
        dry_run = "--dry-run" in sys.argv
        result = applier.apply_to_settings(min_count=3, dry_run=dry_run)

        if result["success"]:
            print(f"✅ {result['message']}")
            if dry_run:
                print()
                print("预览配置:")
                print(json.dumps(result.get("config_preview", {}), indent=2, ensure_ascii=False))
            else:
                print(f"   新增权限: {len(result.get('applied_permissions', []))}")
        else:
            print(f"❌ {result['message']}")
        sys.exit(0 if result["success"] else 1)

    # 显示帮助
    if "--help" in sys.argv:
        print("用法:")
        print("  python permission_applier.py           # 显示报告")
        print("  python permission_applier.py --apply   # 应用权限")
        print("  python permission_applier.py --apply --dry-run  # 预览")
        sys.exit(0)