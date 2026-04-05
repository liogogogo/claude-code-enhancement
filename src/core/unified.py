"""
Claude Code 增强集成模块

架构：
- DurableKnowledgeLayer：持久资产（~/.claude/memory、.claude/knowledge、检索注入）
- ContextManager：可选的商品化能力（代码索引 / 会话摘要等），按需叠加
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .context_manager import ContextManager
from .durable_knowledge import DurableKnowledgeLayer, DurableKnowledgeSettings


@dataclass
class EnhancementConfig:
    """增强配置。"""

    # 代码库向量检索与会话压缩（易被上游替代；可按需关闭）
    enable_context_manager: bool = True
    max_context_tokens: int = 1_000_000
    embedding_model: str = "all-MiniLM-L6-v2"

    # 持久资产（本地/仓库落盘，长期优先维护）
    enable_personal_memory: bool = True
    enable_project_learning: bool = True
    auto_learn_on_start: bool = True

    project_path: Optional[Path] = None


class ClaudeCodeEnhancer:
    """Claude Code 增强器：资产层为核心，代码 RAG 为可选外层。"""

    def __init__(self, config: Optional[EnhancementConfig] = None):
        self.config = config or EnhancementConfig()
        self.project_path = self.config.project_path or Path.cwd()

        self.context_manager: Optional[ContextManager] = None
        self.assets = DurableKnowledgeLayer(
            self.project_path,
            DurableKnowledgeSettings(
                enable_personal_memory=self.config.enable_personal_memory,
                enable_project_learning=self.config.enable_project_learning,
                auto_learn_on_start=self.config.auto_learn_on_start,
            ),
        )

        self._initialize()

    def _initialize(self) -> None:
        if self.config.enable_context_manager:
            self.context_manager = ContextManager(
                project_path=self.project_path,
                max_context_tokens=self.config.max_context_tokens,
                embedding_model=self.config.embedding_model,
            )

    # --- 与子组件对齐的只读属性（兼容旧代码） ---

    @property
    def personal_memory(self):
        return self.assets.personal_memory

    @property
    def project_learner(self):
        return self.assets.project_learner

    @property
    def knowledge_retriever(self):
        return self.assets.knowledge_retriever

    # ==================== 上下文管理（可选） ====================

    def search_code(self, query: str, n_results: int = 10) -> list:
        if not self.context_manager:
            return []
        return self.context_manager.search(query, n_results)

    def get_context_for_query(self, query: str, max_tokens: int = 100_000) -> str:
        if not self.context_manager:
            return ""
        return self.context_manager.get_context_for_query(query, max_tokens)

    def add_conversation_turn(self, role: str, content: str) -> None:
        if self.context_manager:
            self.context_manager.add_conversation_turn(role, content)

    def compact_conversation(self) -> str:
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
    ) -> None:
        self.assets.remember_preference(category, key, value, description)

    def recall_preference(self, category: str, key: str, default: Any = None) -> Any:
        return self.assets.recall_preference(category, key, default)

    def record_command(self, command: str, success: bool = True) -> None:
        self.assets.record_command(command, success)

    def get_command_suggestions(self, prefix: str = "") -> List[str]:
        return self.assets.get_command_suggestions(prefix)

    def find_error_fix(self, error_message: str) -> list:
        return self.assets.find_error_fix(error_message)

    def record_error_fix(
        self,
        error_pattern: str,
        error_type: str,
        fix_description: str,
        fix_code: str,
    ) -> None:
        self.assets.record_error_fix(
            error_pattern,
            error_type,
            fix_description,
            fix_code,
        )

    # ==================== 项目知识 ====================

    def learn_project(self) -> dict:
        return self.assets.learn_project()

    def get_project_conventions(self) -> list:
        return self.assets.get_project_conventions()

    def get_project_patterns(self) -> list:
        return self.assets.get_project_patterns()

    def generate_claudemd(self) -> str:
        return self.assets.generate_claudemd()

    def render_architecture_diagram(self) -> str:
        lines = [
            DurableKnowledgeLayer.architecture_diagram(),
        ]
        if self.context_manager:
            lines.append(
                "(ContextManager: optional — codebase index / conversation compaction)"
            )
        return "\n".join(lines)

    # ==================== 统一接口 ====================

    def prepare_task_context(
        self,
        query: str,
        files: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
        max_items: int = 10,
        max_chars: int = 2400,
    ) -> dict:
        bundle = self.assets.build_asset_bundle(
            query,
            files=files,
            errors=errors,
            max_items=max_items,
            max_chars=max_chars,
        )

        code_context = ""
        if self.context_manager:
            code_context = self.get_context_for_query(query)

        return DurableKnowledgeLayer.merge_code_context(bundle, code_context)

    def prepare_context(self, query: str) -> dict:
        prepared = self.prepare_task_context(query)
        return {
            "query": prepared["query"],
            "code_context": prepared["code_context"],
            "user_preferences": {
                item["key"]: item["value"] for item in prepared["user_preferences"]
            },
            "project_conventions": prepared["project_conventions"],
            "past_fixes": prepared["past_fixes"],
            "knowledge_context": prepared["knowledge_context"],
            "retrieval_trace": prepared["retrieval_trace"],
        }

    def record_task_outcome(
        self,
        query: str,
        success: bool,
        retrieval_trace: Optional[List[Dict[str, Any]]] = None,
        command: str = "",
        error_message: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.assets.record_task_outcome(
            query,
            success,
            retrieval_trace=retrieval_trace,
            command=command,
            error_message=error_message,
            metadata=metadata,
        )

    def learn_from_session(self, actions: List[dict], outcomes: dict) -> None:
        self.assets.learn_from_session(actions, outcomes)

    def get_stats(self) -> dict:
        self.assets.warm_knowledge_retriever()
        stats: Dict[str, Any] = {
            "context_manager": None,
            **self.assets.stats_dict(),
        }
        if self.context_manager:
            stats["context_manager"] = self.context_manager.get_stats()
        return stats

    def export_all(self, export_dir: Path) -> None:
        export_dir.mkdir(parents=True, exist_ok=True)
        self.assets.export_memory(export_dir / "memory_export.json")

        if self.context_manager:
            import shutil

            context_dir = export_dir / "context"
            context_dir.mkdir(exist_ok=True)
            src_dir = self.project_path / ".claude" / "context"
            if src_dir.exists():
                shutil.copytree(src_dir, context_dir, dirs_exist_ok=True)

    def clear_all(self) -> None:
        if self.context_manager:
            self.context_manager.clear_all()


def create_enhancer(project_path: Union[str, Path] = None, **kwargs) -> ClaudeCodeEnhancer:
    """创建增强器"""
    config = EnhancementConfig(
        project_path=Path(project_path) if project_path else Path.cwd(),
        **kwargs,
    )
    return ClaudeCodeEnhancer(config)
