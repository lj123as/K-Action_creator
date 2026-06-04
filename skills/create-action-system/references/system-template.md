# System Template Reference

This document describes the standard template for action-layer systems in KA-Vault.

## Directory Structure

```
action/<system-name>/
├── README.md               # System documentation (required)
├── CLAUDE.md               # Agent configuration (optional, for standalone use)
├── .claude/                # Claude Code integration
│   └── settings.json       # Claude settings
│
├── skills/                 # Knowledge Pack (Skill) layer
│   └── <skill-name>/
│       ├── SKILL.md        # Skill definition (required)
│       ├── scripts/        # Executable scripts
│       ├── references/     # Reference documentation
│       └── assets/         # Static assets
│
├── tools/                  # Atomic Executor (Tool) layer
│   ├── <tool-name>.py      # Python scripts (preferred)
│   └── ...
│
├── workflows/              # Flow Orchestrator (Workflow) layer
│   ├── <workflow>.yaml     # Workflow definitions
│   └── ...
│
├── hooks/                  # Event Handler (Hook) layer
│   ├── pre_tool_call.py    # Before tool execution
│   ├── post_tool_call.py   # After tool execution
│   └── ...
│
├── config/                 # Configuration files
│   └── settings.yaml       # System-wide settings
│
└── mcp/                    # Connector (MCP) layer (optional)
    └── server.json         # MCP server configuration
```

## Component Mapping to Agentic Software Paradigm

| Directory | Agentic Element | Purpose |
|-----------|-----------------|---------|
| `skills/` | Knowledge Pack | Modular capabilities with embedded knowledge |
| `tools/` | Atomic Executor | Deterministic, atomic operations |
| `workflows/` | Flow Orchestrator | Process orchestration, state management |
| `hooks/` | Event Handler | Lifecycle management, cross-cutting concerns |
| `mcp/` | Connector | External system integration |
| `CLAUDE.md` | Decision Unit | Agent configuration (when standalone) |

## Required Files

### README.md

Every system must have a README with:

```markdown
# System Name

> One-line description

## Overview

What this system does and why it exists.

## Components

List of skills, tools, and workflows.

## Usage

How to use the system.

## Related

Links to related documentation.
```

### skills/<name>/SKILL.md

Every skill must have a SKILL.md with:

```yaml
---
name: skill-name
description: When and why to use this skill
---
```

## Optional Files

### CLAUDE.md

For systems that operate as standalone Claude Code projects:

```markdown
# Project Instructions

## Context
What this project is about.

## Commands
Available commands and their usage.

## Conventions
Coding standards and conventions.
```

### .claude/settings.json

```json
{
  "projectRoot": ".",
  "skills": {
    "path": "skills"
  },
  "hooks": {
    "preToolCall": "hooks/pre_tool_call.py"
  }
}
```

## Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| System | lowercase-hyphen | `knowledge-network` |
| Skill | lowercase-hyphen | `create-atomic-note` |
| Tool | snake_case.py | `parse_frontmatter.py` |
| Workflow | snake_case.yaml | `note_creation_flow.yaml` |
| Hook | snake_case.py | `pre_tool_call.py` |

## System Lifecycle

### Creation

1. Define requirements
2. Create GitHub repo (private)
3. Add as submodule
4. Generate structure via RCSF
5. Implement components
6. Register in RCSF Registry

### Maintenance

1. Update components as needed
2. Run verification: `python action/RCSF/Core/verifier.py --system action/<name>`
3. Commit changes in submodule
4. Update parent repo submodule reference

### Deprecation

1. Update status in Registry to "deprecated"
2. Add deprecation notice to README
3. (Optional) Archive or remove submodule

## Integration with RCSF

### Generator Commands

```bash
# Generate skill
python action/RCSF/Core/generator/skill_gen.py \
  --name "my-skill" \
  --description "Skill description" \
  --output "action/<system>/skills/my-skill"

# Generate tool
python action/RCSF/Core/generator/tool_gen.py \
  --name "my_tool" \
  --description "Tool description" \
  --params '["param1", "param2"]' \
  --output "action/<system>/tools"

# Generate workflow
python action/RCSF/Core/generator/workflow_gen.py \
  --name "my_workflow" \
  --description "Workflow description" \
  --steps '["step1", "step2"]' \
  --output "action/<system>/workflows"
```

### Verification

```bash
# Full verification
python action/RCSF/Core/verifier.py --system action/<system-name>

# Quick check
python action/RCSF/Core/verifier.py --system action/<system-name> --quick
```

## Examples

### Minimal System

```
action/my-system/
├── README.md
└── skills/
    └── my-skill/
        └── SKILL.md
```

### Full System

```
action/knowledge-network/
├── README.md
├── CLAUDE.md
├── .claude/
│   └── settings.json
├── skills/
│   ├── create-atomic-note/
│   │   ├── SKILL.md
│   │   └── scripts/
│   ├── knowledge-network/
│   │   └── SKILL.md
│   └── analyze-and-restructure/
│       └── SKILL.md
├── tools/
│   ├── parse_frontmatter.py
│   └── validate_links.py
├── workflows/
│   └── note_creation.yaml
├── hooks/
│   └── post_create_note.py
└── config/
    └── settings.yaml
```
