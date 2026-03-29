"""
自我修改引擎 - 核心模块
整合三层架构，实现自我修改和优化
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import json
from pathlib import Path

from src.layer1.execution_sandbox import ExecutionSandbox, ExecutionEnvironment
from src.layer1.linting_feedback import LintingFeedback, LinterType
from src.layer1.test_verification import TestVerification, TestFramework
from src.layer2.error_learning import ErrorLearningModule, ErrorContext
from src.layer2.contrastive_learning import ContrastiveLearningModule, CodePair
from src.layer2.feedback_loop import FeedbackLoop, FeedbackItem
from src.layer3.adaptation_engine import AdaptationEngine, AdaptationProposal
from src.layer3.evolution_tracker import EvolutionTracker, EvolutionMetric


class ModificationType(Enum):
    """修改类型"""
    PROMPT_UPDATE = "prompt_update"  # 提示词更新
    KNOWLEDGE_ADDITION = "knowledge_addition"  # 知识添加
    STRATEGY_ADJUSTMENT = "strategy_adjustment"  # 策略调整
    ARCHITECTURE_CHANGE = "architecture_change"  # 架构变更


@dataclass
class ModificationProposal:
    """修改提案"""
    modification_type: ModificationType
    description: str
    changes: Dict[str, Any]
    justification: str  # 修改理由
    expected_impact: str  # 预期影响
    safety_score: float  # 安全评分 [0, 1]
    rollback_plan: Optional[str] = None


@dataclass
class ModificationResult:
    """修改结果"""
    proposal: ModificationProposal
    success: bool
    actual_impact: Dict[str, float]
    side_effects: List[str]
    validation_passed: bool


class SelfModificationEngine:
    """
    自我修改引擎

    整合三层架构:
    - Layer 1: 工具增强（执行、Linting、测试）
    - Layer 2: 自我纠错（错误学习、对比学习、反馈循环）
    - Layer 3: 自我迭代（适应引擎、进化追踪）

    功能:
    - 分析当前性能
    - 生成修改提案
    - 评估安全性
    - 执行修改
    - 验证效果
    - 必要时回滚
    """

    def __init__(
        self,
        knowledge_base_path: Optional[str] = None,
        enable_layer1: bool = True,
        enable_layer2: bool = True,
        enable_layer3: bool = True,
    ):
        """
        初始化自我修改引擎

        Args:
            knowledge_base_path: 知识库路径
            enable_layer1: 启用 Layer 1
            enable_layer2: 启用 Layer 2
            enable_layer3: 启用 Layer 3
        """
        self.knowledge_base_path = knowledge_base_path

        # Layer 1: 工具增强
        self.enable_layer1 = enable_layer1
        if enable_layer1:
            self.execution_sandbox = ExecutionSandbox()
            self.linting_feedback = {}  # language -> LintingFeedback
            self.test_verification = {}  # framework -> TestVerification

        # Layer 2: 自我纠错
        self.enable_layer2 = enable_layer2
        if enable_layer2:
            self.error_learning = ErrorLearningModule(knowledge_base_path)
            self.contrastive_learning = None  # Lazy initialization
            self.feedback_loop = FeedbackLoop()

        # Layer 3: 自我迭代
        self.enable_layer3 = enable_layer3
        if enable_layer3:
            self.adaptation_engine = AdaptationEngine(knowledge_base_path)
            self.evolution_tracker = EvolutionTracker(knowledge_base_path)

        # 修改历史
        self.modification_history: List[ModificationResult] = []

    def analyze_and_propose(
        self,
        task: str,
        current_performance: Dict[str, float],
        target_performance: Dict[str, float],
    ) -> List[ModificationProposal]:
        """
        分析当前状态并生成修改提案

        Args:
            task: 任务描述
            current_performance: 当前性能指标
            target_performance: 目标性能指标

        Returns:
            修改提案列表
        """
        proposals = []

        # 1. 分析性能差距
        gaps = self._analyze_performance_gaps(current_performance, target_performance)

        # 2. Layer 3: 适应引擎分析
        if self.enable_layer3:
            adaptation_proposals = self._generate_adaptation_proposals(gaps)
            proposals.extend(adaptation_proposals)

        # 3. Layer 2: 错误学习分析
        if self.enable_layer2:
            error_proposals = self._generate_error_learning_proposals(gaps)
            proposals.extend(error_proposals)

        # 4. 生成综合提案
        if gaps:
            proposals.append(self._generate_comprehensive_proposal(gaps))

        # 按安全评分和预期影响排序
        proposals.sort(
            key=lambda p: (p.safety_score, sum(p.expected_impact.split("%")[0].split("+")[-1] for _ in [0])),
            reverse=True,
        )

        return proposals

    def apply_modification(
        self,
        proposal: ModificationProposal,
        validation_fn: Optional[Callable] = None,
    ) -> ModificationResult:
        """
        应用修改

        Args:
            proposal: 修改提案
            validation_fn: 验证函数（可选）

        Returns:
            修改结果
        """
        # 1. 安全检查
        if not self._check_safety(proposal):
            return ModificationResult(
                proposal=proposal,
                success=False,
                actual_impact={},
                side_effects=["安全检查失败"],
                validation_passed=False,
            )

        # 2. 创建回滚点
        rollback_snapshot = self._create_snapshot()

        try:
            # 3. 执行修改
            self._execute_modification(proposal)

            # 4. 验证效果
            validation_passed = True
            if validation_fn:
                validation_passed = validation_fn()

            # 5. 测量影响
            actual_impact = self._measure_impact(proposal)

            # 6. 记录历史
            result = ModificationResult(
                proposal=proposal,
                success=True,
                actual_impact=actual_impact,
                side_effects=[],
                validation_passed=validation_passed,
            )

            self.modification_history.append(result)

            # Layer 3: 记录进化
            if self.enable_layer3:
                self.evolution_tracker.record_generation(
                    metrics=actual_impact,
                    changes=[proposal.description],
                )

            return result

        except Exception as e:
            # 回滚
            self._rollback(rollback_snapshot)

            return ModificationResult(
                proposal=proposal,
                success=False,
                actual_impact={},
                side_effects=[str(e)],
                validation_passed=False,
            )

    def is_safe(self, proposal: ModificationProposal) -> bool:
        """
        检查提案是否安全

        Args:
            proposal: 修改提案

        Returns:
            是否安全
        """
        # 安全评分阈值
        SAFETY_THRESHOLD = 0.7

        if proposal.safety_score < SAFETY_THRESHOLD:
            return False

        # 检查是否有回滚计划
        if not proposal.rollback_plan and proposal.modification_type in [
            ModificationType.ARCHITECTURE_CHANGE,
            ModificationType.STRATEGY_ADJUSTMENT,
        ]:
            return False

        # TODO: 更详细的安全检查
        # - 语法分析
        # - 依赖检查
        # - 影响范围分析

        return True

    def get_performance_summary(self) -> Dict[str, Any]:
        """
        获取性能摘要

        Returns:
            性能摘要
        """
        summary = {
            "total_modifications": len(self.modification_history),
            "successful_modifications": sum(
                1 for m in self.modification_history if m.success
            ),
        }

        # Layer 2: 错误学习统计
        if self.enable_layer2:
            summary["error_learning"] = self.error_learning.get_statistics()

        # Layer 3: 进化统计
        if self.enable_layer3:
            summary["evolution"] = self.evolution_tracker.generate_report()
            summary["adaptation"] = self.adaptation_engine.get_adaptation_statistics()

        return summary

    def _analyze_performance_gaps(
        self,
        current: Dict[str, float],
        target: Dict[str, float],
    ) -> Dict[str, float]:
        """分析性能差距"""
        gaps = {}

        for key, target_value in target.items():
            if key in current:
                current_value = current[key]
                gap = target_value - current_value

                if gap > 0.01:  # 至少1%的差距
                    gaps[key] = gap

        return gaps

    def _generate_adaptation_proposals(
        self,
        gaps: Dict[str, float],
    ) -> List[ModificationProposal]:
        """生成适应提案"""
        proposals = []

        # 提示词优化
        if "task_success_rate" in gaps:
            proposals.append(ModificationProposal(
                modification_type=ModificationType.PROMPT_UPDATE,
                description="优化代码生成提示词",
                changes={"prompt_type": "code_generation"},
                justification=f"任务成功率低于目标 {gaps['task_success_rate']:.1%}",
                expected_impact=f"+{gaps['task_success_rate'] * 0.5:.1%}",
                safety_score=0.9,
                rollback_plan="恢复前一版本提示词",
            ))

        return proposals

    def _generate_error_learning_proposals(
        self,
        gaps: Dict[str, float],
    ) -> List[ModificationProposal]:
        """生成错误学习提案"""
        proposals = []

        # 知识添加
        if "fix_success_rate" in gaps:
            proposals.append(ModificationProposal(
                modification_type=ModificationType.KNOWLEDGE_ADDITION,
                description="添加历史错误修复案例到知识库",
                changes={"knowledge_type": "error_fixes"},
                justification=f"修复成功率低于目标 {gaps['fix_success_rate']:.1%}",
                expected_impact=f"+{gaps['fix_success_rate'] * 0.3:.1%}",
                safety_score=0.95,
                rollback_plan="移除新增知识条目",
            ))

        return proposals

    def _generate_comprehensive_proposal(
        self,
        gaps: Dict[str, float],
    ) -> ModificationProposal:
        """生成综合提案"""
        return ModificationProposal(
            modification_type=ModificationType.STRATEGY_ADJUSTMENT,
            description="综合优化: 提示词 + 知识库 + 策略",
            changes={"optimization": "comprehensive"},
            justification=f"多项指标未达标: {', '.join(gaps.keys())}",
            expected_impact="综合提升",
            safety_score=0.8,
            rollback_plan="完整回滚所有修改",
        )

    def _check_safety(self, proposal: ModificationProposal) -> bool:
        """检查安全性"""
        # 使用 is_safe 方法
        return self.is_safe(proposal)

    def _create_snapshot(self) -> Dict[str, Any]:
        """创建快照用于回滚"""
        # TODO: 实现完整快照
        return {"timestamp": "now"}

    def _execute_modification(self, proposal: ModificationProposal) -> None:
        """执行修改"""
        # TODO: 实现修改执行
        # 根据修改类型应用不同的修改逻辑
        pass

    def _rollback(self, snapshot: Dict[str, Any]) -> None:
        """回滚到快照"""
        # TODO: 实现回滚逻辑
        pass

    def _measure_impact(self, proposal: ModificationProposal) -> Dict[str, float]:
        """测量修改影响"""
        # TODO: 实现影响测量
        # 返回关键指标的变化
        return {}
