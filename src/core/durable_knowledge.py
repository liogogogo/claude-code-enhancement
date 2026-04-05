"""
持久知识层（核心资产面）

把「最不可替代」的部分收敛到这里：本地个人记忆、项目内知识库、
基于磁盘的检索与注入。代码库向量索引 / 通用 RAG 不放在本层，
由 ClaudeCodeEnhancer 按需叠加，避免与商品化能力强耦合。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from .knowledge_retriever import KnowledgeRetriever
from .project_knowledge_learner import ProjectKnowledgeLearner
from ..memory.personal_memory import PersonalMemory, PreferenceCategory


@dataclass
class DurableKnowledgeSettings:
    """持久资产层开关（与 EnhancementConfig 对齐的子集，避免循环依赖）"""

    enable_personal_memory: bool = True
    enable_project_learning: bool = True
    auto_learn_on_start: bool = True


class DurableKnowledgeLayer:
    """
    个人记忆 + 项目知识 + 检索注入的统一载体。

    设计意图：产品形态可变，但 ~/.claude/memory 与 .claude/knowledge 下的
    结构化资产应长期稳定、可迁移、可归因。

    KnowledgeRetriever 惰性构造：仅在 ``build_asset_bundle`` 或读取
    ``knowledge_retriever`` / 调用 ``warm_knowledge_retriever`` 时创建；
    否则 ``stats_dict`` 中 ``knowledge_retriever`` 为 ``None``。
    """

    @classmethod
    def for_hook_personal_memory(cls, project_path: Path) -> DurableKnowledgeLayer:
        """权限 / 报告 / 管道：个人记忆 + 检索；不跑项目学习（避免扫描仓库）。"""
        return cls(
            Path(project_path),
            DurableKnowledgeSettings(
                enable_personal_memory=True,
                enable_project_learning=False,
                auto_learn_on_start=False,
            ),
        )

    @classmethod
    def for_project_knowledge_only(cls, project_path: Path) -> DurableKnowledgeLayer:
        """仅项目知识（如 PreToolUse 风格注入）；不挂载个人记忆与 ~/.claude/memory 写入。"""
        return cls(
            Path(project_path),
            DurableKnowledgeSettings(
                enable_personal_memory=False,
                enable_project_learning=True,
                auto_learn_on_start=False,
            ),
        )

    @classmethod
    def for_session_bootstrap(cls, project_path: Path) -> DurableKnowledgeLayer:
        """SessionStart：记忆 + 项目知识；是否 learn 由 hook 自行决定。"""
        return cls(
            Path(project_path),
            DurableKnowledgeSettings(
                enable_personal_memory=True,
                enable_project_learning=True,
                auto_learn_on_start=False,
            ),
        )

    @staticmethod
    def default_memory_root() -> Path:
        """个人记忆根目录。不实例化 ``PersonalMemory``、不创建检索器。"""
        return PersonalMemory.default_storage_dir()

    @staticmethod
    def merge_code_context(asset_bundle: Dict[str, Any], code_context: str) -> Dict[str, Any]:
        """
        将代码索引上下文并入 ``build_asset_bundle`` 的结果（与 Enhancer 拼接顺序一致）。
        """
        kc = str(asset_bundle.get("knowledge_context", "") or "")
        cc = code_context or ""
        return {
            **asset_bundle,
            "code_context": cc,
            "injection_text": "\n\n".join(part for part in [kc, cc] if part),
        }

    @staticmethod
    def require_personal_memory(layer: DurableKnowledgeLayer) -> PersonalMemory:
        """在工厂已保证开启个人记忆的场景下，收窄类型。"""
        pm = layer.personal_memory
        if pm is None:
            raise RuntimeError("DurableKnowledgeLayer: personal memory disabled unexpectedly")
        return pm

    def __init__(self, project_path: Path, settings: DurableKnowledgeSettings):
        self.project_path = Path(project_path)
        self.settings = settings
        self.personal_memory: Optional[PersonalMemory] = None
        self.project_learner: Optional[ProjectKnowledgeLearner] = None
        self._knowledge_retriever: Optional[KnowledgeRetriever] = None

        if settings.enable_personal_memory:
            self.personal_memory = PersonalMemory()

        if settings.enable_project_learning:
            self.project_learner = ProjectKnowledgeLearner(self.project_path)
            if settings.auto_learn_on_start:
                self.project_learner.learn()

    @property
    def knowledge_retriever(self) -> KnowledgeRetriever:
        """惰性加载；与 ``personal_memory.memory_dir`` 或默认根目录对齐。"""
        if self._knowledge_retriever is None:
            root = (
                self.personal_memory.memory_dir
                if self.personal_memory
                else PersonalMemory.default_storage_dir()
            )
            self._knowledge_retriever = KnowledgeRetriever(root)
        return self._knowledge_retriever

    def warm_knowledge_retriever(self) -> None:
        """预先构造检索器，使 ``stats_dict`` 含 ``knowledge_retriever`` 块（与惰性加载兼容）。"""
        _ = self.knowledge_retriever

    @staticmethod
    def architecture_diagram() -> str:
        return "\n".join(
            [
                "Hooks / Skills",
                "        │",
                "        ▼",
                "DurableKnowledgeLayer  (持久资产：记忆 + 项目知识 + 检索注入)",
                "        │",
                "        ├── ~/.claude/memory/*",
                "        ├── .claude/knowledge/* (per repo)",
                "        └── KnowledgeRetriever (lazy · 预算、排序、trace)",
                "        │",
                "        ▼",
                "ClaudeCodeEnhancer  (可选叠加 ContextManager 代码索引)",
            ]
        )

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

    def learn_project(self) -> dict:
        if not self.project_learner:
            return {}
        return self.project_learner.learn().to_dict()

    def generate_claudemd(self) -> str:
        if not self.project_learner:
            return ""
        return self.project_learner.generate_style_guide()

    def build_asset_bundle(
        self,
        query: str,
        files: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
        max_items: int = 10,
        max_chars: int = 2400,
    ) -> dict:
        """聚合持久资产，供上层与 commodity RAG 拼接。"""
        context_request: Dict[str, Any] = {
            "task": query,
            "query": query,
            "files": files or [],
            "errors": errors or [],
            "project_path": str(self.project_path),
        }

        injection = self.knowledge_retriever.generate_context_injection(
            context_request,
            max_items=max_items,
            max_chars=max_chars,
        )

        project_knowledge_obj = None
        if self.project_learner:
            project_knowledge_obj = self.project_learner.load_knowledge()
            if project_knowledge_obj is None and self.settings.auto_learn_on_start:
                project_knowledge_obj = self.project_learner.learn()

        injectable_preferences: List[dict] = []
        ranked_error_fixes: List[dict] = []
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
        if project_knowledge_obj:
            project_summary = {
                "project_name": project_knowledge_obj.project_name,
                "structure": project_knowledge_obj.structure.to_dict()
                if project_knowledge_obj.structure
                else None,
                "naming": project_knowledge_obj.naming.to_dict()
                if project_knowledge_obj.naming
                else None,
                "style": project_knowledge_obj.style.to_dict()
                if project_knowledge_obj.style
                else None,
                "common_patterns": project_knowledge_obj.common_patterns,
                "custom_rules": project_knowledge_obj.custom_rules,
            }

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
            "knowledge_context": knowledge_context,
            "selected_items": selected_items,
            "retrieval_trace": retrieval_trace,
            "budget": budget,
            "user_preferences": injectable_preferences,
            "past_fixes": ranked_error_fixes,
            "project_conventions": self.get_project_conventions(),
            "project_patterns": self.get_project_patterns(),
            "project_knowledge": project_summary,
            "architecture_overview": self.architecture_diagram(),
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

    def remember_preference(
        self,
        category: str,
        key: str,
        value: Any,
        description: str = "",
    ) -> None:
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

    def record_command(self, command: str, success: bool = True) -> None:
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
    ) -> None:
        if self.personal_memory:
            self.personal_memory.record_error_fix(
                error_pattern,
                error_type,
                fix_description,
                fix_code,
            )

    def learn_from_session(self, actions: List[dict], outcomes: dict) -> None:
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

    def stats_dict(self) -> dict:
        kr_info = None
        if self._knowledge_retriever is not None:
            kr = self._knowledge_retriever
            kr_info = {
                "usage_stats": len(kr.usage_stats),
                "memory_path": str(kr.memory_path),
            }
        out: Dict[str, Any] = {
            "personal_memory": None,
            "project_learner": None,
            "knowledge_retriever": kr_info,
        }
        if self.personal_memory:
            out["personal_memory"] = self.personal_memory.get_stats()
        if self.project_learner:
            knowledge = self.project_learner.load_knowledge()
            out["project_learner"] = {
                "project_path": str(self.project_path),
                "knowledge_loaded": knowledge is not None,
                "project_name": knowledge.project_name if knowledge else None,
            }
        return out

    def export_memory(self, target_json: Path) -> None:
        if self.personal_memory:
            self.personal_memory.export_memory(target_json)
