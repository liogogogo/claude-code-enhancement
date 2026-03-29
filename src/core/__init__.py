"""
核心模块

功能:
- context_manager: 智能上下文管理 (RAG + 摘要)
- multi_file_reasoning: 多文件推理 (依赖分析、影响预测)
- project_knowledge: 项目知识自动学习
- personal_memory: 个性化记忆
- unified: 统一增强接口
- meta_learning: 元学习算法
- self_modification: 自我修改引擎
- strategy_optimizer: 策略优化
"""

from .context_manager import (
    ContextManager,
    ContextLevel,
    CodeChunk,
    ContextSummary,
    ConversationTurn,
    create_context_manager,
)
from .multi_file_reasoning import (
    MultiFileReasoner,
    Symbol,
    Dependency,
    Impact,
    ImpactLevel,
    DependencyType,
    DependencyNode,
    create_reasoner,
)
from .project_knowledge import (
    ProjectKnowledgeLearner,
    ProjectKnowledge,
    CodePattern,
    ProjectConvention,
    KnowledgeType,
    learn_project,
)
from .unified import (
    ClaudeCodeEnhancer,
    EnhancementConfig,
    create_enhancer,
)

__all__ = [
    # Context Manager
    "ContextManager",
    "ContextLevel",
    "CodeChunk",
    "ContextSummary",
    "ConversationTurn",
    "create_context_manager",
    # Multi-File Reasoning
    "MultiFileReasoner",
    "Symbol",
    "Dependency",
    "Impact",
    "ImpactLevel",
    "DependencyType",
    "DependencyNode",
    "create_reasoner",
    # Project Knowledge
    "ProjectKnowledgeLearner",
    "ProjectKnowledge",
    "CodePattern",
    "ProjectConvention",
    "KnowledgeType",
    "learn_project",
    # Unified
    "ClaudeCodeEnhancer",
    "EnhancementConfig",
    "create_enhancer",
]
