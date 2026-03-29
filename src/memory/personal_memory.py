"""
个性化记忆系统 - 跨会话持久化用户偏好和知识

功能:
- 用户偏好存储
- 常用命令/项目记录
- 错误修复知识库
- 个人工作流学习
- 跨会话上下文恢复

存储位置:
~/.claude/memory/
├── preferences.json      # 用户偏好
├── commands.json         # 常用命令
├── projects.json         # 项目历史
├── error_knowledge.json  # 错误知识库
└── workflows.json        # 工作流模板
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class MemoryType(Enum):
    """记忆类型"""

    PREFERENCE = "preference"  # 用户偏好
    COMMAND = "command"  # 命令记录
    PROJECT = "project"  # 项目历史
    ERROR_FIX = "error_fix"  # 错误修复
    WORKFLOW = "workflow"  # 工作流模板
    CONTEXT = "context"  # 会话上下文


class PreferenceCategory(Enum):
    """偏好类别"""

    CODING_STYLE = "coding_style"  # 代码风格
    TOOLS = "tools"  # 工具偏好
    LANGUAGE = "language"  # 语言偏好
    WORKFLOW = "workflow"  # 工作流偏好
    OUTPUT = "output"  # 输出格式


@dataclass
class MemoryEntry:
    """记忆条目"""

    id: str
    type: MemoryType
    content: Any
    created_at: datetime
    updated_at: datetime
    access_count: int = 0
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "access_count": self.access_count,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEntry":
        return cls(
            id=data["id"],
            type=MemoryType(data["type"]),
            content=data["content"],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            access_count=data.get("access_count", 0),
            metadata=data.get("metadata", {}),
        )


@dataclass
class UserPreference:
    """用户偏好"""

    category: PreferenceCategory
    key: str
    value: Any
    description: str = ""
    confidence: float = 1.0  # 0-1, 表示偏好确定的程度

    def to_dict(self) -> dict:
        return {
            "category": self.category.value,
            "key": self.key,
            "value": self.value,
            "description": self.description,
            "confidence": self.confidence,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserPreference":
        return cls(
            category=PreferenceCategory(data["category"]),
            key=data["key"],
            value=data["value"],
            description=data.get("description", ""),
            confidence=data.get("confidence", 1.0),
        )


@dataclass
class CommandRecord:
    """命令记录"""

    command: str
    frequency: int = 1
    last_used: datetime = field(default_factory=datetime.now)
    success_rate: float = 1.0
    contexts: list[str] = field(default_factory=list)  # 使用场景

    def to_dict(self) -> dict:
        return {
            "command": self.command,
            "frequency": self.frequency,
            "last_used": self.last_used.isoformat(),
            "success_rate": self.success_rate,
            "contexts": self.contexts,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CommandRecord":
        return cls(
            command=data["command"],
            frequency=data.get("frequency", 1),
            last_used=datetime.fromisoformat(data["last_used"]),
            success_rate=data.get("success_rate", 1.0),
            contexts=data.get("contexts", []),
        )


@dataclass
class ErrorFix:
    """错误修复记录"""

    error_pattern: str  # 错误模式 (正则或关键词)
    error_type: str  # 错误类型
    fix_description: str  # 修复描述
    fix_code: str  # 修复代码
    success_count: int = 1
    fail_count: int = 0
    languages: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "error_pattern": self.error_pattern,
            "error_type": self.error_type,
            "fix_description": self.fix_description,
            "fix_code": self.fix_code,
            "success_count": self.success_count,
            "fail_count": self.fail_count,
            "languages": self.languages,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ErrorFix":
        return cls(
            error_pattern=data["error_pattern"],
            error_type=data["error_type"],
            fix_description=data["fix_description"],
            fix_code=data["fix_code"],
            success_count=data.get("success_count", 1),
            fail_count=data.get("fail_count", 0),
            languages=data.get("languages", []),
            created_at=datetime.fromisoformat(data["created_at"]),
        )

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.fail_count
        return self.success_count / total if total > 0 else 0


@dataclass
class WorkflowTemplate:
    """工作流模板"""

    name: str
    description: str
    steps: list[dict]  # [{action, params, condition}]
    triggers: list[str]  # 触发条件
    use_count: int = 0
    last_used: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "triggers": self.triggers,
            "use_count": self.use_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorkflowTemplate":
        return cls(
            name=data["name"],
            description=data["description"],
            steps=data["steps"],
            triggers=data.get("triggers", []),
            use_count=data.get("use_count", 0),
            last_used=datetime.fromisoformat(data["last_used"])
            if data.get("last_used")
            else None,
            created_at=datetime.fromisoformat(data["created_at"]),
        )


class PersonalMemory:
    """
    个性化记忆系统

    功能:
    - 存储用户偏好 (自动学习)
    - 记录常用命令
    - 保存项目历史
    - 错误修复知识库
    - 工作流模板
    """

    def __init__(self, memory_dir: Optional[Path] = None):
        """
        初始化个性化记忆

        Args:
            memory_dir: 记忆存储目录 (默认 ~/.claude/memory/)
        """
        self.memory_dir = memory_dir or Path.home() / ".claude" / "memory"
        self.memory_dir.mkdir(parents=True, exist_ok=True)

        # 存储结构
        self.preferences: dict[str, UserPreference] = {}
        self.commands: dict[str, CommandRecord] = {}
        self.projects: dict[str, dict] = {}
        self.error_fixes: list[ErrorFix] = []
        self.workflows: dict[str, WorkflowTemplate] = {}

        # 加载已有记忆
        self._load_all()

    def _load_all(self):
        """加载所有记忆"""
        self._load_preferences()
        self._load_commands()
        self._load_projects()
        self._load_error_fixes()
        self._load_workflows()

    # ==================== 用户偏好 ====================

    def _load_preferences(self):
        """加载用户偏好"""
        prefs_file = self.memory_dir / "preferences.json"
        if not prefs_file.exists():
            return

        try:
            data = json.loads(prefs_file.read_text())
            for key, pref_data in data.items():
                self.preferences[key] = UserPreference.from_dict(pref_data)
        except Exception as e:
            print(f"Warning: Failed to load preferences: {e}")

    def _save_preferences(self):
        """保存用户偏好"""
        prefs_file = self.memory_dir / "preferences.json"
        data = {key: pref.to_dict() for key, pref in self.preferences.items()}
        prefs_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def set_preference(
        self,
        category: PreferenceCategory,
        key: str,
        value: Any,
        description: str = "",
        confidence: float = 1.0,
    ):
        """
        设置用户偏好

        Args:
            category: 偏好类别
            key: 偏好键
            value: 偏好值
            description: 描述
            confidence: 置信度
        """
        pref_key = f"{category.value}:{key}"
        self.preferences[pref_key] = UserPreference(
            category=category,
            key=key,
            value=value,
            description=description,
            confidence=confidence,
        )
        self._save_preferences()

    def get_preference(
        self,
        category: PreferenceCategory,
        key: str,
        default: Any = None,
    ) -> Any:
        """获取用户偏好"""
        pref_key = f"{category.value}:{key}"
        pref = self.preferences.get(pref_key)
        return pref.value if pref else default

    def learn_preference(self, action: str, context: dict):
        """
        从用户行为学习偏好

        Args:
            action: 用户行为
            context: 上下文
        """
        # 示例：用户选择 prettier 而不是 eslint
        if action == "choose_formatter":
            formatter = context.get("choice")
            current = self.get_preference(
                PreferenceCategory.TOOLS, "formatter", "none"
            )
            if current == formatter:
                # 增强偏好
                self.set_preference(
                    PreferenceCategory.TOOLS,
                    "formatter",
                    formatter,
                    confidence=min(1.0, self.preferences.get(
                        f"tools:formatter"
                    ).confidence + 0.1 if f"tools:formatter" in self.preferences else 0.6),
                )
            else:
                # 设置新偏好
                self.set_preference(
                    PreferenceCategory.TOOLS,
                    "formatter",
                    formatter,
                    confidence=0.6,
                )

    def get_all_preferences(self) -> dict[str, UserPreference]:
        """获取所有偏好"""
        return self.preferences.copy()

    # ==================== 命令记录 ====================

    def _load_commands(self):
        """加载命令记录"""
        cmds_file = self.memory_dir / "commands.json"
        if not cmds_file.exists():
            return

        try:
            data = json.loads(cmds_file.read_text())
            for cmd, record in data.items():
                self.commands[cmd] = CommandRecord.from_dict(record)
        except Exception as e:
            print(f"Warning: Failed to load commands: {e}")

    def _save_commands(self):
        """保存命令记录"""
        cmds_file = self.memory_dir / "commands.json"
        data = {cmd: record.to_dict() for cmd, record in self.commands.items()}
        cmds_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def record_command(self, command: str, success: bool = True, context: str = ""):
        """
        记录命令使用

        Args:
            command: 命令
            success: 是否成功
            context: 使用场景
        """
        if command in self.commands:
            record = self.commands[command]
            record.frequency += 1
            record.last_used = datetime.now()
            if success:
                record.success_rate = (
                    record.success_rate * (record.frequency - 1) + 1
                ) / record.frequency
            else:
                record.success_rate = (
                    record.success_rate * (record.frequency - 1)
                ) / record.frequency
            if context and context not in record.contexts:
                record.contexts.append(context)
        else:
            self.commands[command] = CommandRecord(
                command=command,
                frequency=1,
                success_rate=1.0 if success else 0.0,
                contexts=[context] if context else [],
            )

        self._save_commands()

    def get_frequent_commands(self, limit: int = 10) -> list[tuple[str, int]]:
        """
        获取常用命令

        Args:
            limit: 返回数量

        Returns:
            (命令, 频率) 列表
        """
        sorted_cmds = sorted(
            self.commands.items(),
            key=lambda x: x[1].frequency,
            reverse=True,
        )
        return [(cmd, record.frequency) for cmd, record in sorted_cmds[:limit]]

    def get_command_suggestions(self, prefix: str = "") -> list[str]:
        """
        获取命令建议

        Args:
            prefix: 命令前缀

        Returns:
            建议命令列表
        """
        suggestions = []
        for cmd, record in self.commands.items():
            if cmd.startswith(prefix) and record.success_rate > 0.5:
                suggestions.append(cmd)
        suggestions.sort(key=lambda c: self.commands[c].frequency, reverse=True)
        return suggestions[:5]

    # ==================== 项目历史 ====================

    def _load_projects(self):
        """加载项目历史"""
        projects_file = self.memory_dir / "projects.json"
        if not projects_file.exists():
            return

        try:
            self.projects = json.loads(projects_file.read_text())
        except Exception as e:
            print(f"Warning: Failed to load projects: {e}")

    def _save_projects(self):
        """保存项目历史"""
        projects_file = self.memory_dir / "projects.json"
        projects_file.write_text(
            json.dumps(self.projects, indent=2, ensure_ascii=False)
        )

    def record_project(
        self,
        project_path: str,
        project_type: str = "",
        tech_stack: list[str] = None,
    ):
        """
        记录项目

        Args:
            project_path: 项目路径
            project_type: 项目类型
            tech_stack: 技术栈
        """
        if project_path not in self.projects:
            self.projects[project_path] = {
                "path": project_path,
                "type": project_type,
                "tech_stack": tech_stack or [],
                "first_visit": datetime.now().isoformat(),
                "visit_count": 0,
            }

        self.projects[project_path]["last_visit"] = datetime.now().isoformat()
        self.projects[project_path]["visit_count"] += 1

        if tech_stack:
            existing = set(self.projects[project_path].get("tech_stack", []))
            self.projects[project_path]["tech_stack"] = list(
                existing | set(tech_stack)
            )

        self._save_projects()

    def get_recent_projects(self, limit: int = 10) -> list[dict]:
        """获取最近项目"""
        sorted_projects = sorted(
            self.projects.items(),
            key=lambda x: x[1].get("last_visit", ""),
            reverse=True,
        )
        return [p[1] for p in sorted_projects[:limit]]

    # ==================== 错误修复知识库 ====================

    def _load_error_fixes(self):
        """加载错误修复知识库"""
        errors_file = self.memory_dir / "error_knowledge.json"
        if not errors_file.exists():
            return

        try:
            data = json.loads(errors_file.read_text())
            self.error_fixes = [ErrorFix.from_dict(e) for e in data]
        except Exception as e:
            print(f"Warning: Failed to load error fixes: {e}")

    def _save_error_fixes(self):
        """保存错误修复知识库"""
        errors_file = self.memory_dir / "error_knowledge.json"
        data = [e.to_dict() for e in self.error_fixes]
        errors_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def record_error_fix(
        self,
        error_pattern: str,
        error_type: str,
        fix_description: str,
        fix_code: str,
        languages: list[str] = None,
        success: bool = True,
    ):
        """
        记录错误修复

        Args:
            error_pattern: 错误模式
            error_type: 错误类型
            fix_description: 修复描述
            fix_code: 修复代码
            languages: 相关语言
            success: 是否成功
        """
        # 查找是否已有相同模式的修复
        for fix in self.error_fixes:
            if fix.error_pattern == error_pattern:
                if success:
                    fix.success_count += 1
                else:
                    fix.fail_count += 1
                self._save_error_fixes()
                return

        # 新增修复记录
        self.error_fixes.append(
            ErrorFix(
                error_pattern=error_pattern,
                error_type=error_type,
                fix_description=fix_description,
                fix_code=fix_code,
                languages=languages or [],
            )
        )
        self._save_error_fixes()

    def find_fix_for_error(self, error_message: str) -> list[ErrorFix]:
        """
        查找错误修复

        Args:
            error_message: 错误信息

        Returns:
            匹配的修复列表 (按成功率排序)
        """
        matches = []
        for fix in self.error_fixes:
            if fix.error_pattern.lower() in error_message.lower():
                matches.append(fix)

        matches.sort(key=lambda f: f.success_rate, reverse=True)
        return matches[:5]

    # ==================== 工作流模板 ====================

    def _load_workflows(self):
        """加载工作流模板"""
        workflows_file = self.memory_dir / "workflows.json"
        if not workflows_file.exists():
            return

        try:
            data = json.loads(workflows_file.read_text())
            for name, wf_data in data.items():
                self.workflows[name] = WorkflowTemplate.from_dict(wf_data)
        except Exception as e:
            print(f"Warning: Failed to load workflows: {e}")

    def _save_workflows(self):
        """保存工作流模板"""
        workflows_file = self.memory_dir / "workflows.json"
        data = {name: wf.to_dict() for name, wf in self.workflows.items()}
        workflows_file.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def save_workflow(self, workflow: WorkflowTemplate):
        """保存工作流模板"""
        self.workflows[workflow.name] = workflow
        self._save_workflows()

    def get_workflow(self, name: str) -> Optional[WorkflowTemplate]:
        """获取工作流模板"""
        return self.workflows.get(name)

    def find_matching_workflows(self, context: str) -> list[WorkflowTemplate]:
        """
        查找匹配的工作流

        Args:
            context: 当前上下文

        Returns:
            匹配的工作流列表
        """
        matches = []
        for wf in self.workflows.values():
            for trigger in wf.triggers:
                if trigger.lower() in context.lower():
                    matches.append(wf)
                    break
        return sorted(matches, key=lambda w: w.use_count, reverse=True)

    def record_workflow_usage(self, name: str):
        """记录工作流使用"""
        if name in self.workflows:
            wf = self.workflows[name]
            wf.use_count += 1
            wf.last_used = datetime.now()
            self._save_workflows()

    # ==================== 导出/导入 ====================

    def export_memory(self, export_path: Path):
        """
        导出记忆到文件

        Args:
            export_path: 导出路径
        """
        export_data = {
            "preferences": {k: v.to_dict() for k, v in self.preferences.items()},
            "commands": {k: v.to_dict() for k, v in self.commands.items()},
            "projects": self.projects,
            "error_fixes": [e.to_dict() for e in self.error_fixes],
            "workflows": {k: v.to_dict() for k, v in self.workflows.items()},
            "exported_at": datetime.now().isoformat(),
        }

        export_path.write_text(json.dumps(export_data, indent=2, ensure_ascii=False))

    def import_memory(self, import_path: Path, merge: bool = True):
        """
        从文件导入记忆

        Args:
            import_path: 导入路径
            merge: 是否合并 (True) 或覆盖 (False)
        """
        data = json.loads(import_path.read_text())

        if not merge:
            self.preferences.clear()
            self.commands.clear()
            self.projects.clear()
            self.error_fixes.clear()
            self.workflows.clear()

        for key, pref_data in data.get("preferences", {}).items():
            self.preferences[key] = UserPreference.from_dict(pref_data)

        for cmd, record_data in data.get("commands", {}).items():
            self.commands[cmd] = CommandRecord.from_dict(record_data)

        self.projects.update(data.get("projects", {}))

        for fix_data in data.get("error_fixes", []):
            self.error_fixes.append(ErrorFix.from_dict(fix_data))

        for name, wf_data in data.get("workflows", {}).items():
            self.workflows[name] = WorkflowTemplate.from_dict(wf_data)

        self._save_preferences()
        self._save_commands()
        self._save_projects()
        self._save_error_fixes()
        self._save_workflows()

    # ==================== 统计 ====================

    def get_stats(self) -> dict:
        """获取记忆统计"""
        return {
            "preferences": len(self.preferences),
            "commands": len(self.commands),
            "projects": len(self.projects),
            "error_fixes": len(self.error_fixes),
            "workflows": len(self.workflows),
            "most_used_commands": self.get_frequent_commands(5),
            "recent_projects": len(self.get_recent_projects(5)),
        }


# 便捷函数
def get_memory() -> PersonalMemory:
    """获取全局记忆实例"""
    return PersonalMemory()
