"""
多文件推理模块 (Multi-File Reasoning)

功能:
- 分析文件间的依赖关系
- 追踪符号(函数/类/变量)的跨文件引用
- 预测修改的影响范围
- 建议需要同步修改的文件
- 构建项目依赖图

使用:
    from src.core.multi_file_reasoning import MultiFileReasoner

    reasoner = MultiFileReasoner("/path/to/project")
    reasoner.build_dependency_graph()

    # 分析修改影响
    impacts = reasoner.analyze_change("auth/login.ts", "add MFA support")

    # 追踪符号
    deps = reasoner.trace_symbol("UserSession")

    # 获取相关文件
    related = reasoner.get_related_files("auth/login.ts")
"""

import ast
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional


class DependencyType(Enum):
    """依赖类型"""

    IMPORT = "import"  # 导入依赖
    EXTENDS = "extends"  # 继承
    IMPLEMENTS = "implements"  # 实现
    CALLS = "calls"  # 函数调用
    USES = "uses"  # 使用类型/变量
    REFERENCES = "references"  # 引用


class ImpactLevel(Enum):
    """影响级别"""

    CRITICAL = "critical"  # 必须修改，否则会破坏
    HIGH = "high"  # 很可能需要修改
    MEDIUM = "medium"  # 可能需要修改
    LOW = "low"  # 可选修改


@dataclass
class Symbol:
    """符号定义"""

    name: str
    type: str  # function, class, variable, interface, type
    file_path: str
    line: int
    exported: bool = False
    signature: str = ""

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "type": self.type,
            "file_path": self.file_path,
            "line": self.line,
            "exported": self.exported,
            "signature": self.signature,
        }


@dataclass
class Dependency:
    """依赖关系"""

    source_file: str
    target_file: str
    dependency_type: DependencyType
    symbol: str
    line: int = 0

    def to_dict(self) -> dict:
        return {
            "source_file": self.source_file,
            "target_file": self.target_file,
            "dependency_type": self.dependency_type.value,
            "symbol": self.symbol,
            "line": self.line,
        }


@dataclass
class Impact:
    """影响分析结果"""

    file_path: str
    impact_level: ImpactLevel
    reason: str
    suggested_changes: list[str] = field(default_factory=list)
    symbols_affected: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "impact_level": self.impact_level.value,
            "reason": self.reason,
            "suggested_changes": self.suggested_changes,
            "symbols_affected": self.symbols_affected,
        }


@dataclass
class DependencyNode:
    """依赖图节点"""

    file_path: str
    imports: list[str] = field(default_factory=list)
    imported_by: list[str] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "file_path": self.file_path,
            "imports": self.imports,
            "imported_by": self.imported_by,
            "symbols": [s.to_dict() for s in self.symbols],
            "exports": self.exports,
        }


class MultiFileReasoner:
    """
    多文件推理器

    核心能力:
    1. 构建项目依赖图
    2. 追踪符号引用
    3. 分析修改影响
    4. 建议相关修改
    """

    def __init__(self, project_path: Path | str):
        """
        初始化推理器

        Args:
            project_path: 项目路径
        """
        self.project_path = Path(project_path)

        # 依赖图
        self.dependency_graph: dict[str, DependencyNode] = {}

        # 符号索引: name -> list[Symbol]
        self.symbol_index: dict[str, list[Symbol]] = defaultdict(list)

        # 文件内容缓存
        self._file_cache: dict[str, str] = {}

        # 分析配置
        self.supported_extensions = {
            ".py": self._analyze_python,
            ".ts": self._analyze_typescript,
            ".tsx": self._analyze_typescript,
            ".js": self._analyze_javascript,
            ".jsx": self._analyze_javascript,
            ".go": self._analyze_go,
            ".rs": self._analyze_rust,
        }

        self.exclude_patterns = [
            "node_modules",
            ".git",
            "__pycache__",
            "venv",
            "dist",
            "build",
            ".next",
            "vendor",
            "target",
        ]

    def build_dependency_graph(self) -> dict:
        """
        构建项目依赖图

        Returns:
            构建统计
        """
        stats = {
            "files_analyzed": 0,
            "dependencies_found": 0,
            "symbols_indexed": 0,
        }

        # 收集所有代码文件
        code_files = self._collect_code_files()

        # 分析每个文件
        for file_path in code_files:
            self._analyze_file(file_path)
            stats["files_analyzed"] += 1

        # 统计
        for node in self.dependency_graph.values():
            stats["dependencies_found"] += len(node.imports)
            stats["symbols_indexed"] += len(node.symbols)

        # 解析相对路径导入
        self._resolve_imports()

        return stats

    def _collect_code_files(self) -> list[Path]:
        """收集所有代码文件"""
        files = []

        for ext in self.supported_extensions:
            for file_path in self.project_path.rglob(f"*{ext}"):
                # 检查排除模式
                if any(pattern in str(file_path) for pattern in self.exclude_patterns):
                    continue
                files.append(file_path)

        return files

    def _analyze_file(self, file_path: Path):
        """分析单个文件"""
        ext = file_path.suffix
        rel_path = str(file_path.relative_to(self.project_path))

        # 读取文件内容
        try:
            content = file_path.read_text(encoding="utf-8")
            self._file_cache[rel_path] = content
        except Exception:
            return

        # 创建依赖节点
        node = DependencyNode(file_path=rel_path)

        # 使用对应语言的分析器
        analyzer = self.supported_extensions.get(ext)
        if analyzer:
            analyzer(content, rel_path, node)

        # 存储节点
        self.dependency_graph[rel_path] = node

        # 索引符号
        for symbol in node.symbols:
            self.symbol_index[symbol.name].append(symbol)

    def _analyze_python(self, content: str, file_path: str, node: DependencyNode):
        """分析 Python 文件"""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return

        for item in ast.walk(tree):
            # 导入语句
            if isinstance(item, ast.Import):
                for alias in item.names:
                    node.imports.append(alias.name)
            elif isinstance(item, ast.ImportFrom):
                module = item.module or ""
                node.imports.append(module)

            # 类定义
            elif isinstance(item, ast.ClassDef):
                symbol = Symbol(
                    name=item.name,
                    type="class",
                    file_path=file_path,
                    line=item.lineno,
                    exported=not item.name.startswith("_"),
                )
                node.symbols.append(symbol)
                if symbol.exported:
                    node.exports.append(item.name)

            # 函数定义
            elif isinstance(item, ast.FunctionDef) or isinstance(
                item, ast.AsyncFunctionDef
            ):
                symbol = Symbol(
                    name=item.name,
                    type="function",
                    file_path=file_path,
                    line=item.lineno,
                    exported=not item.name.startswith("_"),
                )
                node.symbols.append(symbol)

    def _analyze_typescript(self, content: str, file_path: str, node: DependencyNode):
        """分析 TypeScript 文件"""
        # 导入语句
        import_patterns = [
            r'import\s+.*?\s+from\s+["\']([^"\']+)["\']',
            r'import\s+["\']([^"\']+)["\']',
        ]

        for pattern in import_patterns:
            for match in re.finditer(pattern, content):
                node.imports.append(match.group(1))

        # 导出语句
        export_pattern = r'export\s+(?:default\s+)?(?:class|function|const|interface|type)\s+(\w+)'
        for match in re.finditer(export_pattern, content):
            node.exports.append(match.group(1))

        # 类定义
        class_pattern = r'(?:export\s+)?class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            node.symbols.append(
                Symbol(
                    name=match.group(1),
                    type="class",
                    file_path=file_path,
                    line=content[: match.start()].count("\n") + 1,
                    exported="export" in content[
                        max(0, match.start() - 20) : match.start()
                    ],
                )
            )

        # 函数定义
        func_pattern = r'(?:export\s+)?(?:async\s+)?function\s+(\w+)'
        for match in re.finditer(func_pattern, content):
            node.symbols.append(
                Symbol(
                    name=match.group(1),
                    type="function",
                    file_path=file_path,
                    line=content[: match.start()].count("\n") + 1,
                    exported="export" in content[
                        max(0, match.start() - 20) : match.start()
                    ],
                )
            )

        # 接口定义
        interface_pattern = r'(?:export\s+)?interface\s+(\w+)'
        for match in re.finditer(interface_pattern, content):
            node.symbols.append(
                Symbol(
                    name=match.group(1),
                    type="interface",
                    file_path=file_path,
                    line=content[: match.start()].count("\n") + 1,
                    exported="export" in content[
                        max(0, match.start() - 20) : match.start()
                    ],
                )
            )

        # 箭头函数 / const 函数
        arrow_pattern = r'(?:export\s+)?const\s+(\w+)\s*=\s*(?:async\s*)?\('
        for match in re.finditer(arrow_pattern, content):
            node.symbols.append(
                Symbol(
                    name=match.group(1),
                    type="function",
                    file_path=file_path,
                    line=content[: match.start()].count("\n") + 1,
                    exported="export" in content[
                        max(0, match.start() - 20) : match.start()
                    ],
                )
            )

    def _analyze_javascript(self, content: str, file_path: str, node: DependencyNode):
        """分析 JavaScript 文件 (复用 TypeScript 分析器)"""
        self._analyze_typescript(content, file_path, node)

    def _analyze_go(self, content: str, file_path: str, node: DependencyNode):
        """分析 Go 文件"""
        # 导入语句
        single_import = r'import\s+"([^"]+)"'
        multi_import = r'import\s+\(([^)]+)\)'

        for match in re.finditer(single_import, content):
            node.imports.append(match.group(1))

        for match in re.finditer(multi_import, content, re.DOTALL):
            imports_block = match.group(1)
            for imp in re.findall(r'"([^"]+)"', imports_block):
                node.imports.append(imp)

        # 结构体定义
        struct_pattern = r'type\s+(\w+)\s+struct'
        for match in re.finditer(struct_pattern, content):
            node.symbols.append(
                Symbol(
                    name=match.group(1),
                    type="class",
                    file_path=file_path,
                    line=content[: match.start()].count("\n") + 1,
                    exported=match.group(1)[0].isupper(),
                )
            )
            if match.group(1)[0].isupper():
                node.exports.append(match.group(1))

        # 函数定义
        func_pattern = r'func\s+(?:\([^)]+\)\s+)?(\w+)'
        for match in re.finditer(func_pattern, content):
            name = match.group(1)
            node.symbols.append(
                Symbol(
                    name=name,
                    type="function",
                    file_path=file_path,
                    line=content[: match.start()].count("\n") + 1,
                    exported=name[0].isupper(),
                )
            )

    def _analyze_rust(self, content: str, file_path: str, node: DependencyNode):
        """分析 Rust 文件"""
        # use 语句
        use_pattern = r'use\s+([^;]+);'
        for match in re.finditer(use_pattern, content):
            node.imports.append(match.group(1).strip())

        # 结构体
        struct_pattern = r'(?:pub\s+)?struct\s+(\w+)'
        for match in re.finditer(struct_pattern, content):
            node.symbols.append(
                Symbol(
                    name=match.group(1),
                    type="class",
                    file_path=file_path,
                    line=content[: match.start()].count("\n") + 1,
                    exported="pub" in content[max(0, match.start() - 10) : match.start()],
                )
            )

        # 函数
        fn_pattern = r'(?:pub\s+)?(?:async\s+)?fn\s+(\w+)'
        for match in re.finditer(fn_pattern, content):
            node.symbols.append(
                Symbol(
                    name=match.group(1),
                    type="function",
                    file_path=file_path,
                    line=content[: match.start()].count("\n") + 1,
                    exported="pub" in content[max(0, match.start() - 10) : match.start()],
                )
            )

    def _resolve_imports(self):
        """解析导入路径到实际文件"""
        for file_path, node in self.dependency_graph.items():
            resolved_imports = []

            for imp in node.imports:
                # 尝试解析相对路径
                resolved = self._resolve_import_path(file_path, imp)
                if resolved:
                    resolved_imports.append(resolved)
                    # 更新被引用文件的 imported_by
                    if resolved in self.dependency_graph:
                        self.dependency_graph[resolved].imported_by.append(file_path)

            node.imports = resolved_imports

    def _resolve_import_path(self, source_file: str, import_path: str) -> Optional[str]:
        """解析导入路径"""
        # 相对路径
        if import_path.startswith("."):
            source_dir = str(Path(source_file).parent)
            relative_path = import_path.lstrip("./")

            # 尝试不同扩展名
            for ext in self.supported_extensions:
                candidate = f"{source_dir}/{relative_path}{ext}"
                if candidate in self.dependency_graph:
                    return candidate
                # index 文件
                candidate = f"{source_dir}/{relative_path}/index{ext}"
                if candidate in self.dependency_graph:
                    return candidate

        # 绝对路径 (从项目根)
        else:
            for ext in self.supported_extensions:
                candidate = f"{import_path}{ext}"
                if candidate in self.dependency_graph:
                    return candidate
                candidate = f"{import_path}/index{ext}"
                if candidate in self.dependency_graph:
                    return candidate

        return None

    def analyze_change(
        self,
        file_path: str,
        change_description: str,
    ) -> list[Impact]:
        """
        分析修改的影响范围

        Args:
            file_path: 被修改的文件
            change_description: 修改描述

        Returns:
            影响列表
        """
        impacts = []

        # 规范化路径
        file_path = str(Path(file_path).relative_to(self.project_path))

        # 获取文件节点
        node = self.dependency_graph.get(file_path)
        if not node:
            return impacts

        # 1. 分析直接依赖者 (imported_by)
        for dependent in node.imported_by:
            impact = Impact(
                file_path=dependent,
                impact_level=ImpactLevel.HIGH,
                reason=f"Directly imports {file_path}",
                symbols_affected=node.exports,
            )

            # 基于修改描述推断可能需要的改动
            impact.suggested_changes = self._infer_changes(
                change_description,
                dependent,
                node.exports,
            )

            impacts.append(impact)

        # 2. 分析间接依赖 (传递性)
        for dependent in node.imported_by:
            dep_node = self.dependency_graph.get(dependent)
            if dep_node:
                for indirect in dep_node.imported_by:
                    if indirect not in [i.file_path for i in impacts]:
                        impacts.append(
                            Impact(
                                file_path=indirect,
                                impact_level=ImpactLevel.MEDIUM,
                                reason=f"Indirectly depends on {file_path} via {dependent}",
                                suggested_changes=[],
                            )
                        )

        # 3. 分析符号引用
        for symbol in node.symbols:
            if symbol.exported:
                references = self._find_symbol_usages(symbol.name, exclude_file=file_path)
                for ref_file, _ in references:
                    existing = next(
                        (i for i in impacts if i.file_path == ref_file), None
                    )
                    if existing:
                        if symbol.name not in existing.symbols_affected:
                            existing.symbols_affected.append(symbol.name)
                    else:
                        impacts.append(
                            Impact(
                                file_path=ref_file,
                                impact_level=ImpactLevel.MEDIUM,
                                reason=f"Uses symbol '{symbol.name}' from {file_path}",
                                symbols_affected=[symbol.name],
                            )
                        )

        # 4. 分析测试文件
        test_files = self._find_related_tests(file_path)
        for test_file in test_files:
            if test_file not in [i.file_path for i in impacts]:
                impacts.append(
                    Impact(
                        file_path=test_file,
                        impact_level=ImpactLevel.HIGH,
                        reason="Related test file - may need updates",
                        suggested_changes=["Update test cases"],
                    )
                )

        # 按影响级别排序
        level_order = {
            ImpactLevel.CRITICAL: 0,
            ImpactLevel.HIGH: 1,
            ImpactLevel.MEDIUM: 2,
            ImpactLevel.LOW: 3,
        }
        impacts.sort(key=lambda i: level_order[i.impact_level])

        return impacts

    def _infer_changes(
        self,
        change_description: str,
        target_file: str,
        affected_symbols: list[str],
    ) -> list[str]:
        """推断需要的修改"""
        suggestions = []
        desc_lower = change_description.lower()

        # 基于关键词推断
        if "add" in desc_lower or "new" in desc_lower:
            suggestions.append("Add usage of new functionality")

        if "remove" in desc_lower or "delete" in desc_lower:
            suggestions.append("Remove references to deleted code")

        if "rename" in desc_lower:
            suggestions.append("Update symbol names")

        if "change" in desc_lower or "modify" in desc_lower:
            suggestions.append("Update function calls/usage")

        if "api" in desc_lower:
            suggestions.append("Update API calls")

        if "type" in desc_lower or "interface" in desc_lower:
            suggestions.append("Update type definitions")

        if not suggestions:
            suggestions.append("Review and update as needed")

        return suggestions

    def _find_symbol_usages(
        self,
        symbol_name: str,
        exclude_file: str = None,
    ) -> list[tuple[str, int]]:
        """查找符号使用位置"""
        usages = []

        for file_path, content in self._file_cache.items():
            if exclude_file and file_path == exclude_file:
                continue

            # 简单文本搜索
            for i, line in enumerate(content.split("\n")):
                if symbol_name in line:
                    # 排除定义行
                    if f"def {symbol_name}" not in line and f"class {symbol_name}" not in line:
                        usages.append((file_path, i + 1))

        return usages

    def _find_related_tests(self, file_path: str) -> list[str]:
        """查找相关测试文件"""
        test_files = []

        # 生成可能的测试文件名
        base = Path(file_path).stem
        possible_names = [
            f"{base}.test.ts",
            f"{base}.test.tsx",
            f"{base}.test.js",
            f"{base}_test.py",
            f"test_{base}.py",
            f"{base}.spec.ts",
            f"{base}.spec.tsx",
        ]

        # 搜索测试目录
        test_dirs = ["tests", "test", "__tests__", "spec"]

        for test_dir in test_dirs:
            for name in possible_names:
                candidate = f"{test_dir}/{name}"
                if candidate in self.dependency_graph:
                    test_files.append(candidate)

        # 同目录下的测试文件
        file_dir = str(Path(file_path).parent)
        for name in possible_names:
            candidate = f"{file_dir}/{name}"
            if candidate in self.dependency_graph:
                test_files.append(candidate)

        return list(set(test_files))

    def trace_symbol(self, symbol_name: str) -> dict:
        """
        追踪符号的完整依赖链

        Args:
            symbol_name: 符号名称

        Returns:
            依赖信息
        """
        result = {
            "symbol": symbol_name,
            "definitions": [],
            "usages": [],
            "callers": [],
            "callees": [],
        }

        # 查找定义
        if symbol_name in self.symbol_index:
            result["definitions"] = [s.to_dict() for s in self.symbol_index[symbol_name]]

        # 查找使用
        result["usages"] = self._find_symbol_usages(symbol_name)

        # 分析调用关系
        for file_path, content in self._file_cache.items():
            # 查找调用此符号的函数
            for line_num, line in enumerate(content.split("\n"), 1):
                if symbol_name in line and "(" in line:
                    # 找到包含此调用的函数
                    func_name = self._find_enclosing_function(content, line_num)
                    if func_name:
                        result["callers"].append(
                            {
                                "function": func_name,
                                "file": file_path,
                                "line": line_num,
                            }
                        )

        return result

    def _find_enclosing_function(self, content: str, line_num: int) -> Optional[str]:
        """找到包含指定行的函数"""
        lines = content.split("\n")
        for i in range(line_num - 1, -1, -1):
            line = lines[i]
            # Python
            match = re.match(r"^\s*def\s+(\w+)", line)
            if match:
                return match.group(1)
            # JavaScript/TypeScript
            match = re.match(r"^\s*(?:async\s+)?function\s+(\w+)", line)
            if match:
                return match.group(1)
            match = re.match(r"^\s*const\s+(\w+)\s*=\s*(?:async\s*)?\(", line)
            if match:
                return match.group(1)
        return None

    def get_related_files(self, file_path: str, depth: int = 2) -> list[str]:
        """
        获取相关文件

        Args:
            file_path: 起始文件
            depth: 搜索深度

        Returns:
            相关文件列表
        """
        file_path = str(Path(file_path).relative_to(self.project_path))

        related = set()
        to_visit = [(file_path, 0)]

        while to_visit:
            current, current_depth = to_visit.pop()

            if current_depth > depth:
                continue

            node = self.dependency_graph.get(current)
            if not node:
                continue

            # 添加导入的文件
            for imp in node.imports:
                if imp not in related:
                    related.add(imp)
                    to_visit.append((imp, current_depth + 1))

            # 添加被导入的文件
            for imp_by in node.imported_by:
                if imp_by not in related:
                    related.add(imp_by)
                    to_visit.append((imp_by, current_depth + 1))

        related.discard(file_path)
        return list(related)

    def get_dependency_chain(self, from_file: str, to_file: str) -> list[list[str]]:
        """
        获取两个文件间的依赖链

        Args:
            from_file: 起始文件
            to_file: 目标文件

        Returns:
            所有可能的路径
        """
        from_file = str(Path(from_file).relative_to(self.project_path))
        to_file = str(Path(to_file).relative_to(self.project_path))

        paths = []
        visited = set()

        def dfs(current: str, path: list[str]):
            if current == to_file:
                paths.append(path.copy())
                return

            if current in visited:
                return

            visited.add(current)
            node = self.dependency_graph.get(current)

            if node:
                for imp in node.imports:
                    path.append(imp)
                    dfs(imp, path)
                    path.pop()

            visited.remove(current)

        dfs(from_file, [from_file])
        return paths

    def export_graph(self, output_path: Path):
        """导出依赖图"""
        data = {
            "nodes": [node.to_dict() for node in self.dependency_graph.values()],
            "exported_at": datetime.now().isoformat(),
        }
        output_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def get_stats(self) -> dict:
        """获取统计信息"""
        total_imports = sum(len(n.imports) for n in self.dependency_graph.values())
        total_exports = sum(len(n.exports) for n in self.dependency_graph.values())
        total_symbols = sum(len(n.symbols) for n in self.dependency_graph.values())

        # 找出最被依赖的文件
        most_depended = sorted(
            self.dependency_graph.items(),
            key=lambda x: len(x[1].imported_by),
            reverse=True,
        )[:5]

        # 找出依赖最多的文件
        most_imports = sorted(
            self.dependency_graph.items(),
            key=lambda x: len(x[1].imports),
            reverse=True,
        )[:5]

        return {
            "files": len(self.dependency_graph),
            "total_imports": total_imports,
            "total_exports": total_exports,
            "total_symbols": total_symbols,
            "unique_symbols": len(self.symbol_index),
            "most_depended": [(f, len(n.imported_by)) for f, n in most_depended],
            "most_imports": [(f, len(n.imports)) for f, n in most_imports],
        }


# 便捷函数
def create_reasoner(project_path: str | Path) -> MultiFileReasoner:
    """创建多文件推理器"""
    reasoner = MultiFileReasoner(Path(project_path))
    reasoner.build_dependency_graph()
    return reasoner
