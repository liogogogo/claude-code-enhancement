# tmux 会话演示 - 完整教程

> **演示时间**: 2026-03-29
> **演示项目**: claude-code-enhancement, matchvision-monorepo

---

## 🎯 演示目标

展示如何使用 `ts` 工具创建和管理独立的项目会话

---

## 📋 演示步骤

### ✅ 第1步：查看初始状态

```bash
ts ls
```

**输出**:
```
📚 tmux 项目会话:

   (没有活跃的会话)

   ❌ [enh] claude-code-enhancement
   ❌ [match] matchvision-monorepo
   ❌ [proj] project
```

**说明**: 当前没有活跃的 tmux 会话

---

### ✅ 第2步：创建第一个会话

```bash
ts new enh
```

**输出**:
```
🚀 创建新会话: pj-enh
✅ 会话已创建（后台运行）
使用 'ts attach enh' 来附加
```

**说明**:
- 会话名称: `pj-enh`
- 项目路径: `/Users/liocc/claude-code-enhancement`
- 状态: 后台运行

---

### ✅ 第3步：验证会话已创建

```bash
ts ls
tmux list-sessions
```

**输出**:
```
📚 tmux 项目会话:

   ✅ [enh] claude-code-enhancement  ← 会话已启动

tmux 会话详情:
pj-enh: 1 windows (created Sun Mar 29 10:58:06 2026)
```

---

### ✅ 第4步：在会话中创建多个窗口

```bash
# 窗口1：编辑器
tmux new-window -t pj-enh -n "编辑器"

# 窗口2：Git状态
tmux new-window -t pj-enh -n "Git"

# 窗口3：测试
tmux new-window -t pj-enh -n "测试"
```

**查看窗口列表**:
```bash
tmux list-windows -t pj-enh
```

**输出**:
```
  1. enh (默认窗口)
  2. 编辑器
  3. Git
  4. 测试 (活跃)
```

**说明**:
- 会话中有 4 个窗口
- 每个窗口可以运行不同的命令
- 所有窗口独立运行

---

### ✅ 第5步：在窗口中创建面板

```bash
# 水平分割（上下）
tmux split-window -v -t pj-enh:1

# 垂直分割（左右）
tmux split-window -h -t pj-enh:1
```

**查看面板列表**:
```bash
tmux list-panes -t pj-enh:1
```

**输出**:
```
  面板 1: zsh [80x12]
  面板 2: zsh [40x11]
  面板 3: zsh [39x11]
```

**说明**:
- 窗口1被分割成 3 个面板
- 每个面板可以运行不同命令
- 面板间可以快速切换（Ctrl-a o）

---

### ✅ 第6步：切换到另一个项目

```bash
ts new match
```

**说明**:
- 创建新的会话 `pj-match`
- 不会影响 `pj-enh` 会话
- 两个会话完全独立

---

### ✅ 第7步：查看所有会话

```bash
ts ls
```

**输出**:
```
📚 tmux 项目会话:

   ✅ [enh] claude-code-enhancement
   ✅ [match] matchvision-monorepo
   ❌ [proj] project
```

**说明**:
- 两个项目会话都在运行
- 可以随时切换

---

### ✅ 第8步：管理会话

```bash
# 停止会话
ts stop match

# 验证已停止
ts ls

# 重新创建
ts new match
```

---

## 🎨 可视化展示

### tmux 会话结构

```
tmux 服务器
├── pj-enh (claude-code-enhancement)
│   ├── 窗口1: enh (3个面板)
│   │   ├── 面板1: zsh
│   │   ├── 面板2: zsh
│   │   └── 面板3: zsh
│   ├── 窗口2: 编辑器
│   ├── 窗口3: Git
│   └── 窗口4: 测试
│
└── pj-match (matchvision-monorepo)
    └── 窗口1: match
```

---

## 🎬 实际使用演示

### 场景1：日常开发工作流

```bash
# 早上启动
ts-start-all

# 切换到项目
ts enh

# 创建工作窗口
Ctrl-a c    # 新窗口：代码编辑
Ctrl-a c    # 新窗口：运行测试
Ctrl-a c    # 新窗口：查看日志

# 分离会话（工作保持）
Ctrl-a d

# 切换到另一个项目
ts match

# 晚上回家
exit

# 第二天早上
ts enh    # 直接回到昨天的状态！
```

### 场景2：运行长期任务

```bash
# 进入项目会话
ts match

# 创建新窗口
Ctrl-a c

# 运行长期任务
python run_long_test.py

# 分离会话（任务继续运行）
Ctrl-a d

# 切换到其他项目工作
ts enh

# 检查任务状态
ts match
Ctrl-a n    # 切换到任务窗口
```

### 场景3：多项目对比

```bash
# 项目A
ts enh
git status
Ctrl-a d    # 分离

# 项目B
ts match
git status
Ctrl-a d    # 分离

# 快速切换
ts switch    # 或 Ctrl-a s
# 选择会话
```

---

## 📊 命令总结

### 会话管理

```bash
ts                    # 列出会话
ts ls                 # 同上
ts <项目>             # 启动或附加
ts new <项目>         # 创建新会话
ts attach <项目>      # 附加到会话
ts stop <项目>        # 停止会话
ts switch             # 选择会话
ts here               # 当前会话信息
```

### tmux 快捷键

```
Ctrl-a d         # 分离（最重要！）
Ctrl-a s         # 切换会话
Ctrl-a c         # 新窗口
Ctrl-a n/p       # 上/下一个窗口
Ctrl-a o         # 切换面板
Ctrl-a "         # 水平分割
Ctrl-a %         # 垂直分割
Ctrl-a x         # 关闭面板
```

---

## 🎓 学习检查清单

### 基础

- [ ] 创建第一个会话: `ts new enh`
- [ ] 附加到会话: `ts enh`
- [ ] 分离会话: `Ctrl-a d`
- [ ] 查看会话: `ts ls`

### 进阶

- [ ] 创建多个窗口: `Ctrl-a c`
- [ ] 重命名窗口: `Ctrl-a ,`
- [ ] 创建面板: `Ctrl-a "` 和 `Ctrl-a %`
- [ ] 切换面板: `Ctrl-a o`

### 高级

- [ ] 多项目并行: `ts-start-all`
- [ ] 会话间切换: `ts switch` 或 `Ctrl-a s`
- [ ] 同步多窗口
- [ ] 复制粘贴

---

## 💡 关键要点

### 1. 独立会话

每个项目有独立的 tmux 会话：
- ✅ 工作状态完全保留
- ✅ 可以同时运行
- ✅ 切换不影响其他项目

### 2. 后台运行

会话在后台运行：
- ✅ 不占用终端
- ✅ 长期任务继续运行
- ✅ 随时可以重新附加

### 3. 多窗口多面板

每个会话可以有：
- 多个窗口（独立任务）
- 每个窗口多个面板（同时查看）

---

## 🚀 立即开始

```bash
# 1. 查看会话
ts

# 2. 创建会话
ts enh

# 3. 开始工作！
```

---

**最后更新**: 2026-03-29
