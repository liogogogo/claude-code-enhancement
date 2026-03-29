---
name: token-optimizer
description: 分析和管理 Claude Code token 消耗，清理旧会话，生成 .claudeignore。用户请求优化 token 或清理会话时自动触发。
---

# Token Optimizer Skill

分析和管理 Claude Code token 消耗。

## 用法

根据用户请求执行以下操作：

### 分析 Token 消耗
```bash
python3 ${CLAUDE_PROJECT_ROOT}/hooks/token_optimizer.py --analyze
```

显示：
- 各目录大小（会话历史、缓存、memory）
- Token 消耗热点
- 优化建议

### 清理旧会话
```bash
# 预览模式（不实际删除）
python3 ${CLAUDE_PROJECT_ROOT}/hooks/token_optimizer.py --clean --days 7

# 执行删除
python3 ${CLAUDE_PROJECT_ROOT}/hooks/token_optimizer.py --clean --execute --days 7
```

### 全部优化
```bash
python3 ${CLAUDE_PROJECT_ROOT}/hooks/token_optimizer.py --optimize
```

### 生成 .claudeignore 模板
```bash
python3 ${CLAUDE_PROJECT_ROOT}/hooks/token_optimizer.py --claudeignore
```

## 执行流程

1. 用户请求优化 token → 运行 `--analyze` 显示当前状态
2. 用户确认清理 → 运行 `--clean --execute`
3. 显示优化结果

## 注意事项

- `--days 7` 表示保留最近 7 天的会话
- 清理会删除 `.claude/projects/` 下的旧 `.jsonl` 文件
- `.claudeignore` 文件需要手动放到项目根目录或 `~/.claudeignore`