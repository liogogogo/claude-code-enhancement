"""
实时 Linting 反馈 - Layer 1 核心模块
提供实时的代码质量反馈
"""

import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class LinterType(Enum):
    """支持的 Linter 类型"""
    GOLANGCI_LINT = "golangci-lint"
    SWIFTLINT = "swiftlint"
    RUFF = "ruff"  # Python
    ESLINT = "eslint"  # JavaScript/TypeScript


class LintSeverity(Enum):
    """问题严重程度"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    CONVENTION = "convention"


@dataclass
class LintIssue:
    """Lint 问题"""
    file: str
    line: int
    column: int
    severity: LintSeverity
    message: str
    rule_id: Optional[str] = None
    context: Optional[str] = None  # 问题代码片段


@dataclass
class LintResult:
    """Lint 结果"""
    success: bool
    issues: List[LintIssue]
    summary: Dict[str, int]  # {"error": 5, "warning": 10, ...}
    execution_time: float


class LintingFeedback:
    """
    实时 Linting 反馈系统

    功能:
    - 多语言 Linter 集成
    - 实时代码质量检测
    - 问题分类和优先级排序
    - 修复建议生成
    """

    def __init__(self, linter_type: LinterType):
        """
        初始化 Linting 反馈系统

        Args:
            linter_type: Linter 类型
        """
        self.linter_type = linter_type
        self._check_linter_available()

    def check_code(
        self,
        code: str,
        filename: str = "temp",
        working_dir: Optional[str] = None,
    ) -> LintResult:
        """
        检查代码质量

        Args:
            code: 要检查的代码
            filename: 文件名（用于确定检查规则）
            working_dir: 工作目录（某些 Linter 需要在项目根目录运行）

        Returns:
            LintResult: 检查结果
        """
        with tempfile.TemporaryDirectory() if not working_dir else tempfile.TemporaryDirectory() as temp_dir:
            # 如果没有提供工作目录，使用临时目录
            work_dir = working_dir or temp_dir

            # 写入代码文件
            code_file = self._prepare_code_file(work_dir, code, filename)

            # 执行 Linter
            try:
                issues = self._run_linter(code_file, work_dir)
                success = all(issue.severity != LintSeverity.ERROR for issue in issues)

                # 生成摘要
                summary = self._generate_summary(issues)

                return LintResult(
                    success=success,
                    issues=issues,
                    summary=summary,
                    execution_time=0.0,  # TODO: 实现精确计时
                )

            except Exception as e:
                return LintResult(
                    success=False,
                    issues=[],
                    summary={},
                    execution_time=0.0,
                )

    def generate_fix_suggestions(self, issues: List[LintIssue]) -> List[Dict[str, Any]]:
        """
        生成修复建议

        Args:
            issues: Lint 问题列表

        Returns:
            修复建议列表 [{"issue": ..., "suggestion": ..., "confidence": ...}]
        """
        suggestions = []

        for issue in issues:
            suggestion = {
                "issue": issue,
                "suggestion": self._generate_suggestion_for_issue(issue),
                "confidence": self._calculate_confidence(issue),
            }
            suggestions.append(suggestion)

        return suggestions

    def _check_linter_available(self):
        """检查 Linter 是否可用"""
        try:
            result = subprocess.run(
                [self.linter_type.value, "--version"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError(f"{self.linter_type.value} 不可用")
        except FileNotFoundError:
            raise RuntimeError(f"{self.linter_type.value} 未安装")

    def _prepare_code_file(self, work_dir: str, code: str, filename: str) -> Path:
        """准备代码文件"""
        # 添加适当的扩展名
        extensions = {
            LinterType.GOLANGCI_LINT: ".go",
            LinterType.SWIFTLINT: ".swift",
            LinterType.RUFF: ".py",
            LinterType.ESLINT: ".js",
        }

        ext = extensions.get(self.linter_type, "")
        filepath = Path(work_dir) / f"{filename}{ext}"

        with open(filepath, "w") as f:
            f.write(code)

        return filepath

    def _run_linter(self, code_file: Path, work_dir: str) -> List[LintIssue]:
        """运行 Linter"""
        if self.linter_type == LinterType.GOLANGCI_LINT:
            return self._run_golangci_lint(code_file, work_dir)
        elif self.linter_type == LinterType.SWIFTLINT:
            return self._run_swiftlint(code_file, work_dir)
        elif self.linter_type == LinterType.RUFF:
            return self._run_ruff(code_file, work_dir)
        elif self.linter_type == LinterType.ESLINT:
            return self._run_eslint(code_file, work_dir)
        else:
            raise NotImplementedError(f"不支持的 Linter: {self.linter_type}")

    def _run_golangci_lint(self, code_file: Path, work_dir: str) -> List[LintIssue]:
        """运行 golangci-lint"""
        result = subprocess.run(
            [
                "golangci-lint",
                "run",
                "--out-format", "json",
                str(code_file),
            ],
            cwd=work_dir,
            capture_output=True,
            text=True,
        )

        issues = []
        # TODO: 解析 JSON 输出
        # golangci-lint 的 JSON 输出格式较复杂，需要详细解析

        return issues

    def _run_swiftlint(self, code_file: Path, work_dir: str) -> List[LintIssue]:
        """运行 SwiftLint"""
        result = subprocess.run(
            [
                "swiftlint",
                "lint",
                "--reporter", "json",
                str(code_file),
            ],
            cwd=work_dir,
            capture_output=True,
            text=True,
        )

        issues = []
        # TODO: 解析 JSON 输出

        return issues

    def _run_ruff(self, code_file: Path, work_dir: str) -> List[LintIssue]:
        """运行 Ruff (Python)"""
        result = subprocess.run(
            [
                "ruff",
                "check",
                "--output-format", "json",
                str(code_file),
            ],
            cwd=work_dir,
            capture_output=True,
            text=True,
        )

        issues = []
        # TODO: 解析 JSON 输出

        return issues

    def _run_eslint(self, code_file: Path, work_dir: str) -> List[LintIssue]:
        """运行 ESLint"""
        result = subprocess.run(
            [
                "eslint",
                "--format", "json",
                str(code_file),
            ],
            cwd=work_dir,
            capture_output=True,
            text=True,
        )

        issues = []
        # TODO: 解析 JSON 输出

        return issues

    def _generate_summary(self, issues: List[LintIssue]) -> Dict[str, int]:
        """生成问题摘要"""
        summary = {
            "error": 0,
            "warning": 0,
            "info": 0,
            "convention": 0,
        }

        for issue in issues:
            summary[issue.severity.value] += 1

        return summary

    def _generate_suggestion_for_issue(self, issue: LintIssue) -> str:
        """为问题生成修复建议"""
        # TODO: 实现智能建议生成
        # 可以基于 Lint 规则数据库或 AI 模型

        if issue.rule_id == "unused":
            return f"删除未使用的变量/函数: {issue.context}"
        elif issue.rule_id == "fmt":
            return f"格式化代码以符合规范"
        else:
            return f"修复问题: {issue.message}"

    def _calculate_confidence(self, issue: LintIssue) -> float:
        """计算修复建议的置信度"""
        # TODO: 实现置信度计算
        # 可以基于历史修复成功率

        return 0.8
