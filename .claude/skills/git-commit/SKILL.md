---
name: git-commit
description: 智能生成 commit message 并提交代码。分析变更内容，生成符合 Conventional Commits 规范的提交信息。
---

# Git Commit Skill

智能分析代码变更，生成规范的 commit message 并执行提交。

## 提交流程

1. **检查工作区状态**
   ```bash
   git status
   git diff --stat
   ```

2. **分析变更内容**
   - 读取 diff 了解具体改动
   - 识别变更类型：feat/fix/refactor/docs/style/test/chore
   - 提取关键修改点

3. **生成 Commit Message**

   格式遵循 Conventional Commits：
   ```
   <type>(<scope>): <description>

   [optional body]

   [optional footer]
   ```

   **类型说明**：
   | 类型 | 说明 |
   |------|------|
   | feat | 新功能 |
   | fix | Bug 修复 |
   | refactor | 重构（非新功能、非修复） |
   | docs | 文档更新 |
   | style | 代码格式（不影响逻辑） |
   | test | 测试相关 |
   | chore | 构建/工具/依赖 |
   | perf | 性能优化 |

4. **执行提交**
   ```bash
   git add <files>
   git commit -m "<generated message>"
   ```

## 示例输出

```
feat(hooks): 添加权限学习 hook

- 自动记录用户授权决策
- 生成权限模式建议
- 支持白名单自动更新

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

## 注意事项

- 提交前确认用户意图
- 危险操作（如删除文件）需用户确认
- 自动添加 Co-Authored-By 标记
- 不自动 push，需用户手动执行
