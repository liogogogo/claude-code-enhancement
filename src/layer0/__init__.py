"""
Layer 0: 基础设施层（Infrastructure Layer）

本层提供底层工具和平台依赖，不涉及智能能力，纯粹的工具封装。

职责:
- 封装外部工具（Docker、Linter、测试框架）
- 提供统一的工具接口
- 处理平台相关的细节

注意: 本层不包含任何智能能力，仅作为上层的基础设施
"""

from .execution_sandbox import ExecutionSandbox, ExecutionEnvironment, ExecutionResult
from .linting_tools import LintingFeedback, LinterType, LintResult, LintIssue
from .test_frameworks import TestVerification, TestFramework, TestResult, TestCase

__all__ = [
    "ExecutionSandbox",
    "ExecutionEnvironment",
    "ExecutionResult",
    "LintingFeedback",
    "LinterType",
    "LintResult",
    "LintIssue",
    "TestVerification",
    "TestFramework",
    "TestResult",
    "TestCase",
]
