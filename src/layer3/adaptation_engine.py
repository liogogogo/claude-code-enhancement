"""
适应引擎 - Layer 3 核心模块
自我修改和自适应学习
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path
import time


class AdaptationStrategy(Enum):
    """适应策略"""
    PROMPT_OPTIMIZATION = "prompt_optimization"  # 提示词优化
    HYPERPARAMETER_TUNING = "hyperparameter_tuning"  # 超参数调优
    ARCHITECTURE_EVOLUTION = "architecture_evolution"  # 架构进化
    KNOWLEDGE_UPDATE = "knowledge_update"  # 知识更新


class AdaptationTrigger(Enum):
    """适应触发条件"""
    PERFORMANCE_DEGRADATION = "performance_degradation"  # 性能下降
    NEW_TASK_TYPE = "new_task_type"  # 新任务类型
    USER_FEEDBACK = "user_feedback"  # 用户反馈
    SCHEDULED = "scheduled"  # 定时触发
    MANUAL = "manual"  # 手动触发


@dataclass
class AdaptationProposal:
    """适应提案"""
    strategy: AdaptationStrategy
    trigger: AdaptationTrigger
    description: str
    changes: Dict[str, Any]  # 具体修改内容
    expected_improvement: float  # 预期改进
    confidence: float  # 置信度
    risk_level: str  # "low", "medium", "high"


@dataclass
class AdaptationResult:
    """适应结果"""
    proposal: AdaptationProposal
    success: bool
    actual_improvement: float
    side_effects: List[str]
    timestamp: float
    validation_score: float


class AdaptationEngine:
    """
    适应引擎

    功能:
    - 监控性能和触发条件
    - 生成适应提案
    - 执行适应操作
    - 验证适应效果
    - 回滚机制
    """

    def __init__(
        self,
        knowledge_base_path: Optional[str] = None,
        max_history_size: int = 1000,
    ):
        """
        初始化适应引擎

        Args:
            knowledge_base_path: 知识库路径
            max_history_size: 最大历史记录数
        """
        self.knowledge_base_path = knowledge_base_path
        self.max_history_size = max_history_size

        self.adaptation_history: List[AdaptationResult] = []
        self.performance_metrics: Dict[str, List[float]] = {}

        # 加载历史记录
        if knowledge_base_path:
            self._load_knowledge_base()

    def monitor_and_adapt(
        self,
        current_metrics: Dict[str, float],
        thresholds: Dict[str, float],
        adaptation_strategies: List[Callable],
    ) -> Optional[AdaptationResult]:
        """
        监控并执行适应

        Args:
            current_metrics: 当前性能指标
            thresholds: 阈值（低于此值触发适应）
            adaptation_strategies: 适应策略函数列表

        Returns:
            适应结果（如果没有触发适应，返回 None）
        """
        # 更新性能指标
        self._update_performance_metrics(current_metrics)

        # 检查是否需要适应
        trigger = self._check_adaptation_triggers(current_metrics, thresholds)

        if not trigger:
            return None

        # 生成适应提案
        proposals = self._generate_proposals(trigger, current_metrics, adaptation_strategies)

        if not proposals:
            return None

        # 选择最佳提案
        best_proposal = self._select_best_proposal(proposals)

        # 执行适应
        result = self._execute_adaptation(best_proposal, current_metrics)

        # 记录历史
        self.adaptation_history.append(result)

        # 保存知识库
        if self.knowledge_base_path:
            self._save_knowledge_base()

        return result

    def optimize_prompt(
        self,
        task_type: str,
        current_prompt: str,
        performance_history: List[float],
    ) -> AdaptationProposal:
        """
        优化提示词

        Args:
            task_type: 任务类型
            current_prompt: 当前提示词
            performance_history: 性能历史

        Returns:
            适应提案
        """
        # 分析性能趋势
        if len(performance_history) < 3:
            return AdaptationProposal(
                strategy=AdaptationStrategy.PROMPT_OPTIMIZATION,
                trigger=AdaptationTrigger.PERFORMANCE_DEGRADATION,
                description="性能数据不足，暂不优化",
                changes={},
                expected_improvement=0.0,
                confidence=0.0,
                risk_level="low",
            )

        # 检查性能是否下降
        recent_avg = sum(performance_history[-3:]) / 3
        overall_avg = sum(performance_history) / len(performance_history)

        if recent_avg >= overall_avg:
            return AdaptationProposal(
                strategy=AdaptationStrategy.PROMPT_OPTIMIZATION,
                trigger=AdaptationTrigger.PERFORMANCE_DEGRADATION,
                description="性能稳定或上升，暂不优化",
                changes={},
                expected_improvement=0.0,
                confidence=0.0,
                risk_level="low",
            )

        # 生成优化建议
        optimized_prompt = self._generate_optimized_prompt(
            task_type, current_prompt, performance_history
        )

        return AdaptationProposal(
            strategy=AdaptationStrategy.PROMPT_OPTIMIZATION,
            trigger=AdaptationTrigger.PERFORMANCE_DEGRADATION,
            description=f"优化 {task_type} 任务的提示词",
            changes={"prompt": optimized_prompt},
            expected_improvement=0.1,  # 预期提升 10%
            confidence=0.7,
            risk_level="low",
        )

    def update_knowledge(
        self,
        new_examples: List[Dict[str, Any]],
        validation_performance: float,
    ) -> AdaptationProposal:
        """
        更新知识库

        Args:
            new_examples: 新示例
            validation_performance: 验证性能

        Returns:
            适应提案
        """
        if validation_performance < 0.7:
            return AdaptationProposal(
                strategy=AdaptationStrategy.KNOWLEDGE_UPDATE,
                trigger=AdaptationTrigger.MANUAL,
                description="验证性能较低，不建议更新",
                changes={},
                expected_improvement=0.0,
                confidence=0.0,
                risk_level="high",
            )

        return AdaptationProposal(
            strategy=AdaptationStrategy.KNOWLEDGE_UPDATE,
            trigger=AdaptationTrigger.MANUAL,
            description=f"添加 {len(new_examples)} 个新示例到知识库",
            changes={"examples": new_examples},
            expected_improvement=0.05,
            confidence=0.8,
            risk_level="low",
        )

    def get_adaptation_statistics(self) -> Dict[str, Any]:
        """
        获取适应统计信息

        Returns:
            统计信息
        """
        if not self.adaptation_history:
            return {
                "total_adaptations": 0,
                "successful_adaptations": 0,
                "success_rate": 0.0,
                "average_improvement": 0.0,
                "by_strategy": {},
            }

        total = len(self.adaptation_history)
        successful = sum(1 for a in self.adaptation_history if a.success)

        # 按策略统计
        by_strategy: Dict[str, Dict[str, Any]] = {}
        for result in self.adaptation_history:
            strategy = result.proposal.strategy.value
            if strategy not in by_strategy:
                by_strategy[strategy] = {
                    "count": 0,
                    "successful": 0,
                    "total_improvement": 0.0,
                }

            by_strategy[strategy]["count"] += 1
            if result.success:
                by_strategy[strategy]["successful"] += 1
                by_strategy[strategy]["total_improvement"] += result.actual_improvement

        # 计算平均值
        for stats in by_strategy.values():
            stats["success_rate"] = stats["successful"] / stats["count"]
            stats["average_improvement"] = (
                stats["total_improvement"] / stats["successful"]
                if stats["successful"] > 0 else 0.0
            )

        return {
            "total_adaptations": total,
            "successful_adaptations": successful,
            "success_rate": successful / total,
            "average_improvement": sum(
                a.actual_improvement for a in self.adaptation_history if a.success
            ) / successful if successful > 0 else 0.0,
            "by_strategy": by_strategy,
        }

    def _update_performance_metrics(self, metrics: Dict[str, float]) -> None:
        """更新性能指标"""
        for key, value in metrics.items():
            if key not in self.performance_metrics:
                self.performance_metrics[key] = []

            self.performance_metrics[key].append(value)

            # 限制历史长度
            if len(self.performance_metrics[key]) > self.max_history_size:
                self.performance_metrics[key] = self.performance_metrics[key][-self.max_history_size:]

    def _check_adaptation_triggers(
        self,
        current_metrics: Dict[str, float],
        thresholds: Dict[str, float],
    ) -> Optional[AdaptationTrigger]:
        """
        检查适应触发条件

        Returns:
            触发器（如果没有触发，返回 None）
        """
        for key, current_value in current_metrics.items():
            if key in thresholds:
                threshold = thresholds[key]

                # 获取历史平均值
                if key in self.performance_metrics and len(self.performance_metrics[key]) > 5:
                    history_avg = sum(self.performance_metrics[key][-5:]) / 5

                    # 性能下降
                    if current_value < threshold and current_value < history_avg * 0.9:
                        return AdaptationTrigger.PERFORMANCE_DEGRADATION

        return None

    def _generate_proposals(
        self,
        trigger: AdaptationTrigger,
        current_metrics: Dict[str, float],
        adaptation_strategies: List[Callable],
    ) -> List[AdaptationProposal]:
        """
        生成适应提案
        """
        proposals = []

        for strategy_fn in adaptation_strategies:
            try:
                proposal = strategy_fn(trigger, current_metrics, self.performance_metrics)
                if proposal:
                    proposals.append(proposal)
            except Exception as e:
                # 记录错误但继续
                continue

        return proposals

    def _select_best_proposal(self, proposals: List[AdaptationProposal]) -> AdaptationProposal:
        """
        选择最佳提案
        """
        # 按置信度和预期改进排序
        scored_proposals = [
            (p, p.confidence * p.expected_improvement * (1 if p.risk_level == "low" else 0.5))
            for p in proposals
        ]

        scored_proposals.sort(key=lambda x: x[1], reverse=True)

        return scored_proposals[0][0]

    def _execute_adaptation(
        self,
        proposal: AdaptationProposal,
        current_metrics: Dict[str, float],
    ) -> AdaptationResult:
        """
        执行适应
        """
        start_time = time.time()

        try:
            # 应用修改
            if proposal.strategy == AdaptationStrategy.PROMPT_OPTIMIZATION:
                # TODO: 实现提示词更新
                success = True
            elif proposal.strategy == AdaptationStrategy.KNOWLEDGE_UPDATE:
                # TODO: 实现知识库更新
                success = True
            else:
                success = False

            # 计算实际改进
            actual_improvement = 0.0  # TODO: 实现改进计算

            return AdaptationResult(
                proposal=proposal,
                success=success,
                actual_improvement=actual_improvement,
                side_effects=[],
                timestamp=time.time(),
                validation_score=0.0,
            )

        except Exception as e:
            return AdaptationResult(
                proposal=proposal,
                success=False,
                actual_improvement=0.0,
                side_effects=[str(e)],
                timestamp=time.time(),
                validation_score=0.0,
            )

    def _generate_optimized_prompt(
        self,
        task_type: str,
        current_prompt: str,
        performance_history: List[float],
    ) -> str:
        """
        生成优化的提示词
        """
        # TODO: 实现智能提示词优化
        # 可以基于:
        # 1. 历史成功案例
        # 2. LLM 生成优化建议
        # 3. A/B 测试结果

        return current_prompt  # 默认返回原提示词

    def _load_knowledge_base(self) -> None:
        """加载知识库"""
        if not self.knowledge_base_path:
            return

        kb_path = Path(self.knowledge_base_path)
        if not kb_path.exists():
            return

        with open(kb_path, "r") as f:
            data = json.load(f)

        # TODO: 加载历史记录
        # self.adaptation_history = [AdaptationResult(**item) for item in data.get("adaptations", [])]

    def _save_knowledge_base(self) -> None:
        """保存知识库"""
        if not self.knowledge_base_path:
            return

        kb_path = Path(self.knowledge_base_path)
        kb_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "adaptations": [
                {
                    "strategy": r.proposal.strategy.value,
                    "success": r.success,
                    "improvement": r.actual_improvement,
                    "timestamp": r.timestamp,
                }
                for r in self.adaptation_history[-self.max_history_size:]
            ],
            "performance_metrics": self.performance_metrics,
        }

        with open(kb_path, "w") as f:
            json.dump(data, f, indent=2)
