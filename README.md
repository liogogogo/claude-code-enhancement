# Claude Code Enhancement

> Make Claude Code **remember you**, **understand your project**, **never repeat mistakes**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://img.shields.io/badge/tests-48%20passing-brightgreen.svg)](tests/)

[中文文档](README.zh.md) | English

---

## 🎯 Who Is This For?

### ✅ Perfect for you if:

| Scenario                           | Pain Point                            | We Solve                                |
| ---------------------------------- | ------------------------------------- | --------------------------------------- |
| **Daily Claude Code user**         | Re-explain project context every time | ✅ Auto-learn project knowledge         |
| **Frequent project switching**     | Manual config for each project        | ✅ One-click switch + persistent memory |
| **Fixed bugs reappear**            | Claude makes same mistakes again      | ✅ Error knowledge base                 |
| **Fear of breaking other modules** | Unknown impact of changes             | ✅ Multi-file reasoning                 |
| **Long conversation context loss** | Claude forgets earlier context        | ✅ Smart context management             |
| **Annoying permission prompts**    | Confirm every single command          | ✅ 28+ commands auto-allowed            |

### ❌ May NOT be for you if:

- You use Claude Code occasionally
- Your project is very simple (single-file scripts)
- You don't want additional dependencies

---

## 🆕 What's New in v2.1

### CLI Enhancement Tools

| Feature | Description | Docs |
|---------|-------------|------|
| **Permission Learning Hook** | Smart permission learning, auto-induct patterns | [Guide](docs/PERMISSION_HOOK_GUIDE.md) |
| **MCP Integration** | Work with official MCP servers | [Guide](docs/MCP_INTEGRATION_GUIDE.md) |
| **Settings Templates** | Project-level config templates (Python/Go/General) | [Guide](docs/SETTINGS_TEMPLATES.md) |

---

## 🚀 Quick Start (5 Minutes)

### Option 1: One-Line Install (Recommended)

```bash
# Install enhancement config
curl -fsSL https://raw.githubusercontent.com/liogogogo/claude-code-enhancement/main/config/install.sh | bash

# Apply changes
source ~/.zshrc  # or ~/.bashrc

# Use it
cc  # Instead of 'claude', skips permission prompts
```

**Immediately get**:

- ✅ 28+ common commands auto-allowed
- ✅ Auto code formatting
- ✅ Dangerous command blocking
- ✅ Task completion sound

### Option 2: Full Install (Advanced Features)

```bash
git clone https://github.com/liogogogo/claude-code-enhancement.git
cd claude-code-enhancement
pip install -e .

# Optional: vector search dependencies
pip install chromadb sentence-transformers
```

### CLI Enhancement Tools (v2.1+)

**Permission Learning Hook**:

```bash
# View permission learning report
python3 hooks/permission_report.py

# View suggestions only
python3 hooks/permission_report.py --suggest
```

**Apply Config Template**:

```bash
# Apply Python project template
mkdir -p .claude
cp templates/settings.python.json .claude/settings.json
```

---

## 📋 Feature Comparison

| Feature                    | Vanilla Claude Code    | + This Project               |
| -------------------------- | ---------------------- | ---------------------------- |
| Remember preferences       | ❌ Resets each time    | ✅ Cross-session persistence |
| Remember project structure | ❌ Need re-explanation | ✅ Auto-learn                |
| Don't repeat errors        | ❌ Makes same mistakes | ✅ Error knowledge base      |
| Change impact analysis     | ⚠️ Limited             | ✅ Multi-file reasoning      |
| Long conversation handling | ⚠️ Forgets context     | ✅ Smart compression         |
| Command permissions        | ⚠️ Prompt every time   | ✅ Auto-allow                |

---

## 💡 Use Cases

### Use Case 1: Large Project Development

```python
from src.core import create_enhancer

enhancer = create_enhancer("/path/to/large-project")

# 1. Auto-learn project structure
stats = enhancer.learn_project()
# {files_analyzed: 156, patterns_found: 23, ...}

# 2. Smart code search
results = enhancer.search_code("authentication flow", n_results=10)

# 3. Analyze change impact
impacts = enhancer.analyze_change("auth/login.ts", "add MFA")
for impact in impacts:
    print(f"{impact.file_path}: {impact.impact_level.value}")
# middleware/auth.ts: high
# tests/auth.test.ts: high
# api/user.ts: medium
```

### Use Case 2: Multi-Project Switching

```python
from src.memory import get_memory

memory = get_memory()

# Project A preferences
memory.set_preference("coding_style", "indentation", "2 spaces")
memory.set_preference("tools", "formatter", "prettier")

# Project B preferences (auto-switch)
memory.set_preference("coding_style", "indentation", "4 spaces")
memory.set_preference("tools", "formatter", "black")

# Claude remembers each project's preferences
```

### Use Case 3: Error Fix Knowledge Accumulation

```python
# First encounter
memory.record_error_fix(
    error_pattern="ModuleNotFoundError: No module named 'requests'",
    error_type="ImportError",
    fix_description="Install the missing package",
    fix_code="pip install requests",
)

# Next time similar error occurs
fixes = memory.find_fix_for_error("ModuleNotFoundError: requests")
# Returns previous fix, Claude doesn't need to guess again
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   User Layer                        │
│   cc command | Claude Code CLI | API calls          │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│           Enhancement Layer (This Project)          │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  Context    │  │ Multi-File  │  │  Personal   │ │
│  │  Manager    │  │  Reasoning  │  │   Memory    │ │
│  │   (RAG)     │  │(Dependency) │  │(Persistent) │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │  Project    │  │   Error     │  │  Workflow   │ │
│  │  Knowledge  │  │  Learning   │  │  Templates  │ │
│  │ (Auto-learn)│  │(No-repeat)  │  │(Automation) │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
└─────────────────────────────────────────────────────┘
```

---

## 📊 Project Maturity

| Aspect            | Status            | Notes                                    |
| ----------------- | ----------------- | ---------------------------------------- |
| **Core Features** | ⚠️ 8 modules     | Architecture complete, implementation partial |
| **Test Coverage** | ⚠️ 4 test files  | Core modules partially covered           |
| **CI/CD**         | ✅ GitHub Actions | Auto test + build                        |
| **Documentation** | ✅ Complete       | API + Quick Start + Architecture         |
| **Open Source**   | ✅ 100%           | LICENSE, CONTRIBUTING, CoC               |

---

## 🔧 Module Implementation Status

| Module | Status | Description |
|--------|--------|-------------|
| **CLI Hooks** | ✅ Production Ready | Permission learning hook fully functional |
| **Personal Memory** | ✅ Usable | Data structures and API complete |
| **Context Manager** | ⚠️ Partial | RAG framework done, vector search needs deps |
| **Project Knowledge** | ⚠️ Partial | Analysis framework ready, learning TBD |
| **Multi-File Reasoning** | 📋 Planned | Architecture designed |
| **Layer 0-3 Pipeline** | 📋 Planned | Data flow not yet connected |

See [Closure Roadmap](docs/CLOSURE_ROADMAP.md) for implementation plan.

---

## 📁 Project Structure

```
claude-code-enhancement/
├── config/                 # One-click install config
│   ├── install.sh
│   └── settings.template.json
├── hooks/                  # CLI Hooks (v2.1+)
│   ├── hooks.json
│   ├── permission_learning_hook.py
│   └── permission_report.py
├── templates/              # Config templates (v2.1+)
│   ├── settings.minimal.json
│   ├── settings.python.json
│   ├── settings.go.json
│   └── settings.local.json
├── src/
│   ├── core/               # Core modules
│   │   ├── context_manager.py      # Context management
│   │   ├── multi_file_reasoning.py # Multi-file reasoning
│   │   ├── project_knowledge.py    # Project knowledge
│   │   └── unified.py              # Unified interface
│   ├── memory/             # Memory system
│   │   └── personal_memory.py
│   └── layer0-3/           # 4-layer architecture
├── tests/                  # Tests (41)
├── docs/                   # Documentation
└── Makefile               # Common commands
```

---

## 📖 Documentation

| Doc                                     | Content           |
| --------------------------------------- | ----------------- |
| [Quick Start](docs/QUICK_START.md)      | 5-minute guide    |
| [API Reference](docs/API.md)            | Full API docs     |
| [Architecture](docs/ARCHITECTURE_V2.md) | 4-layer design    |
| [Permission Hook](docs/PERMISSION_HOOK_GUIDE.md) | Permission learning |
| [MCP Integration](docs/MCP_INTEGRATION_GUIDE.md) | MCP servers |
| [Settings Templates](docs/SETTINGS_TEMPLATES.md) | Config templates |
| [Contributing](CONTRIBUTING.md)         | How to contribute |

---

## 🔧 Common Commands

```bash
make install     # Install dependencies
make test        # Run tests
make test-cov    # Tests with coverage
make lint        # Code linting
make format      # Format code
make build       # Build package
```

---

## 🤝 Contributing

Contributions welcome! See [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📄 License

[MIT License](LICENSE)

---

## ❓ FAQ

### Q: Does this conflict with vanilla Claude Code?

**A**: No. This is an enhancement layer, can be enabled/disabled anytime.

### Q: Any extra cost?

**A**: No. This project is free and open source, uses your Claude API.

### Q: Which languages are supported?

**A**: Code analysis for Python, TypeScript, JavaScript, Go, Rust.

### Q: Where is my data stored?

**A**: Locally in `~/.claude/` directory, never uploaded to any server.

### Q: Can I use this without Claude Code?

**A**: Yes! The core modules (context manager, multi-file reasoner, memory) work standalone.

---

## 🗺️ Roadmap

| Version | Features                               |
| ------- | -------------------------------------- |
| v1.0 ✅ | Core modules, config enhancement       |
| v2.0 ✅ | 4-layer architecture, self-evolution   |
| v2.1 ✅ | Permission learning, MCP integration, templates |
| v2.2 🚧 | LSP integration, better type inference |
| v2.3 📋 | IDE plugins (VS Code, JetBrains)       |

---

**GitHub**: https://github.com/liogogogo/claude-code-enhancement

**Make Claude Code understand you better** 🚀