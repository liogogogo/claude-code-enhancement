"""
LLM 增强的错误分析器 - 用智能分析替代硬编码关键词匹配

核心功能：
1. 使用 LLM 分析错误模式
2. 从历史错误中学习
3. 生成上下文感知的修复建议
4. 关联到知识库中的历史解决方案

解决现有问题：
- ErrorAnalyzer 只用简单关键词匹配
- 无法理解复杂错误场景
- 无法利用历史知识
"""

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class ErrorAnalysis:
    """错误分析结果"""
    error_type: str                    # 错误类型分类
    root_cause: str                    # 根本原因
    severity: str                      # 严重程度: critical, high, medium, low
    affected_components: List[str]     # 受影响的组件
    fix_suggestions: List[str]         # 修复建议
    related_history: List[Dict]        # 相关历史记录
    confidence: float                  # 置信度
    reasoning: str                     # 分析推理过程


class LLMErrorAnalyzer:
    """
    LLM 增强的错误分析器

    使用 LLM 进行深度错误分析，而非简单的关键词匹配。
    """

    def __init__(
        self,
        memory_path: Optional[Path] = None,
        llm_client: Optional[Any] = None,
    ):
        """
        初始化 LLM 错误分析器

        Args:
            memory_path: 记忆存储路径
            llm_client: LLM 客户端（可选，用于高级分析）
        """
        self.memory_path = memory_path or Path.home() / ".claude" / "memory"
        self.llm_client = llm_client

        # 错误知识库
        self.error_knowledge = self._load_error_knowledge()

        # 错误模式识别规则（作为后备）
        self.fallback_patterns = {
            "syntax_error": {
                "patterns": [r"SyntaxError", r"syntax error", r"unexpected token", r"unexpected EOF"],
                "type": "syntax",
                "severity": "critical",
                "suggestions": ["检查语法错误", "确保括号/引号匹配", "运行 linter 检查"],
            },
            "import_error": {
                "patterns": [r"ImportError", r"ModuleNotFoundError", r"No module named"],
                "type": "dependency",
                "severity": "high",
                "suggestions": ["安装缺失依赖", "检查导入路径", "验证虚拟环境"],
            },
            "type_error": {
                "patterns": [r"TypeError", r"type error", r"unsupported operand"],
                "type": "type",
                "severity": "high",
                "suggestions": ["检查变量类型", "添加类型检查", "使用类型注解"],
            },
            "attribute_error": {
                "patterns": [r"AttributeError", r"has no attribute", r"object has no"],
                "type": "attribute",
                "severity": "medium",
                "suggestions": ["检查对象属性", "添加 hasattr 检查", "验证对象类型"],
            },
            "key_error": {
                "patterns": [r"KeyError", r"key not found"],
                "type": "data",
                "severity": "medium",
                "suggestions": ["检查字典键", "使用 .get() 方法", "添加默认值"],
            },
            "file_error": {
                "patterns": [r"FileNotFoundError", r"No such file", r"Permission denied"],
                "type": "file",
                "severity": "high",
                "suggestions": ["检查文件路径", "验证文件权限", "创建必要目录"],
            },
            "test_failure": {
                "patterns": [r"FAILED", r"AssertionError", r"test failed", r"expected"],
                "type": "test",
                "severity": "medium",
                "suggestions": ["检查断言条件", "验证预期值", "查看测试输出详情"],
            },
            "network_error": {
                "patterns": [r"ConnectionError", r"timeout", r"network", r"connection refused"],
                "type": "network",
                "severity": "high",
                "suggestions": ["检查网络连接", "验证 URL 地址", "添加重试逻辑"],
            },
        }

    def analyze(
        self,
        error_output: str,
        context: Optional[Dict[str, Any]] = None,
        use_llm: bool = True,
    ) -> ErrorAnalysis:
        """
        分析错误输出

        Args:
            error_output: 错误输出文本
            context: 上下文信息（代码、文件、命令等）
            use_llm: 是否使用 LLM 进行深度分析

        Returns:
            错误分析结果
        """
        context = context or {}

        # 1. 首先尝试从知识库匹配
        history_match = self._search_history(error_output)

        # 2. 使用模式匹配作为后备
        pattern_match = self._pattern_analysis(error_output)

        # 3. 如果有 LLM 客户端，进行深度分析
        llm_analysis = None
        if use_llm and self.llm_client:
            llm_analysis = self._llm_analysis(error_output, context)

        # 4. 综合结果
        if llm_analysis:
            return llm_analysis
        elif history_match:
            return self._build_from_history(history_match, error_output)
        else:
            return pattern_match

    def _load_error_knowledge(self) -> List[Dict]:
        """加载错误知识库"""
        error_file = self.memory_path / "error_knowledge.json"
        if error_file.exists():
            try:
                return json.loads(error_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                pass
        return []

    def _search_history(self, error_output: str) -> List[Dict]:
        """从历史记录中搜索相似错误"""
        matches = []

        for entry in self.error_knowledge:
            # 计算相似度
            similarity = self._calculate_similarity(
                error_output,
                entry.get("error_pattern", ""),
            )

            if similarity > 0.3:
                entry["similarity"] = similarity
                matches.append(entry)

        # 按相似度排序
        matches.sort(key=lambda x: x.get("similarity", 0), reverse=True)
        return matches[:5]

    def _pattern_analysis(self, error_output: str) -> ErrorAnalysis:
        """使用模式规则分析错误"""
        error_lower = error_output.lower()

        # 检查每个模式
        for error_name, config in self.fallback_patterns.items():
            for pattern in config["patterns"]:
                if re.search(pattern, error_output, re.IGNORECASE):
                    return ErrorAnalysis(
                        error_type=config["type"],
                        root_cause=self._extract_root_cause(error_output, error_name),
                        severity=config["severity"],
                        affected_components=self._extract_components(error_output),
                        fix_suggestions=config["suggestions"],
                        related_history=[],
                        confidence=0.8,
                        reasoning=f"Matched pattern: {error_name}",
                    )

        # 未知错误类型
        return ErrorAnalysis(
            error_type="unknown",
            root_cause="无法识别错误类型",
            severity="medium",
            affected_components=[],
            fix_suggestions=["查看错误详情", "检查日志", "搜索解决方案"],
            related_history=[],
            confidence=0.3,
            reasoning="No matching pattern found",
        )

    def _llm_analysis(
        self,
        error_output: str,
        context: Dict[str, Any],
    ) -> Optional[ErrorAnalysis]:
        """使用 LLM 进行深度分析"""
        if not self.llm_client:
            return None

        # 构建 prompt
        prompt = self._build_analysis_prompt(error_output, context)

        try:
            # 调用 LLM
            response = self._call_llm(prompt)

            # 解析结果
            return self._parse_llm_response(response)
        except Exception:
            return None

    def _build_analysis_prompt(self, error_output: str, context: Dict) -> str:
        """构建分析 prompt"""
        prompt_parts = [
            "Analyze the following error and provide:",
            "1. Error type classification",
            "2. Root cause",
            "3. Severity (critical/high/medium/low)",
            "4. Fix suggestions (list)",
            "",
            "Error output:",
            "```",
            error_output[:2000],  # 限制长度
            "```",
        ]

        if context:
            prompt_parts.append("")
            prompt_parts.append("Context:")
            if context.get("command"):
                prompt_parts.append(f"Command: {context['command']}")
            if context.get("file"):
                prompt_parts.append(f"File: {context['file']}")
            if context.get("language"):
                prompt_parts.append(f"Language: {context['language']}")

        prompt_parts.append("")
        prompt_parts.append("Respond in JSON format:")
        prompt_parts.append('{"error_type": "...", "root_cause": "...", "severity": "...", "suggestions": ["..."]}')

        return "\n".join(prompt_parts)

    def _call_llm(self, prompt: str) -> str:
        """调用 LLM"""
        if not self.llm_client:
            return "{}"

        # 根据客户端类型调用
        if hasattr(self.llm_client, "messages") and hasattr(self.llm_client.messages, "create"):
            # Anthropic 客户端
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-6-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        elif hasattr(self.llm_client, "chat") and hasattr(self.llm_client.chat, "completions"):
            # OpenAI 客户端
            response = self.llm_client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content

        return "{}"

    def _parse_llm_response(self, response: str) -> ErrorAnalysis:
        """解析 LLM 响应"""
        try:
            # 尝试提取 JSON
            json_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())

                return ErrorAnalysis(
                    error_type=data.get("error_type", "unknown"),
                    root_cause=data.get("root_cause", ""),
                    severity=data.get("severity", "medium"),
                    affected_components=[],
                    fix_suggestions=data.get("suggestions", []),
                    related_history=[],
                    confidence=0.9,
                    reasoning="LLM analysis",
                )
        except (json.JSONDecodeError, AttributeError):
            pass

        return None

    def _build_from_history(
        self,
        history_matches: List[Dict],
        error_output: str,
    ) -> ErrorAnalysis:
        """从历史记录构建分析结果"""
        best_match = history_matches[0]

        suggestions = []
        for entry in history_matches:
            if entry.get("suggestion"):
                suggestions.append(entry["suggestion"])

        # 去重
        suggestions = list(dict.fromkeys(suggestions))

        return ErrorAnalysis(
            error_type=best_match.get("error_type", "unknown"),
            root_cause=best_match.get("context", "Unknown cause"),
            severity="medium",
            affected_components=[],
            fix_suggestions=suggestions[:5] if suggestions else ["检查历史记录中的解决方案"],
            related_history=history_matches,
            confidence=best_match.get("similarity", 0.5),
            reasoning="Matched from history",
        )

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        # 使用关键词重叠
        words1 = set(re.findall(r"\w+", text1.lower()))
        words2 = set(re.findall(r"\w+", text2.lower()))

        if not words1 or not words2:
            return 0.0

        intersection = words1 & words2
        union = words1 | words2

        return len(intersection) / len(union)

    def _extract_root_cause(self, error_output: str, error_name: str) -> str:
        """提取根本原因"""
        # 尝试提取错误行
        lines = error_output.split("\n")
        for line in lines:
            if "error" in line.lower() or "exception" in line.lower():
                return line.strip()[:200]

        return f"Detected {error_name}"

    def _extract_components(self, error_output: str) -> List[str]:
        """提取受影响的组件"""
        components = []

        # 提取文件路径
        file_patterns = [
            r'File "([^"]+)"',
            r'([/\w]+\.\w+):',
            r'in ([/\w]+\.\w+)',
        ]

        for pattern in file_patterns:
            matches = re.findall(pattern, error_output)
            components.extend(matches[:3])

        # 提取函数名
        func_pattern = r'in (\w+)\('
        funcs = re.findall(func_pattern, error_output)
        components.extend(funcs[:3])

        return list(dict.fromkeys(components))[:5]

    def record_error(
        self,
        error_output: str,
        fix_applied: Optional[str] = None,
        success: Optional[bool] = None,
    ):
        """
        记录错误和修复结果

        Args:
            error_output: 错误输出
            fix_applied: 应用的修复
            success: 修复是否成功
        """
        entry = {
            "error_pattern": error_output[:500],
            "error_type": self._pattern_analysis(error_output).error_type,
            "timestamp": datetime.now().isoformat(),
            "fix_applied": fix_applied,
            "success": success,
        }

        # 添加到知识库
        self.error_knowledge.append(entry)

        # 保存
        self._save_error_knowledge()

    def _save_error_knowledge(self):
        """保存错误知识库"""
        self.memory_path.mkdir(parents=True, exist_ok=True)
        error_file = self.memory_path / "error_knowledge.json"

        # 保留最近 500 条
        knowledge = self.error_knowledge[-500:]

        error_file.write_text(
            json.dumps(knowledge, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )


def analyze_error(
    error_output: str,
    context: Optional[Dict[str, Any]] = None,
    llm_client: Optional[Any] = None,
) -> ErrorAnalysis:
    """
    便捷函数：分析错误

    Args:
        error_output: 错误输出
        context: 上下文
        llm_client: LLM 客户端

    Returns:
        错误分析结果
    """
    analyzer = LLMErrorAnalyzer(llm_client=llm_client)
    return analyzer.analyze(error_output, context)