# Cursor 项目路径迁移指南

> **归档日期**: 2026-03-29
> **影响**: 所有项目路径已从分散位置迁移到 `~/Development/`

---

## 🚀 快速开始

### 使用快捷命令（推荐）

```bash
# 重新加载配置
source ~/.zshrc

# 在 Cursor 中打开项目
ce enh           # 打开 claude-code-enhancement
ce match         # 打开 matchvision-monorepo
ce docmgr        # 打开 ai_doc_manager
```

---

## 📝 方式 1: Cursor GUI

### 重新打开项目

1. **关闭旧项目**
   - `File → Close Folder`

2. **打开新路径**
   - `File → Open Folder`
   - 选择: `~/Development/active/claude-code-enhancement`

---

## 💻 方式 2: 命令行

### Cursor CLI

```bash
# 安装 Cursor CLI（如果未安装）
# 在 Cursor 中: Cmd+Shift+P → "Shell Command: Install 'cursor' command"

# 打开项目
cursor open ~/Development/active/claude-code-enhancement

# 或使用快捷命令
ce enh
```

### 使用 open 命令

```bash
open -a "Cursor" ~/Development/active/claude-code-enhancement
```

---

## 🎯 项目路径对照

| 项目 | 旧路径 | 新路径 |
|------|--------|--------|
| claude-code-enhancement | `~/claude-code-enhancement` | `~/Development/active/claude-code-enhancement` |
| matchvision-monorepo | `~/matchvision-monorepo` | `~/Development/active/matchvision-monorepo` |
| ai_doc_manager | `~/Documents/ai_doc_manager` | `~/Development/active/ai_doc_manager` |
| tennis-ai-showcase | `~/Documents/tennis-ai-showcase` | `~/Development/active/tennis-ai-showcase` |

---

## 🔄 清理旧引用

### 清理"最近打开"

```bash
# 编辑 Cursor 工作区配置
vim ~/Library/Application\ Support/Cursor/User/globalStorage/workspace.json

# 删除或替换旧路径
```

---

## ✅ 快捷命令（已配置）

重新加载 shell 后可用：

```bash
ce <项目>       # 在 Cursor 中打开
ccd <项目>      # cd + Cursor 打开

# 项目名
enh / claude    # claude-code-enhancement
match           # matchvision-monorepo
docmgr / doc    # ai_doc_manager
tennis          # tennis-ai-showcase
```

---

## 💡 日常工作流

### 开发流程

```bash
# 1. 进入项目目录
enh

# 2. 在 Cursor 中打开
ce

# 3. 或一步到位
ccd enh
```

### tmux + Cursor

```bash
ts enh      # tmux 会话
ce enh      # Cursor 打开
# 在 tmux 中测试，在 Cursor 中编辑
```

---

## ⚠️ 重新索引

首次打开新路径，Cursor 会：
- 重新索引项目（几秒到几分钟）
- 重建符号索引
- 重新读取配置

查看索引进度：右上角活动图标

---

## 🔧 Cursor CLI 安装

```bash
# 在 Cursor 中执行
Cmd+Shift+P → "Shell Command: Install 'cursor' command"

# 验证
cursor --version
```

---

## 📚 完整文档

参见: [docs/CURSOR_MIGRATION.md](docs/CURSOR_MIGRATION.md)（完整版）

---

**准备好了？`ce enh` 开始！** 🚀
