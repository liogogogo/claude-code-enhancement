"""
反馈循环模块 - Layer 2 核心模块
实现多轮反馈和自我纠错
"""

from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import time


class FeedbackType(Enum):
    """反馈类型"""
    CODE_QUALITY = "code_quality"  # 代码质量反馈
    TEST_RESULT = "test_result"  # 测试结果反馈
    LINT_ERROR = "lint_error"  # Lint 错误反馈
    USER_FEEDBACK = "user_feedback"  # 用户反馈
    PERFORMANCE = "performance"  # 性能反馈


class FeedbackAction(Enum):
    """反馈动作"""
    IGNORE = "ignore"  # 忽略
    RETRY = "retry"  # 重试
    FIX = "fix"  # 修复
    REFACTOR = "refactor"  # 重构
    ESCALATE = "escalate"  # 升级（人工介入）


@dataclass
class FeedbackItem:
    """反馈项"""
    feedback_type: FeedbackType
    content: str
    severity: str  # "low", "medium", "high", "critical"
    source: str  # 反馈来源
    metadata: Dict[str, Any]  # 额外元数据
    timestamp: float


@dataclass
class FixProposal:
    """修复提案"""
    action: FeedbackAction
    description: str
    code_changes: Optional[Dict[str, str]]  # {"file_path": "new_code"}
    confidence: float
    estimated_time: float  # 预计修复时间（秒）


@dataclass
class IterationResult:
    """迭代结果"""
    iteration_number: int
    success: bool
    feedback_received: List[FeedbackItem]
    fixes_applied: List[FixProposal]
    final_state: Dict[str, Any]
    time_elapsed: float


class FeedbackLoop:
    """
    反馈循环系统

    功能:
    - 收集多源反馈
    - 分析反馈并生成修复提案
    - 应用修复并验证
    - 迭代直到满足条件
    """

    def __init__(
        self,
        max_iterations: int = 5,
        timeout: float = 300.0,  # 5分钟
        improvement_threshold: float = 0.1,  # 10%改进
    ):
        """
        初始化反馈循环

        Args:
            max_iterations: 最大迭代次数
            timeout: 超时时间（秒）
            improvement_threshold: 改进阈值（低于此值停止迭代）
        """
        self.max_iterations = max_iterations
        self.timeout = timeout
        self.improvement_threshold = improvement_threshold

        self.feedback_history: List[FeedbackItem] = []
        self.iteration_history: List[IterationResult] = []

    def run_iteration(
        self,
        initial_code: Dict[str, str],
        feedback_sources: List[Callable],
        fix_generators: List[Callable],
        validators: List[Callable],
    ) -> IterationResult:
        """
        运行反馈循环迭代

        Args:
            initial_code: 初始代码 {"file_path": "code"}
            feedback_sources: 反馈源函数列表
            fix_generators: 修复生成器函数列表
            validators: 验证器函数列表

        Returns:
            IterationResult: 最终迭代结果
        """
        start_time = time.time()
        current_code = initial_code.copy()

        for iteration in range(1, self.max_iterations + 1):
            # 检查超时
            if time.time() - start_time > self.timeout:
                break

            # 1. 收集反馈
            feedback = self._collect_feedback(current_code, feedback_sources)

            # 2. 分析反馈并生成修复提案
            proposals = self._generate_fix_proposals(feedback, fix_generators)

            # 3. 选择最佳修复方案
            best_proposal = self._select_best_proposal(proposals)

            if not best_proposal or best_proposal.action == FeedbackAction.IGNORE:
                # 无需修复，退出
                break

            # 4. 应用修复
            current_code = self._apply_fix(current_code, best_proposal)

            # 5. 验证修复
            validation_results = self._validate_fix(current_code, validators)

            # 6. 记录迭代结果
            iteration_result = IterationResult(
                iteration_number=iteration,
                success=all(validation_results),
                feedback_received=feedback,
                fixes_applied=[best_proposal],
                final_state={"code": current_code, "validation": validation_results},
                time_elapsed=time.time() - start_time,
            )

            self.iteration_history.append(iteration_result)

            # 如果验证通过，退出
            if iteration_result.success:
                break

        # 返回最终结果
        return self.iteration_history[-1] if self.iteration_history else IterationResult(
            iteration_number=0,
            success=False,
            feedback_received=[],
            fixes_applied=[],
            final_state={"code": current_code},
            time_elapsed=time.time() - start_time,
        )

    def _collect_feedback(
        self,
        code: Dict[str, str],
        feedback_sources: List[Callable],
    ) -> List[FeedbackItem]:
        """
        收集反馈

        Args:
            code: 当前代码
            feedback_sources: 反馈源函数列表

        Returns:
            反馈列表
        """
        all_feedback = []

        for source in feedback_sources:
            try:
                feedback = source(code)
                all_feedback.extend(feedback)
            except Exception as e:
                # 记录错误但继续
                all_feedback.append(FeedbackItem(
                    feedback_type=FeedbackType.USER_FEEDBACK,
                    content=f"反馈源错误: {str(e)}",
                    severity="medium",
                    source="feedback_loop",
                    metadata={},
                    timestamp=time.time(),
                ))

        # 按严重程度排序
        all_feedback.sort(key=lambda x: self._severity_order(x.severity), reverse=True)

        return all_feedback

    def _generate_fix_proposals(
        self,
        feedback: List[FeedbackItem],
        fix_generators: List[Callable],
    ) -> List[FixProposal]:
        """
        生成修复提案

        Args:
            feedback: 反馈列表
            fix_generators: 修复生成器函数列表

        Returns:
            修复提案列表
        """
        proposals = []

        for generator in fix_generators:
            try:
                generator_proposals = generator(feedback)
                proposals.extend(generator_proposals)
            except Exception as e:
                # 记录错误但继续
                continue

        # 按置信度排序
        proposals.sort(key=lambda x: x.confidence, reverse=True)

        return proposals

    def _select_best_proposal(self, proposals: List[FixProposal]) -> Optional[FixProposal]:
        """
        选择最佳修复提案

        Args:
            proposals: 修复提案列表

        Returns:
            最佳提案
        """
        if not proposals:
            return None

        # 选择置信度最高的提案
        return proposals[0]

    def _apply_fix(
        self,
        code: Dict[str, str],
        proposal: FixProposal,
    ) -> Dict[str, str]:
        """
        应用修复

        Args:
            code: 当前代码
            proposal: 修复提案

        Returns:
            修复后的代码
        """
        if not proposal.code_changes:
            return code

        new_code = code.copy()

        for file_path, new_content in proposal.code_changes.items():
            new_code[file_path] = new_content

        return new_code

    def _validate_fix(
        self,
        code: Dict[str, str],
        validators: List[Callable],
    ) -> List[bool]:
        """
        验证修复

        Args:
            code: 当前代码
            validators: 验证器函数列表

        Returns:
            验证结果列表
        """
        results = []

        for validator in validators:
            try:
                result = validator(code)
                results.append(result)
            except Exception as e:
                # 验证失败
                results.append(False)

        return results

    def _severity_order(self, severity: str) -> int:
        """
        严重程度排序

        Returns:
            排序值（越大越严重）
        """
        order = {
            "critical": 4,
            "high": 3,
            "medium": 2,
            "low": 1,
        }
        return order.get(severity, 0)

    def get_iteration_summary(self) -> Dict[str, Any]:
        """
        获取迭代摘要

        Returns:
            摘要信息
        """
        if not self.iteration_history:
            return {
                "total_iterations": 0,
                "successful": False,
                "total_time": 0.0,
                "total_fixes": 0,
            }

        last_iteration = self.iteration_history[-1]

        total_fixes = sum(len(it.fixes_applied) for it in self.iteration_history)
        total_time = sum(it.time_elapsed for it in self.iteration_history)

        return {
            "total_iterations": len(self.iteration_history),
            "successful": last_iteration.success,
            "total_time": total_time,
            "total_fixes": total_fixes,
            "final_iteration": last_iteration.iteration_number,
        }

    def visualize_iterations(self) -> str:
        """
        可视化迭代过程

        Returns:
            格式化的迭代过程字符串
        """
        if not self.iteration_history:
            return "无迭代记录"

        lines = []
        lines.append("=" * 60)
        lines.append("反馈循环迭代过程")
        lines.append("=" * 60)

        for it in self.iteration_history:
            status = "✓ 成功" if it.success else "✗ 失败"
            lines.append(f"\n迭代 {it.iteration_number}: {status}")
            lines.append(f"  时间: {it.time_elapsed:.2f}s")
            lines.append(f"  反馈数: {len(it.feedback_received)}")
            lines.append(f"  修复数: {len(it.fixes_applied)}")

            if it.feedback_received:
                lines.append("\n  主要反馈:")
                for fb in it.feedback_received[:3]:  # 显示前3个
                    lines.append(f"    - [{fb.severity}] {fb.content[:50]}...")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)
