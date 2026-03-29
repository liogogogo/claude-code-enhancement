# Claude Code Enhancement

> 让 Claude Code 记住你的偏好，理解你的项目，不重复犯错

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-41%20passing-brightgreen.svg)](tests/)

---

## 🎯 这个项目适合谁？

### ✅ 适合你，如果：

| 场景                     | 痛点                       | 我们解决                 |
| ------------------------ | -------------------------- | ------------------------ |
| **每天用 Claude Code**   | 每次都要重新解释项目背景   | ✅ 项目知识自动学习      |
| **频繁切换项目**         | 不同项目的配置要手动设置   | ✅ 一键切换 + 记忆持久化 |
| **修复过的问题又出现**   | Claude 会重复犯同样的错    | ✅ 错误知识库，不二过    |
| **改代码怕影响其他模块** | 不知道改动会影响哪些文件   | ✅ 多文件推理，预测影响  |
| **长对话上下文丢失**     | 聊多了 Claude 就忘了前面的 | ✅ 智能上下文管理        |
| **权限确认太繁琐**       | 每个命令都要点确认         | ✅ 28+ 命令自动允许      |

### ❌ 可能不适合，如果：

- 只是偶尔使用 Claude Code
- 项目非常简单（单文件脚本）
- 不想安装额外依赖

---

## 🚀 5 分钟快速开始

### 方式一：一键增强（推荐）

```bash
# 安装增强配置
curl -fsSL https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/config/install.sh | bash

# 生效
source ~/.zshrc

# 使用
cc  # 代替 claude，跳过权限确认
```

**立即获得**：

- ✅ 28+ 常用命令自动允许
- ✅ 自动代码格式化
- ✅ 危险命令拦截
- ✅ 任务完成提示音

### 方式二：完整安装（高级功能）

```bash
git clone https://github.com/liogogogo/claude-code-enhancement.git
cd claude-code-enhancement
pip install -e .

# 可选：向量搜索依赖
pip install chromadb sentence-transformers
```

---

## 📋 功能对比

| 功能         | 原生 Claude Code | + 本项目        |
| ------------ | ---------------- | --------------- |
| 记住用户偏好 | ❌ 每次重置      | ✅ 跨会话持久化 |
| 记住项目结构 | ❌ 需要重复解释  | ✅ 自动学习     |
| 错误不重犯   | ❌ 会重复犯错    | ✅ 错误知识库   |
| 改动影响分析 | ⚠️ 有限          | ✅ 多文件推理   |
| 长对话管理   | ⚠️ 会遗忘        | ✅ 智能压缩     |
| 命令权限     | ⚠️ 每次确认      | ✅ 自动允许     |

---

## 💡 使用场景

### 场景 1：大型项目开发

```python
from src.core import create_enhancer

enhancer = create_enhancer("/path/to/large-project")

# 1. 自动学习项目结构
stats = enhancer.learn_project()
# {files_analyzed: 156, patterns_found: 23, ...}

# 2. 智能搜索代码
results = enhancer.search_code("authentication flow", n_results=10)

# 3. 分析修改影响
impacts = enhancer.analyze_change("auth/login.ts", "add MFA")
for impact in impacts:
    print(f"{impact.file_path}: {impact.impact_level.value}")
# middleware/auth.ts: high
# tests/auth.test.ts: high
# api/user.ts: medium
```

### 场景 2：多项目切换

```python
from src.memory import get_memory

memory = get_memory()

# 项目 A 的偏好
memory.set_preference("coding_style", "indentation", "2 spaces")
memory.set_preference("tools", "formatter", "prettier")

# 项目 B 的偏好（自动切换）
memory.set_preference("coding_style", "indentation", "4 spaces")
memory.set_preference("tools", "formatter", "black")

# Claude 会记住每个项目的偏好
```

### 场景 3：错误修复知识积累

```python
# 第一次遇到错误
memory.record_error_fix(
    error_pattern="ModuleNotFoundError: No module named 'requests'",
    error_type="ImportError",
    fix_description="Install the missing package",
    fix_code="pip install requests",
)

# 下次遇到类似错误
fixes = memory.find_fix_for_error("ModuleNotFoundError: requests")
# 返回之前的修复方案，Claude 不用再猜
```

---

## 🏗️ 架构概览

```
┌─────────────────────────────────────────────────────┐
│                   用户层                             │
│   cc 命令 | Claude Code CLI | API 调用              │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│              增强层 (本项目)                         │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ 上下文管理  │  │ 多文件推理  │  │ 个性化记忆  │ │
│  │ (RAG)      │  │ (依赖分析)  │  │ (持久化)    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ 项目知识    │  │ 错误学习    │  │ 工作流模板  │ │
│  │ (自动学习)  │  │ (不重犯)    │  │ (自动化)    │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 📊 项目成熟度

| 维度         | 状态              | 说明                        |
| ------------ | ----------------- | --------------------------- |
| **核心功能** | ✅ 8 个模块       | 上下文、推理、记忆、知识... |
| **测试覆盖** | ✅ 41 个测试      | 单元 + 集成测试             |
| **CI/CD**    | ✅ GitHub Actions | 自动测试 + 构建             |
| **文档**     | ✅ 完整           | API + 快速开始 + 架构       |
| **开源合规** | ✅ 100%           | LICENSE, CONTRIBUTING, CoC  |

---

## 📁 项目结构

```
claude-code-enhancement/
├── config/                 # 一键安装配置
│   ├── install.sh
│   └── settings.template.json
├── src/
│   ├── core/               # 核心模块
│   │   ├── context_manager.py      # 上下文管理
│   │   ├── multi_file_reasoning.py # 多文件推理
│   │   ├── project_knowledge.py    # 项目知识
│   │   └── unified.py              # 统一接口
│   ├── memory/             # 记忆系统
│   │   └── personal_memory.py
│   └── layer0-3/           # 四层架构
├── tests/                  # 测试 (41 个)
├── docs/                   # 文档
└── Makefile               # 常用命令
```

---

## 📖 文档

| 文档                                | 内容           |
| ----------------------------------- | -------------- |
| [快速开始](docs/QUICK_START.md)     | 5 分钟上手指南 |
| [API 参考](docs/API.md)             | 完整 API 文档  |
| [架构设计](docs/ARCHITECTURE_V2.md) | 四层架构详解   |
| [贡献指南](CONTRIBUTING.md)         | 如何贡献代码   |

---

## 🔧 常用命令

```bash
make install     # 安装依赖
make test        # 运行测试
make test-cov    # 测试 + 覆盖率
make lint        # 代码检查
make format      # 格式化代码
make build       # 构建发布包
```

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 许可证

[MIT License](LICENSE)

---

## ❓ 常见问题

### Q: 和原版 Claude Code 冲突吗？

**A**: 不冲突。本项目是增强层，可以随时开启/关闭。

### Q: 需要额外付费吗？

**A**: 不需要。本项目免费开源，使用你的 Claude API。

### Q: 支持哪些语言？

**A**: Python, TypeScript, JavaScript, Go, Rust 的代码分析。

### Q: 数据存储在哪里？

**A**: 本地 `~/.claude/` 目录，不会上传到任何服务器。

---

**GitHub**: https://github.com/liogogogo/claude-code-enhancement

**让 Claude Code 更懂你** 🚀
