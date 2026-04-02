"""
Claude Code 增强集成模块

整合:
- ContextManager: 智能上下文管理
- PersonalMemory: 个性化记忆
- ProjectKnowledgeLearner: 项目知识学习
- KnowledgeRetriever: 检索、排序和注入增强知识

提供统一的增强接口
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .context_manager import ContextManager
from .knowledge_retriever import KnowledgeRetriever
from .project_knowledge_learner import ProjectKnowledgeLearner
from ..memory.personal_memory import PersonalMemory, PreferenceCategory


@dataclass
class EnhancementConfig:
    """增强配置"""

    enable_context_manager: bool = True
    max_context_tokens: int = 1_000_000
    embedding_model: str = "all-MiniLM-L6-v2"
    enable_personal_memory: bool = True
    enable_project_learning: bool = True
    auto_learn_on_start: bool = True
    project_path: Optional[Path] = None


class ClaudeCodeEnhancer:
    """Claude Code 增强器"""

    def __init__(self, config: Optional[EnhancementConfig] = None):
        self.config = config or EnhancementConfig()
        self.project_path = self.config.project_path or Path.cwd()

        self.context_manager: Optional[ContextManager] = None
        self.personal_memory: Optional[PersonalMemory] = None
        self.project_learner: Optional[ProjectKnowledgeLearner] = None
        self.knowledge_retriever: Optional[KnowledgeRetriever] = None

        self._initialize()

    def _initialize(self):
        if self.config.enable_context_manager:
            self.context_manager = ContextManager(
                project_path=self.project_path,
                max_context_tokens=self.config.max_context_tokens,
                embedding_model=self.config.embedding_model,
            )

        if self.config.enable_personal_memory:
            self.personal_memory = PersonalMemory()
            self.knowledge_retriever = KnowledgeRetriever(self.personal_memory.memory_dir)
        else:
            self.knowledge_retriever = KnowledgeRetriever()

        if self.config.enable_project_learning:
            self.project_learner = ProjectKnowledgeLearner(self.project_path)
            if self.config.auto_learn_on_start:
                self.project_learner.learn()

    # ==================== 上下文管理 ====================

    def search_code(self, query: str, n_results: int = 10) -> list:
        if not self.context_manager:
            return []
        return self.context_manager.search(query, n_results)

    def get_context_for_query(self, query: str, max_tokens: int = 100_000) -> str:
        if not self.context_manager:
            return ""
        return self.context_manager.get_context_for_query(query, max_tokens)

    def add_conversation_turn(self, role: str, content: str):
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
    ):
        if not self.personal_memory:
            return

        try:
            cat = PreferenceCategory(category)
        except ValueError:
            cat = PreferenceCategory.WORKFLOW

        self.personal_memory.set_preference(cat, key, value, description)

    def recall_preference(self, category: str, key: str, default: Any = None) -> Any:
        if not self.personal_memory:
            return default

        try:
            cat = PreferenceCategory(category)
        except ValueError:
            return default

        return self.personal_memory.get_preference(cat, key, default)

    def record_command(self, command: str, success: bool = True):
        if self.personal_memory:
            self.personal_memory.record_command(command, success)

    def get_command_suggestions(self, prefix: str = "") -> List[str]:
        if not self.personal_memory:
            return []
        return self.personal_memory.get_command_suggestions(prefix)

    def find_error_fix(self, error_message: str) -> list:
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
        if self.personal_memory:
            self.personal_memory.record_error_fix(
                error_pattern,
                error_type,
                fix_description,
                fix_code,
            )

    # ==================== 项目知识 ====================

    def learn_project(self) -> dict:
        if not self.project_learner:
            return {}
        knowledge = self.project_learner.learn()
        return knowledge.to_dict()

    def get_project_conventions(self) -> list:
        if not self.project_learner:
            return []
        knowledge = self.project_learner.load_knowledge()
        if not knowledge:
            return []

        conventions = []
        if knowledge.naming:
            conventions.append({"category": "naming", **knowledge.naming.to_dict()})
        if knowledge.style:
            conventions.append({"category": "style", **knowledge.style.to_dict()})
        if knowledge.custom_rules:
            conventions.extend(
                {"category": "custom_rule", "rule": rule} for rule in knowledge.custom_rules
            )
        return conventions

    def get_project_patterns(self) -> list:
        if not self.project_learner:
            return []
        knowledge = self.project_learner.load_knowledge()
        if not knowledge:
            return []
        return knowledge.common_patterns

    def generate_claudemd(self) -> str:
        if not self.project_learner:
            return ""
        return self.project_learner.generate_style_guide()

    def render_architecture_diagram(self) -> str:
        return "\n".join(
            [
                "SessionStartHook / ContextQuery / ProjectKnowledgeHook / PermissionLearningHook",
                "        │",
                "        ▼",
                "ClaudeCodeEnhancer  (统一门面 / 编排入口)",
                "        │",
                "        ├── ContextManager",
                "        │     └── 代码索引、chunk 检索、查询上下文",
                "        │",
                "        ├── KnowledgeRetriever",
                "        │     └── 偏好 / 错误修复 / 项目知识 检索、排序、预算控制、trace",
                "        │",
                "        ├── PersonalMemory",
                "        │     └── preferences / commands / error_fixes / permissions",
                "        │",
                "        ├── ProjectKnowledgeLearner",
                "        │     └── 项目结构、命名、风格、依赖知识",
                "        │",
                "        └── EnhancementPipeline",
                "              └── 可选评估/闭环载体，承接 prepared context 和反馈",
            ]
        )

    # ==================== 统一接口 ====================

    def prepare_task_context(
        self,
        query: str,
        files: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
        max_items: int = 10,
        max_chars: int = 2400,
    ) -> dict:
        context_request = {
            "task": query,
            "query": query,
            "files": files or [],
            "errors": errors or [],
            "project_path": str(self.project_path),
        }

        code_context = ""
        if self.context_manager:
            code_context = self.get_context_for_query(query)

        injection = None
        if self.knowledge_retriever:
            injection = self.knowledge_retriever.generate_context_injection(
                context_request,
                max_items=max_items,
                max_chars=max_chars,
            )

        project_knowledge = None
        if self.project_learner:
            project_knowledge = self.project_learner.load_knowledge()
            if project_knowledge is None and self.config.auto_learn_on_start:
                project_knowledge = self.project_learner.learn()

        injectable_preferences = []
        ranked_error_fixes = []
        if self.personal_memory:
            injectable_preferences = [
                {
                    "category": pref.category.value,
                    "key": pref.key,
                    "value": pref.value,
                    "confidence": pref.confidence,
                    "description": pref.description,
                }
                for pref in self.personal_memory.get_injectable_preferences(limit=3)
            ]
            ranked_error_fixes = [
                {
                    "error_pattern": fix.error_pattern,
                    "error_type": fix.error_type,
                    "fix_description": fix.fix_description,
                    "success_rate": fix.success_rate,
                }
                for fix in self.personal_memory.get_ranked_error_fixes(query, limit=3)
            ]

        project_summary = None
        if project_knowledge:
            project_summary = {
                "project_name": project_knowledge.project_name,
                "structure": project_knowledge.structure.to_dict()
                if project_knowledge.structure
                else None,
                "naming": project_knowledge.naming.to_dict()
                if project_knowledge.naming
                else None,
                "style": project_knowledge.style.to_dict()
                if project_knowledge.style
                else None,
                "common_patterns": project_knowledge.common_patterns,
                "custom_rules": project_knowledge.custom_rules,
            }

        selected_items = []
        retrieval_trace = []
        knowledge_context = ""
        budget = {}
        if injection:
            selected_items = [
                {
                    "knowledge_type": item.knowledge_type,
                    "content": item.content,
                    "source": item.source,
                    "source_id": item.source_id,
                    "relevance": item.relevance,
                    "metadata": item.metadata,
                }
                for item in injection.selected_items
            ]
            retrieval_trace = [item.to_dict() for item in injection.trace]
            knowledge_context = injection.to_markdown()
            budget = injection.budget

        return {
            "query": query,
            "code_context": code_context,
            "knowledge_context": knowledge_context,
            "selected_items": selected_items,
            "retrieval_trace": retrieval_trace,
            "budget": budget,
            "user_preferences": injectable_preferences,
            "past_fixes": ranked_error_fixes,
            "project_conventions": self.get_project_conventions(),
            "project_patterns": self.get_project_patterns(),
            "project_knowledge": project_summary,
            "architecture_overview": self.render_architecture_diagram(),
            "injection_text": "\n\n".join(
                part for part in [knowledge_context, code_context] if part
            ),
        }

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
        if self.personal_memory and command:
            self.personal_memory.record_command(command, success, context=query)

        if self.personal_memory and error_message:
            self.personal_memory.record_error_fix(
                error_pattern=error_message,
                error_type="task_outcome",
                fix_description=query,
                fix_code="",
                success=success,
            )

        if self.personal_memory and retrieval_trace:
            for item in retrieval_trace:
                if not item.get("selected"):
                    continue
                key = f"{item.get('knowledge_type', 'unknown')}:{item.get('source_id', '')}"
                self.personal_memory.record_retrieval_feedback(
                    key,
                    success,
                    metadata={
                        "query": query,
                        "reason": item.get("reason", ""),
                        **(metadata or {}),
                    },
                )

    def learn_from_session(self, actions: List[dict], outcomes: dict):
        for action in actions:
            if action.get("type") == "command":
                self.record_command(action["command"], action.get("success", True))

            if action.get("type") == "fix":
                self.record_error_fix(
                    action.get("error_pattern", ""),
                    action.get("error_type", ""),
                    action.get("description", ""),
                    action.get("code", ""),
                )

        self.record_task_outcome(
            query=outcomes.get("query", "session"),
            success=outcomes.get("success", True),
            retrieval_trace=outcomes.get("retrieval_trace", []),
            command=outcomes.get("command", ""),
            error_message=outcomes.get("error_message", ""),
            metadata=outcomes,
        )

    def get_stats(self) -> dict:
        stats = {
            "context_manager": None,
            "personal_memory": None,
            "project_learner": None,
            "knowledge_retriever": None,
        }

        if self.context_manager:
            stats["context_manager"] = self.context_manager.get_stats()
        if self.personal_memory:
            stats["personal_memory"] = self.personal_memory.get_stats()
        if self.project_learner:
            knowledge = self.project_learner.load_knowledge()
            stats["project_learner"] = {
                "project_path": str(self.project_path),
                "knowledge_loaded": knowledge is not None,
                "project_name": knowledge.project_name if knowledge else None,
            }
        if self.knowledge_retriever:
            stats["knowledge_retriever"] = {
                "usage_stats": len(self.knowledge_retriever.usage_stats),
                "memory_path": str(self.knowledge_retriever.memory_path),
            }

        return stats

    def export_all(self, export_dir: Path):
        export_dir.mkdir(parents=True, exist_ok=True)

        if self.personal_memory:
            self.personal_memory.export_memory(export_dir / "memory_export.json")

        if self.context_manager:
            import shutil

            context_dir = export_dir / "context"
            context_dir.mkdir(exist_ok=True)
            src_dir = self.project_path / ".claude" / "context"
            if src_dir.exists():
                shutil.copytree(src_dir, context_dir, dirs_exist_ok=True)

    def clear_all(self):
        if self.context_manager:
            self.context_manager.clear_all()



def create_enhancer(project_path: Union[str, Path] = None, **kwargs) -> ClaudeCodeEnhancer:
    """创建增强器"""
    config = EnhancementConfig(
        project_path=Path(project_path) if project_path else Path.cwd(),
        **kwargs,
    )
    return ClaudeCodeEnhancer(config)
