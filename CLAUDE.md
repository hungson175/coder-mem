# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a Python-based coding agent that replicates Claude Code functionality using LangChain with support for multiple LLM providers (Grok, Claude/Anthropic, DeepSeek). The project demonstrates reverse engineering of Claude Code through API interception and reimplementation of essential coding tools.

## Development Commands

### Environment Setup
```bash
# Install dependencies
uv sync

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys:
# - XAI_API_KEY for Grok/xAI (REQUIRED - default provider)
# - ANTHROPIC_API_KEY for Claude/Anthropic (optional)
# - DEEPSEEK_API_KEY for DeepSeek (optional)
# - LANGSMITH_* keys for tracing (optional)
```

### Running the Agent

#### Using the Global Launcher (Recommended)
```bash
# Run in current directory (uses Grok by default)
coder-mem

# Run in specific directory
coder-mem /path/to/project

# Show help
coder-mem --help

# To switch LLM providers, use the /model command inside the tool
```

#### Direct Python Execution
```bash
# Primary way to run
uv run python main.py

# Alternative with activated venv
source .venv/bin/activate
python main.py
```

### Code Quality
```bash
# Format code
uv run black .

# Lint code
uv run ruff check .
uv run ruff check . --fix  # Auto-fix issues

# Run tests (if any exist)
uv run pytest
```

## Architecture

### Core Components

**main.py** - Entry point with rich CLI using prompt_toolkit for command autocomplete

**coding_agent/** - Modular package structure:
- `core/` - BaseAgent, CodingAgent, LLM provider abstraction, agent registry, dynamic agent loader
- `tools/` - Tool implementations (Read, Write, Edit, LS, Glob, Grep, Bash, BashOutput, TodoWrite, Task)
- `commands/` - Native commands (/init, /model, /memory) and custom command management
- `utils/` - Context loading (CLAUDE.md, memory files), keyboard interrupt handling, git utilities
- `ui/` - Rich CLI components including diff display

### Key Design Patterns

**Tool Architecture**: Each tool is a `@tool` decorated function where the docstring serves dual purpose as documentation AND prompt engineering for the LLM. These descriptions are carefully crafted prompts - modify only to fix bugs, not for style.

**Code Style**:
- **NO EMOJIS** in code, output, or documentation unless explicitly requested by user
- Use clean text markers like [DEBUG], [ERROR], [INFO] instead

**Dynamic Agent System**:
- `AgentRegistry` (singleton) discovers agents from `~/.claude/agents/*.md` at runtime
- User-defined agents extend `DynamicAgent` which inherits from `BaseAgent`
- `AgentConfigParser` parses markdown files with YAML frontmatter to define custom agents
- Built-in "general-purpose" agent available by default
- Task tool dynamically generates its description from all registered agents

**LLM Provider System**:
- Abstract `LLMProvider` base class with concrete implementations: `ClaudeProvider`, `DeepSeekProvider`, `GrokProvider`
- Provider-specific caching: Anthropic uses manual cache control (`cache_control: ephemeral`), others use auto-caching
- Model switching at runtime via `/model` command preserves conversation history
- Token usage reporting tailored per provider

**Context Loading System**:
- `load_memory_context()` loads CLAUDE.md and memory files into system prompt
- Memory context is cached and injected as HumanMessage after system prompt
- Working directory context updated when `cd` command changes directory

**Background Process Management**: `BackgroundShellManager` manages long-running bash processes with graceful cancellation (Esc/Ctrl+C) and output streaming via `BashOutput` tool.

## Dependencies

### Required External Tools
- **ripgrep (rg)**: Essential for Grep tool functionality. Install via:
  - macOS: `brew install ripgrep`
  - Ubuntu/Debian: `sudo apt install ripgrep`
  - Windows: `winget install BurntSushi.ripgrep.MSVC`

### Python Dependencies
- `langchain-anthropic`: Core LLM integration for Claude
- `langchain-openai`: DeepSeek provider support
- `langchain-xai`: Grok provider support
- `langchain-core`: Tool and message abstractions
- `prompt_toolkit`: Rich CLI with autocomplete
- `rich`: Terminal UI components
- `python-dotenv`: Environment variable management
- `colorama`: Terminal color output

## Environment Variables

Required:
- `XAI_API_KEY`: Get from https://console.x.ai/ (for Grok provider - **REQUIRED**, default)

Optional (for alternative providers):
- `ANTHROPIC_API_KEY`: Get from https://console.anthropic.com/ (for Claude provider)
- `DEEPSEEK_API_KEY`: Get from https://platform.deepseek.com/ (for DeepSeek provider)

Optional:
- `LANGSMITH_TRACING=true`
- `LANGSMITH_API_KEY`: Get from https://smith.langchain.com/
- `LANGSMITH_PROJECT`: Your project name

## Interactive Commands

Within the agent CLI:
- `quit`/`exit`: Exit the agent
- `reset`: Reset conversation history
- `pwd`: Show current working directory
- `cd <path>`: Change working directory
- `/init`: Analyze codebase and create/update CLAUDE.md (native command)
- `/commands`: List all available native and custom commands
- `/memory`: View current memory context
- `/model`: Switch LLM provider or show current model info
- `/context`: Show context usage visualization
- `Ctrl+C` or `Esc`: Cancel long-running tool execution

### Autocomplete Feature
- Type `/` at the beginning to see command suggestions
- Suggestions appear automatically as gray inline text
- Press TAB to show popup menu with all completions

### LLM Provider Management

The agent supports multiple LLM providers that can be switched dynamically:

#### Available Providers
- **Claude/Anthropic** (aliases: `claude`, `sonnet`)
  - Requires `ANTHROPIC_API_KEY`
  - Model: `claude-sonnet-4-20250514`
  - Features: Manual cache control, optimized token usage
- **DeepSeek** (aliases: `deepseek`, `ds`)
  - Requires `DEEPSEEK_API_KEY`
  - Model: `deepseek-chat`
  - Features: Auto-cache management, cost-effective
- **Grok/xAI** (aliases: `grok`, `xai`) **[DEFAULT]**
  - Requires `XAI_API_KEY`
  - Model: `grok-4-fast-reasoning`
  - Features: Auto-cache management, fast inference

#### Using the `/model` Command
```bash
# Show current model and available providers
/model

# Switch providers
/model claude
/model deepseek
/model grok
```

## Creating Custom Agents

Users can define custom agents in `~/.claude/agents/` using markdown files with YAML frontmatter:

```markdown
---
agentType: my-custom-agent
whenToUse: Description of when to use this agent (shown in Task tool)
tools:
  - Read
  - Write
  - Bash
model: grok-4-fast-reasoning  # Optional, defaults to Config.MODEL_NAME
---

# System Prompt

Your custom system prompt here...
```

The agent becomes available immediately for use with the Task tool. The `AgentRegistry` automatically discovers and loads all agent definitions at startup.

## Memory System

Automatic memory system stores learnings in `~/.coder-mem-memory/` (lazy initialization on first use).

**Triggers**: TodoWrite >5 steps, OR user frustration (profanity, "stupid", "garbage", "wtf", "not listening") = critical learning signals for storing failure patterns.

## Reverse Engineering Documentation

The `docs/` directory contains extracted Claude Code system prompts and tool descriptions from API interception using Proxyman. The `data/` directory contains sample API requests/responses. These serve as reference for maintaining fidelity to original Claude Code behavior.

## Example Projects

The `example_projects/` directory contains generated projects (caro game, expense trackers) that demonstrate the agent's capabilities. These are excluded from git via `.gitignore`.