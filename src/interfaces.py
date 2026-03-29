"""
层数据接口 - 定义各层之间的数据传递格式

这些接口确保 Layer 0-3 之间的数据流清晰、类型安全。
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime


class PipelineStage(Enum):
    """管道阶段"""
    LAYER0_INPUT = "layer0_input"
    LAYER0_OUTPUT = "layer0_output"
    LAYER1_OUTPUT = "layer1_output"
    LAYER2_OUTPUT = "layer2_output"
    LAYER3_OUTPUT = "layer3_output"


@dataclass
class Layer0Output:
    """
    Layer 0 输出 - 工具执行结果

    由 ExecutionSandbox、LintingTools、TestFrameworks 产生
    """
    tool_name: str  # 工具名称: "execution", "lint", "test"
    success: bool
    output: str
    errors: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "tool_name": self.tool_name,
            "success": self.success,
            "output": self.output,
            "errors": self.errors,
            "metrics": self.metrics,
            "execution_time": self.execution_time,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Layer0Output":
        return cls(
            tool_name=data["tool_name"],
            success=data["success"],
            output=data["output"],
            errors=data.get("errors", []),
            metrics=data.get("metrics", {}),
            execution_time=data.get("execution_time", 0.0),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
        )


@dataclass
class Layer1Output:
    """
    Layer 1 输出 - 感知结果

    由 Observer、Actor、FeedbackCollector 产生
    """
    observation_type: str  # "code_state", "test_result", "lint_result", "action_result"
    data: Dict[str, Any]
    confidence: float = 1.0
    action_taken: Optional[str] = None  # 如果执行了动作，记录动作类型
    feedback: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "observation_type": self.observation_type,
            "data": self.data,
            "confidence": self.confidence,
            "action_taken": self.action_taken,
            "feedback": self.feedback,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Layer1Output":
        return cls(
            observation_type=data["observation_type"],
            data=data["data"],
            confidence=data.get("confidence", 1.0),
            action_taken=data.get("action_taken"),
            feedback=data.get("feedback"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
        )


@dataclass
class AnalysisFinding:
    """分析发现"""
    finding_type: str  # "error", "warning", "suggestion", "insight"
    description: str
    location: Optional[str] = None  # 文件路径或代码位置
    severity: float = 0.5  # 0-1
    related_code: Optional[str] = None


@dataclass
class Layer2Output:
    """
    Layer 2 输出 - 认知分析结果

    由 ErrorLearner、MultiStepReasoner、KnowledgeTransfer 产生
    """
    analysis_type: str  # "error_analysis", "reasoning", "knowledge_extraction"
    findings: List[AnalysisFinding] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence: float = 0.0
    knowledge_updates: Dict[str, Any] = field(default_factory=dict)
    reasoning_trace: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "analysis_type": self.analysis_type,
            "findings": [
                {
                    "finding_type": f.finding_type,
                    "description": f.description,
                    "location": f.location,
                    "severity": f.severity,
                    "related_code": f.related_code,
                }
                for f in self.findings
            ],
            "suggestions": self.suggestions,
            "confidence": self.confidence,
            "knowledge_updates": self.knowledge_updates,
            "reasoning_trace": self.reasoning_trace,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Layer2Output":
        findings = [
            AnalysisFinding(
                finding_type=f["finding_type"],
                description=f["description"],
                location=f.get("location"),
                severity=f.get("severity", 0.5),
                related_code=f.get("related_code"),
            )
            for f in data.get("findings", [])
        ]
        return cls(
            analysis_type=data["analysis_type"],
            findings=findings,
            suggestions=data.get("suggestions", []),
            confidence=data.get("confidence", 0.0),
            knowledge_updates=data.get("knowledge_updates", {}),
            reasoning_trace=data.get("reasoning_trace", []),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
        )


@dataclass
class ActionStep:
    """行动步骤"""
    step_type: str  # "code_change", "test_run", "file_operation"
    description: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    expected_outcome: Optional[str] = None


@dataclass
class Layer3Output:
    """
    Layer 3 输出 - 元认知决策

    由 AdaptationEngine、EvolutionTracker 产生
    """
    decision: str  # "execute", "modify", "rollback", "learn"
    action_plan: List[ActionStep] = field(default_factory=list)
    reasoning: str = ""
    confidence: float = 0.0
    learning_update: Optional[Dict[str, Any]] = None
    strategy_update: Optional[Dict[str, Any]] = None
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "decision": self.decision,
            "action_plan": [
                {
                    "step_type": s.step_type,
                    "description": s.description,
                    "parameters": s.parameters,
                    "expected_outcome": s.expected_outcome,
                }
                for s in self.action_plan
            ],
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "learning_update": self.learning_update,
            "strategy_update": self.strategy_update,
            "timestamp": self.timestamp.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Layer3Output":
        action_plan = [
            ActionStep(
                step_type=s["step_type"],
                description=s["description"],
                parameters=s.get("parameters", {}),
                expected_outcome=s.get("expected_outcome"),
            )
            for s in data.get("action_plan", [])
        ]
        return cls(
            decision=data["decision"],
            action_plan=action_plan,
            reasoning=data.get("reasoning", ""),
            confidence=data.get("confidence", 0.0),
            learning_update=data.get("learning_update"),
            strategy_update=data.get("strategy_update"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if "timestamp" in data else datetime.now(),
        )


@dataclass
class PipelineContext:
    """
    管道上下文 - 贯穿整个流程的共享状态
    """
    task: str  # 用户任务描述
    project_path: str
    layer0_output: Optional[Layer0Output] = None
    layer1_output: Optional[Layer1Output] = None
    layer2_output: Optional[Layer2Output] = None
    layer3_output: Optional[Layer3Output] = None
    iteration: int = 0
    max_iterations: int = 3
    history: List[Dict[str, Any]] = field(default_factory=list)

    def record_stage(self, stage: PipelineStage, output: Any):
        """记录阶段输出"""
        self.history.append({
            "stage": stage.value,
            "output": output.to_dict() if hasattr(output, 'to_dict') else str(output),
            "timestamp": datetime.now().isoformat(),
        })

    def to_dict(self) -> dict:
        return {
            "task": self.task,
            "project_path": self.project_path,
            "layer0_output": self.layer0_output.to_dict() if self.layer0_output else None,
            "layer1_output": self.layer1_output.to_dict() if self.layer1_output else None,
            "layer2_output": self.layer2_output.to_dict() if self.layer2_output else None,
            "layer3_output": self.layer3_output.to_dict() if self.layer3_output else None,
            "iteration": self.iteration,
            "max_iterations": self.max_iterations,
            "history": self.history,
        }