#!/usr/bin/env python3
"""
项目知识学习器 - 学习项目的编码规范和风格

功能：
1. 分析项目结构和命名规范
2. 提取代码风格（缩进、注释、import 顺序）
3. 识别常用依赖和框架
4. 存储到项目知识库供 Claude 参考

作者: claude-code-enhancement
"""

import ast
import json
import re
from collections import Counter
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


@dataclass
class NamingPatterns:
    """命名规范"""
    variable_style: str = "snake_case"  # snake_case, camelCase, PascalCase
    function_style: str = "snake_case"
    class_style: str = "PascalCase"
    constant_style: str = "UPPER_SNAKE"
    private_prefix: str = "_"  # 或 "__"
    examples: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CodeStyle:
    """代码风格"""
    indent_size: int = 4
    indent_type: str = "space"  # space or tab
    quote_style: str = "double"  # single or double
    max_line_length: int = 88
    import_order: List[str] = field(default_factory=list)  # ["stdlib", "third_party", "local"]
    docstring_style: str = "google"  # google, numpy, rest
    comment_style: str = "#"  # # or //
    examples: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProjectStructure:
    """项目结构"""
    type: str = "unknown"  # library, web_app, cli, api, etc.
    main_language: str = "python"
    framework: Optional[str] = None  # django, flask, fastapi, etc.
    test_framework: Optional[str] = None  # pytest, unittest, etc.
    source_dir: str = "src"
    test_dir: str = "tests"
    config_files: List[str] = field(default_factory=list)
    important_files: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ProjectKnowledge:
    """项目知识库"""
    project_path: str
    project_name: str
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())

    # 核心知识
    structure: Optional[ProjectStructure] = None
    naming: Optional[NamingPatterns] = None
    style: Optional[CodeStyle] = None

    # 依赖和模式
    dependencies: Dict[str, str] = field(default_factory=dict)  # {package: version}
    common_patterns: List[str] = field(default_factory=list)

    # 重要上下文
    entry_points: List[str] = field(default_factory=list)
    key_modules: List[str] = field(default_factory=list)
    api_endpoints: List[str] = field(default_factory=list)

    # 自定义规则
    custom_rules: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "project_path": self.project_path,
            "project_name": self.project_name,
            "last_updated": self.last_updated,
            "structure": self.structure.to_dict() if self.structure else None,
            "naming": self.naming.to_dict() if self.naming else None,
            "style": self.style.to_dict() if self.style else None,
            "dependencies": self.dependencies,
            "common_patterns": self.common_patterns,
            "entry_points": self.entry_points,
            "key_modules": self.key_modules,
            "api_endpoints": self.api_endpoints,
            "custom_rules": self.custom_rules,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectKnowledge":
        return cls(
            project_path=data.get("project_path", ""),
            project_name=data.get("project_name", ""),
            last_updated=data.get("last_updated", datetime.now().isoformat()),
            structure=ProjectStructure(**data["structure"]) if data.get("structure") else None,
            naming=NamingPatterns(**data["naming"]) if data.get("naming") else None,
            style=CodeStyle(**data["style"]) if data.get("style") else None,
            dependencies=data.get("dependencies", {}),
            common_patterns=data.get("common_patterns", []),
            entry_points=data.get("entry_points", []),
            key_modules=data.get("key_modules", []),
            api_endpoints=data.get("api_endpoints", []),
            custom_rules=data.get("custom_rules", []),
        )


class ProjectKnowledgeLearner:
    """
    项目知识学习器

    分析项目并提取编码规范、命名风格、常用模式
    """

    def __init__(self, project_path: Path):
        self.project_path = Path(project_path).resolve()  # 使用绝对路径
        self.knowledge_path = Path.home() / ".claude" / "projects" / self._get_project_id() / "knowledge.json"

    def _get_project_id(self) -> str:
        """获取项目唯一 ID"""
        # 使用路径的 hash 作为 ID
        return str(abs(hash(str(self.project_path))))[:8]

    def learn(self) -> ProjectKnowledge:
        """
        学习项目知识

        Returns:
            ProjectKnowledge: 提取的项目知识
        """
        knowledge = ProjectKnowledge(
            project_path=str(self.project_path),
            project_name=self.project_path.name,
        )

        # 分析各维度
        knowledge.structure = self._analyze_structure()
        knowledge.naming = self._analyze_naming()
        knowledge.style = self._analyze_style()
        knowledge.dependencies = self._extract_dependencies()
        knowledge.entry_points = self._find_entry_points()
        knowledge.key_modules = self._find_key_modules()
        knowledge.api_endpoints = self._find_api_endpoints()
        knowledge.common_patterns = self._extract_patterns()

        # 保存知识
        self._save_knowledge(knowledge)

        return knowledge

    def _analyze_structure(self) -> ProjectStructure:
        """分析项目结构"""
        structure = ProjectStructure()

        # 检测项目类型
        has_pyproject = (self.project_path / "pyproject.toml").exists()
        has_setup_py = (self.project_path / "setup.py").exists()
        has_requirements = (self.project_path / "requirements.txt").exists()
        has_manage_py = (self.project_path / "manage.py").exists()
        has_main_py = (self.project_path / "main.py").exists()
        has_app_py = (self.project_path / "app.py").exists()

        # 检测框架
        if has_manage_py:
            structure.type = "web_app"
            structure.framework = "django"
        elif (self.project_path / "app").exists() and (self.project_path / "requirements.txt").exists():
            # 检查是否是 Flask/FastAPI
            for req_file in ["requirements.txt", "pyproject.toml"]:
                req_path = self.project_path / req_file
                if req_path.exists():
                    content = req_path.read_text().lower()
                    if "fastapi" in content:
                        structure.type = "api"
                        structure.framework = "fastapi"
                    elif "flask" in content:
                        structure.type = "web_app"
                        structure.framework = "flask"
                    break
        elif has_main_py or has_app_py:
            structure.type = "cli"
        elif has_pyproject or has_setup_py:
            structure.type = "library"

        # 检测测试框架
        test_dir = self.project_path / "tests"
        if test_dir.exists():
            for test_file in test_dir.glob("test_*.py"):
                content = test_file.read_text()
                if "pytest" in content:
                    structure.test_framework = "pytest"
                elif "unittest" in content:
                    structure.test_framework = "unittest"
                break

        # 检测源目录
        for src_dir in ["src", "lib", self.project_path.name]:
            if (self.project_path / src_dir).exists():
                structure.source_dir = src_dir
                break

        # 检测配置文件
        config_patterns = ["*.toml", "*.yaml", "*.yml", "*.json", "*.ini", "*.cfg"]
        for pattern in config_patterns:
            for config_file in self.project_path.glob(pattern):
                if config_file.name not in [".git", "__pycache__", "node_modules"]:
                    structure.config_files.append(config_file.name)

        # 检测重要文件
        important_names = ["README", "CHANGELOG", "CONTRIBUTING", "LICENSE", "Makefile"]
        for name in important_names:
            for f in self.project_path.glob(f"{name}*"):
                structure.important_files.append(f.name)

        return structure

    def _analyze_naming(self) -> NamingPatterns:
        """分析命名规范"""
        patterns = NamingPatterns()

        # 收集所有 Python 文件中的名称
        variable_names: List[str] = []
        function_names: List[str] = []
        class_names: List[str] = []
        constant_names: List[str] = []

        py_files = list(self.project_path.glob("**/*.py"))[:20]  # 最多分析 20 个文件

        for py_file in py_files:
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                content = py_file.read_text()
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        function_names.append(node.name)
                        # 提取局部变量
                        for child in ast.walk(node):
                            if isinstance(child, ast.Name) and isinstance(child.ctx, ast.Store):
                                variable_names.append(child.id)
                    elif isinstance(node, ast.ClassDef):
                        class_names.append(node.name)
                    elif isinstance(node, ast.Assign):
                        for target in node.targets:
                            if isinstance(target, ast.Name):
                                # 常量通常是全大写
                                if target.id.isupper() or (target.id.isupper() and '_' in target.id):
                                    constant_names.append(target.id)
                                else:
                                    variable_names.append(target.id)
            except Exception:
                continue

        # 分析命名风格
        patterns.variable_style = self._detect_naming_style(variable_names)
        patterns.function_style = self._detect_naming_style(function_names)
        patterns.class_style = self._detect_naming_style(class_names)
        patterns.constant_style = self._detect_naming_style(constant_names)

        # 检测私有前缀
        private_funcs = [f for f in function_names if f.startswith('_')]
        if private_funcs:
            double_underscore = [f for f in private_funcs if f.startswith('__') and not f.endswith('__')]
            patterns.private_prefix = "__" if double_underscore else "_"

        # 保存示例
        patterns.examples = {
            "variables": variable_names[:10],
            "functions": function_names[:10],
            "classes": class_names[:10],
            "constants": constant_names[:5],
        }

        return patterns

    def _detect_naming_style(self, names: List[str]) -> str:
        """检测命名风格"""
        if not names:
            return "snake_case"

        styles = Counter()
        for name in names:
            if not name:  # 跳过空字符串
                continue
            if name.startswith('_'):
                name = name.lstrip('_')

            if not name:  # 处理全是下划线的情况
                continue

            if name.isupper() and '_' in name:
                styles["UPPER_SNAKE"] += 1
            elif name.islower() and '_' in name:
                styles["snake_case"] += 1
            elif name[0].isupper() and '_' not in name:
                styles["PascalCase"] += 1
            elif name[0].islower() and '_' not in name and any(c.isupper() for c in name):
                styles["camelCase"] += 1
            else:
                styles["snake_case"] += 1

        return styles.most_common(1)[0][0] if styles else "snake_case"

    def _analyze_style(self) -> CodeStyle:
        """分析代码风格"""
        style = CodeStyle()

        py_files = list(self.project_path.glob("**/*.py"))[:10]

        indent_sizes = Counter()
        quote_styles = Counter()
        max_line_lengths = []
        docstring_styles = Counter()

        for py_file in py_files:
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                lines = py_file.read_text().split('\n')

                for line in lines:
                    # 检测缩进
                    if line.startswith(' ') and not line.startswith('  '):
                        indent_sizes[1] += 1
                    elif line.startswith('    ') and not line.startswith('     '):
                        indent_sizes[4] += 1
                    elif line.startswith('\t'):
                        indent_sizes['tab'] += 1

                    # 检测行长度
                    max_line_lengths.append(len(line))

                    # 检测引号风格
                    if '"' in line and "'" not in line:
                        quote_styles["double"] += 1
                    elif "'" in line and '"' not in line:
                        quote_styles["single"] += 1

                # 解析 AST 检测 docstring 风格
                content = '\n'.join(lines)
                tree = ast.parse(content)

                for node in ast.walk(tree):
                    docstring = ast.get_docstring(node)
                    if docstring:
                        if "Args:" in docstring or "Returns:" in docstring:
                            docstring_styles["google"] += 1
                        elif "Parameters" in docstring or "----------" in docstring:
                            docstring_styles["numpy"] += 1
                        elif ":param" in docstring or ":return:" in docstring:
                            docstring_styles["rest"] += 1

            except Exception:
                continue

        # 设置检测到的风格
        if indent_sizes:
            most_common = indent_sizes.most_common(1)[0][0]
            if most_common == 'tab':
                style.indent_type = 'tab'
            else:
                style.indent_size = most_common

        if quote_styles:
            style.quote_style = quote_styles.most_common(1)[0][0]

        if max_line_lengths:
            style.max_line_length = max(max_line_lengths)

        if docstring_styles:
            style.docstring_style = docstring_styles.most_common(1)[0][0]

        # 保存示例
        style.examples = {
            "indent": f"{style.indent_size} {style.indent_type}s",
            "quotes": style.quote_style,
            "max_length": str(style.max_line_length),
            "docstring": style.docstring_style,
        }

        return style

    def _extract_dependencies(self) -> Dict[str, str]:
        """提取依赖"""
        dependencies = {}

        # 从 requirements.txt
        req_file = self.project_path / "requirements.txt"
        if req_file.exists():
            for line in req_file.read_text().split('\n'):
                line = line.strip()
                if line and not line.startswith('#'):
                    # 解析 package==version 或 package>=version
                    match = re.match(r'^([a-zA-Z0-9_-]+)', line)
                    if match:
                        package = match.group(1).lower()
                        # 尝试提取版本
                        version_match = re.search(r'[=<>]+([0-9.]+)', line)
                        version = version_match.group(1) if version_match else "latest"
                        dependencies[package] = version

        # 从 pyproject.toml
        pyproject = self.project_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            # 简单解析 [project.dependencies]
            in_deps = False
            for line in content.split('\n'):
                if 'dependencies' in line.lower():
                    in_deps = True
                elif in_deps and line.strip().startswith('['):
                    in_deps = False
                elif in_deps and '"' in line:
                    match = re.search(r'"([^"]+)"', line)
                    if match:
                        dep = match.group(1)
                        pkg_match = re.match(r'^([a-zA-Z0-9_-]+)', dep)
                        if pkg_match:
                            dependencies[pkg_match.group(1).lower()] = "latest"

        return dependencies

    def _find_entry_points(self) -> List[str]:
        """找到入口文件"""
        entry_points = []

        # 常见入口文件
        entry_names = ["main.py", "app.py", "run.py", "server.py", "__main__.py", "manage.py"]
        for name in entry_names:
            if (self.project_path / name).exists():
                entry_points.append(name)

        # 检查 src/ 目录
        src_dir = self.project_path / "src"
        if src_dir.exists():
            for name in entry_names:
                if (src_dir / name).exists():
                    entry_points.append(f"src/{name}")

        # 检查 pyproject.toml 中的 scripts
        pyproject = self.project_path / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "scripts" in content:
                # 提取脚本入口
                match = re.search(r'\[project\.scripts\](.+?)(?=\[|\Z)', content, re.DOTALL)
                if match:
                    for line in match.group(1).split('\n'):
                        if '=' in line:
                            script = line.split('=')[0].strip()
                            if script:
                                entry_points.append(f"script: {script}")

        return entry_points

    def _find_key_modules(self) -> List[str]:
        """找到关键模块"""
        modules = []

        # 查找 src/ 或项目名目录
        for dir_name in ["src", "lib", self.project_path.name]:
            dir_path = self.project_path / dir_name
            if dir_path.exists() and dir_path.is_dir():
                # 列出子模块
                for item in sorted(dir_path.iterdir()):
                    if item.is_dir() and not item.name.startswith('_'):
                        modules.append(f"{dir_name}/{item.name}")
                    elif item.suffix == '.py' and not item.name.startswith('_'):
                        if item.name not in ['__init__.py', 'main.py', 'app.py']:
                            modules.append(f"{dir_name}/{item.name}")
                break

        return modules[:20]  # 最多 20 个

    def _find_api_endpoints(self) -> List[str]:
        """找到 API 端点（如果是 web 项目）"""
        endpoints = []

        # 查找 FastAPI/Flask 路由
        py_files = list(self.project_path.glob("**/*.py"))[:20]

        for py_file in py_files:
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue

            try:
                content = py_file.read_text()

                # FastAPI 路由
                for match in re.finditer(r'@(?:app|router)\.(?:get|post|put|delete|patch)\(["\']([^"\']+)["\']', content):
                    endpoints.append(match.group(1))

                # Flask 路由
                for match in re.finditer(r'@.*\.route\(["\']([^"\']+)["\']', content):
                    endpoints.append(match.group(1))

            except Exception:
                continue

        return sorted(set(endpoints))[:20]

    def _extract_patterns(self) -> List[str]:
        """提取常见模式"""
        patterns = []

        # 检查是否有特定的模式文件
        pattern_indicators = {
            "uses_logging": "logging" in str(list(self.project_path.glob("**/*.py"))),
            "uses_config": (self.project_path / "config").exists() or list(self.project_path.glob("*config*.py")),
            "uses_database": "models" in str(list(self.project_path.glob("**/*.py"))),
            "uses_migrations": (self.project_path / "migrations").exists(),
            "uses_tests": (self.project_path / "tests").exists() or (self.project_path / "test").exists(),
            "uses_docker": (self.project_path / "Dockerfile").exists() or (self.project_path / "docker-compose.yml").exists(),
            "uses_ci": (self.project_path / ".github").exists() or (self.project_path / ".gitlab-ci.yml").exists(),
        }

        for pattern, exists in pattern_indicators.items():
            if exists:
                patterns.append(pattern)

        return patterns

    def _save_knowledge(self, knowledge: ProjectKnowledge):
        """保存知识到文件"""
        self.knowledge_path.parent.mkdir(parents=True, exist_ok=True)
        self.knowledge_path.write_text(json.dumps(knowledge.to_dict(), indent=2, ensure_ascii=False))

    def load_knowledge(self) -> Optional[ProjectKnowledge]:
        """加载已有知识"""
        if self.knowledge_path.exists():
            try:
                data = json.loads(self.knowledge_path.read_text())
                return ProjectKnowledge.from_dict(data)
            except Exception:
                pass
        return None

    def generate_style_guide(self) -> str:
        """
        生成可读的风格指南

        Returns:
            Markdown 格式的风格指南
        """
        knowledge = self.load_knowledge()
        if not knowledge:
            return "# 项目知识尚未学习，请先运行学习器"

        lines = [
            f"# {knowledge.project_name} 项目风格指南",
            "",
            f"> 最后更新: {knowledge.last_updated}",
            "",
            "## 项目结构",
            "",
        ]

        if knowledge.structure:
            s = knowledge.structure
            lines.extend([
                f"- **类型**: {s.type}",
                f"- **主语言**: {s.main_language}",
            ])
            if s.framework:
                lines.append(f"- **框架**: {s.framework}")
            if s.test_framework:
                lines.append(f"- **测试框架**: {s.test_framework}")
            lines.append(f"- **源码目录**: {s.source_dir}")
            lines.append(f"- **测试目录**: {s.test_dir}")

        lines.extend(["", "## 命名规范", ""])

        if knowledge.naming:
            n = knowledge.naming
            lines.extend([
                f"- **变量**: `{n.variable_style}`",
                f"- **函数**: `{n.function_style}`",
                f"- **类**: `{n.class_style}`",
                f"- **常量**: `{n.constant_style}`",
                f"- **私有前缀**: `{n.private_prefix}`",
            ])

        lines.extend(["", "## 代码风格", ""])

        if knowledge.style:
            s = knowledge.style
            lines.extend([
                f"- **缩进**: {s.indent_size} {s.indent_type}s",
                f"- **引号**: {s.quote_style}",
                f"- **最大行长度**: {s.max_line_length}",
                f"- **Docstring**: {s.docstring_style}",
            ])

        if knowledge.entry_points:
            lines.extend(["", "## 入口文件", ""])
            for ep in knowledge.entry_points:
                lines.append(f"- `{ep}`")

        if knowledge.key_modules:
            lines.extend(["", "## 关键模块", ""])
            for mod in knowledge.key_modules[:10]:
                lines.append(f"- `{mod}`")

        if knowledge.dependencies:
            lines.extend(["", "## 主要依赖", ""])
            for pkg, ver in list(knowledge.dependencies.items())[:10]:
                lines.append(f"- `{pkg}` ({ver})")

        if knowledge.custom_rules:
            lines.extend(["", "## 自定义规则", ""])
            for rule in knowledge.custom_rules:
                lines.append(f"- {rule}")

        return '\n'.join(lines)


def learn_project(project_path: Path) -> ProjectKnowledge:
    """便捷函数：学习项目"""
    learner = ProjectKnowledgeLearner(project_path)
    return learner.learn()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法: python project_knowledge_learner.py <project_path> [--guide]")
        sys.exit(1)

    project_path = Path(sys.argv[1])

    if "--guide" in sys.argv:
        learner = ProjectKnowledgeLearner(project_path)
        print(learner.generate_style_guide())
    else:
        knowledge = learn_project(project_path)
        print(f"✅ 已学习项目: {knowledge.project_name}")
        print(f"   结构: {knowledge.structure.type if knowledge.structure else 'unknown'}")
        print(f"   命名规范: {knowledge.naming.function_style if knowledge.naming else 'unknown'}")
        print(f"   代码风格: {knowledge.style.indent_size if knowledge.style else 'unknown'} 空格缩进")