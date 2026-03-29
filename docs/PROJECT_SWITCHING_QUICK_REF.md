# 项目切换 - 快速参考

## 🎯 三种切换方式对比

| 方式 | 命令 | 会话状态 | 适用场景 |
|------|------|---------|---------|
| **pj** | `pj <项目>` | ❌ 新 shell | 快速查看、简单切换 |
| **ts** | `ts <项目>` | ✅ 独立会话 | **日常开发（推荐）** |
| **cd** | `cd <路径>` | ❌ 当前 shell | 传统方式 |

---

## 🚀 推荐工作流：ts (tmux 会话)

### 为什么选择 ts？

✅ **保持工作状态**
- 切换项目后，之前的工作（窗口、面板、进程）全部保留
- 可以在后台运行长期任务

✅ **多项目并行**
- 同时在多个项目中工作
- 快速切换，无需重新初始化

✅ **高效工作流**
- 多窗口、多面板
- 会话内复制粘贴
- 同步多个窗口

---

## 📖 快速命令

### 基本命令

```bash
ts                   # 列出所有会话
ts enh               # 切换到 claude-code-enhancement
ts match             # 切换到 matchvision-monorepo
ts proj              # 切换到 project
```

### 高级命令

```bash
ts new enh           # 创建新会话（后台）
ts attach enh        # 附加到已有会话
ts stop enh          # 停止会话
ts switch            # 选择会话（菜单）
ts here              # 当前会话信息
```

### 批量操作

```bash
ts-start-all         # 启动所有项目会话
```

---

## ⌨️ tmux 快捷键（在会话内）

### 必记快捷键

```
Ctrl-a d            # 分离会话（最重要！）
Ctrl-a s            # 切换会话
Ctrl-a c            # 创建新窗口
Ctrl-a w            # 列出窗口
Ctrl-a 0-9          # 切换到窗口
```

### 面板操作

```
Ctrl-a "            # 水平分割
Ctrl-a %            # 垂直分割
Ctrl-a o            # 在面板间切换
Ctrl-a x            # 关闭面板
```

---

## 💡 典型场景

### 场景 1: 日常开发

```bash
# 早上启动
ts-start-all

# 切换到项目
ts match

# 在项目中创建多个窗口
Ctrl-a c    # 新窗口（编辑器）
Ctrl-a c    # 新窗口（测试）
Ctrl-a c    # 新窗口（日志）

# 分离会话（工作状态保持）
Ctrl-a d

# 切换到另一个项目
ts enh

# 晚上回家
# 直接关闭终端，会话保持后台运行

# 第二天早上
ts match    # 直接回到昨天的状态
```

### 场景 2: 运行长期任务

```bash
# 在 match 项目
ts match
# Ctrl-a c 创建新窗口
python run_long_test.py    # 运行测试
Ctrl-a d    # 分离，让它在后台运行

# 切换到其他项目工作
ts enh

# 检查测试结果
ts match
Ctrl-a n    # 切换到测试窗口
```

### 场景 3: 多项目对比

```bash
# 在三个项目间快速切换
ts match    # matchvision
Ctrl-a d    # 分离

ts enh      # enhancement
Ctrl-a d    # 分离

ts proj     # project
Ctrl-a d    # 分离

# 随时可以回到任何项目
ts match    # 回到 matchvision（状态完全保留）
```

---

## 🆚 pj vs ts

### 使用 pj 的场景

```bash
# 快速查看项目状态
pj here

# 快速切换（不需要保持状态）
pj match

# 查看所有项目
pj
```

### 使用 ts 的场景

```bash
# 开发工作（需要保持状态）
ts match

# 运行长期任务
ts match → Ctrl-a c → 运行任务 → Ctrl-a d

# 多项目并行
ts-start-all → 随时切换
```

---

## 📊 命令速查表

| 操作 | pj | ts | cd |
|------|----|----|----|
| 列出项目 | `pj` | `ts ls` | ❌ |
| 切换项目 | `pj match` | `ts match` | `cd /path` |
| 项目信息 | `pj here` | `ts here` | `pwd` |
| 会话管理 | ❌ | ✅ | ❌ |
| 后台运行 | ❌ | ✅ | ❌ |

---

## 🎓 学习路径

### 第1天：基础使用

```bash
# 1. 启动项目
ts match

# 2. 分离会话
Ctrl-a d

# 3. 重新附加
ts match
```

### 第2天：多窗口

```bash
# 1. 在会话中
ts match

# 2. 创建窗口
Ctrl-a c    # 编辑器
Ctrl-a c    # 测试

# 3. 切换窗口
Ctrl-a n    # 下一个
Ctrl-a p    # 上一个

# 4. 重命名窗口
Ctrl-a ,
```

### 第3天：多面板

```bash
# 1. 分割面板
Ctrl-a "    # 水平分割
Ctrl-a %    # 垂直分割

# 2. 切换面板
Ctrl-a o    # 在面板间切换

# 3. 关闭面板
Ctrl-a x
```

### 第4天：高级功能

```bash
# 同步多窗口
Ctrl-a :
setw synchronize-panes on

# 选择会话
ts switch
或 Ctrl-a s

# 复制粘贴
Ctrl-a [    # 复制模式
Ctrl-a ]    # 粘贴
```

---

## ✅ 推荐配置

### 已安装的工具

1. **~/.local/bin/pj** - 项目切换工具
2. **~/.local/bin/ts** - tmux 会话管理
3. **~/.tmux.conf** - tmux 配置
4. **~/.zshrc** - shell 快捷方式

### 环境变量

```bash
export PATH="$HOME/.local/bin:$PATH"
```

---

## 🎯 总结

### 何时使用什么？

| 需求 | 推荐工具 |
|------|---------|
| 日常开发 | **ts (tmux)** |
| 长期任务 | **ts (tmux)** |
| 多项目并行 | **ts (tmux)** |
| 快速查看 | pj |
| 简单切换 | pj 或 ts |

### 最佳实践

1. **早上**: `ts-start-all` - 启动所有项目
2. **工作中**: `ts <项目>` - 快速切换
3. **分离**: `Ctrl-a d` - 保持后台运行
4. **下班**: 直接关闭终端
5. **明天**: `ts <项目>` - 继续昨天的工作

---

**核心优势**: ts (tmux) 提供了独立会话，切换项目后工作状态完全保留！

---

**最后更新**: 2026-03-29
