"""
反馈收集器 - 打通 Claude Code 输出到记忆系统的闭环

核心功能：
1. 收集 Claude Code 执行结果（成功/失败）
2. 提取关键信息（错误模式、修复方案、代码风格）
3. 存入 personal_memory 供后续使用

集成点：
- PostToolUse Hook: 收集工具执行结果
- Session End: 汇总会话学习成果
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


class FeedbackType(Enum):
    """反馈类型"""
    SUCCESS = "success"           # 执行成功
    ERROR = "error"               # 执行失败
    PARTIAL = "partial"           # 部分成功
    LEARNING = "learning"         # 学习记录
    PREFERENCE = "preference"     # 用户偏好


@dataclass
class FeedbackItem:
    """反馈条目"""
    feedback_type: FeedbackType
    tool_name: str
    action: str                   # 具体操作
    result: str                   # 结果描述
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    patterns: List[str] = field(default_factory=list)  # 识别的模式
    learnings: List[str] = field(default_factory=list)  # 可学习的内容

    def to_dict(self) -> dict:
        return {
            "feedback_type": self.feedback_type.value,
            "tool_name": self.tool_name,
            "action": self.action,
            "result": self.result,
            "success": self.success,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "patterns": self.patterns,
            "learnings": self.learnings,
        }


class FeedbackCollector:
    """
    反馈收集器

    从 Claude Code 执行中提取学习内容，存入记忆系统。
    """

    def __init__(self, memory_path: Optional[Path] = None):
        """
        初始化反馈收集器

        Args:
            memory_path: 记忆存储路径
        """
        self.memory_path = memory_path or Path.home() / ".claude" / "memory"
        self.memory_path.mkdir(parents=True, exist_ok=True)

        # 会话内的反馈缓存
        self.session_feedback: List[FeedbackItem] = []

        # 错误模式识别规则
        self.error_patterns = {
            "syntax_error": r"SyntaxError|syntax error|unexpected token",
            "import_error": r"ImportError|ModuleNotFoundError|No module named",
            "type_error": r"TypeError|type error",
            "attribute_error": r"AttributeError|has no attribute",
            "key_error": r"KeyError|key not found",
            "value_error": r"ValueError|invalid value",
            "file_error": r"FileNotFoundError|No such file",
            "permission_error": r"PermissionError|Permission denied",
            "test_failure": r"FAILED|AssertionError|test failed",
            "lint_error": r"error:|warning:|E[0-9]{3}|W[0-9]{3}",
        }

        # 成功模式识别规则
        self.success_patterns = {
            "file_created": r"created|wrote|saved",
            "test_passed": r"PASSED|passed|✓",
            "lint_clean": r"no issues|clean|✓",
            "git_success": r"committed|pushed|merged",
        }

    def collect_tool_result(
        self,
        tool_name: str,
        tool_input: Dict[str, Any],
        tool_output: Any,
        success: bool,
    ) -> FeedbackItem:
        """
        收集工具执行结果

        Args:
            tool_name: 工具名称
            tool_input: 工具输入
            tool_output: 工具输出
            success: 是否成功

        Returns:
            反馈条目
        """
        # 确定反馈类型
        feedback_type = FeedbackType.SUCCESS if success else FeedbackType.ERROR

        # 提取操作描述
        action = self._extract_action(tool_name, tool_input)

        # 提取结果描述
        result = self._extract_result(tool_output)

        # 识别模式
        patterns = self._identify_patterns(tool_output, success)

        # 提取学习内容
        learnings = self._extract_learnings(
            tool_name, action, result, patterns, success
        )

        # 创建反馈条目
        feedback = FeedbackItem(
            feedback_type=feedback_type,
            tool_name=tool_name,
            action=action,
            result=result,
            success=success,
            context={
                "input_summary": self._summarize_input(tool_input),
                "output_summary": self._summarize_output(tool_output),
            },
            patterns=patterns,
            learnings=learnings,
        )

        # 缓存到会话
        self.session_feedback.append(feedback)

        # 持久化重要学习
        if learnings:
            self._persist_learning(feedback)

        return feedback

    def _extract_action(self, tool_name: str, tool_input: Dict) -> str:
        """提取操作描述"""
        if tool_name == "Bash":
            cmd = tool_input.get("command", "")
            # 提取主命令
            parts = cmd.split()
            if parts:
                return f"execute: {parts[0]}"
            return "execute command"

        elif tool_name == "Edit":
            file_path = tool_input.get("file_path", "")
            return f"edit: {Path(file_path).name}"

        elif tool_name == "Write":
            file_path = tool_input.get("file_path", "")
            return f"write: {Path(file_path).name}"

        elif tool_name == "Read":
            file_path = tool_input.get("file_path", "")
            return f"read: {Path(file_path).name}"

        return f"use {tool_name}"

    def _extract_result(self, tool_output: Any) -> str:
        """提取结果描述"""
        if isinstance(tool_output, dict):
            # 提取关键信息
            if "output" in tool_output:
                output = tool_output["output"]
                if isinstance(output, str):
                    # 取前200字符
                    return output[:200] + ("..." if len(output) > 200 else "")
            if "error" in tool_output:
                return f"Error: {tool_output['error'][:200]}"

        if isinstance(tool_output, str):
            return tool_output[:200] + ("..." if len(tool_output) > 200 else "")

        return str(tool_output)[:200]

    def _identify_patterns(self, output: Any, success: bool) -> List[str]:
        """识别输出中的模式"""
        patterns = []
        output_str = str(output) if output else ""

        if success:
            for pattern_name, regex in self.success_patterns.items():
                if re.search(regex, output_str, re.IGNORECASE):
                    patterns.append(f"success:{pattern_name}")
        else:
            for pattern_name, regex in self.error_patterns.items():
                if re.search(regex, output_str, re.IGNORECASE):
                    patterns.append(f"error:{pattern_name}")

        return patterns

    def _extract_learnings(
        self,
        tool_name: str,
        action: str,
        result: str,
        patterns: List[str],
        success: bool,
    ) -> List[str]:
        """提取可学习的内容"""
        learnings = []

        if not success:
            # 从失败中学习
            for pattern in patterns:
                if pattern.startswith("error:"):
                    error_type = pattern.split(":")[1]
                    learnings.append(f"avoid:{error_type}:{action}")

                    # 针对特定错误类型的建议
                    if error_type == "import_error":
                        learnings.append("check:dependencies:before_import")
                    elif error_type == "syntax_error":
                        learnings.append("validate:syntax:before_run")
                    elif error_type == "file_error":
                        learnings.append("check:file_exists:before_read")
                    elif error_type == "test_failure":
                        learnings.append("run:tests:after_changes")

        else:
            # 从成功中学习
            for pattern in patterns:
                if pattern.startswith("success:"):
                    success_type = pattern.split(":")[1]
                    learnings.append(f"success:{success_type}:{action}")

        return learnings

    def _summarize_input(self, tool_input: Dict) -> str:
        """总结输入"""
        # 只保留关键字段
        keys_to_keep = ["command", "file_path", "pattern", "url"]
        summary = {}
        for key in keys_to_keep:
            if key in tool_input:
                value = str(tool_input[key])
                summary[key] = value[:100] + ("..." if len(value) > 100 else "")
        return json.dumps(summary, ensure_ascii=False)

    def _summarize_output(self, tool_output: Any) -> str:
        """总结输出"""
        output_str = str(tool_output) if tool_output else ""
        return output_str[:500] + ("..." if len(output_str) > 500 else "")

    def _persist_learning(self, feedback: FeedbackItem):
        """持久化学习内容到 personal_memory"""
        learnings_file = self.memory_path / "learnings.json"

        # 加载现有学习
        learnings = []
        if learnings_file.exists():
            try:
                learnings = json.loads(learnings_file.read_text())
            except (json.JSONDecodeError, IOError):
                pass

        # 添加新学习
        for learning in feedback.learnings:
            learnings.append({
                "learning": learning,
                "source": feedback.tool_name,
                "action": feedback.action,
                "timestamp": feedback.timestamp.isoformat(),
                "context": feedback.context,
            })

        # 保存（保留最近1000条）
        learnings = learnings[-1000:]
        learnings_file.write_text(
            json.dumps(learnings, indent=2, ensure_ascii=False)
        )

        # 同时更新 personal_memory 的 error_fixes
        self._update_error_knowledge(feedback)

    def _update_error_knowledge(self, feedback: FeedbackItem):
        """更新错误知识库"""
        if feedback.success:
            return

        # 加载现有错误知识
        error_file = self.memory_path / "error_knowledge.json"
        error_knowledge = []
        if error_file.exists():
            try:
                error_knowledge = json.loads(error_file.read_text())
            except (json.JSONDecodeError, IOError):
                pass

        # 提取错误信息
        for pattern in feedback.patterns:
            if pattern.startswith("error:"):
                error_type = pattern.split(":")[1]
                error_knowledge.append({
                    "error_pattern": pattern,
                    "error_type": error_type,
                    "context": feedback.action,
                    "timestamp": feedback.timestamp.isoformat(),
                    "suggestion": self._generate_suggestion(error_type),
                })

        # 保存（保留最近500条）
        error_knowledge = error_knowledge[-500:]
        error_file.write_text(
            json.dumps(error_knowledge, indent=2, ensure_ascii=False)
        )

    def _generate_suggestion(self, error_type: str) -> str:
        """生成错误修复建议"""
        suggestions = {
            "syntax_error": "运行前检查语法，使用 linter",
            "import_error": "安装缺失依赖或检查导入路径",
            "type_error": "检查变量类型，添加类型检查",
            "attribute_error": "检查对象是否有该属性",
            "key_error": "检查字典键是否存在",
            "value_error": "验证输入值的合法性",
            "file_error": "检查文件路径是否正确",
            "permission_error": "检查文件权限",
            "test_failure": "检查测试断言和预期值",
            "lint_error": "修复 lint 错误",
        }
        return suggestions.get(error_type, "检查错误详情并修复")

    def get_session_summary(self) -> Dict[str, Any]:
        """
        获取会话总结

        Returns:
            会话统计和学习总结
        """
        total = len(self.session_feedback)
        successes = sum(1 for f in self.session_feedback if f.success)
        failures = total - successes

        # 统计模式
        pattern_counts: Dict[str, int] = {}
        for feedback in self.session_feedback:
            for pattern in feedback.patterns:
                pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1

        # 提取关键学习
        all_learnings = []
        for feedback in self.session_feedback:
            all_learnings.extend(feedback.learnings)

        return {
            "total_actions": total,
            "successes": successes,
            "failures": failures,
            "success_rate": successes / max(total, 1),
            "top_patterns": sorted(
                pattern_counts.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "key_learnings": list(set(all_learnings))[:20],
            "tools_used": list(set(f.tool_name for f in self.session_feedback)),
        }

    def save_session_report(self, path: Optional[Path] = None):
        """保存会话报告"""
        report_path = path or self.memory_path / "session_reports" / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        report_path.parent.mkdir(parents=True, exist_ok=True)

        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.get_session_summary(),
            "feedback_items": [f.to_dict() for f in self.session_feedback],
        }

        report_path.write_text(
            json.dumps(report, indent=2, ensure_ascii=False)
        )

        return report_path


def collect_from_hook(hook_input: dict, hook_output: dict) -> Optional[FeedbackItem]:
    """
    从 Hook 输入输出创建反馈

    Args:
        hook_input: Hook 输入数据
        hook_output: Hook 输出数据

    Returns:
        反馈条目或 None
    """
    collector = FeedbackCollector()

    tool_name = hook_input.get("tool_name", "")
    tool_input = hook_input.get("tool_input", {})
    success = hook_output.get("success", True)

    # 从 tool_result 或 tool_response 获取输出
    tool_output = hook_output.get("tool_result") or hook_output.get("tool_response") or {}

    return collector.collect_tool_result(
        tool_name=tool_name,
        tool_input=tool_input,
        tool_output=tool_output,
        success=success,
    )