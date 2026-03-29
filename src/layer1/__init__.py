"""
Layer 1: 感知行动层（Perception-Action Layer）

本层负责与环境的交互，是智能体与外部世界的接口。

职责:
- 观察（Perception）: 感知环境状态
- 执行（Action）: 在环境中执行操作
- 反馈（Feedback）: 收集执行结果

注意: 本层不包含认知能力，只是感知和行动的接口
"""

from .observation import Observer, ObservationResult
from .action import Actor, ActionResult
from .feedback import FeedbackCollector, FeedbackType

__all__ = [
    "Observer",
    "ObservationResult",
    "Actor",
    "ActionResult",
    "FeedbackCollector",
    "FeedbackType",
]
