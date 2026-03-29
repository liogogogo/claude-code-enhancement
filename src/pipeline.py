"""
增强管道 - 串联 Layer 0-3 的数据流

实现闭环：Layer 0 → Layer 1 → Layer 2 → Layer 3 → Layer 0
"""

from pathlib import Path
from typing import Any, Dict, Optional, Callable
from dataclasses import dataclass, field
import time

from .interfaces import (
    Layer0Output,
    Layer1Output,
    Layer2Output,
    Layer3Output,
    PipelineContext,
    PipelineStage,
    AnalysisFinding,
    ActionStep,
)

# Layer 0
from .layer0 import ExecutionSandbox, ExecutionEnvironment

# Layer 1
from .layer1.observation import Observer, ObservationType, ObservationResult
from .layer1.action import Actor, ActionType, ActionResult
from .layer1.feedback import FeedbackCollector, FeedbackType

# Layer 2
from .layer2.error_learning import ErrorLearningModule
from .layer2.advanced_reasoning import MultiStepReasoner

# Layer 3
from .layer3.adaptation_engine import AdaptationEngine
from .layer3.evolution_tracker import EvolutionTracker

# Memory
from .memory.personal_memory import PersonalMemory


class EnhancementPipeline:
    """
    增强管道 - 四层闭环

    数据流:
    ┌─────────────────────────────────────────────────────────┐
    │                                                          │
    │   Layer 0: 工具执行                                      │
    │   └─→ ExecutionSandbox, LintingTools, TestFrameworks    │
    │                                                          │
    │   Layer 1: 感知行动                                      │
    │   └─→ Observer, Actor, FeedbackCollector                │
    │                                                          │
    │   Layer 2: 认知分析                                      │
    │   └─→ ErrorLearningModule, MultiStepReasoner             │
    │                                                          │
    │   Layer 3: 元认知决策                                    │
    │   └─→ AdaptationEngine, EvolutionTracker                │
    │                                                          │
    │   → 回到 Layer 0 执行决策                                │
    │                                                          │
    └─────────────────────────────────────────────────────────┘
    """

    def __init__(self, project_path: Path, use_docker: bool = False):
        """
        初始化管道

        Args:
            project_path: 项目路径
            use_docker: 是否使用 Docker 沙箱（需要 Docker 环境）
        """
        self.project_path = Path(project_path)

        # Layer 0: 基础设施 (延迟初始化)
        self.sandbox = None
        self.linter = None
        self.tester = None
        self._use_docker = use_docker

        # Layer 1: 感知行动
        self.observer = Observer()
        self.actor = Actor()
        self.feedback = FeedbackCollector()

        # Layer 2: 认知能力
        self.error_learner = ErrorLearningModule()
        self.reasoner = MultiStepReasoner()

        # Layer 3: 元认知
        self.adaptation = AdaptationEngine()
        self.evolution = EvolutionTracker()

        # Memory
        self.memory = PersonalMemory()

        # 运行统计
        self.stats = {
            "total_runs": 0,
            "successful_runs": 0,
            "layer_stats": {
                "layer0": {"calls": 0, "successes": 0},
                "layer1": {"calls": 0, "successes": 0},
                "layer2": {"calls": 0, "successes": 0},
                "layer3": {"calls": 0, "successes": 0},
            },
        }

    def run(self, task: str, context: Optional[Dict[str, Any]] = None) -> Layer3Output:
        """
        运行完整管道

        Args:
            task: 任务描述
            context: 额外上下文

        Returns:
            Layer3Output: 最终决策
        """
        self.stats["total_runs"] += 1

        # 初始化管道上下文
        pipeline_ctx = PipelineContext(
            task=task,
            project_path=str(self.project_path),
        )

        try:
            # === Layer 0: 执行工具 ===
            layer0_output = self._run_layer0(task, context or {})
            pipeline_ctx.layer0_output = layer0_output
            pipeline_ctx.record_stage(PipelineStage.LAYER0_OUTPUT, layer0_output)

            # === Layer 1: 感知 ===
            layer1_output = self._run_layer1(layer0_output, context or {})
            pipeline_ctx.layer1_output = layer1_output
            pipeline_ctx.record_stage(PipelineStage.LAYER1_OUTPUT, layer1_output)

            # === Layer 2: 认知分析 ===
            layer2_output = self._run_layer2(layer1_output, context or {})
            pipeline_ctx.layer2_output = layer2_output
            pipeline_ctx.record_stage(PipelineStage.LAYER2_OUTPUT, layer2_output)

            # === Layer 3: 元认知决策 ===
            layer3_output = self._run_layer3(layer2_output, pipeline_ctx)
            pipeline_ctx.layer3_output = layer3_output
            pipeline_ctx.record_stage(PipelineStage.LAYER3_OUTPUT, layer3_output)

            self.stats["successful_runs"] += 1

            return layer3_output

        except Exception as e:
            # 返回错误决策
            return Layer3Output(
                decision="error",
                reasoning=f"Pipeline error: {str(e)}",
                confidence=0.0,
            )

    def _run_layer0(
        self,
        task: str,
        context: Dict[str, Any],
    ) -> Layer0Output:
        """
        Layer 0: 执行工具

        根据任务类型选择合适的工具执行
        """
        self.stats["layer_stats"]["layer0"]["calls"] += 1

        start_time = time.time()

        # 判断任务类型
        if "test" in task.lower():
            # 执行测试 (简化实现)
            try:
                from .layer0.test_frameworks import TestVerification, TestFramework
                if self.tester is None:
                    self.tester = TestVerification(TestFramework.PYTEST)
                result = self.tester.run_tests(str(self.project_path))
                output = Layer0Output(
                    tool_name="test",
                    success=result.passed > 0 and result.failed == 0,
                    output=f"Passed: {result.passed}, Failed: {result.failed}",
                    errors=[tc.name for tc in result.test_cases if tc.status.value == "failed"],
                    metrics={"pass_rate": result.passed / max(result.total, 1)},
                    execution_time=time.time() - start_time,
                )
            except Exception as e:
                output = Layer0Output(
                    tool_name="test",
                    success=False,
                    output="",
                    errors=[str(e)],
                    metrics={},
                    execution_time=time.time() - start_time,
                )

        elif "lint" in task.lower() or "check" in task.lower():
            # 执行 Lint (简化实现)
            try:
                from .layer0.linting_tools import LintingFeedback, LinterType
                if self.linter is None:
                    self.linter = LintingFeedback(LinterType.RUFF)
                # 读取项目代码进行 lint
                py_files = list(self.project_path.glob("**/*.py"))[:5]
                all_issues = []
                for py_file in py_files:
                    try:
                        code = py_file.read_text()
                        result = self.linter.check_code(code, py_file.name)
                        all_issues.extend([issue.message for issue in result.issues])
                    except Exception:
                        pass
                output = Layer0Output(
                    tool_name="lint",
                    success=len(all_issues) == 0,
                    output=f"Issues found: {len(all_issues)}",
                    errors=all_issues[:10],
                    metrics={"issue_count": len(all_issues)},
                    execution_time=time.time() - start_time,
                )
            except Exception as e:
                output = Layer0Output(
                    tool_name="lint",
                    success=False,
                    output="",
                    errors=[str(e)],
                    metrics={},
                    execution_time=time.time() - start_time,
                )

        else:
            # 默认：观察项目状态
            output = Layer0Output(
                tool_name="observe",
                success=True,
                output="Project observation completed",
                errors=[],
                metrics={},
                execution_time=time.time() - start_time,
            )

        if output.success:
            self.stats["layer_stats"]["layer0"]["successes"] += 1

        return output

    def _run_layer1(
        self,
        layer0_output: Layer0Output,
        context: Dict[str, Any],
    ) -> Layer1Output:
        """
        Layer 1: 感知

        观察 Layer 0 的执行结果，提取有意义的信息
        """
        self.stats["layer_stats"]["layer1"]["calls"] += 1

        # 根据工具类型选择观察类型
        if layer0_output.tool_name == "test":
            obs_type = ObservationType.TEST_RESULT
            data = {
                "passed": layer0_output.metrics.get("pass_rate", 0) > 0.5,
                "pass_rate": layer0_output.metrics.get("pass_rate", 0),
                "failures": layer0_output.errors,
            }
        elif layer0_output.tool_name == "lint":
            obs_type = ObservationType.LINT_RESULT
            data = {
                "clean": layer0_output.success,
                "errors": layer0_output.metrics.get("error_count", 0),
                "error_list": layer0_output.errors,
            }
        else:
            obs_type = ObservationType.CODE_STATE
            data = {
                "tool": layer0_output.tool_name,
                "success": layer0_output.success,
            }

        # 使用 Observer 进行观察
        obs_result = self.observer.observe(obs_type, context)

        output = Layer1Output(
            observation_type=obs_type.value,
            data=data,
            confidence=obs_result.confidence,
            action_taken=None,
            feedback={"layer0_success": layer0_output.success},
        )

        self.stats["layer_stats"]["layer1"]["successes"] += 1
        return output

    def _run_layer2(
        self,
        layer1_output: Layer1Output,
        context: Dict[str, Any],
    ) -> Layer2Output:
        """
        Layer 2: 认知分析

        分析 Layer 1 的感知结果，找出问题和建议
        """
        self.stats["layer_stats"]["layer2"]["calls"] += 1

        findings: list[AnalysisFinding] = []
        suggestions: list[str] = []

        # 分析测试结果
        if layer1_output.observation_type == "test_result":
            if not layer1_output.data.get("passed", True):
                failures = layer1_output.data.get("failures", [])
                for failure in failures[:3]:  # 只分析前3个失败
                    findings.append(AnalysisFinding(
                        finding_type="error",
                        description=f"Test failure: {failure}",
                        severity=0.8,
                    ))
                suggestions.append("Fix failing tests before proceeding")

        # 分析 Lint 结果
        elif layer1_output.observation_type == "lint_result":
            if not layer1_output.data.get("clean", True):
                errors = layer1_output.data.get("error_list", [])
                for error in errors[:3]:
                    findings.append(AnalysisFinding(
                        finding_type="error",
                        description=f"Lint error: {error}",
                        severity=0.6,
                    ))
                suggestions.append("Fix lint errors for code quality")

        # 计算置信度
        confidence = 0.9 if findings else 0.5

        output = Layer2Output(
            analysis_type=f"{layer1_output.observation_type}_analysis",
            findings=findings,
            suggestions=suggestions,
            confidence=confidence,
            knowledge_updates={},
            reasoning_trace=[f"Analyzed {layer1_output.observation_type}"],
        )

        self.stats["layer_stats"]["layer2"]["successes"] += 1
        return output

    def _run_layer3(
        self,
        layer2_output: Layer2Output,
        pipeline_ctx: PipelineContext,
    ) -> Layer3Output:
        """
        Layer 3: 元认知决策

        基于 Layer 2 的分析做出决策
        """
        self.stats["layer_stats"]["layer3"]["calls"] += 1

        # 根据分析结果做决策
        if not layer2_output.findings:
            # 没有问题，可以继续
            decision = "execute"
            reasoning = "No issues found, proceeding with execution"
            action_plan = [
                ActionStep(
                    step_type="continue",
                    description="Continue with planned action",
                )
            ]
            confidence = 0.9

        elif any(f.severity > 0.7 for f in layer2_output.findings):
            # 有严重问题，需要修复
            decision = "modify"
            reasoning = "Critical issues found, modification required"
            action_plan = [
                ActionStep(
                    step_type="fix",
                    description="Fix critical issues",
                    parameters={"issues": [f.description for f in layer2_output.findings if f.severity > 0.7]},
                )
            ]
            confidence = 0.85

        else:
            # 有小问题，可以继续但要注意
            decision = "execute"
            reasoning = "Minor issues found, proceeding with caution"
            action_plan = [
                ActionStep(
                    step_type="note",
                    description="Note issues for later",
                    parameters={"issues": [f.description for f in layer2_output.findings]},
                )
            ]
            confidence = 0.7

        output = Layer3Output(
            decision=decision,
            action_plan=action_plan,
            reasoning=reasoning,
            confidence=confidence,
            learning_update={"findings_count": len(layer2_output.findings)},
        )

        # 记录到进化追踪器（简化版本）
        # EvolutionTracker 用于追踪进化过程，这里记录决策
        try:
            self.evolution.record_generation(
                generation=pipeline_ctx.iteration,
                metrics={"confidence": output.confidence, "decision": output.decision},
            )
        except Exception:
            pass  # 进化追踪是可选的

        self.stats["layer_stats"]["layer3"]["successes"] += 1
        return output

    def run_iteration(self, task: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        运行一次完整迭代（包括执行决策后的反馈）

        这是一个完整的闭环：
        Layer 0 → Layer 1 → Layer 2 → Layer 3 → Layer 0
        """
        # 运行管道
        decision = self.run(task, context)

        # 执行决策
        if decision.decision == "execute":
            # 执行计划
            for step in decision.action_plan:
                self.actor.act(
                    ActionType.COMMAND_EXECUTION,
                    {"command": step.description},
                )

        # 收集反馈
        try:
            feedback = self.feedback.collect_feedback(
                FeedbackType.EXECUTION,
                {"decision": decision.decision, "success": decision.confidence > 0.5},
            )
        except Exception:
            feedback = {"type": "execution", "success": decision.confidence > 0.5}

        # 学习
        if decision.learning_update:
            # 记录学习数据（简化版本）
            self.memory.record_command(
                command=f"pipeline:{decision.decision}",
                success=decision.confidence > 0.5,
                context=decision.reasoning[:100] if decision.reasoning else "",
            )

        return {
            "decision": decision.to_dict(),
            "feedback": feedback,
            "stats": self.stats,
        }

    def get_stats(self) -> Dict[str, Any]:
        """获取运行统计"""
        return self.stats.copy()