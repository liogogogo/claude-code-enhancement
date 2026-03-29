# API 参考

## 核心模块

### ContextManager

智能上下文管理器，用于索引和检索代码。

```python
from src.core import create_context_manager

# 创建实例
cm = create_context_manager("/path/to/project")

# 索引代码库
stats = cm.index_codebase()
# 返回: {files_analyzed, chunks_created, ...}

# 搜索代码
results = cm.search("authentication", n_results=10)
# 返回: [(CodeChunk, similarity_score), ...]

# 获取上下文
context = cm.get_context_for_query("how to login", max_tokens=50000)
# 返回: str (格式化的上下文)
```

#### 方法

| 方法                    | 参数                            | 返回   | 描述       |
| ----------------------- | ------------------------------- | ------ | ---------- |
| `index_codebase`        | `patterns, exclude`             | `dict` | 索引代码库 |
| `search`                | `query, n_results, file_filter` | `list` | 搜索代码   |
| `get_context_for_query` | `query, max_tokens`             | `str`  | 获取上下文 |
| `add_conversation_turn` | `role, content`                 | `None` | 添加对话   |
| `compact_conversation`  | `keep_last_n`                   | `str`  | 压缩对话   |
| `clear_all`             | -                               | `None` | 清空数据   |

---

### MultiFileReasoner

多文件推理器，分析依赖和影响。

```python
from src.core import create_reasoner

# 创建实例
reasoner = create_reasoner("/path/to/project")

# 分析修改影响
impacts = reasoner.analyze_change(
    file_path="auth/login.ts",
    change_description="add MFA support"
)
# 返回: list[Impact]

# 追踪符号
trace = reasoner.trace_symbol("UserSession")
# 返回: {definitions, usages, callers, callees}

# 获取相关文件
related = reasoner.get_related_files("auth/login.ts", depth=2)
# 返回: list[str]
```

#### 方法

| 方法                     | 参数                            | 返回           | 描述         |
| ------------------------ | ------------------------------- | -------------- | ------------ |
| `build_dependency_graph` | -                               | `dict`         | 构建依赖图   |
| `analyze_change`         | `file_path, change_description` | `list[Impact]` | 分析影响     |
| `trace_symbol`           | `symbol_name`                   | `dict`         | 追踪符号     |
| `get_related_files`      | `file_path, depth`              | `list[str]`    | 获取相关文件 |
| `export_graph`           | `output_path`                   | `None`         | 导出依赖图   |

---

### PersonalMemory

个性化记忆系统。

```python
from src.memory import get_memory

memory = get_memory()

# 设置偏好
memory.set_preference(
    category=PreferenceCategory.CODING_STYLE,
    key="indentation",
    value="2 spaces"
)

# 获取偏好
value = memory.get_preference(
    PreferenceCategory.CODING_STYLE,
    "indentation",
    default="4 spaces"
)

# 记录命令
memory.record_command("npm test", success=True)

# 获取命令建议
suggestions = memory.get_command_suggestions("git")

# 记录错误修复
memory.record_error_fix(
    error_pattern="ModuleNotFoundError",
    error_type="ImportError",
    fix_description="Install missing module",
    fix_code="pip install <module>"
)

# 查找修复
fixes = memory.find_fix_for_error("ModuleNotFoundError: requests")
```

#### 方法

| 方法                      | 参数                        | 返回             | 描述     |
| ------------------------- | --------------------------- | ---------------- | -------- |
| `set_preference`          | `category, key, value`      | `None`           | 设置偏好 |
| `get_preference`          | `category, key, default`    | `Any`            | 获取偏好 |
| `record_command`          | `command, success, context` | `None`           | 记录命令 |
| `get_command_suggestions` | `prefix`                    | `list[str]`      | 获取建议 |
| `record_error_fix`        | `pattern, type, desc, code` | `None`           | 记录修复 |
| `find_fix_for_error`      | `error_message`             | `list[ErrorFix]` | 查找修复 |

---

### ClaudeCodeEnhancer

统一增强接口。

```python
from src.core import create_enhancer

enhancer = create_enhancer("/path/to/project")

# 准备上下文
context = enhancer.prepare_context("fix the login bug")

# 搜索代码
results = enhancer.search_code("authentication", n_results=10)

# 记录偏好
enhancer.remember_preference("tools", "formatter", "prettier")

# 获取命令建议
suggestions = enhancer.get_command_suggestions("npm")

# 查找错误修复
fixes = enhancer.find_error_fix("TypeError: undefined is not a function")

# 学习项目
stats = enhancer.learn_project()

# 生成 CLAUDE.md
content = enhancer.generate_claudemd()
```

---

## 数据类

### Impact

```python
@dataclass
class Impact:
    file_path: str
    impact_level: ImpactLevel  # CRITICAL, HIGH, MEDIUM, LOW
    reason: str
    suggested_changes: list[str]
    symbols_affected: list[str]
```

### CodeChunk

```python
@dataclass
class CodeChunk:
    id: str
    content: str
    file_path: str
    start_line: int
    end_line: int
    language: str
    metadata: dict
```

### Symbol

```python
@dataclass
class Symbol:
    name: str
    type: str  # function, class, variable, interface
    file_path: str
    line: int
    exported: bool
    signature: str
```

---

## 枚举

```python
class ImpactLevel(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class ContextLevel(Enum):
    FILE = "file"
    MODULE = "module"
    PROJECT = "project"

class PreferenceCategory(Enum):
    CODING_STYLE = "coding_style"
    TOOLS = "tools"
    LANGUAGE = "language"
    WORKFLOW = "workflow"
    OUTPUT = "output"
```
