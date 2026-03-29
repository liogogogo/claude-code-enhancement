# Claude Code 配置增强

> 一键增强 Claude Code 开发体验

## ✨ 功能

| 功能                | 说明                                           |
| ------------------- | ---------------------------------------------- |
| 🚀 **自动允许命令** | 28+ 常用命令无需确认 (git, npm, pip, cargo 等) |
| 🎨 **自动格式化**   | 编辑文件后自动运行 prettier                    |
| 🛡️ **危险命令拦截** | 阻止 rm -rf, drop table, truncate 等           |
| 🔔 **完成提示音**   | 任务结束时播放声音提醒                         |
| ⚡ **cc 别名**      | 短命令 + 跳过权限确认                          |

## 📦 安装

### 方式一：一行安装 (推荐)

```bash
curl -fsSL https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/config/install.sh | bash
```

### 方式二：克隆后安装

```bash
git clone git@github.com:liogogogo/claude-code-enhancement.git
cd claude-code-enhancement/config
./install.sh
```

### 方式三：手动复制

```bash
# 复制配置模板到 Claude 配置目录
cp settings.template.json ~/.claude/settings.json

# 手动添加别名到 ~/.zshrc 或 ~/.bashrc
echo "alias cc='claude --dangerously-skip-permissions'" >> ~/.zshrc
```

## 🎯 使用

安装完成后：

```bash
# 生效配置
source ~/.zshrc  # 或 source ~/.bashrc

# 使用短命令启动 Claude Code
cc

# 原命令仍然可用
claude
```

## 📁 文件说明

```
config/
├── install.sh              # 安装脚本（支持本地和远程）
├── uninstall.sh            # 卸载脚本
├── settings.template.json  # 配置模板（无敏感信息）
└── README.md               # 本文件
```

## ⚙️ 配置详情

### 自动允许的命令

以下命令执行时无需每次确认：

```
sed, git, cd, npm, yarn, pnpm, bun, pip, pip3
python, python3, node, make, cargo, go
mkdir, cp, mv, touch, cat, ls, curl, jq, echo
which, pwd, rm, kill
```

### Hooks 说明

| Hook          | 触发时机      | 功能                 |
| ------------- | ------------- | -------------------- |
| `PostToolUse` | Edit/Write 后 | 自动 prettier 格式化 |
| `PreToolUse`  | Bash 执行前   | 拦截危险命令         |
| `Stop`        | Claude 停止时 | 播放提示音           |

## 🔧 自定义

### 添加更多自动允许的命令

编辑 `~/.claude/settings.json`：

```json
{
  "permissions": {
    "allow": ["Bash(your-command:*)"]
  }
}
```

### 添加自定义 Hook

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [{ "type": "command", "command": "your-command" }]
      }
    ]
  }
}
```

## 🗑️ 卸载

```bash
# 如果是克隆安装
cd claude-code-enhancement/config
./uninstall.sh

# 或手动恢复备份
cp ~/.claude/settings.json.backup.* ~/.claude/settings.json
```

## 🔄 更新

```bash
# 克隆方式
cd claude-code-enhancement
git pull
./config/install.sh

# 一行安装方式（重新运行即可）
curl -fsSL https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/config/install.sh | bash
```

## 📋 系统要求

- macOS 或 Linux
- [jq](https://stedolan.github.io/jq/) - JSON 处理
- [Node.js](https://nodejs.org/) - prettier 依赖
- [curl](https://curl.se/) 或 wget - 远程安装时需要

### 安装依赖

```bash
# macOS
brew install jq node curl

# Ubuntu/Debian
sudo apt install jq nodejs npm curl

# Arch Linux
sudo pacman -S jq nodejs npm curl
```

## 🆕 在新机器上快速部署

```bash
# 一行命令搞定
curl -fsSL https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/config/install.sh | bash && source ~/.zshrc && cc
```

## ❓ 常见问题

### Q: 安装后 cc 命令找不到？

```bash
source ~/.zshrc  # 或 source ~/.bashrc
```

### Q: prettier 格式化不生效？

确保项目有 prettier 配置，或安装全局 prettier：

```bash
npm install -g prettier
```

### Q: 如何恢复到原始配置？

备份文件位于 `~/.claude/settings.json.backup.*`

```bash
# 查看备份
ls ~/.claude/settings.json.backup.*

# 恢复
cp ~/.claude/settings.json.backup.XXXXXXXX ~/.claude/settings.json
```

## 📚 参考

- [Claude Code 官方文档](https://docs.anthropic.com/claude-code)
- [50 Claude Code Tips](https://www.builder.io/blog/claude-code-tips-best-practices)
- [Claude Code Best Practices](https://antjanus.com/ai/claude-code-best-practices)
