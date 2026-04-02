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
- feedback_collector: 反馈收集器 (打通闭环)
- knowledge_retriever: 知识检索器 (让记忆工作)
- llm_error_analyzer: LLM 错误分析器 (智能分析)
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
from .feedback_collector import (
    FeedbackCollector,
    FeedbackType,
    FeedbackItem,
    collect_from_hook,
)
from .knowledge_retriever import (
    KnowledgeRetriever,
    RetrievedKnowledge,
    ContextInjection,
    get_context_for_claude,
)
from .llm_error_analyzer import (
    LLMErrorAnalyzer,
    ErrorAnalysis,
    analyze_error,
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
    # Feedback Collector
    "FeedbackCollector",
    "FeedbackType",
    "FeedbackItem",
    "collect_from_hook",
    # Knowledge Retriever
    "KnowledgeRetriever",
    "RetrievedKnowledge",
    "ContextInjection",
    "get_context_for_claude",
    # LLM Error Analyzer
    "LLMErrorAnalyzer",
    "ErrorAnalysis",
    "analyze_error",
]
