# MCP 集成指南

> Model Context Protocol (MCP) 让 Claude Code 能够连接外部服务和工具

## 快速开始

### 查看 MCP 状态

```bash
# 在 Claude Code 中运行
/mcp
```

### 配置位置

MCP 服务器配置在 `~/.claude/settings.json` 的 `mcpServers` 字段：

```json
{
  "mcpServers": {
    "服务器名称": {
      "type": "stdio|sse|http|ws",
      "command": "...",  // stdio 类型
      "url": "...",      // 网络类型
      "env": {}          // 环境变量
    }
  }
}
```

---

## 官方 MCP 服务器

### 1. Filesystem (文件系统)

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/liocc/Development"]
    }
  }
}
```

**功能**:
- 读写文件
- 创建目录
- 搜索文件
- 管理 Git 仓库

### 2. Memory (记忆存储)

```json
{
  "mcpServers": {
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    }
  }
}
```

**功能**:
- 跨会话记忆
- 存储用户偏好
- 项目上下文保存

**数据存储**: `~/.mcp/memory.json`

### 3. GitHub

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    }
  }
}
```

**前置条件**:
```bash
# 创建 GitHub Token: https://github.com/settings/tokens
# 需要权限: repo, issues, pull_requests
export GITHUB_TOKEN="ghp_xxxx"
```

**功能**:
- 创建/管理 Issues
- 创建/管理 Pull Requests
- 搜索代码
- 查看仓库信息

### 4. PostgreSQL

```json
{
  "mcpServers": {
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

**前置条件**:
```bash
export DATABASE_URL="postgresql://user:password@localhost:5432/dbname"
```

**功能**:
- 执行 SQL 查询
- 查看表结构
- 数据分析

### 5. SQLite

```json
{
  "mcpServers": {
    "sqlite": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-sqlite", "--db-path", "/path/to/database.db"]
    }
  }
}
```

### 6. Puppeteer (浏览器自动化)

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    }
  }
}
```

**功能**:
- 截图
- 网页抓取
- 表单填写
- 自动化测试

### 7. Fetch (HTTP 客户端)

```json
{
  "mcpServers": {
    "fetch": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-fetch"]
    }
  }
}
```

**功能**:
- HTTP 请求
- API 调用
- 网页内容获取

---

## 服务器类型详解

### stdio (本地进程)

最常用，适合本地工具：

```json
{
  "my-server": {
    "command": "python",
    "args": ["-m", "my_mcp_server"],
    "env": {
      "API_KEY": "${MY_API_KEY}"
    }
  }
}
```

### SSE (Server-Sent Events)

适合托管服务，支持 OAuth：

```json
{
  "asana": {
    "type": "sse",
    "url": "https://mcp.asana.com/sse"
  }
}
```

首次使用会提示浏览器授权。

### HTTP (REST API)

```json
{
  "api-service": {
    "type": "http",
    "url": "https://api.example.com/mcp",
    "headers": {
      "Authorization": "Bearer ${API_TOKEN}"
    }
  }
}
```

### WebSocket

```json
{
  "realtime": {
    "type": "ws",
    "url": "wss://mcp.example.com/ws"
  }
}
```

---

## 环境变量

### 使用方式

```json
{
  "env": {
    "GITHUB_TOKEN": "${GITHUB_TOKEN}",
    "DATABASE_URL": "${DATABASE_URL}"
  }
}
```

### 设置环境变量

**方式 1**: 在 `~/.claude/settings.local.json`:

```json
{
  "env": {
    "GITHUB_TOKEN": "ghp_xxxx",
    "DATABASE_URL": "postgresql://..."
  }
}
```

**方式 2**: 在 Shell 配置 (`~/.zshrc`):

```bash
export GITHUB_TOKEN="ghp_xxxx"
export DATABASE_URL="postgresql://..."
```

---

## 工具命名规则

MCP 工具名称格式：

```
mcp__<server-name>__<tool-name>
```

**示例**:
- `mcp__github__search_repositories`
- `mcp__filesystem__read_file`
- `mcp__memory__store`

### 在 Skills/Commands 中预授权

```markdown
---
allowed-tools: [
  "mcp__github__create_issue",
  "mcp__github__create_pull_request"
]
---
```

---

## 完整配置示例

```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/Users/liocc/Development"]
    },
    "memory": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-memory"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_TOKEN": "${GITHUB_TOKEN}"
      }
    },
    "postgres": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-postgres"],
      "env": {
        "DATABASE_URL": "${DATABASE_URL}"
      }
    }
  }
}
```

---

## 调试

### 启用调试模式

```bash
claude --debug
```

### 查看 MCP 日志

```bash
# macOS
tail -f ~/Library/Logs/Claude/mcp.log

# 或使用 --debug 输出
```

### 常见问题

| 问题 | 解决方案 |
|------|----------|
| 服务器未连接 | 检查 command/url 是否正确 |
| 工具不可用 | 运行 `/mcp` 查看服务器状态 |
| 认证失败 | 检查环境变量是否设置 |
| 权限被拒绝 | 在 settings.json 中添加工具到 permissions.allow |

---

## 参考链接

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [Claude Code MCP 文档](https://docs.claude.com/en/docs/claude-code/mcp)
- [官方 MCP 服务器列表](https://github.com/modelcontextprotocol/servers)
