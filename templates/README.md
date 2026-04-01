# Claude Code 权限等级模板

快速配置 Claude Code 权限的预设模板，按信任等级分类。

## 快速开始

```bash
# 推荐：使用安装脚本（自动检测环境、交互式选择等级和安装位置）
./config/install.sh

# 或直接指定参数
./config/install.sh --level l4 --scope global

# 远程一键安装
curl -fsSL https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/config/install.sh | bash
```

## 权限等级

| 等级   | 文件                 | 信任度  | 适用场景                      |
| ------ | -------------------- | ------- | ----------------------------- |
| **L1** | `l1-minimal.json`    | 🔒 最低 | CI/CD、不熟悉的项目、多人协作 |
| **L2** | `l2-standard-*.json` | 🔐 标准 | 日常开发、个人项目            |
| **L3** | `l3-elevated.json`   | 🔓 提升 | 可信项目、频繁文件操作        |
| **L4** | `l4-full-trust.json` | ♾️ 完全 | 私有项目、完全信任环境        |

## 安装脚本新功能

安装脚本 (`config/install.sh`) 现在支持：

- **环境自动检测** - 识别 CI/公司/容器/个人环境，给出推荐等级
- **交互式等级选择** - 显示详细等级说明，帮助用户选择
- **安装位置选择** - 支持全局 (`~/.claude/`) 或项目级 (`./.claude/`)
- **命令行参数** - 支持 `--level` 和 `--scope` 参数

---

## L1 - Minimal（最小权限）

**适用场景**：CI/CD、不熟悉的开源项目、多人协作

**允许的命令**：

- `git:*` - Git 操作
- `python:*`, `pip:*`, `pytest:*` - Python 工具
- `npm:*`, `node:*` - Node.js 工具
- `go:*` - Go 工具
- `ls`, `find`, `grep`, `mkdir` - 基础文件操作
- `gh:*` - GitHub CLI
- `WebSearch` - 网页搜索

**不包含**：文件删除、移动、MCP 服务器、Hooks

---

## L2 - Standard（标准权限）

### l2-standard-python.json

**适用场景**：Python 项目日常开发

**额外权限**：

- `.venv/bin/python:*` - 虚拟环境
- `ruff:*`, `black:*`, `mypy:*` - 代码质量工具
- MCP filesystem 服务器

### l2-standard-go.json

**适用场景**：Go 项目日常开发

**额外权限**：

- `gofmt:*`, `goimports:*`, `golangci-lint:*` - Go 工具链
- `dlv:*` - Delve 调试器
- `make:*` - Make 构建工具
- MCP filesystem 服务器

---

## L3 - Elevated（提升权限）

**适用场景**：可信项目、需要频繁文件操作

**额外权限**：

- `cp:*`, `mv:*` - 文件复制和移动
- `cat:*`, `head:*`, `tail:*` - 文件查看
- `tmux:*`, `curl:*`, `jq:*` - 系统工具
- `cargo:*` - Rust 工具
- `yarn:*`, `pnpm:*` - 更多包管理器

**额外功能**：

- 环境变量注入 (`ANTHROPIC_API_KEY`, `GITHUB_TOKEN`)
- MCP memory 服务器
- Prettier 自动格式化 Hook
- 权限学习 Hook

**安全拦截**：

- `rm -rf /*` - 禁止删除系统目录
- `sudo:*` - 禁止 sudo
- `chmod -R 777:*` - 禁止危险权限修改

---

## L4 - Full Trust（完全信任）⭐

**适用场景**：私有项目、个人开发环境、完全信任 Claude

**权限**：`allow: ["*"]` - 允许所有操作

**安全拦截**（仅极端危险命令）：

- `rm -rf /*`, `rm -rf /` - 删除整个系统
- `sudo rm -rf:*` - sudo 删除
- `mkfs:*` - 格式化磁盘
- `dd if=/dev/zero:*` - 清空磁盘
- Fork bomb `:(){ :|:& };:`

**推荐用法**：

```bash
# 个人项目目录
cd ~/my-private-project
mkdir -p .claude
cp /path/to/templates/l4-full-trust.json .claude/settings.json
```

---

## 使用方法

### 方法 1：复制到项目

```bash
# 在项目根目录执行
mkdir -p .claude
cp templates/l4-full-trust.json .claude/settings.json
```

### 方法 2：全局配置

```bash
# 应用到用户级配置
cp templates/l3-elevated.json ~/.claude/settings.json
```

### 方法 3：使用安装脚本

```bash
# 交互式选择
./config/install.sh --level l4
```

---

## 安全建议

| 场景                  | 推荐等级 |
| --------------------- | -------- |
| 生产环境服务器        | L1       |
| 公司内部项目          | L2       |
| 个人开发机            | L3       |
| 完全隔离的虚拟机/容器 | L4       |

**注意**：L4 级别虽然保留了极端危险命令的拦截，但仍需谨慎使用。
