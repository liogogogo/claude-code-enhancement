"""
知识检索器 - 让存储的记忆真正工作

核心功能：
1. 从 personal_memory 中检索相关知识
2. 根据当前上下文匹配历史经验
3. 生成可应用的上下文注入

解决问题：
- personal_memory 存储了 error_fixes 但从未被查询
- 项目风格学习了但没有反馈到输出
- 用户偏好存储了但没有影响行为
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class RetrievedKnowledge:
    """检索到的知识"""
    knowledge_type: str          # error_fix, style, preference, pattern
    content: str                 # 知识内容
    relevance: float             # 相关性 0-1
    source: str                  # 来源
    usage_count: int             # 使用次数
    last_used: Optional[datetime] = None

    def to_context_line(self) -> str:
        """转换为上下文行"""
        if self.knowledge_type == "error_fix":
            return f"- 避免错误: {self.content}"
        elif self.knowledge_type == "style":
            return f"- 代码风格: {self.content}"
        elif self.knowledge_type == "preference":
            return f"- 用户偏好: {self.content}"
        elif self.knowledge_type == "pattern":
            return f"- 已知模式: {self.content}"
        return f"- {self.content}"


@dataclass
class ContextInjection:
    """上下文注入"""
    section: str                 # 注入部分名称
    priority: int                # 优先级 (越小越优先)
    lines: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """转换为 Markdown"""
        if not self.lines:
            return ""
        return "\n".join(f"{line}" for line in self.lines)


class KnowledgeRetriever:
    """
    知识检索器

    从存储的记忆中检索相关知识，生成上下文注入。
    """

    def __init__(self, memory_path: Optional[Path] = None):
        """
        初始化知识检索器

        Args:
            memory_path: 记忆存储路径
        """
        self.memory_path = memory_path or Path.home() / ".claude" / "memory"
        self.memory_path.mkdir(parents=True, exist_ok=True)

        # 缓存
        self._cache: Dict[str, List[RetrievedKnowledge]] = {}
        self._last_load_time: Dict[str, datetime] = {}

        # 使用统计
        self.usage_stats_file = self.memory_path / "knowledge_usage.json"
        self.usage_stats: Dict[str, int] = {}
        self._load_usage_stats()

    def retrieve_for_context(
        self,
        context: Dict[str, Any],
        max_items: int = 10,
    ) -> List[RetrievedKnowledge]:
        """
        根据上下文检索相关知识

        Args:
            context: 当前上下文 (包含 task, files, errors 等)
            max_items: 最大返回数量

        Returns:
            相关知识列表
        """
        results = []

        # 1. 检索错误修复知识
        if context.get("errors") or context.get("error_pattern"):
            error_knowledge = self._retrieve_error_fixes(context)
            results.extend(error_knowledge)

        # 2. 检索项目风格知识
        if context.get("project_path"):
            style_knowledge = self._retrieve_project_style(context)
            results.extend(style_knowledge)

        # 3. 检索用户偏好
        preference_knowledge = self._retrieve_preferences(context)
        results.extend(preference_knowledge)

        # 4. 检索成功模式
        if context.get("task"):
            pattern_knowledge = self._retrieve_patterns(context)
            results.extend(pattern_knowledge)

        # 按相关性排序，取前 N 个
        results.sort(key=lambda x: x.relevance, reverse=True)
        results = results[:max_items]

        # 更新使用统计
        for k in results:
            self._record_usage(k)

        return results

    def generate_context_injection(
        self,
        context: Dict[str, Any],
    ) -> ContextInjection:
        """
        生成上下文注入

        Args:
            context: 当前上下文

        Returns:
            可注入到提示词的上下文
        """
        knowledge = self.retrieve_for_context(context)

        lines = []
        error_lines = []
        style_lines = []
        preference_lines = []

        for k in knowledge:
            line = k.to_context_line()
            if k.knowledge_type == "error_fix":
                error_lines.append(line)
            elif k.knowledge_type == "style":
                style_lines.append(line)
            elif k.knowledge_type == "preference":
                preference_lines.append(line)
            else:
                lines.append(line)

        # 组装
        all_lines = []
        if error_lines:
            all_lines.append("## 历史错误教训")
            all_lines.extend(error_lines[:5])
        if style_lines:
            all_lines.append("## 项目代码风格")
            all_lines.extend(style_lines[:5])
        if preference_lines:
            all_lines.append("## 用户偏好")
            all_lines.extend(preference_lines[:3])
        if lines:
            all_lines.append("## 相关经验")
            all_lines.extend(lines[:5])

        return ContextInjection(
            section="knowledge_context",
            priority=10,
            lines=all_lines,
        )

    def query_similar_errors(
        self,
        error_message: str,
        threshold: float = 0.3,
    ) -> List[RetrievedKnowledge]:
        """
        查询相似错误

        Args:
            error_message: 错误信息
            threshold: 相似度阈值

        Returns:
            相似错误列表
        """
        error_knowledge = self._load_knowledge("error_knowledge")
        results = []

        for item in error_knowledge:
            # 计算相似度
            similarity = self._calculate_similarity(
                error_message,
                item.get("error_pattern", ""),
            )

            if similarity >= threshold:
                results.append(RetrievedKnowledge(
                    knowledge_type="error_fix",
                    content=item.get("suggestion", ""),
                    relevance=similarity,
                    source="error_knowledge",
                    usage_count=self.usage_stats.get(item.get("error_pattern", ""), 0),
                ))

        results.sort(key=lambda x: x.relevance, reverse=True)
        return results[:5]

    def get_style_for_file(
        self,
        file_path: str,
    ) -> List[RetrievedKnowledge]:
        """
        获取文件的代码风格

        Args:
            file_path: 文件路径

        Returns:
            代码风格知识
        """
        # 获取项目知识
        project_knowledge = self._load_knowledge("project_knowledge")

        # 提取文件类型
        ext = Path(file_path).suffix.lower()

        results = []
        for item in project_knowledge:
            style = item.get("style", {})
            if not style:
                continue

            # 检查是否匹配文件类型
            file_patterns = item.get("file_patterns", [])
            if ext in file_patterns or any(ext in p for p in file_patterns):
                for key, value in style.items():
                    results.append(RetrievedKnowledge(
                        knowledge_type="style",
                        content=f"{key}: {value}",
                        relevance=0.8,
                        source="project_knowledge",
                        usage_count=0,
                    ))

        return results

    def _retrieve_error_fixes(
        self,
        context: Dict[str, Any],
    ) -> List[RetrievedKnowledge]:
        """检索错误修复知识"""
        results = []

        # 从上下文获取错误信息
        error_info = context.get("errors", [])
        if isinstance(error_info, str):
            error_info = [error_info]

        error_knowledge = self._load_knowledge("error_knowledge")

        for error in error_info:
            for item in error_knowledge:
                # 简单匹配
                pattern = item.get("error_pattern", "")
                if self._match_error(error, pattern):
                    results.append(RetrievedKnowledge(
                        knowledge_type="error_fix",
                        content=item.get("suggestion", ""),
                        relevance=0.9,
                        source="error_knowledge",
                        usage_count=self.usage_stats.get(pattern, 0),
                    ))

        return results

    def _retrieve_project_style(
        self,
        context: Dict[str, Any],
    ) -> List[RetrievedKnowledge]:
        """检索项目风格知识"""
        results = []
        project_path = context.get("project_path", "")

        project_knowledge = self._load_knowledge("project_knowledge")

        for item in project_knowledge:
            if item.get("project_path") == project_path:
                style = item.get("style", {})
                for key, value in style.items():
                    results.append(RetrievedKnowledge(
                        knowledge_type="style",
                        content=f"{key}: {value}",
                        relevance=0.85,
                        source="project_knowledge",
                        usage_count=0,
                    ))

        return results

    def _retrieve_preferences(
        self,
        context: Dict[str, Any],
    ) -> List[RetrievedKnowledge]:
        """检索用户偏好"""
        results = []
        preferences = self._load_knowledge("preferences")

        for key, value in preferences.items():
            # 检查是否与当前上下文相关
            if self._is_preference_relevant(key, context):
                results.append(RetrievedKnowledge(
                    knowledge_type="preference",
                    content=f"{key}: {value.get('value', '')}",
                    relevance=value.get("confidence", 0.5),
                    source="preferences",
                    usage_count=0,
                ))

        return results

    def _retrieve_patterns(
        self,
        context: Dict[str, Any],
    ) -> List[RetrievedKnowledge]:
        """检索成功模式"""
        results = []
        task = context.get("task", "")

        patterns = self._load_knowledge("learnings")

        for item in patterns:
            learning = item.get("learning", "")
            if learning.startswith("success:"):
                # 检查是否与任务相关
                if self._is_task_relevant(learning, task):
                    results.append(RetrievedKnowledge(
                        knowledge_type="pattern",
                        content=learning,
                        relevance=0.7,
                        source="learnings",
                        usage_count=0,
                    ))

        return results

    def _load_knowledge(self, knowledge_type: str) -> List[Dict]:
        """加载知识"""
        # 检查缓存
        now = datetime.now()
        if knowledge_type in self._last_load_time:
            if (now - self._last_load_time[knowledge_type]).seconds < 60:
                if knowledge_type in self._cache:
                    return self._cache[knowledge_type]

        # 从文件加载
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
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 处理不同格式
            if isinstance(data, dict):
                if knowledge_type == "preferences":
                    result = [{"key": k, **v} for k, v in data.items()]
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
        """计算文本相似度"""
        # 简单的关键词匹配
        words1 = set(re.findall(r"\w+", text1.lower()))
        words2 = set(re.findall(r"\w+", text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _match_error(self, error: str, pattern: str) -> bool:
        """匹配错误"""
        error_lower = error.lower()
        pattern_lower = pattern.lower()

        # 直接包含
        if pattern_lower in error_lower:
            return True

        # 正则匹配
        try:
            if re.search(pattern, error, re.IGNORECASE):
                return True
        except re.error:
            pass

        # 关键词匹配
        pattern_words = set(re.findall(r"\w+", pattern_lower))
        error_words = set(re.findall(r"\w+", error_lower))

        if pattern_words & error_words:
            return True

        return False

    def _is_preference_relevant(self, key: str, context: Dict) -> bool:
        """检查偏好是否相关"""
        # 根据偏好类型判断相关性
        if "tools" in key and context.get("task"):
            return True
        if "style" in key and context.get("files"):
            return True
        if "output" in key:
            return True
        return False

    def _is_task_relevant(self, learning: str, task: str) -> bool:
        """检查学习是否与任务相关"""
        # 简单的关键词匹配
        learning_lower = learning.lower()
        task_lower = task.lower()

        # 提取关键词
        task_words = set(re.findall(r"\w+", task_lower))

        for word in task_words:
            if word in learning_lower:
                return True

        return False

    def _load_usage_stats(self):
        """加载使用统计"""
        if self.usage_stats_file.exists():
            try:
                self.usage_stats = json.loads(self.usage_stats_file.read_text())
            except (json.JSONDecodeError, IOError):
                self.usage_stats = {}

    def _record_usage(self, knowledge: RetrievedKnowledge):
        """记录使用"""
        key = f"{knowledge.knowledge_type}:{knowledge.content[:50]}"
        self.usage_stats[key] = self.usage_stats.get(key, 0) + 1

        # 定期保存
        if sum(self.usage_stats.values()) % 10 == 0:
            self._save_usage_stats()

    def _save_usage_stats(self):
        """保存使用统计"""
        self.usage_stats_file.write_text(
            json.dumps(self.usage_stats, indent=2)
        )


def get_context_for_claude(
    task: str,
    files: Optional[List[str]] = None,
    errors: Optional[List[str]] = None,
    project_path: Optional[str] = None,
) -> str:
    """
    获取注入给 Claude 的上下文

    便捷函数，直接生成可注入的上下文字符串。

    Args:
        task: 当前任务
        files: 相关文件
        errors: 错误信息
        project_path: 项目路径

    Returns:
        上下文字符串
    """
    retriever = KnowledgeRetriever()

    context = {
        "task": task,
        "files": files or [],
        "errors": errors or [],
        "project_path": project_path,
    }

    injection = retriever.generate_context_injection(context)
    return injection.to_markdown()