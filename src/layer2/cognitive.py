"""
Layer 2: 认知能力层（简化版）

核心功能：
- 错误分析
- 推理引擎
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
from datetime import datetime
import json
from pathlib import Path


class ErrorSeverity(Enum):
    """错误严重程度"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class AnalysisResult:
    """分析结果"""
    success: bool
    findings: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    confidence: float = 0.0
    reasoning_trace: List[str] = field(default_factory=list)


class ErrorAnalyzer:
    """
    错误分析器

    功能：
    - 分析错误模式
    - 生成修复建议
    """

    def __init__(self, knowledge_path: Optional[Path] = None):
        self.knowledge_path = knowledge_path or Path.home() / ".claude" / "error_knowledge.json"
        self.error_history: List[Dict[str, Any]] = []
        self._load_knowledge()

    def analyze(
        self,
        error_output: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> AnalysisResult:
        """分析错误输出"""
        findings = []
        suggestions = []
        trace = []

        error_lower = error_output.lower()

        # 模式匹配分析
        if "test" in error_lower and ("fail" in error_lower or "error" in error_lower):
            findings.append({
                "type": "test_failure",
                "message": "Test failure detected",
                "severity": ErrorSeverity.HIGH.value,
            })
            suggestions.append("Run tests with verbose output to see details")
            trace.append("Detected test failure pattern")

        if "lint" in error_lower or "error:" in error_lower:
            findings.append({
                "type": "lint_error",
                "message": "Lint error detected",
                "severity": ErrorSeverity.MEDIUM.value,
            })
            suggestions.append("Fix lint errors for code quality")
            trace.append("Detected lint error pattern")

        if "syntax" in error_lower or "syntaxerror" in error_lower:
            findings.append({
                "type": "syntax_error",
                "message": "Syntax error detected",
                "severity": ErrorSeverity.CRITICAL.value,
            })
            suggestions.append("Fix syntax errors before running")
            trace.append("Detected syntax error pattern")

        if "import" in error_lower and "error" in error_lower:
            findings.append({
                "type": "import_error",
                "message": "Import error detected",
                "severity": ErrorSeverity.HIGH.value,
            })
            suggestions.append("Check if required packages are installed")
            trace.append("Detected import error pattern")

        confidence = 0.9 if findings else 0.5

        return AnalysisResult(
            success=len(findings) == 0,
            findings=findings,
            suggestions=suggestions,
            confidence=confidence,
            reasoning_trace=trace,
        )

    def _load_knowledge(self):
        """加载历史知识"""
        if self.knowledge_path.exists():
            try:
                data = json.loads(self.knowledge_path.read_text())
                self.error_history = data.get("errors", [])
            except Exception:
                pass

    def _save_knowledge(self):
        """保存知识"""
        self.knowledge_path.parent.mkdir(parents=True, exist_ok=True)
        data = {"errors": self.error_history[-100:]}
        self.knowledge_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))


class ReasoningEngine:
    """推理引擎"""

    def reason(
        self,
        problem: str,
        context: Dict[str, Any],
    ) -> AnalysisResult:
        """执行推理"""
        trace = []
        findings = []
        suggestions = []

        trace.append(f"Analyzing: {problem[:100]}")

        if context.get("errors"):
            trace.append("Found errors in context")
            findings.append({
                "type": "context_error",
                "message": f"Found {len(context['errors'])} errors",
                "severity": ErrorSeverity.HIGH.value,
            })

        if context.get("test_results"):
            passed = context["test_results"].get("passed", 0)
            failed = context["test_results"].get("failed", 0)
            trace.append(f"Tests: {passed} passed, {failed} failed")
            if failed > 0:
                suggestions.append(f"Fix {failed} failing test(s)")

        return AnalysisResult(
            success=len(findings) == 0,
            findings=findings,
            suggestions=suggestions,
            confidence=0.8 if findings else 0.5,
            reasoning_trace=trace,
        )


__all__ = [
    "ErrorSeverity",
    "AnalysisResult",
    "ErrorAnalyzer",
    "ReasoningEngine",
]