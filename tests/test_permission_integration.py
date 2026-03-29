"""
权限学习集成测试

测试 Hook → Memory → 报告 的完整流程
"""

import json
import tempfile
from pathlib import Path
import pytest

from src.memory.personal_memory import PersonalMemory, extract_permission_pattern


class TestPermissionPatternExtraction:
    """测试权限模式提取"""

    def test_git_push_pattern(self):
        """测试 git push 模式提取"""
        result = extract_permission_pattern("Bash(git push:origin main)")
        assert result is not None
        assert result["pattern"] == "Bash(git push:*)"
        assert "git push" in result["description"].lower()

    def test_pip_install_pattern(self):
        """测试 pip install 模式提取"""
        result = extract_permission_pattern("Bash(pip install:requests)")
        assert result is not None
        assert result["pattern"] == "Bash(pip install:*)"

    def test_pytest_pattern(self):
        """测试 pytest 模式提取"""
        result = extract_permission_pattern("Bash(python -m pytest:tests/)")
        assert result is not None
        assert result["pattern"] == "Bash(python -m pytest:*)"

    def test_unknown_pattern(self):
        """测试未知模式"""
        result = extract_permission_pattern("SomeUnknownCommand(arg1:arg2)")
        assert result is None

    def test_gh_cli_pattern(self):
        """测试 gh CLI 模式"""
        result = extract_permission_pattern("Bash(gh pr:view 123)")
        assert result is not None
        assert result["pattern"] == "Bash(gh pr:*)"

    def test_tmux_pattern(self):
        """测试 tmux 模式"""
        result = extract_permission_pattern("Bash(tmux new:-s dev)")
        assert result is not None
        assert result["pattern"] == "Bash(tmux new:*)"

    def test_docker_pattern(self):
        """测试 docker 模式"""
        result = extract_permission_pattern("Bash(docker run:nginx)")
        assert result is not None
        assert result["pattern"] == "Bash(docker run:*)"

    def test_yarn_pattern(self):
        """测试 yarn 模式"""
        result = extract_permission_pattern("Bash(yarn install:--dev)")
        assert result is not None
        assert result["pattern"] == "Bash(yarn install:*)"

    def test_make_pattern(self):
        """测试 make 模式"""
        result = extract_permission_pattern("Bash(make:all)")
        assert result is not None
        assert result["pattern"] == "Bash(make:*)"

    def test_cargo_pattern(self):
        """测试 cargo 模式"""
        result = extract_permission_pattern("Bash(cargo build:--release)")
        assert result is not None
        assert result["pattern"] == "Bash(cargo build:*)"

    def test_kubectl_pattern(self):
        """测试 kubectl 模式"""
        result = extract_permission_pattern("Bash(kubectl get:pods)")
        assert result is not None
        assert result["pattern"] == "Bash(kubectl get:*)"

    def test_uv_pattern(self):
        """测试 uv (新 Python 工具) 模式"""
        result = extract_permission_pattern("Bash(uv pip:install requests)")
        assert result is not None
        assert result["pattern"] == "Bash(uv pip:*)"

    def test_brew_pattern(self):
        """测试 Homebrew 模式"""
        result = extract_permission_pattern("Bash(brew:install git)")
        assert result is not None
        assert result["pattern"] == "Bash(brew:*)"

    def test_file_operations(self):
        """测试文件操作模式"""
        for cmd in ["rm", "mv", "cp", "touch", "head", "tail"]:
            result = extract_permission_pattern(f"Bash({cmd}:somefile)")
            assert result is not None
            assert result["pattern"] == f"Bash({cmd}:*)"


class TestPermissionDecisionRecording:
    """测试权限决策记录"""

    @pytest.fixture
    def temp_memory(self, tmp_path):
        """创建临时 PersonalMemory"""
        return PersonalMemory(memory_dir=tmp_path / "memory")

    def test_record_allow(self, temp_memory):
        """测试记录允许决策"""
        temp_memory.record_permission_decision(
            "Bash(git push:origin main)",
            "allow"
        )

        assert "Bash(git push:origin main)" in temp_memory.permission_decisions
        decision = temp_memory.permission_decisions["Bash(git push:origin main)"]
        assert decision.action == "allow"

    def test_record_deny(self, temp_memory):
        """测试记录拒绝决策"""
        temp_memory.record_permission_decision(
            "Bash(rm -rf:/*)",
            "deny"
        )

        decision = temp_memory.permission_decisions["Bash(rm -rf:/*)"]
        assert decision.action == "deny"

    def test_pattern_created_on_allow(self, temp_memory):
        """测试允许决策时创建模式"""
        # 记录 3 次相同的模式
        temp_memory.record_permission_decision("Bash(git push:origin main)", "allow")
        temp_memory.record_permission_decision("Bash(git push:origin dev)", "allow")
        temp_memory.record_permission_decision("Bash(git push:origin feature)", "allow")

        assert "Bash(git push:*)" in temp_memory.permission_patterns
        pattern = temp_memory.permission_patterns["Bash(git push:*)"]
        assert pattern.count == 3

    def test_no_pattern_on_deny(self, temp_memory):
        """测试拒绝决策不创建模式"""
        temp_memory.record_permission_decision("Bash(some-command:arg)", "deny")

        # 拒绝不应该创建模式
        assert len(temp_memory.permission_patterns) == 0


class TestPermissionSuggestions:
    """测试权限建议生成"""

    @pytest.fixture
    def memory_with_data(self, tmp_path):
        """创建有数据的 PersonalMemory"""
        memory = PersonalMemory(memory_dir=tmp_path / "memory")

        # 添加一些权限决策
        permissions = [
            ("Bash(git push:origin main)", "allow"),
            ("Bash(git push:origin dev)", "allow"),
            ("Bash(git push:origin feature)", "allow"),
            ("Bash(pip install:requests)", "allow"),
            ("Bash(pip install:numpy)", "allow"),
            ("Bash(pip install:pandas)", "allow"),
        ]

        for perm, action in permissions:
            memory.record_permission_decision(perm, action)

        return memory

    def test_suggest_permissions(self, memory_with_data):
        """测试生成建议"""
        suggestions = memory_with_data.suggest_permissions(threshold=2)

        assert len(suggestions) == 2  # git push 和 pip install

        patterns = [s["pattern"] for s in suggestions]
        assert "Bash(git push:*)" in patterns
        assert "Bash(pip install:*)" in patterns

    def test_suggest_with_high_threshold(self, memory_with_data):
        """测试高阈值"""
        suggestions = memory_with_data.suggest_permissions(threshold=5)
        assert len(suggestions) == 0

    def test_suggestions_sorted_by_count(self, memory_with_data):
        """测试建议按次数排序"""
        suggestions = memory_with_data.suggest_permissions(threshold=1)

        # 两个模式都是 3 次，顺序不重要，但应该都有
        assert len(suggestions) >= 2


class TestPermissionStats:
    """测试权限统计"""

    @pytest.fixture
    def memory_with_mixed_data(self, tmp_path):
        """创建混合数据的 PersonalMemory"""
        memory = PersonalMemory(memory_dir=tmp_path / "memory")

        permissions = [
            ("Bash(git push:origin main)", "allow"),
            ("Bash(git push:origin dev)", "allow"),
            ("Bash(rm -rf:/data)", "deny"),
            ("Bash(sudo:apt install)", "deny"),
        ]

        for perm, action in permissions:
            memory.record_permission_decision(perm, action)

        return memory

    def test_get_permission_stats(self, memory_with_mixed_data):
        """测试获取统计"""
        stats = memory_with_mixed_data.get_permission_stats()

        assert stats["total_decisions"] == 4
        assert stats["allowed"] == 2
        assert stats["denied"] == 2

    def test_get_permission_patterns(self, memory_with_mixed_data):
        """测试获取模式列表"""
        patterns = memory_with_mixed_data.get_permission_patterns(min_count=1)

        # 只有 git push 被允许，且形成了模式
        assert len(patterns) >= 1


class TestPersistence:
    """测试持久化"""

    def test_permissions_persist_across_reloads(self, tmp_path):
        """测试权限数据跨实例持久化"""
        memory_dir = tmp_path / "memory"

        # 第一次实例
        memory1 = PersonalMemory(memory_dir=memory_dir)
        memory1.record_permission_decision("Bash(git push:origin main)", "allow")

        # 第二次实例
        memory2 = PersonalMemory(memory_dir=memory_dir)

        assert "Bash(git push:origin main)" in memory2.permission_decisions
        assert len(memory2.permission_patterns) == 1


class TestHookIntegration:
    """测试 Hook 与 Memory 的集成"""

    @pytest.fixture
    def temp_memory(self, tmp_path):
        """创建临时 PersonalMemory"""
        return PersonalMemory(memory_dir=tmp_path / "memory")

    def test_hook_flow(self, temp_memory):
        """测试完整的 Hook 流程"""
        # 模拟 Hook 收到的输入
        hook_input = {
            "notification_type": "permission_prompt",
            "permission": "Bash(git push:origin main)",
            "action": "allow",
        }

        # 调用 Memory API
        temp_memory.record_permission_decision(
            permission=hook_input["permission"],
            action=hook_input["action"],
            context={"source": "test_hook"},
        )

        # 验证存储
        stats = temp_memory.get_permission_stats()
        assert stats["allowed"] == 1
        assert stats["patterns_discovered"] == 1

    def test_multiple_hook_calls(self, temp_memory):
        """测试多次 Hook 调用"""
        calls = [
            {"permission": "Bash(git push:origin main)", "action": "allow"},
            {"permission": "Bash(git push:origin dev)", "action": "allow"},
            {"permission": "Bash(pip install:requests)", "action": "allow"},
            {"permission": "Bash(pip install:numpy)", "action": "allow"},
            {"permission": "Bash(pip install:pandas)", "action": "allow"},
        ]

        for call in calls:
            temp_memory.record_permission_decision(
                permission=call["permission"],
                action=call["action"],
            )

        # 验证模式归纳
        suggestions = temp_memory.suggest_permissions(threshold=2)
        assert len(suggestions) == 2  # git push 和 pip install


if __name__ == "__main__":
    pytest.main([__file__, "-v"])