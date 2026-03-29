"""
测试个性化记忆模块
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.memory.personal_memory import (
    PersonalMemory,
    MemoryType,
    MemoryEntry,
    UserPreference,
    PreferenceCategory,
    CommandRecord,
    ErrorFix,
    WorkflowTemplate,
    get_memory,
)


@pytest.fixture
def temp_memory_dir():
    """创建临时记忆目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def memory(temp_memory_dir):
    """创建记忆实例"""
    return PersonalMemory(memory_dir=temp_memory_dir)


class TestPersonalMemory:
    """个性化记忆测试"""

    def test_memory_initialization(self, memory):
        """测试记忆初始化"""
        assert memory is not None
        assert isinstance(memory.preferences, dict)
        assert isinstance(memory.commands, dict)

    def test_set_and_get_preference(self, memory):
        """测试设置和获取偏好"""
        memory.set_preference(
            category=PreferenceCategory.CODING_STYLE,
            key="indentation",
            value="2 spaces",
            description="Use 2 spaces for indentation",
        )

        value = memory.get_preference(
            PreferenceCategory.CODING_STYLE,
            "indentation",
        )

        assert value == "2 spaces"

    def test_get_preference_default(self, memory):
        """测试获取不存在的偏好"""
        value = memory.get_preference(
            PreferenceCategory.CODING_STYLE,
            "nonexistent",
            default="default_value",
        )

        assert value == "default_value"

    def test_record_command(self, memory):
        """测试记录命令"""
        memory.record_command("npm test", success=True)
        memory.record_command("npm test", success=True)
        memory.record_command("npm test", success=False)

        freq = memory.get_frequent_commands(limit=5)
        assert len(freq) > 0
        assert freq[0][0] == "npm test"
        assert freq[0][1] == 3

    def test_command_suggestions(self, memory):
        """测试命令建议"""
        memory.record_command("git status")
        memory.record_command("git commit")
        memory.record_command("npm test")

        suggestions = memory.get_command_suggestions("git")

        assert len(suggestions) > 0
        assert all("git" in s for s in suggestions)

    def test_record_error_fix(self, memory):
        """测试记录错误修复"""
        memory.record_error_fix(
            error_pattern="ModuleNotFoundError: No module named 'requests'",
            error_type="ImportError",
            fix_description="Install the missing package",
            fix_code="pip install requests",
            languages=["python"],
        )

        fixes = memory.find_fix_for_error("ModuleNotFoundError: No module named 'requests'")

        assert len(fixes) > 0
        assert fixes[0].error_type == "ImportError"

    def test_find_error_fix_partial_match(self, memory):
        """测试部分匹配错误修复"""
        memory.record_error_fix(
            error_pattern="TypeError: 'NoneType' object",
            error_type="TypeError",
            fix_description="Add null check",
            fix_code="if value is not None:",
            languages=["python"],
        )

        fixes = memory.find_fix_for_error("TypeError: 'NoneType' object is not subscriptable")

        assert len(fixes) > 0

    def test_error_fix_success_rate(self, memory):
        """测试错误修复成功率"""
        memory.record_error_fix(
            error_pattern="test error",
            error_type="TestError",
            fix_description="fix",
            fix_code="fix code",
        )

        # 再次记录同一错误（成功）
        memory.record_error_fix(
            error_pattern="test error",
            error_type="TestError",
            fix_description="fix",
            fix_code="fix code",
            success=True,
        )

        # 记录失败
        memory.record_error_fix(
            error_pattern="test error",
            error_type="TestError",
            fix_description="fix",
            fix_code="fix code",
            success=False,
        )

        fixes = memory.find_fix_for_error("test error")
        assert fixes[0].success_rate == 2/3  # 2 success, 1 fail

    def test_workflow_template(self, memory):
        """测试工作流模板"""
        workflow = WorkflowTemplate(
            name="release",
            description="Release workflow",
            steps=[
                {"action": "run_tests", "params": {}},
                {"action": "build", "params": {}},
                {"action": "publish", "params": {}},
            ],
            triggers=["release", "publish", "deploy"],
        )

        memory.save_workflow(workflow)

        retrieved = memory.get_workflow("release")
        assert retrieved is not None
        assert retrieved.name == "release"
        assert len(retrieved.steps) == 3

    def test_find_matching_workflows(self, memory):
        """测试匹配工作流"""
        workflow = WorkflowTemplate(
            name="test",
            description="Test workflow",
            steps=[{"action": "test"}],
            triggers=["test", "spec"],
        )
        memory.save_workflow(workflow)

        matches = memory.find_matching_workflows("run test for this file")

        assert len(matches) > 0
        assert matches[0].name == "test"

    def test_project_history(self, memory):
        """测试项目历史"""
        memory.record_project(
            project_path="/home/user/projects/myapp",
            project_type="frontend",
            tech_stack=["react", "typescript"],
        )

        recent = memory.get_recent_projects()

        assert len(recent) > 0
        assert recent[0]["path"] == "/home/user/projects/myapp"
        assert "react" in recent[0]["tech_stack"]

    def test_export_import_memory(self, memory, temp_memory_dir):
        """测试导出导入记忆"""
        # 添加一些数据
        memory.set_preference(
            PreferenceCategory.CODING_STYLE,
            "quotes",
            "single",
        )
        memory.record_command("npm test")
        memory.record_error_fix(
            error_pattern="test error",
            error_type="TestError",
            fix_description="fix",
            fix_code="fix",
        )

        # 导出
        export_path = temp_memory_dir / "export.json"
        memory.export_memory(export_path)

        assert export_path.exists()

        # 创建新记忆实例并导入
        new_memory = PersonalMemory(memory_dir=temp_memory_dir / "new")
        new_memory.import_memory(export_path)

        assert len(new_memory.preferences) > 0
        assert len(new_memory.commands) > 0

    def test_get_stats(self, memory):
        """测试获取统计"""
        memory.set_preference(PreferenceCategory.CODING_STYLE, "test", "value")
        memory.record_command("test command")
        memory.record_project("/test/project")

        stats = memory.get_stats()

        assert stats["preferences"] > 0
        assert stats["commands"] > 0
        assert stats["projects"] > 0


class TestUserPreference:
    """用户偏好测试"""

    def test_preference_creation(self):
        """测试偏好创建"""
        pref = UserPreference(
            category=PreferenceCategory.TOOLS,
            key="formatter",
            value="prettier",
            description="Use prettier for formatting",
            confidence=0.9,
        )

        assert pref.category == PreferenceCategory.TOOLS
        assert pref.confidence == 0.9

    def test_preference_serialization(self):
        """测试偏好序列化"""
        pref = UserPreference(
            category=PreferenceCategory.LANGUAGE,
            key="primary",
            value="typescript",
        )

        data = pref.to_dict()
        restored = UserPreference.from_dict(data)

        assert restored.category == pref.category
        assert restored.value == pref.value


class TestCommandRecord:
    """命令记录测试"""

    def test_command_record_creation(self):
        """测试命令记录创建"""
        record = CommandRecord(
            command="npm run build",
            frequency=5,
            success_rate=0.8,
            contexts=["ci", "local"],
        )

        assert record.frequency == 5
        assert record.success_rate == 0.8

    def test_command_record_serialization(self):
        """测试命令记录序列化"""
        record = CommandRecord(
            command="git push",
            frequency=10,
        )

        data = record.to_dict()
        restored = CommandRecord.from_dict(data)

        assert restored.command == record.command
        assert restored.frequency == record.frequency


class TestErrorFix:
    """错误修复测试"""

    def test_error_fix_creation(self):
        """测试错误修复创建"""
        fix = ErrorFix(
            error_pattern="Cannot find module",
            error_type="ModuleError",
            fix_description="Install module",
            fix_code="npm install",
            languages=["javascript"],
        )

        assert fix.error_type == "ModuleError"
        assert fix.success_rate == 1.0

    def test_error_fix_success_rate(self):
        """测试错误修复成功率计算"""
        fix = ErrorFix(
            error_pattern="test",
            error_type="Test",
            fix_description="fix",
            fix_code="fix",
            success_count=3,
            fail_count=1,
        )

        assert fix.success_rate == 0.75


class TestWorkflowTemplate:
    """工作流模板测试"""

    def test_workflow_creation(self):
        """测试工作流创建"""
        workflow = WorkflowTemplate(
            name="deploy",
            description="Deploy to production",
            steps=[
                {"action": "build", "params": {"env": "prod"}},
                {"action": "deploy", "params": {"target": "aws"}},
            ],
            triggers=["deploy", "release"],
        )

        assert len(workflow.steps) == 2
        assert len(workflow.triggers) == 2

    def test_workflow_serialization(self):
        """测试工作流序列化"""
        workflow = WorkflowTemplate(
            name="test",
            description="Test",
            steps=[{"action": "test"}],
            triggers=["test"],
        )

        data = workflow.to_dict()
        restored = WorkflowTemplate.from_dict(data)

        assert restored.name == workflow.name
        assert len(restored.steps) == len(workflow.steps)


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
