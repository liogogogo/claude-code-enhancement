.PHONY: help install dev test test-fast test-cov lint format clean docs build publish

# 默认目标
help:
	@echo "Claude Code Enhancement - Makefile"
	@echo ""
	@echo "使用: make [target]"
	@echo ""
	@echo "目标:"
	@echo "  install      安装依赖"
	@echo "  dev          安装开发依赖"
	@echo "  test         运行所有测试"
	@echo "  test-fast    运行快速测试"
	@echo "  test-cov     运行测试并生成覆盖率报告"
	@echo "  lint         运行代码检查"
	@echo "  format       格式化代码"
	@echo "  clean        清理临时文件"
	@echo "  docs         构建文档"
	@echo "  build        构建包"
	@echo "  publish      发布到 PyPI"

# 安装
install:
	pip install -e .

# 开发依赖
dev:
	pip install -e ".[dev]"
	pip install pytest pytest-cov pytest-asyncio black ruff mypy

# 测试
test:
	pytest tests/ -v --tb=short

test-fast:
	pytest tests/ -v --tb=short -m "not slow and not integration"

test-cov:
	pytest tests/ -v --tb=short --cov=src --cov-report=term-missing --cov-report=html

# 代码检查
lint:
	black --check src/ tests/
	ruff check src/ tests/
	mypy src/

# 格式化
format:
	black src/ tests/
	ruff check --fix src/ tests/

# 清理
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# 文档
docs:
	cd docs && $(MAKE) html

# 构建
build: clean
	python -m build

# 发布
publish: build
	twine upload dist/*
