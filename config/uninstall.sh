#!/bin/bash
#
# Claude Code Enhancement Uninstaller
# 卸载增强配置，恢复原始状态
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

CLAUDE_DIR="$HOME/.claude"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"

echo -e "${YELLOW}卸载 Claude Code Enhancement${NC}"
echo ""

# 查找最新备份
LATEST_BACKUP=$(ls -t "$CLAUDE_DIR"/settings.json.backup.* 2>/dev/null | head -1)

if [ -n "$LATEST_BACKUP" ]; then
    echo -e "${BLUE}发现备份: $LATEST_BACKUP${NC}"
    read -p "是否恢复此备份? [Y/n] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
        cp "$LATEST_BACKUP" "$SETTINGS_FILE"
        echo -e "${GREEN}✓ 已恢复备份${NC}"
    fi
else
    echo -e "${YELLOW}未找到备份文件${NC}"
fi

# 移除别名
echo ""
read -p "是否移除 'cc' 别名? [Y/n] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]] || [[ -z $REPLY ]]; then
    for rc in "$HOME/.zshrc" "$HOME/.bashrc"; do
        if [ -f "$rc" ]; then
            sed -i.bak '/# Claude Code alias/d; /alias cc=/d' "$rc" 2>/dev/null || true
            rm -f "${rc}.bak"
        fi
    done
    echo -e "${GREEN}✓ 已移除别名${NC}"
fi

echo ""
echo -e "${GREEN}卸载完成${NC}"
