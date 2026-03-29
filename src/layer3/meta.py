"""
Layer 3: 元认知层（简化版）

核心功能：
- 决策引擎
- 执行追踪
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime
import json
from pathlib import Path


class DecisionType(Enum):
    """决策类型"""
    EXECUTE = "execute"      # 继续执行
    MODIFY = "modify"        # 修改后执行
    ROLLBACK = "rollback"    # 回滚
    LEARN = "learn"          # 学习记录


@dataclass
class ActionStep:
    """行动步骤"""
    step_type: str
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Decision:
    """决策结果"""
    decision: DecisionType
    reasoning: str
    action_plan: List[ActionStep] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "decision": self.decision.value,
            "reasoning": self.reasoning,
            "action_plan": [
                {"type": s.step_type, "description": s.description}
                for s in self.action_plan
            ],
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat(),
        }


class DecisionEngine:
    """
    决策引擎

    功能：
    - 基于分析结果做决策
    - 生成行动计划
    """

    def __init__(self, history_path: Optional[Path] = None):
        self.history_path = history_path or Path.home() / ".claude" / "decision_history.json"
        self.decision_history: List[Dict[str, Any]] = []

    def decide(
        self,
        analysis_result: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Decision:
        """
        做出决策

        Args:
            analysis_result: 分析结果
            context: 上下文信息

        Returns:
            决策
        """
        findings = analysis_result.get("findings", [])
        suggestions = analysis_result.get("suggestions", [])
        confidence = analysis_result.get("confidence", 0.5)

        # 根据发现的问题做决策
        if not findings:
            decision = DecisionType.EXECUTE
            reasoning = "No issues found, proceeding with execution"
            action_plan = [
                ActionStep("continue", "Continue with planned action")
            ]

        elif any(f.get("severity") == "critical" for f in findings):
            decision = DecisionType.MODIFY
            reasoning = "Critical issues found, modification required"
            action_plan = [
                ActionStep("fix", "Fix critical issues", {"issues": findings})
            ]

        else:
            decision = DecisionType.EXECUTE
            reasoning = "Minor issues found, proceeding with caution"
            action_plan = [
                ActionStep("note", "Note issues for later", {"issues": findings})
            ]

        result = Decision(
            decision=decision,
            reasoning=reasoning,
            action_plan=action_plan,
            confidence=confidence,
        )

        # 记录决策
        self._record_decision(result)

        return result

    def _record_decision(self, decision: Decision):
        """记录决策"""
        self.decision_history.append(decision.to_dict())
        self._save_history()

    def _save_history(self):
        """保存历史"""
        try:
            self.history_path.parent.mkdir(parents=True, exist_ok=True)
            data = {"decisions": self.decision_history[-100:]}
            self.history_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        except Exception:
            pass


class ExecutionTracker:
    """
    执行追踪器

    功能：
    - 记录执行历史
    - 统计成功率
    """

    def __init__(self, stats_path: Optional[Path] = None):
        self.stats_path = stats_path or Path.home() / ".claude" / "execution_stats.json"
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "by_decision": {},
        }
        self._load_stats()

    def record(self, decision: Decision, success: bool):
        """记录执行结果"""
        self.stats["total_runs"] += 1
        if success:
            self.stats["successful_runs"] += 1

        decision_type = decision.decision.value
        if decision_type not in self.stats["by_decision"]:
            self.stats["by_decision"][decision_type] = {"total": 0, "success": 0}
        self.stats["by_decision"][decision_type]["total"] += 1
        if success:
            self.stats["by_decision"][decision_type]["success"] += 1

        self._save_stats()

    def get_success_rate(self) -> float:
        """获取成功率"""
        total = self.stats["total_runs"]
        if total == 0:
            return 0.0
        return self.stats["successful_runs"] / total

    def _load_stats(self):
        """加载统计"""
        if self.stats_path.exists():
            try:
                data = json.loads(self.stats_path.read_text())
                self.stats = data
            except Exception:
                pass

    def _save_stats(self):
        """保存统计"""
        try:
            self.stats_path.parent.mkdir(parents=True, exist_ok=True)
            self.stats_path.write_text(json.dumps(self.stats, indent=2))
        except Exception:
            pass


__all__ = [
    "DecisionType",
    "ActionStep",
    "Decision",
    "DecisionEngine",
    "ExecutionTracker",
]