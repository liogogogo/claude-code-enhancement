"""
上下文管理集成测试

测试 Index → Search → Stats 的完整流程
"""

import json
import tempfile
from pathlib import Path
import pytest

from src.core.context_manager import (
    ContextManager,
    CodeChunk,
    ContextLevel,
    create_context_manager,
)


class TestCodeChunk:
    """测试 CodeChunk 数据类"""

    def test_to_dict(self):
        """测试序列化"""
        chunk = CodeChunk(
            id="test:1:10",
            content="def hello():\n    print('world')",
            file_path="test.py",
            start_line=1,
            end_line=10,
            language="py",
            metadata={"key": "value"},
        )
        data = chunk.to_dict()
        assert data["id"] == "test:1:10"
        assert data["file_path"] == "test.py"
        assert data["language"] == "py"
        assert data["metadata"]["key"] == "value"

    def test_from_dict(self):
        """测试反序列化"""
        data = {
            "id": "test:1:10",
            "content": "def hello():\n    print('world')",
            "file_path": "test.py",
            "start_line": 1,
            "end_line": 10,
            "language": "py",
            "metadata": {"key": "value"},
        }
        chunk = CodeChunk.from_dict(data)
        assert chunk.id == "test:1:10"
        assert chunk.file_path == "test.py"
        assert chunk.language == "py"


class TestContextManagerInit:
    """测试 ContextManager 初始化"""

    def test_init_with_path(self):
        """测试使用路径初始化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = create_context_manager(tmpdir)
            assert cm.project_path == Path(tmpdir)
            # persist_directory 只在需要时创建（如索引或保存状态）
            # 所以这里只验证路径设置正确
            assert str(cm.persist_directory).endswith(".claude/context")

    def test_init_loads_state(self):
        """测试状态加载"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建第一个 manager 并索引
            cm1 = create_context_manager(tmpdir)

            # 创建测试文件
            test_file = Path(tmpdir) / "test.py"
            test_file.write_text("def hello():\n    return 'world'\n")

            cm1.index_codebase()

            # 创建第二个 manager，应该加载状态
            cm2 = create_context_manager(tmpdir)
            stats = cm2.get_stats()
            assert stats["indexed_files"] > 0


class TestIndexing:
    """测试索引功能"""

    def test_index_single_file(self):
        """测试索引单个文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            test_file = Path(tmpdir) / "example.py"
            test_file.write_text(
                """
def function_one():
    return 1

def function_two():
    return 2

class MyClass:
    def method(self):
        return 3
"""
            )

            cm = create_context_manager(tmpdir)
            stats = cm.index_codebase()

            assert stats["files_processed"] == 1
            assert stats["indexed_files"] == 1
            assert stats["total_chunks"] > 0

    def test_index_multiple_files(self):
        """测试索引多个文件"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建多个测试文件
            (Path(tmpdir) / "a.py").write_text("def a(): return 1")
            (Path(tmpdir) / "b.py").write_text("def b(): return 2")
            (Path(tmpdir) / "c.ts").write_text("function c() { return 3; }")

            cm = create_context_manager(tmpdir)
            stats = cm.index_codebase()

            assert stats["files_processed"] >= 2
            assert stats["indexed_files"] >= 2

    def test_index_excludes_patterns(self):
        """测试排除模式"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            (Path(tmpdir) / "main.py").write_text("def main(): pass")
            # 创建 node_modules 目录和文件
            node_modules = Path(tmpdir) / "node_modules"
            node_modules.mkdir(parents=True, exist_ok=True)
            (node_modules / "pkg.py").write_text("def pkg(): pass")

            cm = create_context_manager(tmpdir)
            stats = cm.index_codebase(
                exclude_patterns=["**/node_modules/**"]
            )

            # node_modules 应该被排除
            assert stats["files_processed"] == 1
            assert "node_modules" not in str(cm._indexed_files)


class TestSearch:
    """测试搜索功能"""

    def test_keyword_search(self):
        """测试关键词搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试文件
            (Path(tmpdir) / "auth.py").write_text(
                """
def authenticate(user, password):
    # 验证用户身份
    if verify_password(user, password):
        return create_token(user)
    return None

def verify_password(user, password):
    # 检查密码
    return check_hash(password, user.password_hash)
"""
            )
            (Path(tmpdir) / "utils.py").write_text(
                """
def helper():
    return 'helper function'
"""
            )

            cm = create_context_manager(tmpdir)
            cm.index_codebase()

            # 搜索 authenticate
            results = cm.search("authenticate", n_results=5)

            assert len(results) > 0
            # auth.py 应该在结果中
            found_auth = any(
                "auth.py" in r[0].file_path for r in results
            )
            assert found_auth

    def test_search_returns_chunk_with_score(self):
        """测试搜索返回代码块和分数"""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").write_text(
                "def permission_check():\n    return True\n"
            )

            cm = create_context_manager(tmpdir)
            cm.index_codebase()

            results = cm.search("permission", n_results=1)

            if results:
                chunk, score = results[0]
                assert isinstance(chunk, CodeChunk)
                assert isinstance(score, float)
                assert 0 <= score <= 1

    def test_search_file_filter(self):
        """测试文件过滤"""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "a.py").write_text("def target_func(): pass")
            (Path(tmpdir) / "b.py").write_text("def target_func(): pass")

            cm = create_context_manager(tmpdir)
            cm.index_codebase()

            results = cm.search(
                "target_func",
                file_filter=["a.py"]
            )

            # 只应该返回 a.py 的结果
            for chunk, _ in results:
                assert "a.py" in chunk.file_path

    def test_search_empty_index(self):
        """测试空索引搜索"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = create_context_manager(tmpdir)
            results = cm.search("anything")
            assert results == []


class TestPersistence:
    """测试持久化"""

    def test_state_persists(self):
        """测试状态持久化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 第一次会话
            cm1 = create_context_manager(tmpdir)
            (Path(tmpdir) / "test.py").write_text("def test(): pass")
            cm1.index_codebase()

            stats1 = cm1.get_stats()

            # 第二次会话
            cm2 = create_context_manager(tmpdir)
            stats2 = cm2.get_stats()

            # 应该保持一致
            assert stats2["indexed_files"] == stats1["indexed_files"]

    def test_memory_store_persists(self):
        """测试内存存储持久化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 第一次会话 - 索引
            cm1 = create_context_manager(tmpdir)
            (Path(tmpdir) / "searchable.py").write_text(
                "def find_me(): return 'found'\n"
            )
            cm1.index_codebase()

            # 第二次会话 - 搜索
            cm2 = create_context_manager(tmpdir)
            results = cm2.search("find_me", n_results=5)

            # 应该能找到
            assert len(results) > 0
            found = any("searchable.py" in r[0].file_path for r in results)
            assert found

    def test_clear_all(self):
        """测试清空所有数据"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = create_context_manager(tmpdir)
            (Path(tmpdir) / "test.py").write_text("def test(): pass")
            cm.index_codebase()

            assert cm.get_stats()["indexed_files"] > 0

            cm.clear_all()

            assert cm.get_stats()["indexed_files"] == 0
            # 确保搜索返回空
            assert cm.search("test") == []


class TestStats:
    """测试统计功能"""

    def test_stats_structure(self):
        """测试统计结构"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = create_context_manager(tmpdir)

            stats = cm.get_stats()

            assert "indexed_files" in stats
            assert "total_chunks" in stats
            assert "conversation_turns" in stats
            assert "summaries" in stats
            assert "has_vector_store" in stats

    def test_stats_after_indexing(self):
        """测试索引后的统计"""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").write_text("def test(): pass")

            cm = create_context_manager(tmpdir)
            stats_before = cm.get_stats()

            cm.index_codebase()
            stats_after = cm.get_stats()

            assert stats_after["indexed_files"] > stats_before["indexed_files"]
            assert stats_after["total_chunks"] > stats_before["total_chunks"]


class TestConversationHistory:
    """测试对话历史"""

    def test_add_conversation_turn(self):
        """测试添加对话轮次"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = create_context_manager(tmpdir)

            cm.add_conversation_turn("user", "Hello")
            cm.add_conversation_turn("assistant", "Hi there")

            stats = cm.get_stats()
            assert stats["conversation_turns"] == 2

    def test_get_recent_conversation(self):
        """测试获取最近对话"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cm = create_context_manager(tmpdir)

            cm.add_conversation_turn("user", "First message")
            cm.add_conversation_turn("assistant", "First response")

            recent = cm.get_recent_conversation()
            assert "First message" in recent
            assert "First response" in recent

    def test_conversation_persists(self):
        """测试对话持久化"""
        with tempfile.TemporaryDirectory() as tmpdir:
            cm1 = create_context_manager(tmpdir)
            cm1.add_conversation_turn("user", "Test message")

            cm2 = create_context_manager(tmpdir)
            stats = cm2.get_stats()
            assert stats["conversation_turns"] == 1


class TestSummaries:
    """测试摘要功能"""

    def test_project_summary_generated(self):
        """测试项目摘要生成"""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "a.py").write_text("def a(): pass")
            (Path(tmpdir) / "b.py").write_text("def b(): pass")

            cm = create_context_manager(tmpdir)
            cm.index_codebase()

            assert ContextLevel.PROJECT in cm.summaries
            summary = cm.summaries[ContextLevel.PROJECT]
            assert summary.content
            assert summary.tokens > 0


class TestGetContextForQuery:
    """测试获取查询上下文"""

    def test_returns_formatted_context(self):
        """测试返回格式化上下文"""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "test.py").write_text(
                "def my_function():\n    return 'value'\n"
            )

            cm = create_context_manager(tmpdir)
            cm.index_codebase()

            context = cm.get_context_for_query("my_function", max_tokens=1000)

            assert context
            assert "test.py" in context

    def test_respects_token_limit(self):
        """测试 token 限制"""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建多个文件
            for i in range(10):
                (Path(tmpdir) / f"file_{i}.py").write_text(
                    f"def func_{i}():\n    return {i}\n" * 100
                )

            cm = create_context_manager(tmpdir)
            cm.index_codebase()

            context = cm.get_context_for_query("func", max_tokens=500)
            # 上下文应该有限制
            estimated_tokens = len(context) // 4
            assert estimated_tokens < 1000  # 应该低于限制


if __name__ == "__main__":
    pytest.main([__file__, "-v"])