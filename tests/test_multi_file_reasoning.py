"""
测试多文件推理模块
"""

import pytest
import tempfile
from pathlib import Path

from src.core.multi_file_reasoning import (
    MultiFileReasoner,
    ImpactLevel,
    DependencyType,
    Symbol,
    Dependency,
    Impact,
    DependencyNode,
    create_reasoner,
)


@pytest.fixture
def sample_project():
    """创建示例项目"""
    with tempfile.TemporaryDirectory() as tmpdir:
        project = Path(tmpdir)

        # 创建文件结构
        (project / "src").mkdir()
        (project / "tests").mkdir()

        # auth/login.ts
        (project / "src" / "auth").mkdir()
        (project / "src" / "auth" / "login.ts").write_text('''
import { UserSession } from './session';
import { validateInput } from '../utils/validation';

export interface LoginCredentials {
    email: string;
    password: string;
}

export class LoginService {
    async login(credentials: LoginCredentials): Promise<UserSession> {
        validateInput(credentials);
        // login logic
        return new UserSession();
    }
}

export const login = async (email: string, password: string) => {
    const service = new LoginService();
    return service.login({ email, password });
};
''')

        # auth/session.ts
        (project / "src" / "auth" / "session.ts").write_text('''
export class UserSession {
    userId: string;
    token: string;

    isValid(): boolean {
        return !!this.token;
    }
}
''')

        # utils/validation.ts
        (project / "src" / "utils").mkdir()
        (project / "src" / "utils" / "validation.ts").write_text('''
export function validateInput(input: any): boolean {
    return input != null;
}
''')

        # middleware/auth.ts
        (project / "src" / "middleware").mkdir()
        (project / "src" / "middleware" / "auth.ts").write_text('''
import { UserSession } from '../auth/session';

export function authenticate(session: UserSession): boolean {
    return session.isValid();
}
''')

        # tests/auth.test.ts
        (project / "tests" / "auth.test.ts").write_text('''
import { LoginService } from '../src/auth/login';

describe('LoginService', () => {
    it('should login', async () => {
        const service = new LoginService();
        // test
    });
});
''')

        yield project


class TestMultiFileReasoner:
    """多文件推理器测试"""

    def test_build_dependency_graph(self, sample_project):
        """测试构建依赖图"""
        reasoner = MultiFileReasoner(sample_project)
        stats = reasoner.build_dependency_graph()

        assert stats["files_analyzed"] > 0
        assert stats["dependencies_found"] > 0
        assert stats["symbols_indexed"] > 0

    def test_analyze_file_extracts_symbols(self, sample_project):
        """测试符号提取"""
        reasoner = MultiFileReasoner(sample_project)
        reasoner.build_dependency_graph()

        # 检查 login.ts 的符号
        login_node = reasoner.dependency_graph.get("src/auth/login.ts")
        assert login_node is not None

        symbol_names = [s.name for s in login_node.symbols]
        assert "LoginService" in symbol_names
        assert "login" in symbol_names
        assert "LoginCredentials" in symbol_names

    def test_analyze_file_extracts_imports(self, sample_project):
        """测试导入提取"""
        reasoner = MultiFileReasoner(sample_project)
        reasoner.build_dependency_graph()

        login_node = reasoner.dependency_graph.get("src/auth/login.ts")
        assert login_node is not None
        assert len(login_node.imports) > 0

    def test_analyze_change_impact(self, sample_project):
        """测试修改影响分析"""
        reasoner = MultiFileReasoner(sample_project)
        reasoner.build_dependency_graph()

        impacts = reasoner.analyze_change(
            "src/auth/login.ts",
            "add MFA support"
        )

        assert len(impacts) > 0

        # 检查影响级别
        impact_files = [i.file_path for i in impacts]

        # 测试文件应该被识别
        test_impacts = [i for i in impacts if "test" in i.file_path]
        assert len(test_impacts) > 0

    def test_trace_symbol(self, sample_project):
        """测试符号追踪"""
        reasoner = MultiFileReasoner(sample_project)
        reasoner.build_dependency_graph()

        trace = reasoner.trace_symbol("UserSession")

        assert len(trace["definitions"]) > 0
        assert trace["definitions"][0]["name"] == "UserSession"

    def test_get_related_files(self, sample_project):
        """测试获取相关文件"""
        reasoner = MultiFileReasoner(sample_project)
        reasoner.build_dependency_graph()

        related = reasoner.get_related_files("src/auth/login.ts")

        # 应该包含 session.ts (被导入)
        assert len(related) > 0

    def test_find_related_tests(self, sample_project):
        """测试查找相关测试"""
        reasoner = MultiFileReasoner(sample_project)
        reasoner.build_dependency_graph()

        tests = reasoner._find_related_tests("src/auth/login.ts")

        assert len(tests) > 0
        assert any("test" in t for t in tests)

    def test_export_graph(self, sample_project):
        """测试导出依赖图"""
        reasoner = MultiFileReasoner(sample_project)
        reasoner.build_dependency_graph()

        output_path = sample_project / "dependency_graph.json"
        reasoner.export_graph(output_path)

        assert output_path.exists()

        import json
        data = json.loads(output_path.read_text())
        assert "nodes" in data
        assert len(data["nodes"]) > 0

    def test_get_stats(self, sample_project):
        """测试获取统计"""
        reasoner = MultiFileReasoner(sample_project)
        reasoner.build_dependency_graph()

        stats = reasoner.get_stats()

        assert stats["files"] > 0
        assert stats["total_symbols"] > 0
        assert len(stats["most_depended"]) > 0

    def test_create_reasoner_helper(self, sample_project):
        """测试便捷函数"""
        reasoner = create_reasoner(sample_project)

        assert reasoner is not None
        assert len(reasoner.dependency_graph) > 0


class TestSymbol:
    """符号测试"""

    def test_symbol_creation(self):
        """测试符号创建"""
        symbol = Symbol(
            name="testFunction",
            type="function",
            file_path="test.ts",
            line=10,
            exported=True,
        )

        assert symbol.name == "testFunction"
        assert symbol.exported is True

    def test_symbol_to_dict(self):
        """测试符号序列化"""
        symbol = Symbol(
            name="TestClass",
            type="class",
            file_path="test.ts",
            line=5,
        )

        data = symbol.to_dict()

        assert data["name"] == "TestClass"
        assert data["type"] == "class"
        assert data["line"] == 5


class TestImpact:
    """影响测试"""

    def test_impact_creation(self):
        """测试影响创建"""
        impact = Impact(
            file_path="test.ts",
            impact_level=ImpactLevel.HIGH,
            reason="Direct dependency",
            suggested_changes=["Update imports"],
        )

        assert impact.impact_level == ImpactLevel.HIGH
        assert len(impact.suggested_changes) == 1

    def test_impact_to_dict(self):
        """测试影响序列化"""
        impact = Impact(
            file_path="test.ts",
            impact_level=ImpactLevel.CRITICAL,
            reason="API change",
            symbols_affected=["login", "logout"],
        )

        data = impact.to_dict()

        assert data["impact_level"] == "critical"
        assert len(data["symbols_affected"]) == 2


# 运行测试
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
