# 快速开始指南

## 🚀 5 分钟上手

### 1. 安装

```bash
# 一行安装
curl -fsSL https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/config/install.sh | bash
```

### 2. 验证

```bash
source ~/.zshrc
cc  # 启动 Claude Code
```

### 3. 使用

```bash
# 在项目中
cd your-project
cc
```

---

## 📚 核心功能

### 1. 上下文管理

自动管理代码上下文，智能检索相关代码：

```python
from src.core import create_context_manager

cm = create_context_manager("/path/to/project")
cm.index_codebase()

# 搜索代码
results = cm.search("authentication flow")
```

### 2. 多文件推理

分析修改的影响范围：

```python
from src.core import create_reasoner

reasoner = create_reasoner("/path/to/project")
impacts = reasoner.analyze_change("auth/login.ts", "add MFA")

for impact in impacts:
    print(f"{impact.file_path}: {impact.impact_level.value}")
```

### 3. 个性化记忆

记住你的偏好和常用命令：

```python
from src.memory import get_memory

memory = get_memory()
memory.set_preference("coding_style", "indentation", "2 spaces")
```

---

## 🔧 配置

### CLAUDE.md

在项目根目录创建 `CLAUDE.md`：

```markdown
# 项目概述

## 开发命令

- npm test: 运行测试
- npm run build: 构建

## 代码规范

- 使用 2 空格缩进
- 使用单引号
```

---

## 📖 更多文档

- [API 文档](API.md)
- [架构设计](ARCHITECTURE.md)
- [贡献指南](../CONTRIBUTING.md)

---

## ❓ 常见问题

### Q: 如何更新？

```bash
curl -fsSL https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/config/install.sh | bash
```

### Q: 如何卸载？

```bash
cd claude-code-enhancement/config
./uninstall.sh
```

### Q: 配置文件在哪里？

```
~/.claude/
├── settings.json       # 主配置
├── memory/             # 个性化记忆
└── context/            # 上下文缓存
```
