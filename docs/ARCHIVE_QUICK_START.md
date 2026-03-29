# 项目归档快速指南

> **创建时间**: 2026-03-29
> **目标**: 统一管理所有项目到 `~/Development/`

---

## 🎯 推荐方案：按状态分类

```
~/Development/
├── active/        # 活跃开发 (4个项目)
│   ├── claude-code-enhancement/
│   ├── matchvision-monorepo/
│   ├── ai_doc_manager/
│   └── tennis-ai-showcase/
├── on-hold/       # 暂停 (2个项目)
│   ├── tennis_yolo/
│   └── TrackNetV4_plus/
├── completed/     # 已完成 (1个项目)
│   └── ai-resume-showcase/
└── reference/     # 参考资料 (3个项目)
    ├── github_cv/
    ├── new_cv/
    └── openclaw-config/
```

---

## 🚀 快速开始

### Step 1: 预览归档计划

```bash
preview-archive
```

**会显示**:
- 所有项目的移动路径
- Git 仓库状态
- 磁盘空间占用
- 分类统计

### Step 2: 确认并执行

```bash
archive-projects status
```

**会执行**:
- 创建 `~/Development/` 目录结构
- 移动所有项目到对应分类
- 保持 Git 历史完整
- 生成项目清单
- 创建工具更新指南

### Step 3: 更新工具配置

归档完成后，查看更新指南:

```bash
cat ~/Development/UPDATE_TOOLS.md
```

然后编辑 `~/.local/bin/ts` 和 `~/.local/bin/pj`:

```bash
# 更新项目路径为:
"enh:$HOME/Development/active/claude-code-enhancement"
"match:$HOME/Development/active/matchvision-monorepo"
# ...
```

### Step 4: 测试切换

```bash
# 测试 ts (tmux 会话)
ts enh

# 测试 pj (新 shell)
pj match
```

---

## 📊 项目分类详情

### ✅ Active (活跃开发)

| 项目 | 技术栈 | 说明 |
|------|--------|------|
| claude-code-enhancement | Python 3.11+, PyTorch | Claude Code 自我增强系统 |
| matchvision-monorepo | Go 1.24+, Swift 6.0 | 网球视频分析平台 |
| ai_doc_manager | Python | AI 文档管理器 |
| tennis-ai-showcase | Python | 网球 AI 展示 |

### ⏸️ On-hold (暂停)

| 项目 | 说明 |
|------|------|
| tennis_yolo | 暂时搁置 |
| TrackNetV4_plus | 暂时搁置 |

### ✅ Completed (已完成)

| 项目 | 说明 |
|------|------|
| ai-resume-showcase | 已完成的简历展示项目 |

### 📚 Reference (参考资料)

| 项目 | 类型 |
|------|------|
| github_cv | 参考资料 |
| new_cv | 参考资料 |
| openclaw-config | 配置参考 |

---

## 🔧 其他方案

### 方案 A: 扁平结构

```bash
archive-projects flat
```

```
~/Development/
├── active/    # 所有活跃项目
├── archive/   # 所有归档项目
└── temp/      # 临时项目
```

### 方案 B: 按类型分类

```bash
archive-projects category
```

```
~/Development/
├── ai-projects/       # AI 相关
├── mobile-projects/   # 移动端
├── web-projects/      # Web 项目
└── config/            # 配置
```

---

## ⚠️ 注意事项

### Git 历史保护

所有 Git 仓库的历史会自动保留:

```bash
# 验证 Git 历史
cd ~/Development/active/claude-code-enhancement
git log --oneline
# 可以看到完整的提交历史
```

### 重复项目处理

检测到重复的 `project` 目录:
- `/Users/liocc/project`
- `/Users/liocc/Documents/project`

归档脚本会提示手动处理这两个目录。

### 工具配置更新

归档后**必须**更新:
- `~/.local/bin/ts` - 项目路径
- `~/.local/bin/pj` - 项目路径
- `~/.local/bin/ts-start-all` - 启动脚本

---

## 📋 验证清单

归档完成后，验证:

- [ ] 所有项目已移动到 `~/Development/`
- [ ] Git 历史完整 (随机抽查几个仓库)
- [ ] `ts` 和 `pj` 工具正常工作
- [ ] 查看项目清单: `cat ~/Development/README.md`
- [ ] 清理旧目录 (如果为空)

---

## 🎯 后续优化

归档完成后，可以进一步优化:

### 1. 项目 README

在每个项目根目录创建 `README.md`:

```markdown
# 项目名称

**状态**: active | on-hold | completed | reference

## 描述
简短描述...

## 技术栈
- 语言: Python 3.11+
- 框架: ...

## 快速开始
\`\`\`bash
# 安装依赖
pip install -r requirements.txt

# 运行
python main.py
\`\`\`
```

### 2. 自动化脚本

创建快速启动脚本:

```bash
# ~/.local/bin/dev-quick
#!/bin/bash
cd ~/Development/active/claude-code-enhancement
ts attach enh
```

### 3. 备份策略

```bash
# 定期备份活跃项目
rsync -av ~/Development/active/ ~/Backup/active_$(date +%Y%m%d)/
```

---

## 💡 常见问题

### Q: 会丢失 Git 历史吗?

**A**: 不会。脚本使用 `mv` 移动目录，Git 会自动追踪历史。

### Q: 可以撤销吗?

**A**: 可以，手动移回原位置即可。Git 历史不受影响。

### Q: 如何修改项目分类?

**A**: 编辑 `~/.local/bin/preview-archive` 中的 `STATUS_MAP`，重新运行。

### Q: 归档后如何切换项目?

**A**:
```bash
# 使用 ts (推荐)
ts enh          # 切换到 claude-code-enhancement
ts match        # 切换到 matchvision-monorepo

# 或使用 cd
cd ~/Development/active/claude-code-enhancement
```

---

## 📚 相关文档

- [PROJECT_ARCHIVE_PLAN.md](PROJECT_ARCHIVE_PLAN.md) - 完整归档方案
- [PROJECT_SWITCHING.md](PROJECT_SWITCHING.md) - 项目切换指南
- [TMUX_GUIDE.md](TMUX_GUIDE.md) - tmux 会话管理

---

## ✅ 立即开始

```bash
# 1. 预览
preview-archive

# 2. 确认
archive-projects status

# 3. 验证
ls -la ~/Development/

# 4. 更新工具
cat ~/Development/UPDATE_TOOLS.md

# 5. 测试
ts enh
```

---

**准备好了吗？运行 `preview-archive` 开始吧！** 🚀
