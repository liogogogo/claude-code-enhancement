#!/bin/bash
#
# Claude Code Enhancement Installer
# 一键安装 Claude Code 增强配置
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置路径
CLAUDE_DIR="$HOME/.claude"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
BACKUP_FILE="$CLAUDE_DIR/settings.json.backup.$(date +%Y%m%d%H%M%S)"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TEMPLATE_FILE="$SCRIPT_DIR/settings.template.json"

echo -e "${BLUE}╔════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Claude Code Enhancement Installer        ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════╝${NC}"
echo ""

# 检查依赖
check_dependencies() {
    echo -e "${YELLOW}[1/5] 检查依赖...${NC}"

    local missing=()

    if ! command -v jq &> /dev/null; then
        missing+=("jq")
    fi

    if ! command -v npx &> /dev/null; then
        missing+=("node/npm")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "${RED}缺少依赖: ${missing[*]}${NC}"
        echo ""
        echo "安装建议:"
        echo "  macOS: brew install jq node"
        echo "  Ubuntu: sudo apt install jq nodejs npm"
        echo "  Arch: sudo pacman -S jq nodejs npm"
        exit 1
    fi

    echo -e "${GREEN}✓ 依赖检查通过${NC}"
}

# 备份现有配置
backup_settings() {
    echo -e "${YELLOW}[2/5] 备份现有配置...${NC}"

    if [ -f "$SETTINGS_FILE" ]; then
        cp "$SETTINGS_FILE" "$BACKUP_FILE"
        echo -e "${GREEN}✓ 已备份到: $BACKUP_FILE${NC}"
    else
        echo -e "${BLUE}ℹ 不存在现有配置，将创建新配置${NC}"
    fi
}

# 合并配置
merge_settings() {
    echo -e "${YELLOW}[3/5] 合并配置...${NC}"

    mkdir -p "$CLAUDE_DIR"

    if [ -f "$SETTINGS_FILE" ]; then
        # 合并现有配置和模板
        # 保留现有的 env 和 extraKnownMarketplaces
        jq -s '.[0] * .[1]' "$SETTINGS_FILE" "$TEMPLATE_FILE" > "$SETTINGS_FILE.tmp"
        mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
    else
        cp "$TEMPLATE_FILE" "$SETTINGS_FILE"
    fi

    echo -e "${GREEN}✓ 配置已合并${NC}"
}

# 安装 shell 别名
install_alias() {
    echo -e "${YELLOW}[4/5] 安装 shell 别名...${NC}"

    local alias_line='alias cc='"'"'claude --dangerously-skip-permissions'"'"

    # 检测 shell 配置文件
    local shell_rc=""
    if [ -n "$ZSH_VERSION" ]; then
        shell_rc="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        shell_rc="$HOME/.bashrc"
    fi

    if [ -n "$shell_rc" ]; then
        if ! grep -q "alias cc=" "$shell_rc" 2>/dev/null; then
            echo "" >> "$shell_rc"
            echo "# Claude Code alias" >> "$shell_rc"
            echo "$alias_line" >> "$shell_rc"
            echo -e "${GREEN}✓ 已添加 'cc' 别名到 $shell_rc${NC}"
            echo -e "${BLUE}  运行 'source $shell_rc' 生效${NC}"
        else
            echo -e "${BLUE}ℹ 'cc' 别名已存在${NC}"
        fi
    fi
}

# 显示完成信息
show_complete() {
    echo ""
    echo -e "${YELLOW}[5/5] 安装完成!${NC}"
    echo ""
    echo -e "${GREEN}已启用的功能:${NC}"
    echo "  ✓ 28+ 常用命令自动允许（无需确认）"
    echo "  ✓ 自动格式化（prettier）"
    echo "  ✓ 危险命令拦截（rm -rf, drop table 等）"
    echo "  ✓ 任务完成提示音"
    echo "  ✓ 'cc' 别名（跳过权限确认）"
    echo ""
    echo -e "${BLUE}下一步:${NC}"
    echo "  1. source ~/.zshrc  # 或 ~/.bashrc"
    echo "  2. cc               # 使用短命令启动"
    echo ""
    echo -e "${BLUE}恢复备份 (如需要):${NC}"
    echo "  cp $BACKUP_FILE $SETTINGS_FILE"
    echo ""
}

# 主流程
main() {
    check_dependencies
    backup_settings
    merge_settings
    install_alias
    show_complete
}

main "$@"
