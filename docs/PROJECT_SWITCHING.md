# 项目切换系统 - 快速上手

## 🎯 三种切换方式

| 方式 | 命令 | 状态保持 | 推荐场景 |
|------|------|----------|----------|
| **ts** | `ts <项目>` | ✅ 完全保持 | **日常开发** ⭐ |
| **pj** | `pj <项目>` | ❌ 新shell | 快速查看 |
| **cd** | `cd <路径>` | ❌ 当前shell | 传统方式 |

---

## 🚀 ts (tmux 会话) - 推荐使用

### 基本命令

```bash
ts                    # 查看所有会话
ts enh               # 切换到 claude-code-enhancement
ts match             # 切换到 matchvision-monorepo
ts proj              # 切换到 project
```

### 重要快捷键

```
Ctrl-a d            # 分离会话（保持后台运行）
Ctrl-a s            # 切换会话
Ctrl-a c            # 创建新窗口
```

---

## 📖 完整演示

已创建详细演示：
- [docs/TMUX_DEMO.md](docs/TMUX_DEMO.md) - 完整教程
- [docs/TMUX_GUIDE.md](docs/TMUX_GUIDE.md) - 使用指南
- [docs/PROJECT_SWITCHING_QUICK_REF.md](docs/PROJECT_SWITCHING_QUICK_REF.md) - 快速参考

---

## ✅ 现在试试

```bash
# 1. 查看所有会话
ts

# 2. 切换到项目
ts enh

# 3. 创建窗口
Ctrl-a c

# 4. 分离
Ctrl-a d

# 5. 切换回
ts enh
```

---

**核心优势**: 独立会话，工作状态完全保留！🎉
