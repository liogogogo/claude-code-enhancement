"""
反馈模块 - Layer 1: 感知行动层

负责收集执行后的反馈信息
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class FeedbackType(Enum):
    """反馈类型"""
    OBSERVATION = "observation"  # 观察反馈
    ACTION_RESULT = "action_result"  # 执行结果反馈
    EXTERNAL = "external"  # 外部反馈（用户、系统）


@dataclass
class FeedbackItem:
    """反馈项"""
    feedback_type: FeedbackType
    source: str  # 反馈源
    content: Any  # 反馈内容
    timestamp: float
    metadata: Dict[str, Any]


class FeedbackCollector:
    """
    反馈收集器

    职责:
    - 收集来自各源的反馈
    - 整合反馈信息
    - 提供给上层认知层使用
    """

    def __init__(self):
        """初始化反馈收集器"""
        self.feedback_buffer: List[FeedbackItem] = []
        self.feedback_sources: List[Callable] = []

    def register_feedback_source(self, source: Callable) -> None:
        """
        注册反馈源

        Args:
            source: 反馈源函数
        """
        self.feedback_sources.append(source)

    def collect_feedback(
        self,
        context: Dict[str, Any],
    ) -> List[FeedbackItem]:
        """
        收集反馈

        Args:
            context: 上下文信息

        Returns:
            反馈列表
        """
        all_feedback = []

        # 从注册的反馈源收集
        for source in self.feedback_sources:
            try:
                feedback = source(context)
                all_feedback.extend(feedback)
            except Exception as e:
                # 记录错误但继续
                all_feedback.append(FeedbackItem(
                    feedback_type=FeedbackType.EXTERNAL,
                    source="feedback_collector",
                    content=f"反馈源错误: {str(e)}",
                    timestamp=self._get_timestamp(),
                    metadata={},
                ))

        # 存储到缓冲区
        self.feedback_buffer.extend(all_feedback)

        # 限制缓冲区大小
        if len(self.feedback_buffer) > 1000:
            self.feedback_buffer = self.feedback_buffer[-1000:]

        return all_feedback

    def add_feedback(
        self,
        feedback_type: FeedbackType,
        source: str,
        content: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        添加反馈

        Args:
            feedback_type: 反馈类型
            source: 反馈源
            content: 反馈内容
            metadata: 元数据
        """
        item = FeedbackItem(
            feedback_type=feedback_type,
            source=source,
            content=content,
            timestamp=self._get_timestamp(),
            metadata=metadata or {},
        )

        self.feedback_buffer.append(item)

    def get_recent_feedback(
        self,
        limit: int = 10,
        feedback_type: Optional[FeedbackType] = None,
    ) -> List[FeedbackItem]:
        """
        获取最近的反馈

        Args:
            limit: 数量限制
            feedback_type: 反馈类型过滤

        Returns:
            反馈列表
        """
        recent = self.feedback_buffer[-limit:]

        if feedback_type is not None:
            recent = [f for f in recent if f.feedback_type == feedback_type]

        return recent

    def get_feedback_summary(self) -> Dict[str, Any]:
        """
        获取反馈摘要

        Returns:
            摘要信息
        """
        if not self.feedback_buffer:
            return {
                "total_feedback": 0,
                "by_type": {},
                "by_source": {},
            }

        by_type: Dict[str, int] = {}
        by_source: Dict[str, int] = {}

        for feedback in self.feedback_buffer:
            # 按类型统计
            type_name = feedback.feedback_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1

            # 按来源统计
            source_name = feedback.source
            by_source[source_name] = by_source.get(source_name, 0) + 1

        return {
            "total_feedback": len(self.feedback_buffer),
            "by_type": by_type,
            "by_source": by_source,
            "latest_feedback": self.feedback_buffer[-1] if self.feedback_buffer else None,
        }

    def clear_buffer(self) -> None:
        """清空缓冲区"""
        self.feedback_buffer.clear()

    def _get_timestamp(self) -> float:
        """获取时间戳"""
        import time
        return time.time()
