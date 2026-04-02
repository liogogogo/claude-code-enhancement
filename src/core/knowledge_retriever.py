"""
知识检索器 - 让存储的记忆真正工作

核心功能：
1. 从 personal_memory 中检索相关知识
2. 根据当前上下文匹配历史经验
3. 生成可应用的上下文注入
4. 对候选结果进行排序、预算控制和追踪
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .project_knowledge_learner import ProjectKnowledgeLearner


@dataclass
class RetrievedKnowledge:
    """检索到的知识"""

    knowledge_type: str  # error_fix, style, preference, pattern, structure
    content: str
    relevance: float
    source: str
    usage_count: int
    source_id: str = ""
    last_used: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_context_line(self) -> str:
        """转换为上下文行"""
        if self.knowledge_type == "error_fix":
            return f"- 避免错误: {self.content}"
        if self.knowledge_type == "style":
            return f"- 代码风格: {self.content}"
        if self.knowledge_type == "preference":
            return f"- 用户偏好: {self.content}"
        if self.knowledge_type == "pattern":
            return f"- 已知模式: {self.content}"
        if self.knowledge_type == "structure":
            return f"- 项目结构: {self.content}"
        return f"- {self.content}"


@dataclass
class RetrievalTraceItem:
    """检索追踪项"""

    knowledge_type: str
    source: str
    source_id: str
    score: float
    selected: bool
    reason: str
    content_preview: str

    def to_dict(self) -> dict:
        return {
            "knowledge_type": self.knowledge_type,
            "source": self.source,
            "source_id": self.source_id,
            "score": self.score,
            "selected": self.selected,
            "reason": self.reason,
            "content_preview": self.content_preview,
        }


@dataclass
class ContextInjection:
    """上下文注入"""

    section: str
    priority: int
    lines: List[str] = field(default_factory=list)
    selected_items: List[RetrievedKnowledge] = field(default_factory=list)
    trace: List[RetrievalTraceItem] = field(default_factory=list)
    budget: Dict[str, Any] = field(default_factory=dict)

    def to_markdown(self) -> str:
        """转换为 Markdown"""
        if not self.lines:
            return ""
        return "\n".join(self.lines)


class KnowledgeRetriever:
    """知识检索器"""

    DEFAULT_TYPE_LIMITS = {
        "error_fix": 3,
        "style": 4,
        "preference": 3,
        "pattern": 2,
        "structure": 2,
    }

    def __init__(self, memory_path: Optional[Path] = None):
        self.memory_path = memory_path or Path.home() / ".claude" / "memory"
        self.memory_path.mkdir(parents=True, exist_ok=True)

        self._cache: Dict[str, List[dict]] = {}
        self._last_load_time: Dict[str, datetime] = {}

        self.usage_stats_file = self.memory_path / "knowledge_usage.json"
        self.usage_stats: Dict[str, int] = {}
        self._load_usage_stats()

    def retrieve_for_context(
        self,
        context: Dict[str, Any],
        max_items: int = 10,
        max_chars: int = 2400,
        type_limits: Optional[Dict[str, int]] = None,
    ) -> List[RetrievedKnowledge]:
        """根据上下文检索相关知识"""
        candidates = self._collect_candidates(context)
        ranked = sorted(candidates, key=self._score_knowledge, reverse=True)

        limits = {**self.DEFAULT_TYPE_LIMITS, **(type_limits or {})}
        selected: List[RetrievedKnowledge] = []
        counts: Dict[str, int] = {}
        total_chars = 0

        for item in ranked:
            type_count = counts.get(item.knowledge_type, 0)
            type_limit = limits.get(item.knowledge_type, max_items)
            if type_count >= type_limit:
                continue
            projected_chars = total_chars + len(item.to_context_line())
            if len(selected) >= max_items or projected_chars > max_chars:
                continue
            selected.append(item)
            counts[item.knowledge_type] = type_count + 1
            total_chars = projected_chars
            self._record_usage(item)

        return selected

    def generate_context_injection(
        self,
        context: Dict[str, Any],
        max_items: int = 10,
        max_chars: int = 2400,
        type_limits: Optional[Dict[str, int]] = None,
    ) -> ContextInjection:
        """生成上下文注入及追踪信息"""
        candidates = self._collect_candidates(context)
        ranked = sorted(candidates, key=self._score_knowledge, reverse=True)
        limits = {**self.DEFAULT_TYPE_LIMITS, **(type_limits or {})}

        selected: List[RetrievedKnowledge] = []
        trace: List[RetrievalTraceItem] = []
        counts: Dict[str, int] = {}
        total_chars = 0

        for item in ranked:
            score = self._score_knowledge(item)
            reason = "selected"
            selected_flag = True

            type_count = counts.get(item.knowledge_type, 0)
            type_limit = limits.get(item.knowledge_type, max_items)
            if type_count >= type_limit:
                selected_flag = False
                reason = f"type_limit:{item.knowledge_type}"
            elif len(selected) >= max_items:
                selected_flag = False
                reason = "item_budget"
            elif total_chars + len(item.to_context_line()) > max_chars:
                selected_flag = False
                reason = "char_budget"

            if selected_flag:
                selected.append(item)
                counts[item.knowledge_type] = type_count + 1
                total_chars += len(item.to_context_line())
                self._record_usage(item)

            trace.append(
                RetrievalTraceItem(
                    knowledge_type=item.knowledge_type,
                    source=item.source,
                    source_id=item.source_id,
                    score=round(score, 4),
                    selected=selected_flag,
                    reason=reason,
                    content_preview=item.content[:120],
                )
            )

        grouped_lines = self._build_section_lines(selected)
        budget = {
            "max_items": max_items,
            "selected_items": len(selected),
            "max_chars": max_chars,
            "selected_chars": total_chars,
            "type_limits": limits,
        }

        return ContextInjection(
            section="knowledge_context",
            priority=10,
            lines=grouped_lines,
            selected_items=selected,
            trace=trace,
            budget=budget,
        )

    def query_similar_errors(
        self,
        error_message: str,
        threshold: float = 0.3,
    ) -> List[RetrievedKnowledge]:
        """查询相似错误"""
        error_knowledge = self._load_knowledge("error_knowledge")
        results = []

        for item in error_knowledge:
            pattern = item.get("error_pattern", "")
            similarity = self._calculate_similarity(error_message, pattern)
            if similarity < threshold:
                continue
            content = item.get("fix_description") or item.get("suggestion", "")
            results.append(
                RetrievedKnowledge(
                    knowledge_type="error_fix",
                    content=content,
                    relevance=similarity,
                    source="error_knowledge",
                    usage_count=self.usage_stats.get(pattern, 0),
                    source_id=pattern,
                    metadata={
                        "success_count": item.get("success_count", 1),
                        "fail_count": item.get("fail_count", 0),
                    },
                )
            )

        results.sort(key=self._score_knowledge, reverse=True)
        return results[:5]

    def get_style_for_file(self, file_path: str) -> List[RetrievedKnowledge]:
        """获取文件的代码风格"""
        return self._retrieve_project_style(
            {
                "project_path": str(Path(file_path).resolve().parent),
                "files": [file_path],
            }
        )

    def _collect_candidates(self, context: Dict[str, Any]) -> List[RetrievedKnowledge]:
        results: List[RetrievedKnowledge] = []
        if context.get("errors") or context.get("error_pattern"):
            results.extend(self._retrieve_error_fixes(context))
        if context.get("project_path"):
            results.extend(self._retrieve_project_style(context))
        results.extend(self._retrieve_preferences(context))
        if context.get("task"):
            results.extend(self._retrieve_patterns(context))
        return results

    def _build_section_lines(self, knowledge: List[RetrievedKnowledge]) -> List[str]:
        lines: List[str] = []
        buckets = {
            "error_fix": [],
            "style": [],
            "preference": [],
            "pattern": [],
            "structure": [],
        }
        for item in knowledge:
            buckets.setdefault(item.knowledge_type, []).append(item.to_context_line())

        if buckets["error_fix"]:
            lines.append("## 历史错误教训")
            lines.extend(buckets["error_fix"])
        if buckets["style"] or buckets["structure"]:
            lines.append("## 项目知识")
            lines.extend(buckets["style"])
            lines.extend(buckets["structure"])
        if buckets["preference"]:
            lines.append("## 用户偏好")
            lines.extend(buckets["preference"])
        if buckets["pattern"]:
            lines.append("## 相关经验")
            lines.extend(buckets["pattern"])
        return lines

    def _score_knowledge(self, knowledge: RetrievedKnowledge) -> float:
        score = knowledge.relevance
        score += min(knowledge.usage_count, 5) * 0.03

        if knowledge.knowledge_type == "preference":
            score += float(knowledge.metadata.get("confidence", 0.0)) * 0.2
        elif knowledge.knowledge_type == "error_fix":
            success_count = knowledge.metadata.get("success_count", 1)
            fail_count = knowledge.metadata.get("fail_count", 0)
            total = success_count + fail_count
            success_rate = success_count / total if total else 0.0
            score += success_rate * 0.25
        elif knowledge.knowledge_type in {"style", "structure"}:
            score += 0.1

        return score

    def _retrieve_error_fixes(self, context: Dict[str, Any]) -> List[RetrievedKnowledge]:
        results = []
        error_info = context.get("errors") or context.get("error_pattern") or []
        if isinstance(error_info, str):
            error_info = [error_info]

        error_knowledge = self._load_knowledge("error_knowledge")
        for error in error_info:
            for item in error_knowledge:
                pattern = item.get("error_pattern", "")
                if not self._match_error(error, pattern):
                    continue
                content = item.get("fix_description") or item.get("suggestion", "")
                results.append(
                    RetrievedKnowledge(
                        knowledge_type="error_fix",
                        content=content,
                        relevance=0.9,
                        source="error_knowledge",
                        usage_count=self.usage_stats.get(pattern, 0),
                        source_id=pattern,
                        metadata={
                            "error_type": item.get("error_type", ""),
                            "success_count": item.get("success_count", 1),
                            "fail_count": item.get("fail_count", 0),
                        },
                    )
                )
        return results

    def _retrieve_project_style(self, context: Dict[str, Any]) -> List[RetrievedKnowledge]:
        results = []
        project_path = context.get("project_path")
        if not project_path:
            return results

        learner = ProjectKnowledgeLearner(Path(project_path))
        knowledge = learner.load_knowledge()
        if knowledge:
            if knowledge.style:
                style = knowledge.style
                style_entries = {
                    "indent_size": style.indent_size,
                    "indent_type": style.indent_type,
                    "quote_style": style.quote_style,
                    "max_line_length": style.max_line_length,
                    "docstring_style": style.docstring_style,
                }
                for key, value in style_entries.items():
                    results.append(
                        RetrievedKnowledge(
                            knowledge_type="style",
                            content=f"{key}: {value}",
                            relevance=0.85,
                            source="project_knowledge_learner",
                            usage_count=0,
                            source_id=f"style:{key}",
                        )
                    )

            if knowledge.naming:
                naming = knowledge.naming
                naming_entries = {
                    "variable_style": naming.variable_style,
                    "function_style": naming.function_style,
                    "class_style": naming.class_style,
                    "constant_style": naming.constant_style,
                    "private_prefix": naming.private_prefix,
                }
                for key, value in naming_entries.items():
                    results.append(
                        RetrievedKnowledge(
                            knowledge_type="style",
                            content=f"{key}: {value}",
                            relevance=0.82,
                            source="project_knowledge_learner",
                            usage_count=0,
                            source_id=f"naming:{key}",
                        )
                    )

            if knowledge.structure:
                structure = knowledge.structure
                structure_entries = {
                    "type": structure.type,
                    "framework": structure.framework,
                    "source_dir": structure.source_dir,
                    "test_framework": structure.test_framework,
                }
                for key, value in structure_entries.items():
                    if value:
                        results.append(
                            RetrievedKnowledge(
                                knowledge_type="structure",
                                content=f"{key}: {value}",
                                relevance=0.78,
                                source="project_knowledge_learner",
                                usage_count=0,
                                source_id=f"structure:{key}",
                            )
                        )

            for pattern in knowledge.common_patterns[:5]:
                results.append(
                    RetrievedKnowledge(
                        knowledge_type="pattern",
                        content=pattern,
                        relevance=0.7,
                        source="project_knowledge_learner",
                        usage_count=0,
                        source_id=f"pattern:{pattern}",
                    )
                )

        if results:
            return results

        legacy_project_knowledge = self._load_knowledge("project_knowledge")
        for item in legacy_project_knowledge:
            if item.get("project_path") != str(project_path):
                continue
            style = item.get("style", {})
            for key, value in style.items():
                results.append(
                    RetrievedKnowledge(
                        knowledge_type="style",
                        content=f"{key}: {value}",
                        relevance=0.75,
                        source="project_knowledge",
                        usage_count=0,
                        source_id=f"legacy:{key}",
                    )
                )
        return results

    def _retrieve_preferences(self, context: Dict[str, Any]) -> List[RetrievedKnowledge]:
        results = []
        preferences = self._load_knowledge("preferences")
        for value in preferences:
            key = value.get("key", "")
            category = value.get("category", "")
            if not self._is_preference_relevant(f"{category}:{key}", context):
                continue
            results.append(
                RetrievedKnowledge(
                    knowledge_type="preference",
                    content=f"{key}: {value.get('value', '')}",
                    relevance=value.get("confidence", 0.5),
                    source="preferences",
                    usage_count=0,
                    source_id=f"{category}:{key}",
                    metadata={
                        "confidence": value.get("confidence", 0.5),
                        "description": value.get("description", ""),
                    },
                )
            )
        return results

    def _retrieve_patterns(self, context: Dict[str, Any]) -> List[RetrievedKnowledge]:
        results = []
        task = context.get("task", "")
        patterns = self._load_knowledge("learnings")
        for item in patterns:
            learning = item.get("learning", "")
            if not learning.startswith("success:"):
                continue
            if not self._is_task_relevant(learning, task):
                continue
            results.append(
                RetrievedKnowledge(
                    knowledge_type="pattern",
                    content=learning,
                    relevance=0.7,
                    source="learnings",
                    usage_count=0,
                    source_id=learning[:60],
                )
            )
        return results

    def _load_knowledge(self, knowledge_type: str) -> List[Dict[str, Any]]:
        now = datetime.now()
        if knowledge_type in self._last_load_time:
            if (now - self._last_load_time[knowledge_type]).seconds < 60:
                if knowledge_type in self._cache:
                    return self._cache[knowledge_type]

        file_map = {
            "error_knowledge": "error_knowledge.json",
            "project_knowledge": "projects.json",
            "preferences": "preferences.json",
            "learnings": "learnings.json",
            "commands": "commands.json",
        }

        file_name = file_map.get(knowledge_type, f"{knowledge_type}.json")
        file_path = self.memory_path / file_name
        if not file_path.exists():
            self._cache[knowledge_type] = []
            return []

        try:
            with open(file_path, "r", encoding="utf-8") as file:
                data = json.load(file)

            if isinstance(data, dict):
                if knowledge_type == "preferences":
                    result = [{"storage_key": key, **value} for key, value in data.items()]
                else:
                    result = list(data.values()) if data else []
            else:
                result = data if isinstance(data, list) else []

            self._cache[knowledge_type] = result
            self._last_load_time[knowledge_type] = now
            return result
        except (json.JSONDecodeError, IOError):
            self._cache[knowledge_type] = []
            return []

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        words1 = set(re.findall(r"\w+", text1.lower()))
        words2 = set(re.findall(r"\w+", text2.lower()))
        if not words1 or not words2:
            return 0.0
        return len(words1 & words2) / len(words1 | words2)

    def _match_error(self, error: str, pattern: str) -> bool:
        error_lower = error.lower()
        pattern_lower = pattern.lower()
        if pattern_lower in error_lower:
            return True
        try:
            if re.search(pattern, error, re.IGNORECASE):
                return True
        except re.error:
            pass
        pattern_words = set(re.findall(r"\w+", pattern_lower))
        error_words = set(re.findall(r"\w+", error_lower))
        return bool(pattern_words & error_words)

    def _is_preference_relevant(self, key: str, context: Dict[str, Any]) -> bool:
        if "tools" in key and context.get("task"):
            return True
        if "style" in key and (context.get("files") or context.get("project_path")):
            return True
        if "output" in key or "workflow" in key:
            return True
        return False

    def _is_task_relevant(self, learning: str, task: str) -> bool:
        learning_lower = learning.lower()
        task_words = set(re.findall(r"\w+", task.lower()))
        return any(word in learning_lower for word in task_words)

    def _load_usage_stats(self):
        if self.usage_stats_file.exists():
            try:
                self.usage_stats = json.loads(self.usage_stats_file.read_text())
            except (json.JSONDecodeError, IOError):
                self.usage_stats = {}

    def _record_usage(self, knowledge: RetrievedKnowledge):
        key = f"{knowledge.knowledge_type}:{knowledge.source_id or knowledge.content[:50]}"
        self.usage_stats[key] = self.usage_stats.get(key, 0) + 1
        if sum(self.usage_stats.values()) % 10 == 0:
            self._save_usage_stats()

    def _save_usage_stats(self):
        self.usage_stats_file.write_text(json.dumps(self.usage_stats, indent=2, ensure_ascii=False))


def get_context_for_claude(
    task: str,
    files: Optional[List[str]] = None,
    errors: Optional[List[str]] = None,
    project_path: Optional[str] = None,
) -> str:
    """便捷函数，直接生成可注入的上下文字符串。"""
    retriever = KnowledgeRetriever()
    context = {
        "task": task,
        "files": files or [],
        "errors": errors or [],
        "project_path": project_path,
    }
    injection = retriever.generate_context_injection(context)
    return injection.to_markdown()
