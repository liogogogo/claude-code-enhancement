"""
项目知识自动学习系统

功能:
- 自动分析项目结构
- 学习项目约定和模式
- 提取架构知识
- 生成项目文档
- 持续更新知识库

输出:
- .claude/knowledge/
├── architecture.json    # 架构知识
├── conventions.json     # 编码约定
├── patterns.json        # 设计模式
├── dependencies.json    # 依赖关系
└── learnings.json       # 学习记录
"""

import json
import re
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Optional, Union, List, Dict, Tuple, Set


class KnowledgeType(Enum):
    """知识类型"""

    ARCHITECTURE = "architecture"  # 架构
    CONVENTION = "convention"  # 约定
    PATTERN = "pattern"  # 模式
    DEPENDENCY = "dependency"  # 依赖
    API = "api"  # API
    LEARNING = "learning"  # 学习


@dataclass
class ProjectKnowledge:
    """项目知识"""

    type: KnowledgeType
    key: str
    value: Any
    confidence: float = 1.0
    source: str = ""  # 来源文件/分析
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    examples: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "type": self.type.value,
            "key": self.key,
            "value": self.value,
            "confidence": self.confidence,
            "source": self.source,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "examples": self.examples,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ProjectKnowledge":
        return cls(
            type=KnowledgeType(data["type"]),
            key=data["key"],
            value=data["value"],
            confidence=data.get("confidence", 1.0),
            source=data.get("source", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            examples=data.get("examples", []),
        )


@dataclass
class CodePattern:
    """代码模式"""

    name: str
    description: str
    pattern: str  # 正则或模板
    examples: List[str]
    frequency: int = 1
    languages: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "pattern": self.pattern,
            "examples": self.examples,
            "frequency": self.frequency,
            "languages": self.languages,
        }


@dataclass
class ProjectConvention:
    """项目约定"""

    category: str  # naming, structure, style, etc.
    rule: str
    description: str
    examples: List[str]
    exceptions: List[str] = field(default_factory=list)
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "rule": self.rule,
            "description": self.description,
            "examples": self.examples,
            "exceptions": self.exceptions,
            "confidence": self.confidence,
        }


class ProjectKnowledgeLearner:
    """
    项目知识自动学习器

    功能:
    - 分析项目结构
    - 提取编码约定
    - 识别设计模式
    - 构建依赖图
    - 学习 API 模式
    """

    def __init__(self, project_path: Path):
        """
        初始化学习器

        Args:
            project_path: 项目路径
        """
        self.project_path = Path(project_path)
        self.knowledge_dir = self.project_path / ".claude" / "knowledge"
        self.knowledge_dir.mkdir(parents=True, exist_ok=True)

        # 知识存储
        self.knowledge: Dict[str, ProjectKnowledge] = {}
        self.patterns: List[CodePattern] = []
        self.conventions: List[ProjectConvention] = []

        # 分析缓存
        self._file_cache: Dict[str, str] = {}
        self._analysis_cache: dict = {}

        # 加载已有知识
        self._load_knowledge()

    def _load_knowledge(self):
        """加载已有知识"""
        for knowledge_file in self.knowledge_dir.glob("*.json"):
            try:
                data = json.loads(knowledge_file.read_text())
                if "type" in data:
                    # 单个知识
                    k = ProjectKnowledge.from_dict(data)
                    self.knowledge[f"{k.type.value}:{k.key}"] = k
                elif isinstance(data, list):
                    # 知识列表
                    if knowledge_file.stem == "patterns":
                        self.patterns = [CodePattern(**p) for p in data]
                    elif knowledge_file.stem == "conventions":
                        self.conventions = [ProjectConvention(**c) for c in data]
            except Exception as e:
                print(f"Warning: Failed to load {knowledge_file}: {e}")

    def _save_knowledge(self, filename: str, data: Any):
        """保存知识到文件"""
        file_path = self.knowledge_dir / f"{filename}.json"
        if isinstance(data, list) and data and hasattr(data[0], "to_dict"):
            file_path.write_text(
                json.dumps([d.to_dict() for d in data], indent=2, ensure_ascii=False)
            )
        elif isinstance(data, dict) and data and hasattr(
            next(iter(data.values())), "to_dict"
        ):
            file_path.write_text(
                json.dumps(
                    {k: v.to_dict() for k, v in data.items()},
                    indent=2,
                    ensure_ascii=False,
                )
            )
        else:
            file_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))

    def analyze_project(self) -> dict:
        """
        分析项目

        Returns:
            分析统计
        """
        stats = {
            "files_analyzed": 0,
            "patterns_found": 0,
            "conventions_learned": 0,
            "dependencies_mapped": 0,
        }

        # 1. 分析项目结构
        self._analyze_structure()

        # 2. 分析代码文件
        for file_path in self._get_code_files():
            self._analyze_file(file_path)
            stats["files_analyzed"] += 1

        # 3. 提取约定
        self._extract_conventions()
        stats["conventions_learned"] = len(self.conventions)

        # 4. 识别模式
        self._identify_patterns()
        stats["patterns_found"] = len(self.patterns)

        # 5. 分析依赖
        deps = self._analyze_dependencies()
        stats["dependencies_mapped"] = len(deps)

        # 保存所有知识
        self._save_all()

        return stats

    def _get_code_files(
        self,
        extensions: List[str] = None,
        exclude: List[str] = None,
    ) -> List[Path]:
        """获取代码文件"""
        if extensions is None:
            extensions = [".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java"]

        if exclude is None:
            exclude = [
                "node_modules",
                ".git",
                "__pycache__",
                "venv",
                "dist",
                "build",
                ".next",
                "vendor",
            ]

        files = []
        for ext in extensions:
            for file_path in self.project_path.rglob(f"*{ext}"):
                if not any(excl in str(file_path) for excl in exclude):
                    files.append(file_path)

        return files

    def _analyze_structure(self):
        """分析项目结构"""
        structure = {}

        # 获取目录结构
        for item in self.project_path.iterdir():
            if item.is_dir() and not item.name.startswith("."):
                structure[item.name] = self._get_dir_summary(item)

        # 存储架构知识
        self.knowledge["architecture:structure"] = ProjectKnowledge(
            type=KnowledgeType.ARCHITECTURE,
            key="structure",
            value=structure,
            source="directory_analysis",
        )

        # 识别项目类型
        project_type = self._identify_project_type()
        self.knowledge["architecture:type"] = ProjectKnowledge(
            type=KnowledgeType.ARCHITECTURE,
            key="type",
            value=project_type,
            source="config_analysis",
        )

    def _get_dir_summary(self, dir_path: Path, depth: int = 2) -> dict:
        """获取目录摘要"""
        if depth <= 0:
            return {"truncated": True}

        summary = {"files": [], "dirs": {}}
        try:
            for item in sorted(dir_path.iterdir()):
                if item.name.startswith("."):
                    continue
                if item.is_file():
                    summary["files"].append(item.name)
                elif item.is_dir():
                    summary["dirs"][item.name] = self._get_dir_summary(
                        item, depth - 1
                    )
        except PermissionError:
            pass

        return summary

    def _identify_project_type(self) -> dict:
        """识别项目类型"""
        indicators = {
            "frontend_react": ["package.json", "src/App.tsx", "src/App.jsx"],
            "frontend_vue": ["package.json", "src/App.vue"],
            "backend_node": ["package.json", "src/index.ts", "src/index.js"],
            "backend_python": ["requirements.txt", "setup.py", "pyproject.toml"],
            "backend_go": ["go.mod", "main.go"],
            "backend_rust": ["Cargo.toml", "src/main.rs"],
            "monorepo": ["pnpm-workspace.yaml", "lerna.json", "nx.json"],
            "library": ["setup.py", "pyproject.toml", "Cargo.toml"],
        }

        detected = {}
        for ptype, files in indicators.items():
            matches = sum(
                1 for f in files if (self.project_path / f).exists()
            )
            if matches > 0:
                detected[ptype] = matches / len(files)

        return detected

    def _analyze_file(self, file_path: Path):
        """分析单个文件"""
        try:
            content = file_path.read_text(encoding="utf-8")
            self._file_cache[str(file_path)] = content

            # 提取导入/依赖
            imports = self._extract_imports(content, file_path.suffix)

            # 提取函数/类定义
            definitions = self._extract_definitions(content, file_path.suffix)

            # 存储文件级知识
            rel_path = str(file_path.relative_to(self.project_path))
            self.knowledge[f"file:{rel_path}"] = ProjectKnowledge(
                type=KnowledgeType.ARCHITECTURE,
                key=f"file:{rel_path}",
                value={
                    "imports": imports,
                    "definitions": definitions,
                    "size": len(content),
                    "lines": content.count("\n") + 1,
                },
                source=str(file_path),
            )

        except Exception as e:
            print(f"Warning: Failed to analyze {file_path}: {e}")

    def _extract_imports(self, content: str, ext: str) -> List[str]:
        """提取导入语句"""
        imports = []

        if ext in [".ts", ".tsx", ".js", ".jsx"]:
            # ES6 imports
            patterns = [
                r'import\s+.*?\s+from\s+["\']([^"\']+)["\']',
                r'import\s+["\']([^"\']+)["\']',
                r'require\(["\']([^"\']+)["\']\)',
            ]
            for pattern in patterns:
                imports.extend(re.findall(pattern, content))

        elif ext == ".py":
            # Python imports
            patterns = [
                r'^import\s+(\S+)',
                r'^from\s+(\S+)\s+import',
            ]
            for pattern in patterns:
                imports.extend(re.findall(pattern, content, re.MULTILINE))

        elif ext == ".go":
            # Go imports
            pattern = r'import\s+(?:\([^)]+\)|"([^"]+)")'
            imports.extend(re.findall(pattern, content, re.DOTALL))

        return list(set(imports))

    def _extract_definitions(self, content: str, ext: str) -> dict:
        """提取定义"""
        definitions = {"functions": [], "classes": [], "variables": []}

        if ext == ".py":
            # Python
            definitions["classes"].extend(
                re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
            )
            definitions["functions"].extend(
                re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
            )
            definitions["functions"].extend(
                re.findall(r'^async\s+def\s+(\w+)', content, re.MULTILINE)
            )

        elif ext in [".ts", ".tsx", ".js", ".jsx"]:
            # JavaScript/TypeScript
            definitions["classes"].extend(
                re.findall(r'class\s+(\w+)', content)
            )
            definitions["functions"].extend(
                re.findall(r'function\s+(\w+)', content)
            )
            definitions["functions"].extend(
                re.findall(r'const\s+(\w+)\s*=\s*(?:async\s*)?\(', content)
            )
            definitions["variables"].extend(
                re.findall(r'(?:const|let|var)\s+(\w+)', content)
            )

        elif ext == ".go":
            # Go
            definitions["functions"].extend(
                re.findall(r'func\s+(?:\([^)]+\)\s+)?(\w+)', content)
            )
            definitions["classes"].extend(
                re.findall(r'type\s+(\w+)\s+struct', content)
            )

        return definitions

    def _extract_conventions(self):
        """提取编码约定"""
        # 命名约定
        naming_conventions = self._analyze_naming_conventions()
        for conv in naming_conventions:
            self.conventions.append(conv)

        # 文件结构约定
        structure_conventions = self._analyze_structure_conventions()
        for conv in structure_conventions:
            self.conventions.append(conv)

    def _analyze_naming_conventions(self) -> List[ProjectConvention]:
        """分析命名约定"""
        conventions = []

        # 收集所有名称
        names = {"classes": [], "functions": [], "variables": [], "files": []}

        for file_path, content in self._file_cache.items():
            ext = Path(file_path).suffix

            if ext == ".py":
                names["classes"].extend(
                    re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
                )
                names["functions"].extend(
                    re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
                )
                names["variables"].extend(
                    re.findall(r'^(\w+)\s*=', content, re.MULTILINE)
                )

            elif ext in [".ts", ".tsx", ".js", ".jsx"]:
                names["classes"].extend(re.findall(r'class\s+(\w+)', content))
                names["functions"].extend(
                    re.findall(r'function\s+(\w+)|const\s+(\w+)\s*=', content)
                )

            names["files"].append(Path(file_path).stem)

        # 分析命名模式
        for category, name_list in names.items():
            if not name_list:
                continue

            patterns = Counter()
            for name in name_list:
                if "_" in name and name.islower():
                    patterns["snake_case"] += 1
                elif name[0].isupper() and "_" not in name:
                    patterns["PascalCase"] += 1
                elif name[0].islower() and any(
                    c.isupper() for c in name[1:]
                ):
                    patterns["camelCase"] += 1
                elif name.isupper():
                    patterns["UPPER_CASE"] += 1
                else:
                    patterns["other"] += 1

            if patterns:
                dominant = patterns.most_common(1)[0]
                if dominant[1] / len(name_list) > 0.6:  # 60% 以上
                    conventions.append(
                        ProjectConvention(
                            category=f"naming_{category}",
                            rule=f"Use {dominant[0]}",
                            description=f"{category.replace('_', ' ').title()} should use {dominant[0]}",
                            examples=[
                                n
                                for n in name_list[:3]
                                if dominant[0].replace("_", " ")
                                in self._get_naming_style(n)
                            ],
                            confidence=dominant[1] / len(name_list),
                        )
                    )

        return conventions

    def _get_naming_style(self, name: str) -> str:
        """获取命名风格"""
        if "_" in name and name.islower():
            return "snake case"
        elif name[0].isupper() and "_" not in name:
            return "PascalCase"
        elif name[0].islower() and any(c.isupper() for c in name[1:]):
            return "camelCase"
        elif name.isupper():
            return "UPPER CASE"
        return "other"

    def _analyze_structure_conventions(self) -> List[ProjectConvention]:
        """分析结构约定"""
        conventions = []

        # 检查测试文件位置
        test_patterns = []
        for file_path in self._file_cache.keys():
            if "test" in file_path.lower() or "spec" in file_path.lower():
                path = Path(file_path)
                if "tests" in path.parts or "test" in path.parts:
                    test_patterns.append("separate_dir")
                elif path.stem.endswith(".test") or path.stem.endswith(".spec"):
                    test_patterns.append("colocated")

        if test_patterns:
            dominant = Counter(test_patterns).most_common(1)[0]
            conventions.append(
                ProjectConvention(
                    category="testing",
                    rule=(
                        "Tests in separate directory"
                        if dominant[0] == "separate_dir"
                        else "Tests colocated with source"
                    ),
                    description="Test file organization",
                    examples=[],
                    confidence=dominant[1] / len(test_patterns),
                )
            )

        return conventions

    def _identify_patterns(self):
        """识别设计模式"""
        # 简单的模式识别
        patterns_to_check = [
            (
                "singleton",
                r"(?:getInstance|_instance|__new__)",
                "Singleton pattern detected",
            ),
            (
                "factory",
                r"(?:Factory|create\w+|build\w+)",
                "Factory pattern detected",
            ),
            (
                "observer",
                r"(?:subscribe|addListener|on\(|emit\()",
                "Observer pattern detected",
            ),
            (
                "middleware",
                r"(?:middleware|use\(|next\(\))",
                "Middleware pattern detected",
            ),
            (
                "decorator",
                r"@\w+\s*(?:def|class|function)",
                "Decorator pattern detected",
            ),
        ]

        for content in self._file_cache.values():
            for pattern_name, regex, description in patterns_to_check:
                if re.search(regex, content):
                    existing = next(
                        (p for p in self.patterns if p.name == pattern_name), None
                    )
                    if existing:
                        existing.frequency += 1
                    else:
                        self.patterns.append(
                            CodePattern(
                                name=pattern_name,
                                description=description,
                                pattern=regex,
                                examples=[],
                                frequency=1,
                            )
                        )

    def _analyze_dependencies(self) -> dict:
        """分析依赖关系"""
        dependencies = {}

        # package.json
        pkg_json = self.project_path / "package.json"
        if pkg_json.exists():
            try:
                data = json.loads(pkg_json.read_text())
                dependencies["npm"] = {
                    **data.get("dependencies", {}),
                    **data.get("devDependencies", {}),
                }
            except Exception:
                pass

        # requirements.txt
        reqs = self.project_path / "requirements.txt"
        if reqs.exists():
            try:
                deps = []
                for line in reqs.read_text().splitlines():
                    line = line.strip()
                    if line and not line.startswith("#"):
                        deps.append(line.split("==")[0].split(">=")[0].split("<=")[0])
                dependencies["python"] = deps
            except Exception:
                pass

        # go.mod
        go_mod = self.project_path / "go.mod"
        if go_mod.exists():
            try:
                deps = []
                for line in go_mod.read_text().splitlines():
                    if "\t" in line and not line.startswith(("module", "go ")):
                        deps.append(line.split()[0])
                dependencies["go"] = deps
            except Exception:
                pass

        # 存储依赖知识
        self.knowledge["dependencies:all"] = ProjectKnowledge(
            type=KnowledgeType.DEPENDENCY,
            key="all",
            value=dependencies,
            source="config_files",
        )

        return dependencies

    def _save_all(self):
        """保存所有知识"""
        self._save_knowledge("architecture", self.knowledge)
        self._save_knowledge("patterns", self.patterns)
        self._save_knowledge("conventions", self.conventions)

    def learn_from_interaction(
        self,
        action: str,
        context: dict,
        outcome: str,
    ):
        """
        从交互中学习

        Args:
            action: 执行的动作
            context: 上下文
            outcome: 结果 (success/failure)
        """
        learning = ProjectKnowledge(
            type=KnowledgeType.LEARNING,
            key=f"interaction:{datetime.now().isoformat()}",
            value={
                "action": action,
                "context": context,
                "outcome": outcome,
            },
            source="user_interaction",
        )

        self.knowledge[f"learning:{datetime.now().timestamp()}"] = learning
        self._save_all()

    def get_convention_for(self, category: str) -> Optional[ProjectConvention]:
        """获取特定类别的约定"""
        for conv in self.conventions:
            if conv.category == category:
                return conv
        return None

    def get_patterns(self) -> List[CodePattern]:
        """获取所有模式"""
        return self.patterns

    def generate_claudemd(self) -> str:
        """
        生成 CLAUDE.md 内容

        Returns:
            CLAUDE.md 内容
        """
        lines = [
            f"# {self.project_path.name}",
            "",
            "> Auto-generated by Project Knowledge Learner",
            "",
            "## Project Type",
            "",
        ]

        # 项目类型
        ptype = self.knowledge.get("architecture:type")
        if ptype:
            for t, conf in ptype.value.items():
                if conf > 0.5:
                    lines.append(f"- {t}: {conf:.0%} confidence")

        lines.extend(["", "## Coding Conventions", ""])

        # 约定
        for conv in self.conventions:
            lines.append(f"- **{conv.category}**: {conv.rule}")
            if conv.examples:
                lines.append(f"  - Examples: {', '.join(conv.examples[:3])}")

        lines.extend(["", "## Design Patterns", ""])

        # 模式
        for pattern in self.patterns:
            lines.append(f"- **{pattern.name}**: {pattern.description}")
            lines.append(f"  - Frequency: {pattern.frequency}")

        lines.extend(["", "## Dependencies", ""])

        # 依赖
        deps = self.knowledge.get("dependencies:all")
        if deps:
            for dep_type, dep_list in deps.value.items():
                lines.append(f"### {dep_type.upper()}")
                if isinstance(dep_list, dict):
                    for name, version in list(dep_list.items())[:10]:
                        lines.append(f"- {name}: {version}")
                else:
                    for dep in dep_list[:10]:
                        lines.append(f"- {dep}")

        lines.extend(["", "---", "*This file is auto-generated. Update as needed.*", ""])

        return "\n".join(lines)

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            "knowledge_entries": len(self.knowledge),
            "patterns_identified": len(self.patterns),
            "conventions_learned": len(self.conventions),
            "files_analyzed": len(self._file_cache),
        }


# 便捷函数
def learn_project(project_path: Union[str, Path]) -> ProjectKnowledgeLearner:
    """学习项目"""
    learner = ProjectKnowledgeLearner(Path(project_path))
    learner.analyze_project()
    return learner
