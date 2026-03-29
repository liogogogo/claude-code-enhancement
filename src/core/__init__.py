"""
核心模块

功能:
- context_manager: 智能上下文管理 (RAG + 摘要)
- project_knowledge: 项目知识自动学习
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
