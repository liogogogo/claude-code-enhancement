"""
Layer 2: 认知能力层（简化版）

核心功能：
- 错误分析
- 推理引擎
"""

from .cognitive import ErrorAnalyzer, ReasoningEngine, AnalysisResult, ErrorSeverity
from .feedback_loop import FeedbackLoop, FeedbackType, FeedbackAction

__all__ = [
    "ErrorAnalyzer",
    "ReasoningEngine",
    "AnalysisResult",
    "ErrorSeverity",
    "FeedbackLoop",
    "FeedbackType",
    "FeedbackAction",
]