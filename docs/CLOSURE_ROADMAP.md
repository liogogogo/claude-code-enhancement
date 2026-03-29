# 闭环实现路线图

> 目标：从架构设计到可用的端到端系统
> 时间：4 周
> 优先级：最小可用闭环优先

---

## 当前状态

### 问题诊断

```
┌─────────────────────────────────────────────────────────────┐
│                    当前架构状态                              │
├─────────────────────────────────────────────────────────────┤
│  hooks/ (CLI) ──────×────── src/ (Python Core)              │
│     │                         │                              │
│     ↓                         ↓                              │
│  独立运行                   独立运行                          │
│  无数据共享                 无调用链                          │
├─────────────────────────────────────────────────────────────┤
│  Layer 0 ───×─── Layer 1 ───×─── Layer 2 ───×─── Layer 3   │
│                                                              │
│  各层独立实现，无数据流，无调用链                             │
└─────────────────────────────────────────────────────────────┘
```

### 数据统计

| 指标 | 声称 | 实际 | 问题 |
|------|------|------|------|
| 测试数 | 41 | 4 文件 | ❌ 严重夸大 |
| TODO/FIXME | 0 | 79 | ❌ 骨架代码 |
| 闭环模块 | 8 | 0 | ❌ 无集成 |

---

## 目标架构

```
┌─────────────────────────────────────────────────────────────┐
│                    目标：三层闭环                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           闭环 1：CLI Hook + Memory                  │    │
│  │                                                      │    │
│  │   Hook 触发 ──→ Python API ──→ 存储结果              │    │
│  │       │              ↑               │               │    │
│  │       └──────────────┴───────────────┘               │    │
│  │                   查询反馈                           │    │
│  └─────────────────────────────────────────────────────┘    │
│                           ↓                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           闭环 2：Core + CLI                         │    │
│  │                                                      │    │
│  │   Claude Code ──→ ContextManager ──→ 智能上下文      │    │
│  │        │              ↑                  │           │    │
│  │        └──────────────┴──────────────────┘           │    │
│  │                   项目知识反馈                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                           ↓                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │           闭环 3：Layer 数据流                        │    │
│  │                                                      │    │
│  │   Layer 0 ──→ Layer 1 ──→ Layer 2 ──→ Layer 3       │    │
│  │      ↑           │           │           │          │    │
│  │      └───────────┴───────────┴───────────┘          │    │
│  │                   反馈闭环                           │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## Phase 1：数据可信度修复（1-2 天）

### 目标

让 README 与实际代码一致

### 任务清单

#### 1.1 修正 README 数据

```diff
- [![Tests](https://img.shields.io/badge/tests-41%20passing-brightgreen.svg)](tests/)
+ [![Tests](https://img.shields.io/badge/tests-4%20files-yellow.svg)](tests/)

- | **Test Coverage** | ✅ 41 tests       | Unit + integration tests                 |
+ | **Test Coverage** | ⚠️ 4 test files   | Core modules partially covered           |
```

#### 1.2 添加实现状态标注

在 README 中明确标注各模块状态：

```markdown
## 模块实现状态

| 模块 | 状态 | 说明 |
|------|------|------|
| CLI Hooks | ✅ 可用 | Permission learning 完整实现 |
| Context Manager | ⚠️ 部分 | RAG 框架完成，向量搜索需依赖 |
| Personal Memory | ⚠️ 部分 | 数据结构完整，API 可用 |
| Layer 0-3 | 📋 规划中 | 架构设计完成，待实现 |
```

#### 1.3 清理骨架代码

```bash
# 统计并处理 TODO
grep -r "TODO\|FIXME\|pass$" src/ > todo_list.txt
# 逐个评估：实现 / 删除 / 标注
```

---

## Phase 2：最小可用闭环（1 周）

### 目标

让 CLI Hook 与 Python Core 打通

### 闭环设计

```
┌─────────────────────────────────────────────────────────────┐
│                    闭环 1：权限学习闭环                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Claude Code                                                │
│       │                                                      │
│       ↓ 权限请求                                             │
│   ┌─────────────┐                                            │
│   │ Hook 触发   │                                            │
│   │ (Python)    │                                            │
│   └──────┬──────┘                                            │
│          │                                                    │
│          ↓ 调用                                               │
│   ┌─────────────┐                                            │
│   │ Personal    │                                            │
│   │ Memory API  │                                            │
│   └──────┬──────┘                                            │
│          │                                                    │
│          ↓ 存储                                               │
│   ┌─────────────┐                                            │
│   │ JSON Store  │                                            │
│   │ ~/.claude/  │                                            │
│   └──────┬──────┘                                            │
│          │                                                    │
│          ↓ 查询                                               │
│   ┌─────────────┐                                            │
│   │ 报告/建议   │                                            │
│   │ 输出        │                                            │
│   └─────────────┘                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 任务清单

#### 2.1 重构 permission_learning_hook.py

```python
# 当前：独立脚本，自己实现存储
# 目标：调用 PersonalMemory API

# 修改前
def record_permission(permission: str, action: str):
    data = load_learning_data()
    # 自己实现存储逻辑
    save_learning_data(data)

# 修改后
from src.memory import PersonalMemory

def record_permission(permission: str, action: str):
    memory = PersonalMemory()
    memory.record_permission_decision(
        permission=permission,
        action=action,
        context={"source": "claude_code"}
    )
```

#### 2.2 扩展 PersonalMemory API

```python
# src/memory/personal_memory.py 新增方法

class PersonalMemory:
    # 现有方法...

    def record_permission_decision(
        self,
        permission: str,
        action: str,  # "allow" | "deny"
        context: dict
    ) -> None:
        """记录权限决策"""
        pass

    def get_permission_patterns(self) -> List[dict]:
        """获取权限模式统计"""
        pass

    def suggest_permissions(self, threshold: int = 3) -> List[str]:
        """生成权限建议"""
        pass
```

#### 2.3 添加集成测试

```python
# tests/test_permission_integration.py

def test_hook_to_memory_integration():
    """测试 Hook 调用 Memory 的完整流程"""
    # 1. Hook 触发
    # 2. 调用 Memory API
    # 3. 验证存储
    # 4. 查询验证
    pass

def test_permission_suggestion_workflow():
    """测试权限建议生成"""
    # 1. 记录多个权限决策
    # 2. 生成建议
    # 3. 验证建议正确
    pass
```

### 验收标准

- [ ] Hook 正确调用 PersonalMemory API
- [ ] 权限数据存储在 `~/.claude/memory/permissions.json`
- [ ] `permission_report.py` 从 Memory API 读取数据
- [ ] 集成测试通过
- [ ] 端到端测试：触发 Hook → 存储 → 查询 → 报告

---

## Phase 3：Core 模块闭环（1 周）

### 目标

让 ContextManager 与 Claude Code 集成

### 闭环设计

```
┌─────────────────────────────────────────────────────────────┐
│                    闭环 2：上下文管理闭环                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   项目目录                                                   │
│       │                                                      │
│       ↓ 分析                                                 │
│   ┌─────────────┐                                            │
│   │ Project     │                                            │
│   │ Knowledge   │                                            │
│   │ Learner     │                                            │
│   └──────┬──────┘                                            │
│          │                                                    │
│          ↓ 代码嵌入                                           │
│   ┌─────────────┐                                            │
│   │ Context     │                                            │
│   │ Manager     │                                            │
│   │ (RAG)       │                                            │
│   └──────┬──────┘                                            │
│          │                                                    │
│          ↓ 智能检索                                           │
│   ┌─────────────┐                                            │
│   │ Claude Code │                                            │
│   │ 查询接口    │                                            │
│   └─────────────┘                                            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 任务清单

#### 3.1 完善 ContextManager

```python
# src/core/context_manager.py

class ContextManager:
    # 当前：框架完成，搜索未实现
    # 目标：实现向量搜索

    def search(self, query: str, n_results: int = 10) -> List[CodeChunk]:
        """向量搜索代码"""
        if not HAS_CHROMA:
            # 降级方案：关键词搜索
            return self._keyword_search(query, n_results)

        # 向量搜索
        query_embedding = self.encoder.encode(query)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results
        )
        return self._parse_results(results)
```

#### 3.2 添加 CLI 查询接口

```python
# hooks/context_query.py

"""
上下文查询工具

用法:
    python3 hooks/context_query.py "authentication flow"
    python3 hooks/context_query.py --stats
"""

from src.core import ContextManager

def main():
    import sys
    query = sys.argv[1] if len(sys.argv) > 1 else None

    cm = ContextManager(project_path=Path.cwd())

    if query:
        results = cm.search(query)
        for r in results:
            print(f"{r.file_path}:{r.start_line}")
            print(f"  {r.content[:100]}...")
    else:
        stats = cm.get_stats()
        print(f"文件数: {stats['files']}")
        print(f"代码块: {stats['chunks']}")
```

#### 3.3 集成测试

```python
# tests/test_context_integration.py

def test_project_analysis_and_search():
    """测试项目分析和搜索"""
    # 1. 分析项目
    cm = ContextManager(project_path=test_project)
    cm.analyze_project()

    # 2. 搜索
    results = cm.search("authentication")

    # 3. 验证结果相关
    assert len(results) > 0
    assert "auth" in results[0].content.lower()
```

### 验收标准

- [ ] 项目分析生成代码嵌入
- [ ] 向量搜索返回相关结果
- [ ] 降级方案（无 chromadb）可用
- [ ] CLI 查询工具可用
- [ ] 集成测试通过

---

## Phase 4：Layer 数据流闭环（2 周）

### 目标

让 Layer 0-3 形成数据流

### 闭环设计

```
┌─────────────────────────────────────────────────────────────┐
│                    闭环 3：四层数据流                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Layer 0: 工具执行结果                               │   │
│   │  {test_results, lint_errors, execution_output}      │   │
│   └─────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│                         ↓ 观察数据                           │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Layer 1: 感知结果                                   │   │
│   │  {code_state, errors, performance_metrics}          │   │
│   └─────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│                         ↓ 分析推理                           │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Layer 2: 认知结果                                   │   │
│   │  {root_cause, fix_suggestions, knowledge_updates}   │   │
│   └─────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│                         ↓ 元决策                             │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  Layer 3: 决策结果                                   │   │
│   │  {action_plan, strategy_update, learning_log}       │   │
│   └─────────────────────┬───────────────────────────────┘   │
│                         │                                    │
│                         ↓ 执行反馈                           │
│   ┌─────────────────────────────────────────────────────┐   │
│   │  回到 Layer 0 执行                                   │   │
│   └─────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 任务清单

#### 4.1 定义层数据接口

```python
# src/interfaces.py

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

@dataclass
class Layer0Output:
    """Layer 0 输出"""
    tool_name: str
    success: bool
    output: str
    errors: List[str]
    metrics: Dict[str, float]

@dataclass
class Layer1Output:
    """Layer 1 输出"""
    observation_type: str
    data: Dict[str, Any]
    confidence: float

@dataclass
class Layer2Output:
    """Layer 2 输出"""
    analysis_type: str
    findings: List[str]
    suggestions: List[str]
    confidence: float

@dataclass
class Layer3Output:
    """Layer 3 输出"""
    decision: str
    action_plan: List[str]
    learning_update: Optional[Dict[str, Any]]
```

#### 4.2 实现数据流管道

```python
# src/pipeline.py

from .layer0 import ExecutionSandbox, LintingTools, TestFrameworks
from .layer1 import Observer, Actor, FeedbackCollector
from .layer2 import ErrorLearner, MultiStepReasoner
from .layer3 import AdaptationEngine, EvolutionTracker

class EnhancementPipeline:
    """四层增强管道"""

    def __init__(self, project_path: Path):
        # Layer 0
        self.sandbox = ExecutionSandbox()
        self.linter = LintingTools()
        self.tester = TestFrameworks()

        # Layer 1
        self.observer = Observer()
        self.actor = Actor()
        self.feedback = FeedbackCollector()

        # Layer 2
        self.error_learner = ErrorLearner()
        self.reasoner = MultiStepReasoner()

        # Layer 3
        self.adaptation = AdaptationEngine()
        self.evolution = EvolutionTracker()

    def run(self, task: str, context: dict) -> Layer3Output:
        """运行完整管道"""
        # Layer 1: 观察
        obs = self.observer.observe(
            ObservationType.CODE_STATE,
            context
        )

        # Layer 2: 推理
        analysis = self.reasoner.reason(
            problem=task,
            context=obs.data
        )

        # Layer 3: 决策
        decision = self.adaptation.decide(analysis)

        # Layer 1: 执行
        action = self.actor.act(
            ActionType.CODE_MODIFICATION,
            decision.action_plan
        )

        # Layer 0: 验证
        test_result = self.tester.run(action.output)

        # Layer 1: 收集反馈
        feedback = self.feedback.collect(action, test_result)

        # Layer 2: 学习
        self.error_learner.learn(feedback)

        # Layer 3: 更新策略
        self.evolution.track(decision, feedback)

        return decision
```

#### 4.3 端到端测试

```python
# tests/test_pipeline.py

def test_full_pipeline_with_code_fix():
    """测试完整管道：代码修复"""
    pipeline = EnhancementPipeline(test_project)

    # 输入：有 bug 的代码
    result = pipeline.run(
        task="fix the authentication bug",
        context={"file": "auth.py", "error": "null pointer"}
    )

    # 验证：
    # 1. Layer 3 输出了决策
    assert result.decision is not None
    # 2. 有行动计划
    assert len(result.action_plan) > 0
    # 3. 学习更新
    assert result.learning_update is not None
```

### 验收标准

- [ ] 层间数据接口定义清晰
- [ ] Pipeline 类实现完整
- [ ] 端到端测试通过
- [ ] 可以从任务输入到执行输出

---

## 验收总表

| Phase | 内容 | 时间 | 验收标准 |
|-------|------|------|----------|
| 1 | 数据可信度 | 1-2 天 | README 与实际一致 |
| 2 | 权限学习闭环 | 1 周 | Hook → Memory → 报告 |
| 3 | 上下文管理闭环 | 1 周 | 项目分析 → 搜索 → 查询 |
| 4 | Layer 数据流闭环 | 2 周 | Layer 0→1→2→3→0 |

---

## 成功指标

### 代码质量

- [ ] 测试覆盖率 > 60%
- [ ] 集成测试 > 5 个
- [ ] TODO/FIXME < 20 个

### 功能完整性

- [ ] 至少 1 个端到端闭环可用
- [ ] CLI 工具与 Python Core 集成
- [ ] Layer 数据流可运行

### 文档一致性

- [ ] README 数据真实
- [ ] 模块状态标注清晰
- [ ] API 文档与代码同步

---

## 执行建议

### 优先级原则

1. **先闭环，后扩展** - 让一个流程跑通，再添加功能
2. **先集成，后优化** - 先打通调用链，再优化性能
3. **先测试，后实现** - 测试驱动开发

### 每周里程碑

| 周次 | 目标 | 交付物 |
|------|------|--------|
| W1 | Phase 1-2 | README 修正 + 权限闭环 |
| W2 | Phase 3 | 上下文闭环 |
| W3-4 | Phase 4 | Layer 闭环 |

---

**下一步：从 Phase 1 开始？**
