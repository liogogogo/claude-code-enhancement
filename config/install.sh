#!/bin/bash
#
# Claude Code Enhancement Installer
# 一键安装 Claude Code 增强配置
#
# 用法:
#   本地: ./install.sh
#   远程: curl -fsSL https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/config/install.sh | bash
#   指定等级: ./install.sh --level l4
#   项目级安装: ./install.sh --scope project --level l3
#
# 权限等级:
#   l1 - Minimal (最小权限，CI/CD)
#   l2-python - Standard Python
#   l2-go - Standard Go
#   l3 - Elevated (提升权限)
#   l4 - Full Trust (完全信任)
#

set -e

# 参数
LEVEL=""
SCOPE=""  # "global" or "project"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
DIM='\033[2m'
NC='\033[0m'

# 配置路径（默认全局，后续可根据 scope 调整）
CLAUDE_DIR="$HOME/.claude"
SETTINGS_FILE=""
BACKUP_FILE=""
REPO_URL="git@github.com:liogogogo/claude-code-enhancement.git"
RAW_URL="https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/config"

# 等级详细信息 (使用函数返回，兼容 bash 3.x)
get_level_info() {
    local level="$1"
    case $level in
        l1)
            echo "🔒 L1 - Minimal|最小权限模式|CI/CD、不熟悉的项目|git, python, npm, go, ls, grep|无文件删除、无 MCP、无 Hooks"
            ;;
        l2-python)
            echo "🔐 L2 - Standard Python|标准 Python 项目|日常开发、个人项目|venv, pytest, ruff, black, mypy|MCP filesystem"
            ;;
        l2-go)
            echo "🔐 L2 - Standard Go|标准 Go 项目|日常开发、个人项目|gofmt, goimports, golangci-lint, dlv, make|MCP filesystem"
            ;;
        l3)
            echo "🔓 L3 - Elevated|提升权限模式|可信项目、频繁文件操作|cp, mv, curl, jq, tmux, cargo|环境变量、MCP memory、Prettier Hook"
            ;;
        l4)
            echo "♾️  L4 - Full Trust|完全信任模式|私有项目、完全信任环境|允许所有操作|仅拦截极端危险命令 (rm -rf /, mkfs)"
            ;;
    esac
}

# 检测脚本目录（本地或远程）
if [ -n "$0" ] && [ "$0" != "bash" ] && [ "$0" != "-bash" ]; then
    SCRIPT_DIR="$(cd "$(dirname "$0")" 2>/dev/null && pwd)"
else
    SCRIPT_DIR=""
fi

# 显示等级详细信息
show_level_details() {
    local level="$1"
    local info
    info=$(get_level_info "$level")

    local title desc scenario commands features
    title=$(echo "$info" | cut -d'|' -f1)
    desc=$(echo "$info" | cut -d'|' -f2)
    scenario=$(echo "$info" | cut -d'|' -f3)
    commands=$(echo "$info" | cut -d'|' -f4)
    features=$(echo "$info" | cut -d'|' -f5)

    echo -e "${MAGENTA}┌─────────────────────────────────────────────────────────┐${NC}"
    echo -e "${MAGENTA}│ ${title}                              ${NC}"
    echo -e "${MAGENTA}├─────────────────────────────────────────────────────────┤${NC}"
    echo -e "${MAGENTA}│${NC} ${DIM}描述:${NC} $desc"
    echo -e "${MAGENTA}│${NC} ${DIM}场景:${NC} $scenario"
    echo -e "${MAGENTA}│${NC} ${DIM}命令:${NC} $commands"
    echo -e "${MAGENTA}│${NC} ${DIM}特性:${NC} $features"
    echo -e "${MAGENTA}└─────────────────────────────────────────────────────────┘${NC}"
}

# 检测环境并推荐等级
detect_environment() {
    local env_type="personal"
    local recommend="l4"
    local reasons=()

    # 检测 CI 环境
    if [ -n "$CI" ] || [ -n "$GITHUB_ACTIONS" ] || [ -n "$GITLAB_CI" ] || [ -n "$JENKINS_URL" ]; then
        env_type="ci"
        recommend="l1"
        reasons+=("检测到 CI 环境")
    fi

    # 检测公司环境
    if [ -n "$CORPORATE_ENV" ] || [[ "$HOSTNAME" == *corp* ]] || [[ "$HOSTNAME" == *company* ]]; then
        env_type="corporate"
        recommend="l2-python"
        reasons+=("检测到公司环境")
    fi

    # 检测是否在 git 仓库中（项目级安装候选）
    local in_git=false
    if git rev-parse --is-inside-work-tree &>/dev/null; then
        in_git=true
    fi

    # 检测虚拟机/容器
    if [ -f "/.dockerenv" ] || [ -n "$container" ]; then
        env_type="container"
        recommend="l4"
        reasons+=("检测到容器环境")
    fi

    echo "$env_type:$recommend:${reasons[*]}:$in_git"
}

# 显示安装位置选择
select_scope() {
    local in_git="$1"

    echo -e "${YELLOW}选择安装位置:${NC}"
    echo ""
    echo -e "  ${DIM}1)${NC} 全局 (~/.claude/) - 所有项目共享配置"
    if [ "$in_git" = "true" ]; then
        echo -e "  ${DIM}2)${NC} 当前项目 (./.claude/) - 仅当前项目使用 ${BLUE}★ Git 仓库检测${NC}"
    else
        echo -e "  ${DIM}2)${NC} 当前目录 (./.claude/) - 仅当前目录使用"
    fi
    echo ""

    read -p "请选择 [1-2, 默认 1]: " -n 1 -r
    echo

    case $REPLY in
        2)
            SCOPE="project"
            CLAUDE_DIR="$(pwd)/.claude"
            ;;
        1|"")
            SCOPE="global"
            CLAUDE_DIR="$HOME/.claude"
            ;;
        *)
            SCOPE="global"
            CLAUDE_DIR="$HOME/.claude"
            ;;
    esac

    SETTINGS_FILE="$CLAUDE_DIR/settings.json"
    BACKUP_FILE="$CLAUDE_DIR/settings.json.backup.$(date +%Y%m%d%H%M%S)"

    echo -e "${GREEN}✓ 安装位置: $CLAUDE_DIR${NC}"
}

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
    echo -e "${YELLOW}[2/6] 准备配置模板 ($LEVEL)...${NC}"

    TEMPLATE_FILE="/tmp/claude-settings.template.json"
    TEMPLATES_DIR="templates"

    # 尝试本地模板目录
    if [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/../$TEMPLATES_DIR/$TEMPLATE_NAME" ]; then
        cp "$SCRIPT_DIR/../$TEMPLATES_DIR/$TEMPLATE_NAME" "$TEMPLATE_FILE"
        echo -e "${GREEN}✓ 使用本地模板: $TEMPLATE_NAME${NC}"
    elif [ -n "$SCRIPT_DIR" ] && [ -f "$SCRIPT_DIR/$TEMPLATE_NAME" ]; then
        cp "$SCRIPT_DIR/$TEMPLATE_NAME" "$TEMPLATE_FILE"
        echo -e "${GREEN}✓ 使用本地模板: $TEMPLATE_NAME${NC}"
    else
        # 远程下载
        echo -e "${BLUE}  从 GitHub 下载模板...${NC}"
        local TEMPLATE_URL="https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/$TEMPLATES_DIR/$TEMPLATE_NAME"
        if command -v curl &> /dev/null; then
            curl -fsSL "$TEMPLATE_URL" -o "$TEMPLATE_FILE"
        elif command -v wget &> /dev/null; then
            wget -q "$TEMPLATE_URL" -O "$TEMPLATE_FILE"
        else
            echo -e "${RED}✗ 需要 curl 或 wget${NC}"
            exit 1
        fi
        echo -e "${GREEN}✓ 模板下载完成: $TEMPLATE_NAME${NC}"
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

# 选择权限等级
select_level() {
    # 解析命令行参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --level|-l)
                LEVEL="$2"
                shift 2
                ;;
            --scope|-s)
                SCOPE="$2"
                shift 2
                ;;
            --help|-h)
                echo "用法: $0 [选项]"
                echo ""
                echo "选项:"
                echo "  --level, -l <等级>   指定权限等级"
                echo "  --scope, -s <范围>   安装范围: global (全局) 或 project (项目)"
                echo "  --help, -h           显示帮助"
                echo ""
                echo "权限等级:"
                echo "  l1         - Minimal (最小权限，CI/CD)"
                echo "  l2-python  - Standard Python"
                echo "  l2-go      - Standard Go"
                echo "  l3         - Elevated (提升权限)"
                echo "  l4         - Full Trust (完全信任) ⭐"
                echo ""
                echo "示例:"
                echo "  $0 --level l4                    # 全局安装 L4"
                echo "  $0 --scope project --level l3    # 项目级安装 L3"
                exit 0
                ;;
            *)
                shift
                ;;
        esac
    done

    # 如果没有指定等级，显示交互式选择
    if [ -z "$LEVEL" ]; then
        # 检测环境
        local env_info
        env_info=$(detect_environment)
        IFS=':' read -r env_type recommend reasons in_git <<< "$env_info"

        # 显示环境检测结果
        echo -e "${BLUE}🔍 环境检测:${NC}"
        case $env_type in
            ci)        echo -e "   检测到 ${YELLOW}CI/CD 环境${NC}" ;;
            corporate) echo -e "   检测到 ${YELLOW}公司环境${NC}" ;;
            container) echo -e "   检测到 ${YELLOW}容器环境${NC}" ;;
            *)         echo -e "   检测到 ${GREEN}个人开发环境${NC}" ;;
        esac
        echo ""

        # 显示等级选择表格
        echo -e "${YELLOW}选择权限等级:${NC}"
        echo ""
        echo -e "  ${DIM}1)${NC} 🔒 L1 - Minimal      ${DIM}(最小权限，CI/CD)${NC}"
        echo -e "  ${DIM}2)${NC} 🔐 L2 - Python       ${DIM}(标准 Python 项目)${NC}"
        echo -e "  ${DIM}3)${NC} 🔐 L2 - Go           ${DIM}(标准 Go 项目)${NC}"
        echo -e "  ${DIM}4)${NC} 🔓 L3 - Elevated     ${DIM}(提升权限，可信项目)${NC}"
        echo -e "  ${DIM}5)${NC} ♾️  L4 - Full Trust   ${DIM}(完全信任)${NC} ${GREEN}★ 推荐${NC}"
        echo ""

        # 显示推荐
        if [ -n "$recommend" ] && [ "$recommend" != "l4" ]; then
            echo -e "${YELLOW}💡 根据环境检测，推荐: ${GREEN}$recommend${NC}"
            echo ""
        fi

        read -p "请选择 [1-5, 默认基于推荐]: " -n 1 -r
        echo

        case $REPLY in
            1) LEVEL="l1" ;;
            2) LEVEL="l2-python" ;;
            3) LEVEL="l2-go" ;;
            4) LEVEL="l3" ;;
            5) LEVEL="l4" ;;
            "")
                # 使用推荐值
                LEVEL="${recommend:-l4}"
                ;;
            *)
                LEVEL="${recommend:-l4}"
                ;;
        esac

        # 显示选中等级的详细信息
        echo ""
        show_level_details "$LEVEL"

        # 确认选择
        echo ""
        read -p "确认使用此等级? [Y/n]: " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Nn]$ ]]; then
            echo -e "${YELLOW}已取消，请重新运行脚本${NC}"
            exit 0
        fi
    fi

    # 验证等级
    case $LEVEL in
        l1) TEMPLATE_NAME="l1-minimal.json" ;;
        l2-python) TEMPLATE_NAME="l2-standard-python.json" ;;
        l2-go) TEMPLATE_NAME="l2-standard-go.json" ;;
        l3) TEMPLATE_NAME="l3-elevated.json" ;;
        l4) TEMPLATE_NAME="l4-full-trust.json" ;;
        *)
            echo -e "${RED}✗ 无效的等级: $LEVEL${NC}"
            echo "有效选项: l1, l2-python, l2-go, l3, l4"
            exit 1
            ;;
    esac

    echo -e "${GREEN}✓ 已选择: $LEVEL ($TEMPLATE_NAME)${NC}"
}

# 显示完成信息
show_complete() {
    echo ""
    echo -e "${GREEN}══════════════════════════════════════════════${NC}"
    echo -e "${GREEN}            安装完成!                        ${NC}"
    echo -e "${GREEN}══════════════════════════════════════════════${NC}"
    echo ""
    echo -e "${CYAN}安装信息:${NC}"
    echo -e "  ${DIM}位置:${NC} $SETTINGS_FILE"
    echo -e "  ${DIM}等级:${NC} $LEVEL"
    echo -e "  ${DIM}范围:${NC} $([ "$SCOPE" = "project" ] && echo "项目级" || echo "全局")"
    echo ""
    echo -e "${CYAN}已启用的功能:${NC}"
    echo "  ✓ 常用命令自动允许 (git, npm, pip, cargo...)"
    echo "  ✓ 危险命令拦截 (rm -rf, mkfs...)"
    if [ "$LEVEL" = "l3" ] || [ "$LEVEL" = "l4" ]; then
        echo "  ✓ 自动格式化 (prettier)"
        echo "  ✓ 权限学习 Hook"
    fi
    echo "  ✓ 'cc' 别名 (跳过权限确认)"
    echo ""
    echo -e "${YELLOW}下一步:${NC}"
    if [ "$SCOPE" = "global" ]; then
        echo -e "  ${BLUE}source ~/.zshrc${NC}   # 或 source ~/.bashrc"
    else
        echo -e "  ${BLUE}# 配置仅在当前项目生效${NC}"
    fi
    echo -e "  ${BLUE}cc${NC}                # 使用短命令启动"
    echo ""
    echo -e "${YELLOW}恢复备份 (如需要):${NC}"
    echo "  cp $BACKUP_FILE $SETTINGS_FILE"
    echo ""
    echo -e "${YELLOW}在新机器上一键安装:${NC}"
    echo -e "  ${BLUE}curl -fsSL https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/config/install.sh | bash${NC}"
    echo ""
    echo -e "${DIM}提示: 运行 --help 查看所有选项${NC}"
    echo ""
}

# 主流程
main() {
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --level|-l)
                LEVEL="$2"
                shift 2
                ;;
            --scope|-s)
                SCOPE="$2"
                shift 2
                ;;
            --help|-h)
                select_level --help
                ;;
            *)
                shift
                ;;
        esac
    done

    # 环境检测
    local env_info
    env_info=$(detect_environment)
    IFS=':' read -r env_type recommend reasons in_git <<< "$env_info"

    # 如果没有通过参数指定 scope，则交互式选择
    if [ -z "$SCOPE" ]; then
        select_scope "$in_git"
    else
        if [ "$SCOPE" = "project" ]; then
            CLAUDE_DIR="$(pwd)/.claude"
        else
            CLAUDE_DIR="$HOME/.claude"
        fi
        SETTINGS_FILE="$CLAUDE_DIR/settings.json"
        BACKUP_FILE="$CLAUDE_DIR/settings.json.backup.$(date +%Y%m%d%H%M%S)"
        echo -e "${GREEN}✓ 安装位置: $CLAUDE_DIR${NC}"
    fi

    # 选择权限等级
    select_level "$@"

    check_dependencies
    download_template
    backup_settings
    merge_settings
    install_alias
    verify_installation
    show_complete
}

main "$@"
