# tmux 项目会话管理 - 完整指南

> **更新**: 2026-03-29
> **工具**: tmux + ts 会话管理器

---

## 🎯 核心概念

**独立会话**：每个项目都有独立的 tmux 会话
- ✅ 切换项目时保持之前的工作状态
- ✅ 可以同时运行多个项目（多个窗口）
- ✅ 后台运行，不占用终端

---

## 📚 快速开始

### 1. 基本使用

```bash
# 查看所有会话
ts ls

# 切换到项目（会自动创建）
ts enh              # claude-code-enhancement
ts match           # matchvision-monorepo
ts proj            # project
```

### 2. 高级用法

```bash
# 启动新会话（不附加）
ts new enh

# 附加到已有会话
ts attach enh

# 停止会话
ts stop enh

# 切换会话（在tmux内）
ts switch          # 显示选择菜单
ts switch enh     # 直接切换

# 查看当前会话信息
ts here
```

---

## 🚀 典型工作流

### 场景 1: 单项目开发

```bash
# 1. 启动项目
ts match

# 2. 在项目内工作
# （现在你在 tmux 会话中）

# 3. 创建新窗口（Ctrl-a c）
# 可以运行不同的任务：
# - 窗口1: 编辑器
# - 窗口2: 测试
# - 窗口3: Git 日志

# 4. 分离会话（Ctrl-a d）
# 会话在后台保持运行

# 5. 稍后重新附加
ts match
```

### 场景 2: 多项目切换

```bash
# 1. 启动第一个项目
ts enh
# 做一些工作...

# 2. 分离会话（Ctrl-a d）
# 回到主终端

# 3. 切换到第二个项目
ts match
# 做一些其他工作...

# 4. 快速切换回第一个项目
ts switch enh
# 或在 tmux 内按 Ctrl-a s，选择会话
```

### 场景 3: 启动所有项目（后台）

```bash
# 一次性启动所有项目
ts-start-all

# 然后随时切换
ts enh
ts match
ts proj
```

---

## ⌨️ tmux 快捷键

### 前缀键

**前缀**: `Ctrl-a` （默认是 Ctrl-b，已修改）

### 常用快捷键

```
会话管理:
  Ctrl-a s          选择/切换会话
  Ctrl-a d          分离会话（后台运行）
  Ctrl-a $          重命名会话

窗口管理:
  Ctrl-a c          创建新窗口
  Ctrl-a w          列出窗口
  Ctrl-a n          下一个窗口
  Ctrl-a p          上一个窗口
  Ctrl-a 0-9        切换到窗口 0-9
  Ctrl-a &          关闭窗口

面板管理:
  Ctrl-a "          水平分割面板
  Ctrl-a %          垂直分割面板
  Ctrl-a o          在面板间切换
  Ctrl-a 方向键     切换到指定方向的面板
  Ctrl-a x          关闭面板

其他:
  Ctrl-a r          重新加载配置
  Ctrl-a ?          显示帮助
  Ctrl-a :          进入命令模式
```

---

## 🎨 状态栏说明

```
[pj-enh] ← 会话名
1:enh* ← 当前窗口
```

- **[pj-enh]**: 会话名称
- **1**: 窗口编号
- **:enh**: 窗口名称
- **\***: 表示活跃窗口

---

## 💡 高级技巧

### 1. 在项目中创建多个窗口

```bash
# 在 tmux 会话内
Ctrl-a c           # 创建新窗口
Ctrl-a ,           # 重命名窗口
# 例如: 编辑器、测试、日志
```

### 2. 同步多个窗口

```bash
Ctrl-a :           # 进入命令模式
setw synchronize-panes on    # 开启同步
# 现在在所有窗口中输入相同的命令

Ctrl-a :           # 关闭同步
setw synchronize-panes off
```

### 3. 保存和恢复会话

```bash
# 查看当前会话
tmux list-sessions

# 分离但保持运行
Ctrl-a d

# 稍后重新附加
ts <项目名>
```

### 4. 在不同项目中复制粘贴

```bash
# tmux 复制模式
Ctrl-a [           # 进入复制模式
# 使用 vi 键移动: h,j,k,l
# v 开始选择, y 复制

# 粘贴
Ctrl-a ]           # 粘贴到当前位置
```

---

## 🔧 自定义配置

### 添加新项目

编辑 `~/.local/bin/ts`，在 `get_projects()` 函数中添加：

```bash
get_projects() {
    echo "enh:/Users/liocc/claude-code-enhancement"
    echo "match:/Users/liocc/matchvision-monorepo"
    echo "proj:/Users/liocc/project"
    echo "newproject:/path/to/new/project"    # 添加新项目
}
```

### 修改 tmux 配置

编辑 `~/.tmux.conf`：

```bash
# 重新加载配置
Ctrl-a :           # 进入命令模式
source-file ~/.tmux.conf

# 或在终端中
tmux source-file ~/.tmux.conf
```

---

## 📊 项目会话状态

```bash
# 查看所有会话
ts ls

# 示例输出:
📚 tmux 项目会话:

   ✅ [enh] claude-code-enhancement     ← 会话已启动
   ❌ [match] matchvision-monorepo       ← 未启动
   ✅ [proj] project                     ← 会话已启动
```

---

## 🛑 清理和维护

```bash
# 停止单个会话
ts stop enh

# 停止所有会话
for session in enh match proj; do
    ts stop $session
done

# 查看所有 tmux 进程
ps aux | grep tmux

# 清理死掉的会话
tmux kill-server    # 停止 tmux 服务器（会停止所有会话）
```

---

## 🎯 最佳实践

### 日常开发

1. **早上开始工作时**
   ```bash
   ts-start-all     # 启动所有项目会话
   ```

2. **切换项目**
   ```bash
   ts match         # 快速切换
   ```

3. **在工作时**
   - 使用 `Ctrl-a c` 创建多个窗口
   - 使用 `Ctrl-a d` 分离会话
   - 工作状态保持不变

4. **下班前**
   - 直接关闭终端
   - 所有会话保持后台运行
   - 明天直接 `ts match` 继续

### 多任务处理

```bash
# 在一个项目中运行长期任务
ts match
Ctrl-a c           # 新窗口
python run_tests.py    # 运行测试
Ctrl-a d           # 分离，让它在后台运行

# 切换到另一个项目
ts enh
# 继续其他工作...

# 稍后检查测试结果
ts match
Ctrl-a n           # 切换到测试窗口
```

---

## ❓ 常见问题

### Q: tmux 会话消失了怎么办？

```bash
# 查看所有会话
tmux list-sessions

# 如果会话存在，重新附加
ts <项目名>

# 如果会话不存在，重新创建
ts start <项目名>
```

### Q: 如何在项目间复制内容？

使用 tmux 的复制模式或系统剪贴板：
```bash
# tmux 复制模式
Ctrl-a [           # 进入复制模式
# 选择文本后按 y

# 粘贴到另一个会话
ts another-project
Ctrl-a ]           # 粘贴
```

### Q: 如何查看当前在哪个项目？

```bash
ts here            # 如果在 tmux 会话中
tmux display -p '#S'    # 显示会话名
```

---

## 📚 相关命令

```bash
# 项目切换（不使用 tmux）
pj                   # 列出项目
pj match             # 切换项目（启动新 shell）

# tmux 会话管理
ts                   # 列出会话
ts match             # 切换会话（保持状态）

# 查看所有 tmux 进程
tmux list-sessions
```

---

## 🎉 总结

**优势**:
- ✅ 每个项目独立会话
- ✅ 工作状态保持不变
- ✅ 后台运行，随时切换
- ✅ 多窗口、多面板支持

**工作流**:
1. `ts-start-all` - 启动所有项目
2. `ts <项目名>` - 快速切换
3. `Ctrl-a d` - 分离会话
4. 持续使用，无需重新初始化

---

**最后更新**: 2026-03-29
