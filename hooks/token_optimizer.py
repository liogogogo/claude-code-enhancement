#!/usr/bin/env python3
"""
Token 优化工具 - 分析和优化 Token 消耗

用法:
    python3 hooks/token_optimizer.py --analyze    # 分析 token 消耗
    python3 hooks/token_optimizer.py --clean      # 清理旧会话
    python3 hooks/token_optimizer.py --optimize   # 优化所有可优化的
"""

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path


def analyze_token_usage():
    """分析 Token 使用情况"""
    claude_dir = Path.home() / ".claude"

    print("=" * 60)
    print("📊 Token 消耗分析")
    print("=" * 60)

    # 分析各目录
    directories = [
        ("projects", "会话历史（每次加载）"),
        ("downloads", "下载缓存"),
        ("file-history", "文件历史"),
        ("plugins", "插件系统"),
        ("memory", "自动记忆"),
    ]

    total_size = 0
    for name, desc in directories:
        path = claude_dir / name
        if path.exists():
            size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
            total_size += size
            size_mb = size / (1024 * 1024)
            impact = "🔴 高" if size_mb > 10 else ("🟡 中" if size_mb > 1 else "🟢 低")
            print(f"{impact} {name}: {size_mb:.1f} MB - {desc}")

    print(f"\n总计: {total_size / (1024 * 1024):.1f} MB")

    # 分析会话文件
    print("\n" + "=" * 60)
    print("📝 会话文件分析")
    print("=" * 60)

    projects_dir = claude_dir / "projects"
    if projects_dir.exists():
        for project_dir in sorted(projects_dir.iterdir()):
            if project_dir.is_dir():
                jsonl_files = list(project_dir.glob("*.jsonl"))
                subagent_files = list(project_dir.rglob("*.meta.json"))

                size = sum(f.stat().st_size for f in jsonl_files)
                size_mb = size / (1024 * 1024)

                print(f"\n📁 {project_dir.name}")
                print(f"   会话文件: {len(jsonl_files)} 个, {size_mb:.1f} MB")
                print(f"   子代理元数据: {len(subagent_files)} 个")

                # 找最旧的会话
                if jsonl_files:
                    oldest = min(jsonl_files, key=lambda f: f.stat().st_mtime)
                    mtime = datetime.fromtimestamp(oldest.stat().st_mtime)
                    age = datetime.now() - mtime
                    print(f"   最旧会话: {age.days} 天前")

    # 分析 memory 文件
    print("\n" + "=" * 60)
    print("🧠 Memory 文件分析")
    print("=" * 60)

    memory_dir = Path.home() / ".claude/projects/-Users-liocc/memory"
    if memory_dir.exists():
        for md_file in memory_dir.glob("*.md"):
            lines = len(md_file.read_text().split('\n'))
            size = md_file.stat().st_size
            print(f"📄 {md_file.name}: {lines} 行, {size} 字节")

    return total_size


def clean_old_sessions(days: int = 7, dry_run: bool = True):
    """
    清理旧会话

    Args:
        days: 保留最近几天的会话
        dry_run: 只显示不执行
    """
    claude_dir = Path.home() / ".claude"
    projects_dir = claude_dir / "projects"

    if not projects_dir.exists():
        print("没有找到 projects 目录")
        return

    cutoff = datetime.now() - timedelta(days=days)
    deleted_size = 0
    deleted_count = 0

    print(f"\n🧹 清理 {days} 天前的会话")
    print("=" * 60)

    for project_dir in projects_dir.iterdir():
        if not project_dir.is_dir():
            continue

        # 清理会话文件
        for jsonl_file in project_dir.glob("*.jsonl"):
            mtime = datetime.fromtimestamp(jsonl_file.stat().st_mtime)
            if mtime < cutoff:
                size = jsonl_file.stat().st_size
                deleted_size += size
                deleted_count += 1

                if dry_run:
                    print(f"[DRY] 删除: {jsonl_file.name} ({size / 1024:.0f} KB)")
                else:
                    jsonl_file.unlink()
                    print(f"删除: {jsonl_file.name}")

        # 清理子代理元数据
        for meta_file in project_dir.rglob("*.meta.json"):
            mtime = datetime.fromtimestamp(meta_file.stat().st_mtime)
            if mtime < cutoff:
                size = meta_file.stat().st_size
                deleted_size += size

                if dry_run:
                    print(f"[DRY] 删除: {meta_file.relative_to(project_dir)}")
                else:
                    meta_file.unlink()

    print(f"\n{'[预览]' if dry_run else '[完成]'} 删除 {deleted_count} 个文件，释放 {deleted_size / (1024 * 1024):.1f} MB")

    if dry_run:
        print("\n提示: 使用 --clean --execute 执行实际删除")


def optimize_memory():
    """优化 Memory 文件"""
    memory_dir = Path.home() / ".claude/projects/-Users-liocc/memory"
    memory_file = memory_dir / "MEMORY.md"

    if not memory_file.exists():
        print("Memory 文件不存在")
        return

    print("\n🔧 优化 Memory 文件")
    print("=" * 60)

    content = memory_file.read_text()
    original_size = len(content)

    # 读取所有引用的 memory 文件
    lines = content.split('\n')
    kept_lines = []
    removed_refs = []

    for line in lines:
        if line.startswith("- [") and "](" in line:
            # 提取文件名
            match = content_extract_link(line)
            if match:
                ref_file = memory_dir / match
                if not ref_file.exists():
                    removed_refs.append(match)
                    continue
        kept_lines.append(line)

    if removed_refs:
        new_content = '\n'.join(kept_lines)
        memory_file.write_text(new_content)
        print(f"移除无效引用: {len(removed_refs)} 个")
        for ref in removed_refs:
            print(f"  - {ref}")
        print(f"节省: {original_size - len(new_content)} 字节")
    else:
        print("Memory 文件已优化，无需更改")


def content_extract_link(line: str) -> str:
    """从 markdown 链接中提取文件名"""
    import re
    match = re.search(r'\]\(([^)]+)\)', line)
    return match.group(1) if match else None


def optimize_hooks():
    """优化 Hook 输出，减少不必要的上下文"""
    print("\n⚡ Hook 优化建议")
    print("=" * 60)

    suggestions = [
        ("项目知识 Hook", "只在首次编辑时注入，避免重复注入"),
        ("权限学习 Hook", "使用缓存，避免每次都写入文件"),
        ("SessionStart Hook", "按需索引，跳过大型项目自动索引"),
    ]

    for name, suggestion in suggestions:
        print(f"📌 {name}")
        print(f"   建议: {suggestion}\n")


def generate_claudignore():
    """生成 .claudeignore 文件"""
    claudeignore_content = """# Claude Code 忽略文件
# 这些文件不会被索引，减少 token 消耗

# 依赖目录
node_modules/
.venv/
venv/
__pycache__/
.pytest_cache/
.mypy_cache/

# 构建产物
dist/
build/
*.egg-info/
.eggs/

# 大型文件
*.min.js
*.min.css
*.bundle.js
*.lock
package-lock.json
yarn.lock
pnpm-lock.yaml

# 数据文件
*.csv
*.xlsx
*.parquet
*.pkl
*.pickle

# 媒体文件
*.png
*.jpg
*.jpeg
*.gif
*.mp4
*.mp3

# 日志和缓存
*.log
*.cache
.cache/

# IDE
.idea/
.vscode/
*.swp
*.swo

# 测试覆盖率
htmlcov/
.coverage
coverage.xml

# 文档（可选）
# docs/
# *.md
"""

    print("\n📝 建议创建 .claudeignore 文件")
    print("=" * 60)
    print(claudeignore_content)

    return claudeignore_content


def main():
    parser = argparse.ArgumentParser(description="Token 优化工具")
    parser.add_argument("--analyze", action="store_true", help="分析 token 消耗")
    parser.add_argument("--clean", action="store_true", help="清理旧会话")
    parser.add_argument("--execute", action="store_true", help="执行实际删除（配合 --clean）")
    parser.add_argument("--optimize", action="store_true", help="执行所有优化")
    parser.add_argument("--days", type=int, default=7, help="保留最近几天的会话")
    parser.add_argument("--claudeignore", action="store_true", help="生成 .claudeignore 模板")

    args = parser.parse_args()

    if args.analyze or args.optimize:
        analyze_token_usage()

    if args.clean or args.optimize:
        clean_old_sessions(days=args.days, dry_run=not args.execute)

    if args.optimize:
        optimize_memory()
        optimize_hooks()

    if args.claudeignore:
        generate_claudignore()

    if not any([args.analyze, args.clean, args.optimize, args.claudeignore]):
        # 默认显示分析
        analyze_token_usage()
        print("\n💡 使用 --help 查看更多选项")


if __name__ == "__main__":
    main()