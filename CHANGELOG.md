# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Multi-file reasoning module (`multi_file_reasoning.py`)
- Context manager with RAG support (`context_manager.py`)
- Personal memory system (`personal_memory.py`)
- Project knowledge learner (`project_knowledge.py`)
- Unified enhancement interface (`unified.py`)
- Comprehensive test suite (41 tests)
- One-line installer script
- Standard open-source templates (CONTRIBUTING, CODE_OF_CONDUCT)

### Changed

- Improved project structure
- Enhanced documentation

### Fixed

- **Permission Learning Hook** - 修复 Claude Code Notification hook 输入格式变更导致的学习失效问题
  - 新增 PreToolUse/PostToolUse 组合捕获机制
  - 通过工具执行生命周期记录权限决策
  - 成功执行 = 用户允许，自动归纳模式
  - 对高频安全模式支持自动批准

## [1.0.0] - 2026-03-29

### Added

- Initial release
- Four-layer architecture (Layer 0-3)
- Self-modification engine
- Meta-learning optimizer (MAML)
- Strategy optimizer (PPO)
- Continuous learning with EWC/MAS/GEM
- Evolution tracker
- Docker execution sandbox
- Linting tools integration
- Test frameworks integration

### Architecture

- Layer 0: Infrastructure (Docker, Linter, Tests)
- Layer 1: Perception-Action (Observer, Actor, Feedback)
- Layer 2: Cognitive (Reasoning, Transfer, Learning)
- Layer 3: Meta-Cognitive (Evolution, Adaptation)

---

## Version History

| Version | Date       | Description                              |
| ------- | ---------- | ---------------------------------------- |
| 1.0.0   | 2026-03-29 | Initial release                          |
| 1.1.0   | TBD        | Multi-file reasoning, context management |

---

[Unreleased]: https://github.com/liogogogo/claude-code-enhancement/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/liogogogo/claude-code-enhancement/releases/tag/v1.0.0
