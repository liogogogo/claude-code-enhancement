"""
Claude Code 增强集成模块

整合:
- ContextManager: 智能上下文管理
- PersonalMemory: 个性化记忆
- ProjectKnowledgeLearner: 项目知识学习

提供统一的增强接口
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .context_manager import ContextManager, ContextLevel
from .project_knowledge import ProjectKnowledgeLearner
from ..memory.personal_memory import PersonalMemory, PreferenceCategory


@dataclass
class EnhancementConfig:
    """增强配置"""

    # 上下文管理
    enable_context_manager: bool = True
    max_context_tokens: int = 1_000_000
    embedding_model: str = "all-MiniLM-L6-v2"

    # 个性化记忆
    enable_personal_memory: bool = True

    # 项目知识
    enable_project_learning: bool = True
    auto_learn_on_start: bool = True

    # 项目路径
    project_path: Optional[Path] = None


class ClaudeCodeEnhancer:
    """
    Claude Code 增强器

    整合所有增强功能，提供统一接口
    """

    def __init__(self, config: Optional[EnhancementConfig] = None):
        """
        初始化增强器

        Args:
            config: 增强配置
        """
        self.config = config or EnhancementConfig()
        self.project_path = self.config.project_path or Path.cwd()

        # 初始化组件
        self.context_manager: Optional[ContextManager] = None
        self.personal_memory: Optional[PersonalMemory] = None
        self.project_learner: Optional[ProjectKnowledgeLearner] = None

        self._initialize()

    def _initialize(self):
        """初始化组件"""
        if self.config.enable_context_manager:
            self.context_manager = ContextManager(
                project_path=self.project_path,
                max_context_tokens=self.config.max_context_tokens,
                embedding_model=self.config.embedding_model,
            )

        if self.config.enable_personal_memory:
            self.personal_memory = PersonalMemory()

        if self.config.enable_project_learning:
            self.project_learner = ProjectKnowledgeLearner(self.project_path)
            if self.config.auto_learn_on_start:
                self.project_learner.analyze_project()

    # ==================== 上下文管理 ====================

    def search_code(self, query: str, n_results: int = 10) -> list:
        """
        搜索代码

        Args:
            query: 查询
            n_results: 结果数量

        Returns:
            搜索结果
        """
        if not self.context_manager:
            return []
        return self.context_manager.search(query, n_results)

    def get_context_for_query(self, query: str, max_tokens: int = 100_000) -> str:
        """
        获取查询上下文

        Args:
            query: 查询
            max_tokens: 最大 token

        Returns:
            上下文字符串
        """
        if not self.context_manager:
            return ""
        return self.context_manager.get_context_for_query(query, max_tokens)

    def add_conversation_turn(self, role: str, content: str):
        """添加对话轮次"""
        if self.context_manager:
            self.context_manager.add_conversation_turn(role, content)

    def compact_conversation(self) -> str:
        """压缩对话"""
        if not self.context_manager:
            return ""
        return self.context_manager.compact_conversation()

    # ==================== 个性化记忆 ====================

    def remember_preference(
        self,
        category: str,
        key: str,
        value: Any,
        description: str = "",
    ):
        """
        记住偏好

        Args:
            category: 类别
            key: 键
            value: 值
            description: 描述
        """
        if not self.personal_memory:
            return

        try:
            cat = PreferenceCategory(category)
        except ValueError:
            cat = PreferenceCategory.WORKFLOW

        self.personal_memory.set_preference(cat, key, value, description)

    def recall_preference(self, category: str, key: str, default: Any = None) -> Any:
        """
        回忆偏好

        Args:
            category: 类别
            key: 键
            default: 默认值

        Returns:
            偏好值
        """
        if not self.personal_memory:
            return default

        try:
            cat = PreferenceCategory(category)
        except ValueError:
            return default

        return self.personal_memory.get_preference(cat, key, default)

    def record_command(self, command: str, success: bool = True):
        """记录命令使用"""
        if self.personal_memory:
            self.personal_memory.record_command(command, success)

    def get_command_suggestions(self, prefix: str = "") -> list[str]:
        """获取命令建议"""
        if not self.personal_memory:
            return []
        return self.personal_memory.get_command_suggestions(prefix)

    def find_error_fix(self, error_message: str) -> list:
        """
        查找错误修复

        Args:
            error_message: 错误信息

        Returns:
            修复建议列表
        """
        if not self.personal_memory:
            return []
        return self.personal_memory.find_fix_for_error(error_message)

    def record_error_fix(
        self,
        error_pattern: str,
        error_type: str,
        fix_description: str,
        fix_code: str,
    ):
        """记录错误修复"""
        if self.personal_memory:
            self.personal_memory.record_error_fix(
                error_pattern,
                error_type,
                fix_description,
                fix_code,
            )

    # ==================== 项目知识 ====================

    def learn_project(self) -> dict:
        """
        学习项目

        Returns:
            学习统计
        """
        if not self.project_learner:
            return {}
        return self.project_learner.analyze_project()

    def get_project_conventions(self) -> list:
        """获取项目约定"""
        if not self.project_learner:
            return []
        return self.project_learner.conventions

    def get_project_patterns(self) -> list:
        """获取项目模式"""
        if not self.project_learner:
            return []
        return self.project_learner.patterns

    def generate_claudemd(self) -> str:
        """生成 CLAUDE.md 内容"""
        if not self.project_learner:
            return ""
        return self.project_learner.generate_claudemd()

    # ==================== 统一接口 ====================

    def prepare_context(self, query: str) -> dict:
        """
        准备完整的上下文

        Args:
            query: 查询

        Returns:
            上下文数据
        """
        context = {
            "query": query,
            "code_context": "",
            "user_preferences": {},
            "project_conventions": [],
            "past_fixes": [],
        }

        # 代码上下文
        if self.context_manager:
            context["code_context"] = self.get_context_for_query(query)

        # 用户偏好
        if self.personal_memory:
            prefs = self.personal_memory.get_all_preferences()
            context["user_preferences"] = {
                k: v.value for k, v in prefs.items()
            }

        # 项目约定
        if self.project_learner:
            context["project_conventions"] = [
                c.to_dict() for c in self.project_learner.conventions
            ]

        # 历史修复
        if self.personal_memory:
            context["past_fixes"] = self.personal_memory.find_fix_for_error(query)

        return context

    def learn_from_session(
        self,
        actions: list[dict],
        outcomes: dict,
    ):
        """
        从会话中学习

        Args:
            actions: 执行的动作列表
            outcomes: 结果统计
        """
        for action in actions:
            # 记录命令
            if action.get("type") == "command":
                self.record_command(
                    action["command"],
                    action.get("success", True),
                )

            # 记录错误修复
            if action.get("type") == "fix":
                self.record_error_fix(
                    action.get("error_pattern", ""),
                    action.get("error_type", ""),
                    action.get("description", ""),
                    action.get("code", ""),
                )

            # 项目学习
            if self.project_learner:
                self.project_learner.learn_from_interaction(
                    action.get("type", ""),
                    action.get("context", {}),
                    "success" if action.get("success") else "failure",
                )

    def get_stats(self) -> dict:
        """获取统计信息"""
        stats = {
            "context_manager": None,
            "personal_memory": None,
            "project_learner": None,
        }

        if self.context_manager:
            stats["context_manager"] = self.context_manager.get_stats()

        if self.personal_memory:
            stats["personal_memory"] = self.personal_memory.get_stats()

        if self.project_learner:
            stats["project_learner"] = self.project_learner.get_stats()

        return stats

    def export_all(self, export_dir: Path):
        """导出所有数据"""
        export_dir.mkdir(parents=True, exist_ok=True)

        if self.personal_memory:
            self.personal_memory.export_memory(export_dir / "memory_export.json")

        if self.context_manager:
            # 上下文管理器已有持久化，复制即可
            import shutil

            context_dir = export_dir / "context"
            context_dir.mkdir(exist_ok=True)
            src_dir = self.project_path / ".claude" / "context"
            if src_dir.exists():
                shutil.copytree(src_dir, context_dir, dirs_exist_ok=True)

    def clear_all(self):
        """清空所有数据"""
        if self.context_manager:
            self.context_manager.clear_all()

        # 个人记忆不清空，保留用户偏好


# 便捷函数
def create_enhancer(
    project_path: str | Path = None,
    **kwargs,
) -> ClaudeCodeEnhancer:
    """创建增强器"""
    config = EnhancementConfig(
        project_path=Path(project_path) if project_path else Path.cwd(),
        **kwargs,
    )
    return ClaudeCodeEnhancer(config)
