# 项目归档方案

> **目标**: 将所有项目统一归档到一个目录
> **日期**: 2026-03-29

---

## 🎯 归档目标

1. **统一管理**: 所有项目在一个父目录下
2. **清晰分类**: 按类型/状态组织
3. **便于切换**: 快速访问任何项目
4. **保持历史**: Git 历史完整保留
5. **易于备份**: 一个目录包含所有项目

---

## 📁 推荐目录结构

### 方案 A: 扁平结构（推荐）

```
~/Development/
├── active/                    # 活跃项目
│   ├── claude-code-enhancement/
│   ├── matchvision-monorepo/
│   ├── ai_doc_manager/
│   └── tennis-ai-showcase/
├── archive/                  # 归档项目
│   ├── ai-resume-showcase/
│   ├── tennis_yolo/
│   ├── TrackNetV4_plus/
│   ├── github_cv/
│   ├── new_cv/
│   └── openclaw-config/
└── temp/                     # 临时项目
```

### 方案 B: 分类结构（按类型）

```
~/Development/
├── ai-projects/              # AI 相关
│   ├── claude-code-enhancement/
│   ├── ai_doc_manager/
│   ├── tennis-ai-showcase/
│   └── TrackNetV4_plus/
├── mobile-projects/         # 移动端
│   ├── tennis_yolo/
│   └── matchvision-monorepo/
├── web-projects/             # Web 项目
│   ├── github_cv/
│   └── new_cv/
└── config/                   # 配置
    └── openclaw-config/
```

### 方案 C: 状态结构（推荐⭐）

```
~/Development/
├── active/                    # 正在开发
│   ├── claude-code-enhancement/
│   ├── matchvision-monorepo/
│   ├── ai_doc_manager/
│   └── tennis-ai-showcase/
├── on-hold/                  # 暂停
│   ├── tennis_yolo/
│   └── TrackNetV4_plus/
├── completed/                # 已完成
│   ├── ai-resume-showcase/
│   └── github_cv/
└── reference/                # 参考资料
    ├── new_cv/
    └── openclaw-config/
```

---

## 🚀 推荐方案：方案 C（状态结构）

### 为什么选择方案 C？

1. **清晰的状态管理**
   - active: 当前工作重点
   - on-hold: 暂停但可能恢复
   - completed: 已完成的项目

2. **灵活的调整**
   - 项目状态随时可以调整
   - 支持项目并行开发

3. **易于备份**
   - 只备份 active/ 目录
   - 或整个 Development/ 目录

---

## 📋 具体归档计划

### 第1步：创建目录结构

```bash
# 创建主目录
mkdir -p ~/Development
cd ~/Development

# 创建子目录
mkdir -p active on-hold completed reference
```

### 第2步：移动项目

#### 活跃项目 (active/)

```
claude-code-enhancement  → ~/Development/active/claude-code-enhancement
matchvision-monorepo      → ~/Development/active/matchvision-monorepo
ai_doc_manager            → ~/Development/active/ai_doc_manager
tennis-ai-showcase       → ~/Development/active/tennis-ai-showcase
```

#### 暂停/归档项目

```
tennis_yolo              → ~/Development/on-hold/tennis_yolo
TrackNetV4_plus          → ~/Development/on-hold/TrackNetV4_plus
ai-resume-showcase      → ~/Development/completed/ai-resume-showcase
github_cv                 → ~/Development/reference/github_cv
new_cv                     → ~/Development/reference/new_cv
openclaw-config           → ~/Development/reference/openclaw-config
```

#### 处理重复的 project

```
/Users/liocc/project → 对比内容后决定
/Users/liocc/Documents/project → 合并或删除
```

---

## ⚙️ 自动化归档脚本

我可以为你创建一个自动归档脚本：

```bash
#!/bin/bash
# 自动归档所有项目到 ~/Development/

# 移动项目并保持 Git 历史
move_project() {
    local src="$1"
    local dest="$2"

    echo "移动: $src → $dest"

    # 使用 git 移动（保持历史）
    if [ -d "$src/.git" ]; then
        git -C "$src" remote -v
        mv "$src" "$dest"
    else
        mv "$src" "$dest"
    fi
}

# 执行归档
# ... 具体实现
```

---

## 🎯 分类建议

### 按项目状态

**active (活跃开发)**:
- claude-code-enhancement ⭐
- matchvision-monorepo
- ai_doc_manager
- tennis-ai-showcase

**on-hold (暂停)**:
- tennis_yolo
- TrackNetV4_plus

**completed (已完成)**:
- ai-resume-showcase

**reference (参考)**:
- github_cv
- new_cv
- openclaw-config

---

## 📋 实施步骤

### 选项 1: 手动归档（你控制每一步）

1. 创建目录结构
2. 逐个移动项目
3. 验证每个项目的 Git 历史完整
4. 更新工具配置（ts, pj）

### 选项 2: 自动归档（我帮你完成）

1. 你确认分类方案
2. 我创建自动化脚本
3. 执行归档
4. 验证结果

---

## ⚠️ 注意事项

### Git 历史保护

使用 `git mv` 而不是 `mv`：
```bash
# 推荐
git mv /Users/liocc/project ~/Development/active/project

# 而不是
mv /Users/liocc/project ~/Development/active/project
```

### 配置更新

归档后需要更新：
- `~/.local/bin/ts` - 项目路径
- `~/.local/bin/pj` - 项目路径
- `~/.local/bin/ts-start-all` - 启动脚本

---

## 💡 额外建议

### 1. 项目 README

在每个项目根目录创建 `README.md`:
```markdown
# 项目名称

## 状态: active | on-hold | completed | reference

## 描述
简短描述...

## 技术栈
- 语言: Python 3.11+
- 框架: ...

## 链接
- 文档: ...
- 部署: ...
```

### 2. 项目清单

创建 `~/Development/README.md`:
```markdown
# 开发项目总览

## 活跃项目
- [claude-code-enhancement](active/claude-code-enhancement/)
- [matchvision-monorepo](active/matchvision-monorepo/)
- ...

## 暂停项目
- [tennis_yolo](on-hold/tennis_yolo/)
- ...
```

---

## 🎯 下一步行动

**请告诉我**:

1. **选择方案**: 方案 A（扁平）或 方案 B（分类）或 方案 C（状态）？

2. **项目分类**: 哪些项目是 active/on-hold/completed？

3. **执行方式**:
   - **选项 A**: 我提供脚本，你来执行（推荐）
   - **选项 B**: 我自动执行（需要你的确认）

---

**准备好了吗？告诉我你的选择，我会立即为你创建归档方案！** 🚀
