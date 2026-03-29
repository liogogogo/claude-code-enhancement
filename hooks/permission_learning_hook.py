#!/usr/bin/env python3
"""
Permission Learning Hook for Claude Code

功能：
1. 记录用户允许的权限模式
2. 智能归纳通用权限规则
3. 提供权限建议

用法：
- 配置为 Notification hook，监听 permission_prompt 事件
- 记录用户决策到 ~/.claude/permission_learning.json
- 定期分析并生成权限建议

作者: claude-code-enhancement
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from collections import Counter
from typing import Dict, List, Any, Optional

# 配置
PERMISSION_LEARNING_FILE = os.path.expanduser("~/.claude/permission_learning.json")
SUGGESTION_FILE = os.path.expanduser("~/.claude/permission_suggestions.json")
DEBUG_LOG = os.path.expanduser("/tmp/permission-learning-debug.log")

# 权限模式归纳规则
PATTERN_RULES = [
    # Git 相关
    {
        "match": r"^Bash\(git (\w+):.*\)$",
        "pattern": "Bash(git {command}:*)",
        "description": "Git {command} 命令",
    },
    # Python 相关
    {
        "match": r"^Bash\(pip install:.*\)$",
        "pattern": "Bash(pip install:*)",
        "description": "pip 安装包",
    },
    {
        "match": r"^Bash\(pip3 install:.*\)$",
        "pattern": "Bash(pip3 install:*)",
        "description": "pip3 安装包",
    },
    {
        "match": r"^Bash\(python -m pytest:.*\)$",
        "pattern": "Bash(python -m pytest:*)",
        "description": "pytest 测试",
    },
    {
        "match": r"^Bash\(\.venv/bin/python.*\)$",
        "pattern": "Bash(.venv/bin/python:*)",
        "description": "虚拟环境 Python",
    },
    # 文件操作
    {
        "match": r"^Bash\(mkdir:.*\)$",
        "pattern": "Bash(mkdir:*)",
        "description": "创建目录",
    },
    {
        "match": r"^Bash\(ls:.*\)$",
        "pattern": "Bash(ls:*)",
        "description": "列出目录",
    },
    {
        "match": r"^Bash\(find:.*\)$",
        "pattern": "Bash(find:*)",
        "description": "查找文件",
    },
    {
        "match": r"^Bash\(grep:.*\)$",
        "pattern": "Bash(grep:*)",
        "description": "搜索内容",
    },
    # gh CLI
    {
        "match": r"^Bash\(gh (\w+):.*\)$",
        "pattern": "Bash(gh {command}:*)",
        "description": "GitHub CLI {command}",
    },
    # tmux
    {
        "match": r"^Bash\(tmux (\w+):.*\)$",
        "pattern": "Bash(tmux {command}:*)",
        "description": "tmux {command}",
    },
    # curl
    {
        "match": r"^Bash\(curl:.*\)$",
        "pattern": "Bash(curl:*)",
        "description": "HTTP 请求",
    },
    # cd 命令
    {
        "match": r"^Bash\(cd:.*\)$",
        "pattern": "Bash(cd:*)",
        "description": "切换目录",
    },
    # chmod
    {
        "match": r"^Bash\(chmod:.*\)$",
        "pattern": "Bash(chmod:*)",
        "description": "修改权限",
    },
    # source
    {
        "match": r"^Bash\(source:.*\)$",
        "pattern": "Bash(source:*)",
        "description": "执行脚本",
    },
]


def debug_log(message: str):
    """写入调试日志"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(DEBUG_LOG, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


def load_learning_data() -> Dict[str, Any]:
    """加载权限学习数据"""
    if os.path.exists(PERMISSION_LEARNING_FILE):
        try:
            with open(PERMISSION_LEARNING_FILE, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
    return {
        "allowed_permissions": {},
        "denied_permissions": {},
        "pattern_usage": {},
        "suggestions_generated": [],
    }


def save_learning_data(data: Dict[str, Any]):
    """保存权限学习数据"""
    os.makedirs(os.path.dirname(PERMISSION_LEARNING_FILE), exist_ok=True)
    with open(PERMISSION_LEARNING_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def extract_pattern(permission: str) -> Optional[Dict[str, str]]:
    """从具体权限中提取通用模式"""
    for rule in PATTERN_RULES:
        match = re.match(rule["match"], permission)
        if match:
            groups = match.groups()
            pattern = rule["pattern"]
            description = rule["description"]

            # 替换占位符
            if "{command}" in pattern and groups:
                pattern = pattern.replace("{command}", groups[0])
                description = description.replace("{command}", groups[0])

            return {
                "original": permission,
                "pattern": pattern,
                "description": description,
            }
    return None


def record_permission(permission: str, action: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """记录权限决策"""
    timestamp = datetime.now().isoformat()

    if action == "allow":
        if permission not in data["allowed_permissions"]:
            data["allowed_permissions"][permission] = {
                "count": 0,
                "first_seen": timestamp,
                "last_seen": timestamp,
            }
        data["allowed_permissions"][permission]["count"] += 1
        data["allowed_permissions"][permission]["last_seen"] = timestamp

        # 提取并记录模式
        pattern_info = extract_pattern(permission)
        if pattern_info:
            pattern = pattern_info["pattern"]
            if pattern not in data["pattern_usage"]:
                data["pattern_usage"][pattern] = {
                    "count": 0,
                    "description": pattern_info["description"],
                    "examples": [],
                }
            data["pattern_usage"][pattern]["count"] += 1
            if permission not in data["pattern_usage"][pattern]["examples"]:
                data["pattern_usage"][pattern]["examples"].append(permission)

    elif action == "deny":
        if permission not in data["denied_permissions"]:
            data["denied_permissions"][permission] = {
                "count": 0,
                "first_seen": timestamp,
            }
        data["denied_permissions"][permission]["count"] += 1

    return data


def generate_suggestions(data: Dict[str, Any], threshold: int = 3) -> List[Dict[str, Any]]:
    """生成权限建议"""
    suggestions = []

    for pattern, info in data["pattern_usage"].items():
        if info["count"] >= threshold:
            suggestions.append({
                "pattern": pattern,
                "count": info["count"],
                "description": info["description"],
                "examples": info["examples"][:3],
                "suggestion": f"建议添加: {pattern}",
            })

    # 按使用次数排序
    suggestions.sort(key=lambda x: x["count"], reverse=True)

    return suggestions


def save_suggestions(suggestions: List[Dict[str, Any]]):
    """保存建议到文件"""
    os.makedirs(os.path.dirname(SUGGESTION_FILE), exist_ok=True)
    with open(SUGGESTION_FILE, "w") as f:
        json.dump({
            "generated_at": datetime.now().isoformat(),
            "suggestions": suggestions,
        }, f, indent=2, ensure_ascii=False)


def format_suggestions_report(suggestions: List[Dict[str, Any]]) -> str:
    """格式化建议报告"""
    if not suggestions:
        return "暂无权限建议"

    lines = ["# 权限学习建议\n"]
    lines.append("基于你的使用习惯，建议添加以下权限规则：\n")

    for i, s in enumerate(suggestions, 1):
        lines.append(f"## {i}. {s['description']}")
        lines.append(f"- 模式: `{s['pattern']}`")
        lines.append(f"- 使用次数: {s['count']}")
        lines.append(f"- 示例: `{s['examples'][0]}`")
        lines.append("")

    lines.append("---")
    lines.append("将以上模式添加到 ~/.claude/settings.json 的 permissions.allow 中")

    return "\n".join(lines)


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

    # 加载并更新学习数据
    data = load_learning_data()
    data = record_permission(permission, action, data)

    # 生成建议
    suggestions = generate_suggestions(data)
    data["suggestions_generated"] = [s["pattern"] for s in suggestions]

    # 保存数据
    save_learning_data(data)
    save_suggestions(suggestions)

    # 输出建议（如果有新的高频模式）
    if suggestions:
        report = format_suggestions_report(suggestions[:5])
        print(report, file=sys.stderr)

    sys.exit(0)


if __name__ == "__main__":
    main()
