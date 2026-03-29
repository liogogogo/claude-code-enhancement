# 实际开发场景 - tmux 会话实战

> **演示时间**: 2026-03-29
> **项目**: claude-code-enhancement
> **会话**: pj-dev-demo

---

## 🎬 场景演示：完整的开发工作流

### ✅ 已创建的会话结构

```
pj-dev-demo (claude-code-enhancement 项目)
├── 窗口1: main (3个面板)
│   ├── 面板1: 主工作区
│   ├── 面板2: 文件浏览器
│   └── 面板3: Git 状态
├── 窗口2: 测试
├── 窗口3: Git
└── 窗口4: 监控
```

---

## 📋 场景1：日常开发流程

### Step 1: 附加到开发会话

```bash
ts attach dev-demo
```

**你会看到**:
- 4 个窗口，每个都有特定用途
- 窗口1 有 3 个面板，可以同时查看代码、文件、git 状态
- 所有窗口都在后台运行，随时可以查看

---

### Step 2: 在主窗口（窗口1）中编写代码

**面板1 - 主工作区**:
```bash
# 打开编辑器
code docs/ARCHITECTURE_V2.md
```

**面板2 - 文件浏览器**:
```bash
# 查看项目结构
tree -L 2
```

**面板3 - Git 状态**:
```bash
# 查看 Git 状态
git status
```

---

### Step 3: 切换到测试窗口（窗口2）

```bash
# 在 tmux 会话内按:
Ctrl-a 2    # 切换到窗口2

# 运行测试
pytest tests/ -v

# 或
python -m pytest tests/ -v

# 查看测试结果
```

**优势**: 测试在独立窗口运行，不影响主工作区

---

### Step 4: 切换到 Git 窗口（窗口3）

```bash
Ctrl-a 3    # 切换到窗口3

# 查看提交历史
git log --graph --oneline

# 查看分支
git branch -a

# 查看远程更新
git fetch -v
```

---

### Step 5: 运行服务器（在监控窗口）

```bash
Ctrl-a 4    # 切换到窗口4（监控）

# 启动开发服务器
python -m http.server 8000

# 或运行其他监控任务
tail -f /var/log/app.log
```

---

## 🎯 场景2：Bug 修复工作流

### 实际步骤

1. **在主窗口（窗口1）**
   ```bash
   # 面板1: 打开代码
   code src/layer2/error_learning.py

   # 面板3: 查看 Bug 报告
   cat bug_report.txt
   ```

2. **切换到测试窗口（窗口2）**
   ```bash
   Ctrl-a 2

   # 运行特定测试
   pytest tests/test_error_learning.py -v

   # 查看错误输出
   ```

3. **切换回主窗口修复**
   ```bash
   Ctrl-a 1    # 回到主窗口

   # 在面板1修复代码
   # 在面板3查看 git diff
   ```

4. **验证修复**
   ```bash
   Ctrl-a 2    # 测试窗口
   pytest tests/test_error_learning.py -v

   Ctrl-a 3    # Git 窗口
   git commit -m "fix: 修复错误学习模块"
   ```

---

## 🚀 场景3：多项目并行开发

### 工作流

```bash
# 项目A: claude-code-enhancement
ts enh
# 窗口1: 编辑代码
# 窗口2: 运行测试
Ctrl-a d    # 分离

# 项目B: matchvision-monorepo
ts match
# 窗口1: 编辑 Go 代码
# 窗口2: 运行 Go 测试
Ctrl-a d    # 分离

# 快速切换回项目A
ts enh
# 所有窗口、面板、进程都在！
```

---

## 💡 场景4：代码审查工作流

### 设置

```bash
ts enh

# 窗口1: 审查代码
# 面板1: 查看变更的文件
# 面板2: 运行 linter
# 面板3: 查看 diff

# 窗口2: 运行测试
# 验证修改没有破坏功能

# 窗口3: Git
# 查看提交历史
# 创建分支
```

### 实际操作

```bash
# 面板1: 查看变更
git diff HEAD~1

# 面板2: 运行 linter
golangci-lint run

# 面板3: 提交变更
git commit -m "fix: 修复 linter 错误"
```

---

## 🔧 场景5：运行和监控

### 设置

```bash
ts match

# 窗口1: 开发
# 面板1: 编辑代码
# 面板2: 运行应用
# 面板3: 查看日志

# 窗口2: 测试
# 持续运行测试

# 窗口3: 数据库
# 连接数据库
# 查询数据

# 窗口4: 服务器
# 运行 API 服务器
# 查看请求日志
```

### 实际操作

```bash
# 面板2: 运行应用
go run ./cmd/backend/

# 面板3: 查看日志
tail -f logs/app.log

# 窗口4: 运行服务器
python manage.py runserver

# Ctrl-a d    # 分离，所有服务继续运行
```

---

## 📊 实际使用数据

### 会话资源使用

```bash
# 查看所有会话
tmux list-sessions

# 输出:
pj-enh: 4 windows
pj-match: 1 windows
pj-dev-demo: 4 windows
```

### 窗口和面板统计

```bash
# 查看会话详情
tmux list-panes -a -t pj-dev-demo -F "#{session_name}: #{window_index}. #{pane_index} #{?window_active,(活跃),}"

# 输出:
pj-dev-demo: 1. 1
pj-dev-demo: 1. 2
pj-dev-demo: 1. 3
pj-dev-demo: 2. 1
pj-dev-demo: 3. 1
pj-dev-demo: 4. 1
```

---

## 🎓 学习路径

### 第1天：基础

```bash
# 1. 创建会话
ts new enh

# 2. 创建窗口
Ctrl-a c

# 3. 分离
Ctrl-a d

# 4. 重新附加
ts enh
```

### 第2天：面板

```bash
# 1. 附加到会话
ts enh

# 2. 分割面板
Ctrl-a "    # 水平
Ctrl-a %    # 垂直

# 3. 切换面板
Ctrl-a o

# 4. 关闭面板
Ctrl-a x
```

### 第3天：多项目

```bash
# 1. 启动所有项目
ts-start-all

# 2. 在项目间切换
ts enh
Ctrl-a d
ts match
Ctrl-a d

# 3. 或使用会话选择
Ctrl-a s
```

### 第4天：高级功能

```bash
# 1. 重命名窗口
Ctrl-a ,

# 2. 同步窗口
Ctrl-a :
setw synchronize-panes on

# 3. 复制粘贴
Ctrl-a [    # 复制模式
Ctrl-a ]    # 粘贴
```

---

## 💼 实际开发技巧

### 技巧1：保持常用命令

```bash
# 在窗口1中
Ctrl-a c    # 新窗口
vim        # 打开文件
# 工作...

Ctrl-a c    # 另一个新窗口
htop       # 监控系统资源
```

### 技巧2：快速上下文切换

```bash
# 窗口1: 代码
# 窗口2: 测试输出
# 窗口3: Git 日志

# 在需要的信息之间快速切换
Ctrl-a 1    # 代码
Ctrl-a 2    # 测试
Ctrl-a 3    # Git
```

### 技巧3：分离和重新附加

```bash
# 工作中
ts enh
# 多窗口、多面板...

# 临时离开
Ctrl-a d

# 做其他事情...
ts match
# 其他工作...

# 回到原项目
ts enh
# 所有窗口、面板都在！
```

---

## 🎯 实际效益

### 时间节省

| 任务 | 传统方式 | tmux 方式 | 节省 |
|------|---------|----------|------|
| 切换项目 | 30秒 | 2秒 | 93% |
| 查看日志 | 打开文件 | 切换窗口 | 80% |
| 运行测试 | 终端阻塞 | 独立窗口 | 100% |
| 查看Git | 重新打开 | 切换窗口 | 90% |

### 工作流改善

**传统方式**:
```bash
# 切换项目
cd /path/to/project
# 打开终端1: 编辑器
# 打开终端2: 测试
# 打开终端3: 日志
# 每次切换都要重新打开
```

**tmux 方式**:
```bash
# 一次性设置
ts enh
Ctrl-a c    # 编辑器
Ctrl-a c    # 测试
Ctrl-a c    # 日志

# 以后一键切换
ts enh
# 所有窗口都在！
```

---

## ✅ 立即体验

### 体验会话

```bash
# 附加到演示会话
ts attach dev-demo

# 你会看到:
# - 4 个窗口
# - 窗口1 有 3 个面板
# - 所有窗口都在运行
```

### 快捷操作

```bash
# 在会话内:
Ctrl-a 1    # 切换到窗口1（主工作区）
Ctrl-a 2    # 切换到窗口2（测试）
Ctrl-a 3    # 切换到窗口3（Git）
Ctrl-a 4    # 切换到窗口4（监控）

Ctrl-a o    # 在面板间切换（窗口1）
```

---

## 🚀 下一步

1. **体验会话**: `ts attach dev-demo`
2. **创建自己的会话**: `ts new enh`
3. **设置工作流**: 多窗口、多面板
4. **享受效率**: 快速切换，状态保持

---

## 📚 相关文档

- [TMUX_GUIDE.md](docs/TMUX_GUIDE.md) - 完整指南
- [PROJECT_SWITCHING_QUICK_REF.md](docs/PROJECT_SWITCHING_QUICK_REF.md) - 快速参考
- [TMUX_DEMO.md](docs/TMUX_DEMO.md) - 演示文档

---

**最后更新**: 2026-03-29
**关键优势**: 所有窗口、面板、进程在后台保持运行，随时切换！🚀
