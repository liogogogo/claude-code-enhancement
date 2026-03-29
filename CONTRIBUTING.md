# 贡献指南

感谢你考虑为 Claude Code Enhancement 项目做出贡献！

## 🚀 快速开始

### 1. Fork 并克隆

```bash
git clone https://github.com/YOUR_USERNAME/claude-code-enhancement.git
cd claude-code-enhancement
```

### 2. 创建虚拟环境

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 安装开发依赖

```bash
pip install -e ".[dev]"
pip install pytest pytest-cov pytest-asyncio
```

### 4. 运行测试

```bash
./run_tests.sh
# 或
make test
```

## 📋 开发流程

### 创建分支

```bash
git checkout -b feature/your-feature-name
# 或
git checkout -b fix/your-bug-fix
```

### 代码风格

- 使用 **Black** 格式化代码
- 使用 **Ruff** 检查代码
- 使用 **mypy** 进行类型检查

```bash
make lint  # 运行所有检查
```

### 提交信息

使用约定式提交：

```
feat: 添加多文件推理功能
fix: 修复依赖图构建错误
docs: 更新 API 文档
test: 添加上下文管理器测试
refactor: 重构记忆模块
```

### 提交 PR

1. 推送到你的 fork
2. 创建 Pull Request
3. 等待 CI 通过和代码审查

## 🧪 测试规范

### 运行测试

```bash
# 快速测试
make test-fast

# 完整测试
make test

# 带覆盖率
make test-cov
```

### 测试要求

- 新功能必须有测试
- 测试覆盖率不低于 80%
- 所有测试必须通过

## 📁 项目结构

```
src/
├── core/           # 核心模块
│   ├── context_manager.py
│   ├── multi_file_reasoning.py
│   ├── project_knowledge.py
│   └── unified.py
├── memory/         # 记忆系统
├── layer0-3/       # 四层架构
└── utils/          # 工具函数

tests/              # 测试文件
docs/               # 文档
config/             # 配置模板
```

## 🔍 代码审查清单

- [ ] 代码风格符合规范
- [ ] 测试覆盖充分
- [ ] 文档已更新
- [ ] 无安全漏洞
- [ ] 向后兼容

## 📞 联系方式

- GitHub Issues: [提交问题](https://github.com/liogogogo/claude-code-enhancement/issues)
- Discussions: [参与讨论](https://github.com/liogogogo/claude-code-enhancement/discussions)

## 📄 许可证

贡献的代码将以 MIT 许可证发布。
