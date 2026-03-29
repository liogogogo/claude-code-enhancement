# Claude Code 增强系统

> **基于**: ICLR 2025 "A SELF-IMPROVING CODING AGENT" 等前沿研究
> **目标**: 让 Claude Code 具备更强的编码能力和自适应学习能力
> **版本**: 2.0.0（架构重构版）
> **许可证**: MIT

---

## 🎯 项目概述

本项目旨在实现一个**四层自我进化架构**，让 Claude Code 这样的 AI 编码助手能够：

1. **基础设施**（Layer 0）：提供工具封装（Docker、Linter、测试框架）
2. **感知行动**（Layer 1）：与环境交互（观察、执行、反馈）
3. **认知能力**（Layer 2）：通用智能能力（推理、学习、迁移、记忆）
4. **元认知**（Layer 3）：自我进化（元学习、持续学习、自我反思）

**✨ 核心创新**：清晰区分**通用能力**（Layer 2/3）和**基础设施**（Layer 0/1），使认知能力可迁移到任何领域。

---

## 🏗️ 核心架构（v2.0）

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: 元认知层（Meta-Cognitive Layer）                  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  自我反思 | 元学习 | 持续学习 | 策略优化 | 进化追踪    │ │
│  │  核心: 关于"学习"的学习，自我进化                        │ │
│  │  通用性: ✅ 完全通用                                    │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: 认知能力层（Cognitive Layer）                     │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  推理 | 学习 | 迁移 | 记忆 | 纠错                       │ │
│  │  核心: 通用智能能力                                      │ │
│  │  通用性: ✅ 完全通用                                    │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: 感知行动层（Perception-Action Layer）            │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  观察 | 执行 | 反馈（与环境交互的接口）                 │ │
│  │  核心: 感知-行动循环                                    │ │
│  │  通用性: ⚠️ 接口通用，实现依赖场景                      │ │
│  └─────────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  Layer 0: 基础设施层（Infrastructure Layer）                │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │  Docker | Linter | 测试框架（底层工具）                 │ │
│  │  核心: 工具封装，平台依赖                                │ │
│  │  通用性: ❌ 特定于开发场景                              │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**架构优势**：

- ✅ 清晰的层次分离
- ✅ 通用能力与基础设施分离
- ✅ 符合认知科学的"感知-认知-元认知"模型
- ✅ Layer 2/3 可用于任何领域，不限于软件开发

详见 [完整架构文档](docs/ARCHITECTURE_V2.md)

---

## 📦 技术栈

### 核心语言

- **Python 3.11+**: 主要实现语言
- **PyTorch**: 深度学习框架

### 机器学习

- **PyTorch**: 深度学习框架
- **Transformers**: LLM 集成
- **Stable-Baselines3**: 强化学习（可选）

### 工具集成

- **Docker**: 代码执行沙箱（可选）
- **LLM API**: Anthropic Claude API

---

## 📁 项目结构

```
claude-code-enhancement/
├── README.md                          ← 本文件
├── LICENSE                            ← MIT 许可证
├── pyproject.toml                     ← Python 配置
├── requirements.txt                   ← Python 依赖
├── docs/
│   ├── ARCHITECTURE_V2.md             ← 架构文档（v2.0）
│   └── LAYER_2_3_ENHANCEMENTS.md      ← Layer 2/3 详细说明
├── src/
│   ├── layer0/                        ← 基础设施层（工具封装）
│   │   ├── execution_sandbox.py      ← Docker 执行沙箱
│   │   ├── linting_tools.py          ← Linter 工具集
│   │   └── test_frameworks.py        ← 测试框架集成
│   │
│   ├── layer1/                        ← 感知行动层（环境交互）
│   │   ├── observation.py            ← 观察器
│   │   ├── action.py                 ← 执行器
│   │   └── feedback.py               ← 反馈收集器
│   │
│   ├── layer2/                        ← 认知能力层（通用智能）
│   │   ├── advanced_reasoning.py     ← 高级推理（因果、反事实）
│   │   ├── knowledge_transfer.py     ← 知识迁移（零样本、少样本）
│   │   ├── error_learning.py         ← 错误学习
│   │   ├── contrastive_learning.py   ← 对比学习
│   │   └── feedback_loop.py          ← 反馈循环
│   │
│   ├── layer3/                        ← 元认知层（自我进化）
│   │   ├── continuous_learning.py    ← 持续学习（克服遗忘）
│   │   ├── adaptation_engine.py      ← 适应引擎
│   │   └── evolution_tracker.py      ← 进化追踪
│   │
│   └── core/                          ← 核心模块（整合架构）
│       ├── meta_learning.py          ← MAML 元学习
│       ├── strategy_optimizer.py     ← PPO 策略优化
│       └── self_modification.py      ← 自我修改引擎
│
├── tests/                             ← 测试
├── examples/                          ← 使用示例
└── data/                              ← 数据（知识库、检查点等）
```

---

## 🚀 快速开始

### ⚡ 一键增强 Claude Code (推荐)

```bash
# 一行命令安装增强配置
curl -fsSL https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/config/install.sh | bash

# 生效别名
source ~/.zshrc  # 或 source ~/.bashrc

# 使用短命令启动
cc
```

增强功能：

- 28+ 常用命令自动允许（无需确认）
- 自动格式化（prettier）
- 危险命令拦截（rm -rf, drop table 等）
- 任务完成提示音
- `cc` 别名（跳过权限确认）

详见 [config/README.md](config/README.md)

---

### 📦 完整安装 (Python 项目)

```bash
# 克隆项目
git clone https://github.com/liogogogo/claude-code-enhancement.git
cd claude-code-enhancement

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 使用示例

#### 1. 感知行动层（Layer 1）

```python
from src.layer1 import Observer, Actor, FeedbackCollector

# 观察环境状态
observer = Observer()
result = observer.observe(
    observation_type=ObservationType.CODE_STATE,
    context={"project_path": "/path/to/project"},
)

# 执行操作
actor = Actor()
result = actor.act(
    action_type=ActionType.CODE_GENERATION,
    parameters={"description": "创建一个 REST API"},
)

# 收集反馈
collector = FeedbackCollector()
feedback = collector.collect_feedback(context={"last_action": result})
```

#### 2. 认知能力层（Layer 2）

```python
from src.layer2 import MultiStepReasoner, KnowledgeTransfer

# 高级推理（因果分析）
reasoner = MultiStepReasoner()
chain = reasoner.reason(
    problem="为什么性能下降了？",
    context={"metrics": {...}},
    reasoning_type=ReasoningType.CAUSAL,
)

# 知识迁移（少样本学习）
transfer = KnowledgeTransfer(model)
result = transfer.few_shot_transfer(
    target_data=new_domain_data,
    k_shot=5,  # 仅用 5 个样本
)
```

#### 3. 元认知层（Layer 3）

```python
from src.layer3 import ContinualLearning, AdaptationEngine

# 持续学习（克服灾难性遗忘）
continual_learner = ContinualLearning(
    model=model,
    strategy=LearningStrategy.EWC,
)
for task in task_sequence:
    continual_learner.learn_task(task)

# 适应引擎（自动优化）
engine = AdaptationEngine()
result = engine.monitor_and_adapt(
    current_metrics={"accuracy": 0.75},
    thresholds={"accuracy": 0.80},
)
```

---

## 📊 性能目标

| 指标                 | 当前  | 目标  | 提升 |
| -------------------- | ----- | ----- | ---- |
| **HumanEval pass@1** | ~60%  | 85%   | +25% |
| **平均修复时间**     | 5min  | 2min  | -60% |
| **用户满意度**       | 4.2/5 | 4.8/5 | +14% |
| **任务成功率**       | 75%   | 95%   | +20% |
| **跨域适应样本需求** | 100%  | 10%   | -90% |

---

## 🔬 研究基础

### 核心论文

1. **[ICLR 2025] A SELF-IMPROVING CODING AGENT**
   - 自我改进架构

2. **[ICLR 2025] TRAINING LANGUAGE MODELS TO SELF-CORRECT**
   - 自我纠错训练

3. **[NeurIPS 2024] Code World Models**
   - 代码世界模型

4. **MAML (Model-Agnostic Meta-Learning)**
   - 快速适应算法

5. **EWC (Elastic Weight Consolidation)**
   - 克服灾难性遗忘

---

## 🎯 关键特性

### ✅ 通用能力（Layer 2/3）

- **高级推理**: 因果推理、反事实推理、多步推理
- **知识迁移**: 跨域迁移、零样本/少样本学习
- **持续学习**: 克服灾难性遗忘、终身学习
- **元学习**: 快速适应新任务（MAML）

这些能力是**完全通用的**，可应用于任何领域！

### ⚠️ 场景特定（Layer 0/1）

- **代码执行**: Docker 沙箱
- **代码质量**: Linter 集成
- **测试验证**: 测试框架

这些是**特定于开发场景**的工具。

---

## 🤝 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

---

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 📞 联系

- **作者**: liocc
- **项目**: Claude Code Enhancement System
- **邮箱**: [GitHub Issues](https://github.com/liogogogo/claude-code-enhancement/issues)

---

**🎉 让 Claude Code 变得更智能！**
