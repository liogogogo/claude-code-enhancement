# Settings 模板使用指南

## 快速开始

### 1. 选择模板

| 模板 | 适用场景 |
|------|----------|
| `settings.minimal.json` | 最小配置，常用命令 |
| `settings.python.json` | Python 项目 |
| `settings.go.json` | Go 项目 |
| `settings.local.json` | 完整配置，所有功能 |

### 2. 应用模板

**方式一：项目级配置（推荐）**

```bash
# 在项目根目录
mkdir -p .claude
cp ~/Development/active/claude-code-enhancement/templates/settings.python.json .claude/settings.json
```

**方式二：全局配置**

```bash
# 合并到全局配置
cat ~/Development/active/claude-code-enhancement/templates/settings.minimal.json >> ~/.claude/settings.json
```

### 3. 自定义

编辑 `.claude/settings.json`，根据项目需求调整：

```json
{
  "permissions": {
    "allow": [
      "Bash(git:*)",
      // 添加项目特定的权限...
    ]
  }
}
```

---

## 模板详解

### settings.minimal.json

最小配置，包含：
- Git 操作
- Python/Node/Go 基本命令
- 文件操作
- GitHub CLI
- Web 搜索

适合：新项目快速启动

### settings.python.json

Python 项目专用：
- pip/pip3 安装
- 虚拟环境支持
- pytest 测试
- ruff/black/mypy 代码质量

### settings.go.json

Go 项目专用：
- go build/test/run
- gofmt/goimports 格式化
- golangci-lint
- dlv 调试器
- make 构建工具

### settings.local.json

完整配置模板：
- 所有常用权限
- 环境变量配置
- MCP 服务器
- Hooks 配置

---

## 权限模式说明

### 通配符规则

| 模式 | 含义 |
|------|------|
| `Bash(git:*)` | 所有 git 命令 |
| `Bash(git push:*)` | 所有 git push 操作 |
| `Bash(pip install:*)` | 所有 pip install 操作 |

### 精确匹配

```json
"Bash(ls -la)"
```

只允许 `ls -la` 这一个命令。

---

## 环境变量

### 安全存储

敏感信息放在 `settings.local.json`：

```json
{
  "env": {
    "GITHUB_TOKEN": "${GITHUB_TOKEN}",
    "DATABASE_URL": "${DATABASE_URL}"
  }
}
```

### Shell 配置

在 `~/.zshrc` 中设置：

```bash
export GITHUB_TOKEN="ghp_xxxx"
export DATABASE_URL="postgresql://..."
```

---

## MCP 服务器

### 项目根目录变量

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "${PROJECT_ROOT}"]
    }
  }
}
```

`${PROJECT_ROOT}` 会自动替换为项目根目录路径。

---

## Hooks

### 配置位置

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "permission_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "python3 ${PROJECT_ROOT}/hooks/permission_learning_hook.py"
          }
        ]
      }
    ]
  }
}
```

### 支持的 Hook 类型

| Hook | 触发时机 |
|------|----------|
| PreToolUse | 工具执行前 |
| PostToolUse | 工具执行后 |
| Notification | 通知事件 |
| Stop | 会话结束 |
| UserPromptSubmit | 用户提交消息 |

---

## 最佳实践

### 1. 项目级优先

每个项目独立配置，避免全局污染。

### 2. 最小权限原则

只添加需要的权限，不用通配符 `Bash(*)`。

### 3. 敏感信息隔离

Token、密码放在 `settings.local.json`，不要提交到 git。

### 4. 团队共享

非敏感配置提交到 `.claude/settings.json`，团队成员共享。

### 5. .gitignore 配置

```gitignore
# Claude Code
.claude/settings.local.json
```
