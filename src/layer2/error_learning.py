"""
错误学习模块 - Layer 2 核心模块
从错误中学习，实现自动修复
"""

import json
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import numpy as np


class ErrorType(Enum):
    """错误类型分类"""
    SYNTAX_ERROR = "syntax_error"
    RUNTIME_ERROR = "runtime_error"
    LOGIC_ERROR = "logic_error"
    TYPE_ERROR = "type_error"
    IMPORT_ERROR = "import_error"
    COMPILATION_ERROR = "compilation_error"
    TEST_FAILURE = "test_failure"
    LINT_ERROR = "lint_error"


class ErrorSeverity(Enum):
    """错误严重程度"""
    CRITICAL = "critical"  # 阻塞执行
    HIGH = "high"  # 严重影响功能
    MEDIUM = "medium"  # 影响部分功能
    LOW = "low"  # 轻微问题
    INFO = "info"  # 建议性改进


@dataclass
class ErrorContext:
    """错误上下文"""
    language: str
    code: str
    file_path: str
    line_number: int
    function_name: Optional[str] = None
    stack_trace: Optional[str] = None


@dataclass
class ErrorInstance:
    """错误实例"""
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    context: ErrorContext
    fix_suggestion: Optional[str] = None
    confidence: float = 0.0  # 修复建议的置信度


@dataclass
class FixAttempt:
    """修复尝试记录"""
    original_code: str
    fixed_code: str
    error_instance: ErrorInstance
    success: bool
    validation_result: Optional[str] = None
    timestamp: str = ""  # ISO format timestamp


class ErrorLearningModule:
    """
    错误学习模块

    功能:
    - 错误分类和聚类
    - 从历史错误中学习
    - 生成智能修复建议
    - 跟踪修复成功率
    """

    def __init__(self, knowledge_base_path: Optional[str] = None):
        """
        初始化错误学习模块

        Args:
            knowledge_base_path: 错误知识库路径
        """
        self.knowledge_base_path = knowledge_base_path
        self.error_history: List[FixAttempt] = []
        self.error_patterns: Dict[str, List[ErrorInstance]] = {}

        # 加载历史知识库
        if knowledge_base_path:
            self._load_knowledge_base()

    def classify_error(
        self,
        error_message: str,
        context: ErrorContext,
    ) -> ErrorInstance:
        """
        分类错误

        Args:
            error_message: 错误消息
            context: 错误上下文

        Returns:
            ErrorInstance: 分类后的错误实例
        """
        # 基于规则和机器学习分类错误类型
        error_type = self._classify_error_type(error_message, context)
        severity = self._classify_severity(error_message, error_type)

        # 生成修复建议
        fix_suggestion, confidence = self._generate_fix_suggestion(
            error_type,
            error_message,
            context,
        )

        return ErrorInstance(
            error_type=error_type,
            severity=severity,
            message=error_message,
            context=context,
            fix_suggestion=fix_suggestion,
            confidence=confidence,
        )

    def learn_from_fix(
        self,
        error_instance: ErrorInstance,
        original_code: str,
        fixed_code: str,
        success: bool,
    ) -> None:
        """
        从修复中学习

        Args:
            error_instance: 错误实例
            original_code: 原始代码
            fixed_code: 修复后的代码
            success: 修复是否成功
        """
        from datetime import datetime

        attempt = FixAttempt(
            original_code=original_code,
            fixed_code=fixed_code,
            error_instance=error_instance,
            success=success,
            timestamp=datetime.now().isoformat(),
        )

        self.error_history.append(attempt)

        # 更新错误模式
        if success:
            self._update_error_patterns(error_instance)

    def suggest_fix(self, error_instance: ErrorInstance) -> str:
        """
        建议修复方案

        Args:
            error_instance: 错误实例

        Returns:
            修复后的代码
        """
        # 查找相似的历史错误
        similar_errors = self._find_similar_errors(error_instance)

        if similar_errors:
            # 基于历史成功修复生成建议
            best_fix = self._select_best_fix(similar_errors)
            return best_fix.fixed_code

        # 使用规则生成修复
        return self._apply_rule_based_fix(error_instance)

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取错误统计信息

        Returns:
            统计信息字典
        """
        if not self.error_history:
            return {
                "total_attempts": 0,
                "success_rate": 0.0,
                "error_types": {},
                "most_common_errors": [],
            }

        total_attempts = len(self.error_history)
        successful_attempts = sum(1 for a in self.error_history if a.success)

        # 按错误类型统计
        error_type_counts: Dict[str, int] = {}
        for attempt in self.error_history:
            error_type = attempt.error_instance.error_type.value
            error_type_counts[error_type] = error_type_counts.get(error_type, 0) + 1

        # 最常见的错误
        most_common = sorted(
            error_type_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )[:5]

        return {
            "total_attempts": total_attempts,
            "success_rate": successful_attempts / total_attempts,
            "error_types": error_type_counts,
            "most_common_errors": most_common,
        }

    def _classify_error_type(
        self,
        error_message: str,
        context: ErrorContext,
    ) -> ErrorType:
        """
        分类错误类型

        基于错误消息和上下文进行分类
        """
        error_lower = error_message.lower()

        # 语法错误
        if any(keyword in error_lower for keyword in [
            "syntax error", "parse error", "unexpected token",
            "invalid syntax", "syntaxerror"
        ]):
            return ErrorType.SYNTAX_ERROR

        # 类型错误
        if any(keyword in error_lower for keyword in [
            "type error", "cannot use", "type mismatch",
            "cannot convert", "incompatible types"
        ]):
            return ErrorType.TYPE_ERROR

        # 导入错误
        if any(keyword in error_lower for keyword in [
            "import error", "module not found", "no module named",
            "undefined", "not declared"
        ]):
            return ErrorType.IMPORT_ERROR

        # 运行时错误
        if any(keyword in error_lower for keyword in [
            "runtime error", "panic", "exception",
            "null pointer", "nil pointer"
        ]):
            return ErrorType.RUNTIME_ERROR

        # 编译错误
        if any(keyword in error_lower for keyword in [
            "compilation error", "build error", "linker error"
        ]):
            return ErrorType.COMPILATION_ERROR

        # 默认为逻辑错误
        return ErrorType.LOGIC_ERROR

    def _classify_severity(
        self,
        error_message: str,
        error_type: ErrorType,
    ) -> ErrorSeverity:
        """
        分类错误严重程度
        """
        # 关键错误类型默认为高严重程度
        if error_type in [ErrorType.SYNTAX_ERROR, ErrorType.COMPILATION_ERROR]:
            return ErrorSeverity.CRITICAL

        # 运行时错误通常为高严重程度
        if error_type == ErrorType.RUNTIME_ERROR:
            return ErrorSeverity.HIGH

        # Lint 错误通常为低严重程度
        if error_type == ErrorType.LINT_ERROR:
            return ErrorSeverity.LOW

        return ErrorSeverity.MEDIUM

    def _generate_fix_suggestion(
        self,
        error_type: ErrorType,
        error_message: str,
        context: ErrorContext,
    ) -> Tuple[Optional[str], float]:
        """
        生成修复建议和置信度
        """
        # 查找历史相似错误
        similar_errors = self._find_similar_errors_by_type(error_type)

        if similar_errors:
            # 计算平均置信度
            avg_confidence = np.mean([e.confidence for e in similar_errors])

            # 选择最成功的修复
            successful_fixes = [
                e for e in similar_errors
                if e.fix_suggestion and e.confidence > 0.7
            ]

            if successful_fixes:
                best_suggestion = successful_fixes[0].fix_suggestion
                return best_suggestion, avg_confidence

        # 使用规则生成建议
        rule_suggestion = self._generate_rule_based_suggestion(
            error_type, error_message, context
        )
        return rule_suggestion, 0.6

    def _generate_rule_based_suggestion(
        self,
        error_type: ErrorType,
        error_message: str,
        context: ErrorContext,
    ) -> Optional[str]:
        """
        基于规则生成修复建议
        """
        suggestions = {
            ErrorType.SYNTAX_ERROR: "检查语法错误，确保所有括号、引号匹配",
            ErrorType.TYPE_ERROR: "检查类型匹配，确保变量类型正确",
            ErrorType.IMPORT_ERROR: "检查导入路径，确保依赖已安装",
            ErrorType.RUNTIME_ERROR: "检查空指针、数组越界等运行时问题",
            ErrorType.COMPILATION_ERROR: "检查编译错误，确保所有依赖正确",
            ErrorType.LOGIC_ERROR: "检查算法逻辑，确保实现符合预期",
            ErrorType.TEST_FAILURE: "检查测试用例，确保实现符合测试要求",
            ErrorType.LINT_ERROR: "遵循 Linter 建议，修复代码风格问题",
        }

        return suggestions.get(error_type)

    def _find_similar_errors(self, error: ErrorInstance) -> List[FixAttempt]:
        """
        查找相似的历史错误
        """
        similar = []

        for attempt in self.error_history:
            # 简单的相似度判断：同类型 + 相似消息
            if attempt.error_instance.error_type == error.error_type:
                # TODO: 实现更复杂的相似度计算（如嵌入向量）
                similar.append(attempt)

        return similar

    def _find_similar_errors_by_type(self, error_type: ErrorType) -> List[ErrorInstance]:
        """
        按类型查找相似错误
        """
        # 从历史记录中查找同类型的错误
        similar = []
        for attempt in self.error_history:
            if attempt.error_instance.error_type == error_type:
                similar.append(attempt.error_instance)

        return similar

    def _select_best_fix(self, similar_errors: List[FixAttempt]) -> FixAttempt:
        """
        选择最佳修复方案
        """
        # 选择成功的修复中置信度最高的
        successful = [e for e in similar_errors if e.success]

        if not successful:
            # 如果没有成功的，返回最近的
            return similar_errors[-1]

        # 按置信度排序
        return max(successful, key=lambda x: x.error_instance.confidence)

    def _apply_rule_based_fix(self, error: ErrorInstance) -> str:
        """
        应用基于规则的修复
        """
        # TODO: 实现规则引擎
        return error.context.code  # 默认返回原代码

    def _update_error_patterns(self, error: ErrorInstance) -> None:
        """
        更新错误模式
        """
        error_key = f"{error.error_type.value}:{error.message[:50]}"

        if error_key not in self.error_patterns:
            self.error_patterns[error_key] = []

        self.error_patterns[error_key].append(error)

    def _load_knowledge_base(self) -> None:
        """
        加载知识库
        """
        if not self.knowledge_base_path:
            return

        kb_path = Path(self.knowledge_base_path)
        if not kb_path.exists():
            return

        with open(kb_path, "r") as f:
            data = json.load(f)

        # TODO: 加载历史错误数据
        # self.error_history = [FixAttempt(**item) for item in data.get("fixes", [])]

    def _save_knowledge_base(self) -> None:
        """
        保存知识库
        """
        if not self.knowledge_base_path:
            return

        kb_path = Path(self.knowledge_base_path)
        kb_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "fixes": [asdict(attempt) for attempt in self.error_history],
            "patterns": {
                k: [asdict(e) for e in v]
                for k, v in self.error_patterns.items()
            },
        }

        with open(kb_path, "w") as f:
            json.dump(data, f, indent=2)
