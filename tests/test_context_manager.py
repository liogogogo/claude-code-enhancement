"""
测试上下文管理模块
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.core.context_manager import (
    ContextManager,
    ContextLevel,
    CodeChunk,
    ContextSummary,
    ConversationTurn,
    create_context_manager,
)


@pytest.fixture
def sample_project():
    """创建示例项目"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir)

        # 创建文件结构
        (project / "src").mkdir()

        # Python 文件
        (project / "src" / "main.py").write_text('''
from utils import helper

class MainService:
    def __init__(self):
        self.helper = helper.Helper()

    def process(self, data):
        """Process data"""
        return self.helper.transform(data)

    def validate(self, input_data):
        """Validate input"""
        if not input_data:
            raise ValueError("Input cannot be empty")
        return True

def main():
    service = MainService()
    result = service.process({"key": "value"})
    print(result)

if __name__ == "__main__":
    main()
''')

        (project / "src" / "utils").mkdir()
        (project / "src" / "utils" / "__init__.py").write_text("")
        (project / "src" / "utils" / "helper.py").write_text('''
class Helper:
    def transform(self, data):
        """Transform data"""
        return {"transformed": data}

    def validate(self, data):
        """Validate data"""
        return data is not None
''')

        # TypeScript 文件
        (project / "src" / "api.ts").write_text('''
import { User } from './types';

export class ApiService {
    async getUser(id: string): Promise<User> {
        const response = await fetch(`/api/users/${id}`);
        return response.json();
    }

    async createUser(data: Partial<User>): Promise<User> {
        const response = await fetch('/api/users', {
            method: 'POST',
            body: JSON.stringify(data),
        });
        return response.json();
    }
}
''')

        (project / "src" / "types.ts").write_text('''
export interface User {
    id: string;
    name: string;
    email: string;
}

export interface ApiResponse<T> {
    data: T;
    status: number;
}
''')

        yield project


@pytest.fixture
def context_manager(sample_project):
    """创建上下文管理器"""
    return ContextManager(
        project_path=sample_project,
        persist_directory=sample_project / ".claude" / "context",
    )


class TestContextManager:
    """上下文管理器测试"""

    def test_initialization(self, context_manager):
        """测试初始化"""
        assert context_manager is not None
        assert context_manager.project_path.exists()

    def test_index_codebase(self, context_manager):
        """测试索引代码库"""
        stats = context_manager.index_codebase()

        assert stats["files_processed"] > 0
        assert stats["total_chunks"] > 0
        assert len(context_manager._indexed_files) > 0

    def test_search_code(self, context_manager):
        """测试代码搜索"""
        context_manager.index_codebase()

        results = context_manager.search("process data", n_results=5)

        assert isinstance(results, list)
        # 结果格式: [(CodeChunk, similarity), ...]
        if len(results) > 0:
            chunk, score = results[0]
            assert isinstance(chunk, CodeChunk)
            assert 0 <= score <= 1

    def test_search_with_file_filter(self, context_manager):
        """测试带文件过滤的搜索"""
        context_manager.index_codebase()

        results = context_manager.search(
            "transform",
            n_results=5,
            file_filter=["src/utils/helper.py"],
        )

        # 所有结果应该来自指定文件
        for chunk, _ in results:
            assert "helper.py" in chunk.file_path

    def test_get_context_for_query(self, context_manager):
        """测试获取查询上下文"""
        context_manager.index_codebase()

        context = context_manager.get_context_for_query(
            query="how to process data",
            max_tokens=10000,
        )

        assert isinstance(context, str)
        assert len(context) > 0
        # 应该包含文件路径引用
        assert "src/" in context

    def test_add_conversation_turn(self, context_manager):
        """测试添加对话轮次"""
        context_manager.add_conversation_turn(
            role="user",
            content="How do I use the MainService?",
        )

        context_manager.add_conversation_turn(
            role="assistant",
            content="MainService can be used to process data...",
        )

        assert len(context_manager.conversation_history) == 2

    def test_get_recent_conversation(self, context_manager):
        """测试获取最近对话"""
        for i in range(5):
            context_manager.add_conversation_turn(
                role="user" if i % 2 == 0 else "assistant",
                content=f"Message {i}",
            )

        recent = context_manager.get_recent_conversation(max_tokens=1000)

        assert isinstance(recent, str)
        assert "Message" in recent

    def test_compact_conversation(self, context_manager):
        """测试压缩对话"""
        for i in range(20):
            context_manager.add_conversation_turn(
                role="user" if i % 2 == 0 else "assistant",
                content=f"Long message content number {i}" * 10,
            )

        summary = context_manager.compact_conversation(keep_last_n=5)

        assert len(context_manager.conversation_history) <= 5
        assert isinstance(summary, str)

    def test_generate_summaries(self, context_manager):
        """测试生成摘要"""
        context_manager.index_codebase()

        # 摘要应该在索引后自动生成
        assert ContextLevel.PROJECT in context_manager.summaries

        summary = context_manager.summaries[ContextLevel.PROJECT]
        assert summary.tokens > 0
        assert len(summary.content) > 0

    def test_clear_all(self, context_manager):
        """测试清空所有数据"""
        context_manager.index_codebase()
        context_manager.add_conversation_turn("user", "test")

        context_manager.clear_all()

        assert len(context_manager._indexed_files) == 0
        assert len(context_manager.conversation_history) == 0

    def test_get_stats(self, context_manager):
        """测试获取统计"""
        context_manager.index_codebase()

        stats = context_manager.get_stats()

        assert "indexed_files" in stats
        assert "conversation_turns" in stats
        assert stats["indexed_files"] > 0

    def test_persistence(self, sample_project):
        """测试持久化"""
        # 创建并索引
        cm1 = ContextManager(
            project_path=sample_project,
            persist_directory=sample_project / ".claude" / "context",
        )
        cm1.index_codebase()
        cm1.add_conversation_turn("user", "test message")
        stats1 = cm1.get_stats()

        # 创建新实例（应该加载持久化数据）
        cm2 = ContextManager(
            project_path=sample_project,
            persist_directory=sample_project / ".claude" / "context",
        )
        stats2 = cm2.get_stats()

        assert stats2["indexed_files"] == stats1["indexed_files"]
        assert len(cm2.conversation_history) > 0

    def test_create_context_manager_helper(self, sample_project):
        """测试便捷函数"""
        cm = create_context_manager(sample_project)

        assert cm is not None
        assert cm.project_path == sample_project


class TestCodeChunk:
    """代码块测试"""

    def test_chunk_creation(self):
        """测试代码块创建"""
        chunk = CodeChunk(
            id="test.py:0:10",
            content="def hello():\n    pass",
            file_path="test.py",
            start_line=1,
            end_line=2,
            language="python",
        )

        assert chunk.id == "test.py:0:10"
        assert chunk.language == "python"

    def test_chunk_serialization(self):
        """测试代码块序列化"""
        chunk = CodeChunk(
            id="test.py:0:5",
            content="code",
            file_path="test.py",
            start_line=1,
            end_line=5,
            language="python",
            metadata={"test": True},
        )

        data = chunk.to_dict()
        restored = CodeChunk.from_dict(data)

        assert restored.id == chunk.id
        assert restored.metadata == chunk.metadata


class TestContextSummary:
    """上下文摘要测试"""

    def test_summary_creation(self):
        """测试摘要创建"""
        summary = ContextSummary(
            level=ContextLevel.PROJECT,
            content="Project summary",
            tokens=100,
            created_at=datetime.now(),
            source_files=["file1.py", "file2.py"],
        )

        assert summary.level == ContextLevel.PROJECT
        assert len(summary.source_files) == 2

    def test_summary_serialization(self):
        """测试摘要序列化"""
        summary = ContextSummary(
            level=ContextLevel.MODULE,
            content="Module summary",
            tokens=50,
            created_at=datetime.now(),
        )

        data = summary.to_dict()
        assert data["level"] == "module"


class TestConversationTurn:
    """对话轮次测试"""

    def test_turn_creation(self):
        """测试轮次创建"""
        turn = ConversationTurn(
            id="turn_1",
            role="user",
            content="Hello",
            tokens=5,
            timestamp=datetime.now(),
        )

        assert turn.role == "user"
        assert turn.tokens == 5

    def test_turn_serialization(self):
        """测试轮次序列化"""
        turn = ConversationTurn(
            id="turn_2",
            role="assistant",
            content="Hi there",
            tokens=10,
            timestamp=datetime.now(),
            metadata={"model": "claude"},
        )

        data = turn.to_dict()
        restored = ConversationTurn(
            id=data["id"],
            role=data["role"],
            content=data["content"],
            tokens=data["tokens"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )

        assert restored.id == turn.id
        assert restored.metadata == turn.metadata


class TestContextLevels:
    """上下文级别测试"""

    def test_level_values(self):
        """测试级别值"""
        assert ContextLevel.FILE.value == "file"
        assert ContextLevel.MODULE.value == "module"
        assert ContextLevel.PROJECT.value == "project"


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
