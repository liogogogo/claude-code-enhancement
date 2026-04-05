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
import time
from datetime import datetime
from pathlib import Path

# 禁用所有 stderr 输出，避免被 Claude Code 误判为错误
# 只保留致命错误
_original_stderr = sys.stderr


def _suppress_stderr():
    """抑制 stderr 输出"""
    if os.environ.get("PERMISSION_HOOK_DEBUG"):
        return  # 调试模式不抑制
    sys.stderr = open(os.devnull, "w")


def _restore_stderr():
    """恢复 stderr"""
    sys.stderr = _original_stderr


# 调试日志
DEBUG_LOG = os.path.expanduser("/tmp/permission-learning-debug.log")


def debug_log(message: str):
    """写入调试日志"""
    if not os.environ.get("PERMISSION_HOOK_DEBUG"):
        return
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(DEBUG_LOG, "a") as f:
            f.write(f"[{timestamp}] {message}\n")
    except Exception:
        pass


# 延迟导入，避免启动时的错误
_extract_permission_pattern = None
_durable_layer = None
_layer_project_path = None


def _lazy_import():
    """延迟导入依赖模块"""
    global _extract_permission_pattern

    if _extract_permission_pattern is not None:
        return True

    try:
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from src.memory.personal_memory import extract_permission_pattern

        _extract_permission_pattern = extract_permission_pattern
        return True
    except Exception as e:
        debug_log(f"Import error: {e}")
        return False


def _reset_durable_layer_cache():
    global _durable_layer, _layer_project_path
    _durable_layer = None
    _layer_project_path = None


def _personal_memory_via_assets(cwd: str = ""):
    """
    通过 DurableKnowledgeLayer 取 PersonalMemory（持久资产统一入口）。

    Hook 热路径不启用 project_learner，避免重复扫描 .claude/knowledge。
    """
    global _durable_layer, _layer_project_path

    if not _lazy_import():
        return None

    try:
        project_root = Path(__file__).parent.parent
        if str(project_root) not in sys.path:
            sys.path.insert(0, str(project_root))

        from src.core.durable_knowledge import DurableKnowledgeLayer

        path = Path(cwd or os.getcwd()).resolve()
        if _durable_layer is None or _layer_project_path != path:
            _durable_layer = DurableKnowledgeLayer.for_hook_personal_memory(path)
            _layer_project_path = path
        return _durable_layer.personal_memory
    except Exception as e:
        debug_log(f"Durable layer error: {e}")
        return None


def get_hook_event(input_data: dict) -> str:
    """获取 hook 事件类型"""
    return input_data.get("hook_event_name", "")


def format_permission_string(tool_name: str, tool_input: dict) -> str:
    """将工具调用转换为权限字符串格式"""
    try:
        if tool_name == "Bash":
            command = tool_input.get("command", "")
            if not command:
                return "Bash"

            parts = command.split()
            if not parts:
                return "Bash"

            main_cmd = parts[0]

            # 特殊处理复合命令
            if "&&" in command or ";" in command:
                main_cmd = command.split("&&")[0].split(";")[0].strip().split()[0]

            args_str = command.replace(main_cmd, "").strip()
            if args_str:
                first_arg = args_str.split()[0] if args_str.split() else ""
                return f"Bash({main_cmd}:{first_arg})"
            else:
                return f"Bash({main_cmd})"

        elif tool_name in ("Edit", "Write", "Read"):
            file_path = tool_input.get("file_path", "")
            if file_path:
                parts = Path(file_path).parts
                if len(parts) > 2:
                    short_path = f".../{parts[-1]}"
                else:
                    short_path = file_path
                return f"{tool_name}({short_path})"
            return tool_name

        elif tool_name == "Glob":
            pattern = tool_input.get("pattern", "")
            return f"Glob({pattern})" if pattern else "Glob"

        elif tool_name == "Grep":
            pattern = tool_input.get("pattern", "")
            return f"Grep({pattern})" if pattern else "Grep"

        elif tool_name == "WebFetch":
            url = tool_input.get("url", "")
            if url:
                try:
                    from urllib.parse import urlparse

                    domain = urlparse(url).netloc
                    return f"WebFetch(domain:{domain})"
                except Exception:
                    pass
            return "WebFetch"

        elif tool_name == "WebSearch":
            return "WebSearch"

        elif tool_name.startswith("mcp__"):
            return tool_name

        return tool_name
    except Exception:
        return tool_name


def handle_pre_tool_use(input_data: dict) -> dict:
    """处理 PreToolUse 事件"""
    try:
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})
        tool_use_id = input_data.get("tool_use_id", "")

        debug_log(f"PreToolUse: {tool_name}")

        permission = format_permission_string(tool_name, tool_input)

        # 记录到临时文件
        pending_dir = Path("/tmp/permission-pending")
        pending_dir.mkdir(exist_ok=True)
        pending_file = pending_dir / f"{tool_use_id}.json"

        pending_data = {
            "tool_use_id": tool_use_id,
            "permission": permission,
            "timestamp": datetime.now().isoformat(),
            "tool_name": tool_name,
            "tool_input": tool_input,
            "cwd": input_data.get("cwd", ""),
            "hook_event_name": input_data.get("hook_event_name", ""),
        }
        pending_file.write_text(json.dumps(pending_data))

        debug_log(f"Written: {pending_file}")
    except Exception as e:
        debug_log(f"PreToolUse error: {e}")

    return {"decision": "allow"}


def handle_post_tool_use(input_data: dict) -> dict:
    """处理 PostToolUse 事件"""
    try:
        tool_use_id = input_data.get("tool_use_id", "")
        debug_log(f"PostToolUse: {tool_use_id}")

        pending_dir = Path("/tmp/permission-pending")
        pending_file = pending_dir / f"{tool_use_id}.json"

        if not pending_file.exists():
            # 清理旧文件
            for f in pending_dir.glob("*.json"):
                if time.time() - f.stat().st_mtime > 300:
                    f.unlink()
            return {}

        pending_data = json.loads(pending_file.read_text())
        permission = pending_data.get("permission", "")
        decision_context = {
            "tool_name": pending_data.get("tool_name", ""),
            "cwd": pending_data.get("cwd", ""),
            "hook_event_name": pending_data.get("hook_event_name", ""),
            "timestamp": pending_data.get("timestamp", ""),
        }

        # 记录权限决策
        if permission:
            try:
                memory = _personal_memory_via_assets(pending_data.get("cwd", ""))
                if memory:
                    memory.record_permission_decision(
                        permission=permission,
                        action="allow",
                        context=decision_context,
                    )
                    debug_log(f"Recorded: {permission}")
            except Exception as e:
                debug_log(f"Record error: {e}")

        pending_file.unlink(missing_ok=True)
    except Exception as e:
        debug_log(f"PostToolUse error: {e}")

    return {}


def _pattern_is_recent(pattern_obj) -> bool:
    """权限模式是否足够新鲜"""
    last_seen = getattr(pattern_obj, "last_seen", None)
    if not last_seen:
        return False
    return (datetime.now() - last_seen).days <= 30


def handle_permission_request(input_data: dict) -> dict:
    """处理 PermissionRequest 事件"""
    try:
        tool_name = input_data.get("tool_name", "")
        tool_input = input_data.get("tool_input", {})

        debug_log(f"PermissionRequest: {tool_name}")

        permission = format_permission_string(tool_name, tool_input)

        if _lazy_import():
            pattern_info = _extract_permission_pattern(permission)
            if pattern_info:
                pattern = pattern_info["pattern"]
                memory = _personal_memory_via_assets(input_data.get("cwd", ""))
                if not memory:
                    return {}
                patterns = memory.get_permission_patterns(min_count=2)

                for pp in patterns:
                    if pp.pattern == pattern and pp.count >= 3 and _pattern_is_recent(pp):
                        debug_log(f"Auto-approve: {pattern}")
                        return {
                            "hookSpecificOutput": {
                                "hookEventName": "PermissionRequest",
                                "decision": {"behavior": "allow"},
                            }
                        }
    except Exception as e:
        debug_log(f"PermissionRequest error: {e}")

    return {}


def handle_notification(input_data: dict) -> dict:
    """处理 Notification 事件"""
    debug_log(f"Notification: {input_data.get('notification_type', '')}")
    return {}


def main():
    """主函数"""
    _reset_durable_layer_cache()

    # 抑制 stderr（除非调试模式）
    if not os.environ.get("PERMISSION_HOOK_DEBUG"):
        _suppress_stderr()

    try:
        raw_input = sys.stdin.read()
        if not raw_input:
            sys.exit(0)

        try:
            input_data = json.loads(raw_input)
        except json.JSONDecodeError:
            sys.exit(0)

        if not isinstance(input_data, dict):
            sys.exit(0)

    except Exception:
        sys.exit(0)

    debug_log(f"Input: {json.dumps(input_data, ensure_ascii=False)[:200]}")

    event = get_hook_event(input_data)
    debug_log(f"Event: {event}")

    output = {}

    try:
        if event == "PreToolUse":
            output = handle_pre_tool_use(input_data)
        elif event == "PostToolUse":
            output = handle_post_tool_use(input_data)
        elif event == "PermissionRequest":
            output = handle_permission_request(input_data)
        elif event == "Notification":
            output = handle_notification(input_data)
    except Exception as e:
        debug_log(f"Handler error: {e}")

    if output:
        try:
            print(json.dumps(output))
        except Exception:
            pass

    sys.exit(0)


if __name__ == "__main__":
    main()
