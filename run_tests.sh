#!/bin/bash
#
# 运行测试脚本
#

set -e

cd "$(dirname "$0")"

echo "========================================"
echo "  Claude Code Enhancement - Test Suite"
echo "========================================"
echo ""

# 检查依赖
if ! command -v pytest &> /dev/null; then
    echo "Installing test dependencies..."
    pip install pytest pytest-cov pytest-asyncio
fi

# 运行测试
echo "Running tests..."
echo ""

# 快速测试 (排除 slow 和 integration)
if [ "$1" == "--fast" ]; then
    pytest tests/ -v --tb=short -m "not slow and not integration" --cov=src --cov-report=term-missing
# 完整测试
elif [ "$1" == "--all" ]; then
    pytest tests/ -v --tb=short --cov=src --cov-report=html
# 默认: 单元测试
else
    pytest tests/ -v --tb=short -m "not integration" --cov=src --cov-report=term-missing
fi

echo ""
echo "========================================"
echo "  Tests completed!"
echo "========================================"
