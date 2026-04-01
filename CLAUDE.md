# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Claude Code Enhancement - A system that enhances Claude Code with persistent memory, project knowledge learning, and intelligent context management. Provides a 4-layer cognitive architecture for self-improving AI assistance.

## Development Commands

```bash
make install     # Install dependencies
make dev         # Install dev dependencies (pytest, black, ruff, mypy)
make test        # Run all tests: pytest tests/ -v --tb=short
make test-fast   # Run fast tests only (excludes slow/integration)
make test-cov    # Tests with coverage report
make lint        # Code linting (black --check, ruff, mypy)
make format      # Format code (black + ruff --fix)
```

Run single test file: `pytest tests/test_personal_memory.py -v`
Run specific test: `pytest tests/test_personal_memory.py::test_record_command -v`

## Architecture: 4-Layer Cognitive System

```
Layer 3 (Meta-Cognitive)  →  Self-reflection, strategy optimization, evolution tracking
Layer 2 (Cognitive)       →  Reasoning, learning, error analysis, knowledge transfer
Layer 1 (Perception)      →  Observation, action execution, feedback collection
Layer 0 (Infrastructure)  →  Docker sandbox, linters, test frameworks
```

**Data flow**: Layer 0 → Layer 1 → Layer 2 → Layer 3 → back to Layer 0 (closed loop)

## Key Modules

| Path | Purpose |
|------|---------|
| `src/core/unified.py` | Main entry point - `ClaudeCodeEnhancer` class |
| `src/core/context_manager.py` | RAG-based context management |
| `src/core/project_knowledge.py` | Project style/convention learning |
| `src/memory/personal_memory.py` | Persistent user preferences, error fixes |
| `src/pipeline.py` | 4-layer pipeline orchestration |
| `hooks/permission_learning_hook.py` | CLI hook for permission auto-learning |
| `.claude/skills/` | Custom skills (token-optimizer, review, git-commit, etc.) |

## Code Style

- **Python 3.11+** with type hints
- **Formatting**: `black` + `ruff` (line-length: 100)
- **Docstrings**: Google style
- **禁止自动运行测试** — User manually verifies after changes