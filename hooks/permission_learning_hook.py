#!/usr/bin/env python3
"""
Permission Learning Hook for Claude Code

使用 PreToolUse 和 PermissionRequest hook 学习用户权限偏好。

策略：
1. PreToolUse: 记录所有工具调用（执行成功 = 用户允许）
2. PermissionRequest: 对已知安全模式自动批准
3. 定期分析并生成权限建议

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

from src.memory.personal_memory import PersonalMemory, extract_permission_pattern

# 调试日志
DEBUG_LOG = os.path.expanduser("/tmp/permission-learning-debug.log")


def debug_log(message: str):
    """写入调试日志"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(DEBUG_LOG, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


def get_hook_event(input_data: dict) -> str:
    """获取 hook 事件类型"""
    return input_data.get("hook_event_name", "")


def format_permission_string(tool_name: str, tool_input: dict) -> str:
    """
    将工具调用转换为权限字符串格式

    Args:
        tool_name: 工具名称
        tool_input: 工具输入参数

    Returns:
        权限字符串，如 "Bash(git push:origin main)"
    """
    if tool_name == "Bash":
        command = tool_input.get("command", "")
        if not command:
            return "Bash"

        # 解析命令：提取主要命令和参数
        parts = command.split()
        if not parts:
            return "Bash"

        main_cmd = parts[0]

        # 特殊处理复合命令
        if "&&" in command or ";" in command:
            # 复合命令，只取第一部分
            main_cmd = command.split("&&")[0].split(";")[0].strip().split()[0]

        # 构建权限字符串
        # 格式: Bash(cmd:args) 或 Bash(cmd)
        args_str = command.replace(main_cmd, "").strip()
        if args_str:
            # 简化参数，只保留关键部分
            first_arg = args_str.split()[0] if args_str.split() else ""
            return f"Bash({main_cmd}:{first_arg})"
        else:
            return f"Bash({main_cmd})"

    elif tool_name == "Edit" or tool_name == "Write":
        file_path = tool_input.get("file_path", "")
        if file_path:
            # 只保留文件名或最后一级目录
            parts = Path(file_path).parts
            if len(parts) > 2:
                short_path = f".../{parts[-1]}"
            else:
                short_path = file_path
            return f"{tool_name}({short_path})"
        return tool_name

    elif tool_name == "Read":
        file_path = tool_input.get("file_path", "")
        if file_path:
            parts = Path(file_path).parts
            if len(parts) > 2:
                short_path = f".../{parts[-1]}"
            else:
                short_path = file_path
            return f"Read({short_path})"
        return "Read"

    elif tool_name == "Glob":
        pattern = tool_input.get("pattern", "")
        if pattern:
            return f"Glob({pattern})"
        return "Glob"

    elif tool_name == "Grep":
        pattern = tool_input.get("pattern", "")
        if pattern:
            return f"Grep({pattern})"
        return "Grep"

    elif tool_name == "WebFetch":
        url = tool_input.get("url", "")
        if url:
            # 提取域名
            try:
                from urllib.parse import urlparse
                domain = urlparse(url).netloc
                return f"WebFetch(domain:{domain})"
            except Exception:
                return "WebFetch"
        return "WebFetch"

    elif tool_name == "WebSearch":
        return "WebSearch"

    elif tool_name.startswith("mcp__"):
        # MCP 工具
        return tool_name

    else:
        return tool_name


def handle_pre_tool_use(input_data: dict) -> dict:
    """
    处理 PreToolUse 事件

    记录工具调用，用于后续学习。
    """
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    tool_use_id = input_data.get("tool_use_id", "")

    debug_log(f"PreToolUse: {tool_name}, input: {json.dumps(tool_input)[:200]}")

    # 转换为权限字符串
    permission = format_permission_string(tool_name, tool_input)
    debug_log(f"Permission string: {permission}")

    # 记录到临时文件，等待 PostToolUse 确认执行结果
    pending_file = Path("/tmp/permission-pending.json")
    try:
        pending_data = {
            "tool_use_id": tool_use_id,
            "permission": permission,
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "tool_input": tool_input,
        }
        with open(pending_file, "w") as f:
            json.dump(pending_data, f)
    except Exception as e:
        debug_log(f"Error writing pending file: {e}")

    # 允许执行（不做阻止）
    return {"decision": "allow"}


def handle_post_tool_use(input_data: dict) -> dict:
    """
    处理 PostToolUse 事件

    工具成功执行 = 用户允许了该权限。
    """
    tool_name = input_data.get("tool_name", "")
    tool_use_id = input_data.get("tool_use_id", "")
    tool_response = input_data.get("tool_response", {})

    debug_log(f"PostToolUse: {tool_name}, tool_use_id: {tool_use_id}")

    # 检查是否有对应的 pending 记录
    pending_file = Path("/tmp/permission-pending.json")
    if not pending_file.exists():
        debug_log("No pending file found")
        return {}

    try:
        pending_data = json.loads(pending_file.read_text())
        if pending_data.get("tool_use_id") != tool_use_id:
            debug_log(f"tool_use_id mismatch: {pending_data.get('tool_use_id')} != {tool_use_id}")
            return {}

        permission = pending_data.get("permission", "")

        # 检查是否执行成功
        # tool_response 可能包含错误信息
        is_success = True
        if isinstance(tool_response, dict):
            if tool_response.get("error") or tool_response.get("isError"):
                is_success = False

        if is_success:
            debug_log(f"Tool executed successfully, recording permission: {permission}")

            # 使用 PersonalMemory 记录权限决策
            try:
                memory = PersonalMemory()
                memory.record_permission_decision(
                    permission=permission,
                    action="allow",
                    context={
                        "tool_name": tool_name,
                        "source": "post_tool_use_hook",
                    },
                )
                debug_log("Recorded via PersonalMemory")

                # 生成建议
                suggestions = memory.suggest_permissions(threshold=3)
                if suggestions:
                    debug_log(f"Generated {len(suggestions)} suggestions")

            except Exception as e:
                debug_log(f"Error using PersonalMemory: {e}")

        # 清理 pending 文件
        pending_file.unlink(missing_ok=True)

    except Exception as e:
        debug_log(f"Error processing pending file: {e}")

    return {}


def handle_permission_request(input_data: dict) -> dict:
    """
    处理 PermissionRequest 事件

    对已知的安全模式自动批准。
    """
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})

    debug_log(f"PermissionRequest: {tool_name}")

    permission = format_permission_string(tool_name, tool_input)
    pattern_info = extract_permission_pattern(permission)

    if pattern_info:
        pattern = pattern_info["pattern"]
        debug_log(f"Extracted pattern: {pattern}")

        # 检查是否是高频使用的安全模式
        try:
            memory = PersonalMemory()
            patterns = memory.get_permission_patterns(min_count=2)

            # 查找匹配的模式
            for pp in patterns:
                if pp.pattern == pattern and pp.count >= 3:
                    debug_log(f"Auto-approving pattern: {pattern} (count: {pp.count})")

                    # 返回自动批准决策
                    return {
                        "hookSpecificOutput": {
                            "hookEventName": "PermissionRequest",
                            "decision": {
                                "behavior": "allow",
                            },
                        },
                    }

        except Exception as e:
            debug_log(f"Error checking patterns: {e}")

    # 不自动批准，让用户决定
    return {}


def handle_notification(input_data: dict) -> dict:
    """
    处理 Notification 事件（兼容旧配置）

    新版本不传递 permission/action，所以这里不做处理。
    """
    notification_type = input_data.get("notification_type", "")
    debug_log(f"Notification: {notification_type}")

    # 新版本没有 permission 字段，跳过
    if "permission" not in input_data:
        debug_log("No permission field in Notification, skipping")
        return {}

    # 兼容旧版本格式
    permission = input_data.get("permission", "")
    action = input_data.get("action", "")

    if permission and action:
        debug_log(f"Legacy format: {permission} -> {action}")
        try:
            memory = PersonalMemory()
            memory.record_permission_decision(permission=permission, action=action)
        except Exception as e:
            debug_log(f"Error: {e}")

    return {}


def main():
    """主函数"""
    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            debug_log("No input received")
            sys.exit(0)

        input_data = json.loads(raw_input)
    except json.JSONDecodeError as e:
        debug_log(f"JSON decode error: {e}")
        sys.exit(0)

    debug_log(f"Input: {json.dumps(input_data, ensure_ascii=False)[:300]}")

    # 获取事件类型
    event = get_hook_event(input_data)
    debug_log(f"Event: {event}")

    # 根据事件类型处理
    output = {}

    if event == "PreToolUse":
        output = handle_pre_tool_use(input_data)
    elif event == "PostToolUse":
        output = handle_post_tool_use(input_data)
    elif event == "PermissionRequest":
        output = handle_permission_request(input_data)
    elif event == "Notification":
        output = handle_notification(input_data)
    else:
        debug_log(f"Unknown event: {event}")

    # 输出结果（如果有）
    if output:
        print(json.dumps(output))
        debug_log(f"Output: {json.dumps(output)[:200]}")

    sys.exit(0)


if __name__ == "__main__":
    main()