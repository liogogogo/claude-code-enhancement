# Claude Code Enhancement Config

一键增强 Claude Code 开发体验的配置集。

## 功能

| 功能             | 说明                                           |
| ---------------- | ---------------------------------------------- |
| **自动允许命令** | 28+ 常用命令无需确认 (git, npm, pip, cargo 等) |
| **自动格式化**   | 编辑文件后自动运行 prettier                    |
| **危险命令拦截** | 阻止 rm -rf, drop table, truncate 等           |
| **完成提示音**   | 任务结束时播放声音提醒                         |
| **cc 别名**      | 短命令 + 跳过权限确认                          |

## 快速安装

```bash
# 克隆仓库
git clone git@github.com:liogogogo/claude-code-enhancement.git

# 运行安装脚本
cd claude-code-enhancement/config
chmod +x install.sh
./install.sh

# 生效别名
source ~/.zshrc  # 或 source ~/.bashrc
```

## 一行安装 (新机器)

```bash
git clone git@github.com:liogogogo/claude-code-enhancement.git ~/claude-code-enhancement && ~/claude-code-enhancement/config/install.sh
```

## 卸载

```bash
./uninstall.sh
```

## 文件说明

```
config/
├── settings.template.json  # 配置模板 (无敏感信息)
├── install.sh              # 安装脚本
├── uninstall.sh            # 卸载脚本
└── README.md               # 本文件
```

## 自定义

### 添加更多自动允许的命令

编辑 `settings.template.json`，在 `permissions.allow` 数组中添加：

```json
"Bash(your-command:*)"
```

### 添加更多 Hook

```json
"hooks": {
  "PostToolUse": [
    {
      "matcher": "Edit|Write",
      "hooks": [
        { "type": "command", "command": "your-command" }
      ]
    }
  ]
}
```

### 可用 Hook 事件

- `PreToolUse` - 工具执行前
- `PostToolUse` - 工具执行后
- `Stop` - Claude 停止时
- `Notification` - 通知时

## 注意事项

- 安装脚本会自动备份现有配置
- 模板不包含 API 密钥等敏感信息
- 首次安装需要手动配置 API 密钥

## 参考

- [Claude Code 官方文档](https://docs.anthropic.com/claude-code)
- [50 Claude Code Tips](https://www.builder.io/blog/claude-code-tips-best-practices)
