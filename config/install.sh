#!/bin/bash
#
# Claude Code Enhancement Installer
# 一键安装 Claude Code 增强配置
#
# 用法:
#   本地: ./install.sh
#   远程: curl -fsSL https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/config/install.sh | bash
#

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# 配置路径
CLAUDE_DIR="$HOME/.claude"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
BACKUP_FILE="$CLAUDE_DIR/settings.json.backup.$(date +%Y%m%d%H%M%S)"
REPO_URL="git@github.com:liogogogo/claude-code-enhancement.git"
RAW_URL="https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/config"

# 检测脚本目录（本地或远程）
if [ -n "$0" ] && [ "$0" != "bash" ] && [ "$0" != "-bash" ]; then
    SCRIPT_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
else
    SCRIPT_DIR=""
fi

echo -e "${CYAN}"
echo "╔══════════════════════════════════════════════════════════╗"
echo "║        Claude Code Enhancement Installer                 ║"
echo "║        一键增强你的 Claude Code 开发体验                  ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# 检查并安装依赖
check_dependencies() {
    echo -e "${YELLOW}[1/6] 检查依赖...${NC}"

    local missing=()
    local install_cmd=""

    # 检测系统
    if [[ "$OSTYPE" == "darwin"* ]]; then
        install_cmd="brew install"
    elif command -v apt-get &> /dev/null; then
        install_cmd="sudo apt-get install -y"
    elif command -v pacman &> /dev/null; then
        install_cmd="sudo pacman -S --noconfirm"
    elif command -v dnf &> /dev/null; then
        install_cmd="sudo dnf install -y"
    fi

    # 检查 jq
    if ! command -v jq &> /dev/null; then
        missing+=("jq")
    fi

    # 检查 node (prettier 需要)
    if ! command -v node &> /dev/null; then
        missing+=("node")
    fi

    if [ ${#missing[@]} -gt 0 ]; then
        echo -e "${RED}✗ 缺少依赖: ${missing[*]}${NC}"
        echo ""

        if [ -n "$install_cmd" ]; then
            echo -e "${YELLOW}建议运行:${NC}"
            echo "  $install_cmd ${missing[*]}"
            echo ""

            read -p "是否自动安装? [y/N] " -n 1 -r
            echo

            if [[ $REPLY =~ ^[Yy]$ ]]; then
                eval "$install_cmd ${missing[*]}"
            else
                exit 1
            fi
        else
            echo "请手动安装后重试"
            exit 1
        fi
    fi

    echo -e "${GREEN}✓ 依赖检查通过${NC}"
}

# 下载模板文件
download_template() {
    echo -e "${YELLOW}[2/6] 准备配置模板...${NC}"

    TEMPLATE_FILE="/tmp/claude-settings.template.json"

    if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/settings.template.json" ]; then
        # 本地文件
        cp "$SCRIPT_DIR/settings.template.json" "$TEMPLATE_FILE"
        echo -e "${GREEN}✓ 使用本地模板${NC}"
    else
        # 远程下载
        echo -e "${BLUE}  从 GitHub 下载模板...${NC}"
        if command -v curl &> /dev/null; then
            curl -fsSL "$RAW_URL/settings.template.json" -o "$TEMPLATE_FILE"
        elif command -v wget &> /dev/null; then
            wget -q "$RAW_URL/settings.template.json" -O "$TEMPLATE_FILE"
        else
            echo -e "${RED}✗ 需要 curl 或 wget${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ 模板下载完成${NC}"
    fi
}

# 备份现有配置
backup_settings() {
    echo -e "${YELLOW}[3/6] 备份现有配置...${NC}"

    mkdir -p "$CLAUDE_DIR"

    if [ -f "$SETTINGS_FILE" ]; then
        cp "$SETTINGS_FILE" "$BACKUP_FILE"
        echo -e "${GREEN}✓ 已备份到: $BACKUP_FILE${NC}"
    else
        echo -e "${BLUE}ℹ 不存在现有配置，将创建新配置${NC}"
    fi
}

# 合并配置
merge_settings() {
    echo -e "${YELLOW}[4/6] 合并配置...${NC}"

    if [ -f "$SETTINGS_FILE" ]; then
        # 智能合并：保留现有的 env、extraKnownMarketplaces 等
        # 模板中的 permissions 和 hooks 会覆盖/合并
        jq -s '
            .[0] * .[1] |
            # 合并 permissions.allow 数组（去重）
            .permissions.allow = ((.[0].permissions.allow // []) + (.[1].permissions.allow // [])) | unique
        ' "$SETTINGS_FILE" "$TEMPLATE_FILE" > "$SETTINGS_FILE.tmp" 2>/dev/null || {
            # 如果 jq 合并失败，直接使用模板
            cp "$TEMPLATE_FILE" "$SETTINGS_FILE.tmp"
        }
        mv "$SETTINGS_FILE.tmp" "$SETTINGS_FILE"
    else
        cp "$TEMPLATE_FILE" "$SETTINGS_FILE"
    fi

    echo -e "${GREEN}✓ 配置已合并${NC}"
}

# 安装 shell 别名
install_alias() {
    echo -e "${YELLOW}[5/6] 安装 shell 别名...${NC}"

    local alias_line='alias cc='"'"'claude --dangerously-skip-permissions'"'"
    local marker="# Claude Code Enhancement"

    # 检测 shell 配置文件
    local shell_rc=""
    if [ -n "$ZSH_VERSION" ]; then
        shell_rc="$HOME/.zshrc"
    elif [ -n "$BASH_VERSION" ]; then
        shell_rc="$HOME/.bashrc"
    else
        # 尝试检测
        if [ -f "$HOME/.zshrc" ]; then
            shell_rc="$HOME/.zshrc"
        elif [ -f "$HOME/.bashrc" ]; then
            shell_rc="$HOME/.bashrc"
        fi
    fi

    if [ -n "$shell_rc" ]; then
        if ! grep -q "$marker" "$shell_rc" 2>/dev/null; then
            echo "" >> "$shell_rc"
            echo "$marker" >> "$shell_rc"
            echo "$alias_line" >> "$shell_rc"
            echo -e "${GREEN}✓ 已添加 'cc' 别名到 $shell_rc${NC}"
            echo -e "${BLUE}  运行 'source $shell_rc' 生效${NC}"
        else
            echo -e "${BLUE}ℹ 'cc' 别名已存在${NC}"
        fi
    fi
}

# 验证安装
verify_installation() {
    echo -e "${YELLOW}[6/6] 验证安装...${NC}"

    local errors=0

    if [ ! -f "$SETTINGS_FILE" ]; then
        echo -e "${RED}✗ 配置文件不存在${NC}"
        errors=$((errors + 1))
    fi

    if ! jq empty "$SETTINGS_FILE" 2>/dev/null; then
        echo -e "${RED}✗ 配置文件 JSON 格式错误${NC}"
        errors=$((errors + 1))
    fi

    if [ $errors -eq 0 ]; then
        echo -e "${GREEN}✓ 安装验证通过${NC}"
    else
        echo -e "${RED}✗ 发现 $errors 个错误${NC}"
        exit 1
    fi
}

# 显示完成信息
show_complete() {
    echo ""
    echo -e "${GREEN}══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}            安装完成!                        ${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}已启用的功能:${NC}"
    echo "  ✓ 28+ 常用命令自动允许 (git, npm, pip, cargo...)"
    echo "  ✓ 自动格式化 (prettier)"
    echo "  ✓ 危险命令拦截 (rm -rf, drop table...)"
    echo "  ✓ 任务完成提示音"
    echo "  ✓ 'cc' 别名 (跳过权限确认)"
    echo ""
    echo -e "${YELLOW}下一步:${NC}"
    echo -e "  ${BLUE}source ~/.zshrc${NC}   # 或 source ~/.bashrc"
    echo -e "  ${BLUE}cc${NC}                # 使用短命令启动"
    echo ""
    echo -e "${YELLOW}恢复备份 (如需要):${NC}"
    echo "  cp $BACKUP_FILE $SETTINGS_FILE"
    echo ""
    echo -e "${YELLOW}在新机器上一键安装:${NC}"
    echo -e "  ${BLUE}curl -fsSL https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/config/install.sh | bash${NC}"
    echo ""
}

# 主流程
main() {
    check_dependencies
    download_template
    backup_settings
    merge_settings
    install_alias
    verify_installation
    show_complete
}

main "$@"
