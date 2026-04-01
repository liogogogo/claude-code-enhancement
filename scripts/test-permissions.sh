#!/bin/bash
#
# 测试 Claude Code 权限配置
#
# 用法: ./scripts/test-permissions.sh [level]
#   level: l1, l2-python, l2-go, l3, l4 (默认 l4)

set -e

# 颜色
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

LEVEL="${1:-l4}"
TEMPLATES_DIR="$(cd "$(dirname "$0")/../templates" && pwd)"

# 映射等级到文件
case $LEVEL in
    l1) TEMPLATE="l1-minimal.json" ;;
    l2-python) TEMPLATE="l2-standard-python.json" ;;
    l2-go) TEMPLATE="l2-standard-go.json" ;;
    l3) TEMPLATE="l3-elevated.json" ;;
    l4) TEMPLATE="l4-full-trust.json" ;;
    *)
        echo -e "${RED}无效等级: $LEVEL${NC}"
        echo "有效选项: l1, l2-python, l2-go, l3, l4"
        exit 1
        ;;
esac

echo -e "${CYAN}══════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Claude Code 权限配置测试${NC}"
echo -e "${CYAN}══════════════════════════════════════════════${NC}"
echo ""

# 1. 验证模板存在
echo -e "${YELLOW}[1/4] 验证模板文件...${NC}"
TEMPLATE_PATH="$TEMPLATES_DIR/$TEMPLATE"
if [ ! -f "$TEMPLATE_PATH" ]; then
    echo -e "${RED}✗ 模板不存在: $TEMPLATE_PATH${NC}"
    exit 1
fi
echo -e "${GREEN}✓ 模板: $TEMPLATE${NC}"

# 2. 验证 JSON 格式
echo -e "${YELLOW}[2/4] 验证 JSON 格式...${NC}"
if ! jq empty "$TEMPLATE_PATH" 2>/dev/null; then
    echo -e "${RED}✗ JSON 格式错误${NC}"
    exit 1
fi
echo -e "${GREEN}✓ JSON 格式正确${NC}"

# 3. 显示权限配置
echo -e "${YELLOW}[3/4] 权限配置内容:${NC}"
echo ""
echo -e "${BLUE}允许:${NC}"
jq -r '.permissions.allow[]' "$TEMPLATE_PATH" | head -20 | while read line; do
    echo "  ✓ $line"
done
ALLOW_COUNT=$(jq '.permissions.allow | length' "$TEMPLATE_PATH")
if [ "$ALLOW_COUNT" -gt 20 ]; then
    echo "  ... 共 $ALLOW_COUNT 条"
elif [ "$ALLOW_COUNT" -eq 1 ]; then
    TOTAL=$(jq -r '.permissions.allow[0]' "$TEMPLATE_PATH")
    if [ "$TOTAL" = "*" ]; then
        echo -e "${GREEN}  ★ 允许所有操作 (*)${NC}"
    fi
fi

echo ""
echo -e "${BLUE}拒绝:${NC}"
if jq -e '.permissions.deny' "$TEMPLATE_PATH" > /dev/null 2>&1; then
    jq -r '.permissions.deny[]' "$TEMPLATE_PATH" 2>/dev/null | while read line; do
        echo "  ✗ $line"
    done
else
    echo "  (无)"
fi

# 4. 应用配置
echo ""
echo -e "${YELLOW}[4/4] 应用配置...${NC}"
CLAUDE_DIR=".claude"
mkdir -p "$CLAUDE_DIR"
cp "$TEMPLATE_PATH" "$CLAUDE_DIR/settings.json"
echo -e "${GREEN}✓ 已应用到 $CLAUDE_DIR/settings.json${NC}"

# 5. 显示测试建议
echo ""
echo -e "${CYAN}══════════════════════════════════════════════${NC}"
echo -e "${GREEN}  配置已应用!${NC}"
echo -e "${CYAN}══════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}测试方法:${NC}"
echo ""
echo "1. 启动 Claude Code:"
echo -e "   ${BLUE}claude${NC}"
echo ""
echo "2. 测试命令 (应该不再有权限提示):"
echo -e "   ${BLUE}>>> ls${NC}"
echo -e "   ${BLUE}>>> git status${NC}"
echo -e "   ${BLUE}>>> pip list${NC}"
echo ""
echo "3. 测试危险命令 (应该被拦截):"
echo -e "   ${BLUE}>>> rm -rf /${NC}"
echo ""
echo -e "${YELLOW}当前等级: ${GREEN}$LEVEL${NC}"
echo ""
