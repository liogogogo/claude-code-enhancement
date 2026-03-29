# Permission Learning Hook 使用指南

## 功能概述

Permission Learning Hook 是一个智能权限学习系统：

1. **自动记录** - 记录你对每个权限请求的决策（允许/拒绝）
2. **模式归纳** - 从具体命令中提取通用权限模式
3. **智能建议** - 基于使用频率生成权限建议

## 安装

### 方式一：项目级配置（推荐）

在项目根目录创建 `.claude/settings.json`：

```json
{
  "permissions": {
    "allow": []
  }
}
```

然后将 `hooks/hooks.json` 的内容复制进去。

### 方式二：全局配置

编辑 `~/.claude/settings.json`，添加：

```json
{
  "hooks": {
    "Notification": [
      {
        "matcher": "permission_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "python3 /Users/liocc/Development/active/claude-code-enhancement/hooks/permission_learning_hook.py",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

## 使用

### 日常使用

Hook 会在每次权限请求时自动运行，记录你的决策。

### 查看学习报告

```bash
# 完整报告
python3 ~/Development/active/claude-code-enhancement/hooks/permission_report.py

# 只看建议
python3 ~/Development/active/claude-code-enhancement/hooks/permission_report.py --suggest

# 只看统计
python3 ~/Development/active/claude-code-enhancement/hooks/permission_report.py --stats
```

### 导出建议

```bash
# 生成可直接复制到 settings.json 的格式
python3 ~/Development/active/claude-code-enhancement/hooks/permission_report.py --export
```

## 数据存储

| 文件 | 用途 |
|------|------|
| `~/.claude/permission_learning.json` | 学习数据（允许/拒绝记录） |
| `~/.claude/permission_suggestions.json` | 生成的建议 |

## 支持的模式

Hook 会自动归纳以下类型的权限模式：

| 类型 | 示例 | 归纳模式 |
|------|------|----------|
| Git | `Bash(git push:origin main)` | `Bash(git push:*)` |
| pip | `Bash(pip install:requests)` | `Bash(pip install:*)` |
| pytest | `Bash(python -m pytest:tests/)` | `Bash(python -m pytest:*)` |
| mkdir | `Bash(mkdir:-p foo/bar)` | `Bash(mkdir:*)` |
| gh CLI | `Bash(gh pr view:123)` | `Bash(gh pr:*)` |
| tmux | `Bash(tmux new-session:-s foo)` | `Bash(tmux new-session:*)` |
| ... | ... | ... |

## 自定义模式

编辑 `permission_learning_hook.py` 中的 `PATTERN_RULES` 添加新的模式规则：

```python
PATTERN_RULES = [
    {
        "match": r"^Bash\(your-command (\w+):.*\)$",
        "pattern": "Bash(your-command {command}:*)",
        "description": "Your command description",
    },
    # ...
]
```

## 隐私说明

- 所有数据存储在本地 `~/.claude/` 目录
- 不发送任何数据到远程服务器
- 可随时删除学习数据文件

## 故障排查

查看调试日志：

```bash
tail -f /tmp/permission-learning-debug.log
```
