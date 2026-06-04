---
name: create-action-system
description: This skill guides the creation of new action-layer systems in the KA-Vault. It covers the complete workflow from GitHub repository setup, submodule integration, to RCSF-based system implementation. Use this skill when creating new automation systems (like knowledge-network, product-development) in the action layer.
license: MIT
---

# Create Action System

This skill provides a complete workflow for creating new systems in the action layer of KA-Vault, following the RCSF (Recursive Capability Synthesis Framework) architecture.

## Overview

Every new system in `action/` follows this standard process:

```
1. GitHub Setup     →  Create private repository
2. Submodule Setup  →  Add to action/ as git submodule
3. RCSF Build       →  Generate system components using RCSF
4. Verification     →  Validate system completeness
```

## Prerequisites

- Git configured with GitHub authentication (SSH or HTTPS token)
- Access to RCSF Core at `action/RCSF/Core/`
- Write access to the KA-Vault repository

## Workflow

### Step 1: Define System Requirements

Before creating anything, clarify:

1. **System Name**: Short, lowercase, hyphen-separated (e.g., `knowledge-network`, `product-dev`)
2. **Purpose**: One sentence describing what the system manages
3. **Core Capabilities**: List of 3-5 main functions
4. **Components Needed**: Which of the six elements are required
   - [ ] Agents (Decision Unit)
   - [ ] Workflows (Flow Orchestrator)
   - [ ] Skills (Knowledge Pack)
   - [ ] Tools (Atomic Executor)
   - [ ] Hooks (Event Handler)
   - [ ] MCP (Connector)

### Step 2: Create GitHub Repository

Execute the following to create a private GitHub repository:

```bash
# Create new private repository
gh repo create <org-or-user>/<system-name> --private --description "<system description>"

# Example:
gh repo create huya/ka-knowledge-network --private --description "Knowledge network management system for KA-Vault"
```

**Naming Convention**: Prefix with `ka-` for KA-Vault systems (e.g., `ka-knowledge-network`, `ka-product-dev`)

### Step 3: Add as Git Submodule

Add the new repository as a submodule under `action/`:

```bash
# Navigate to vault root
cd <vault-root>

# Add submodule
git submodule add git@github.com:<org-or-user>/<system-name>.git action/<system-name>

# Initialize submodule
git submodule update --init --recursive

# Commit the submodule addition
git add .gitmodules action/<system-name>
git commit -m "Add <system-name> system as submodule"
```

### Step 4: Initialize System Structure

Use RCSF to generate the system skeleton:

```bash
# Option A: Use RCSF designer (if available)
python action/RCSF/Core/designer.py --name <system-name> --template base-system

# Option B: Manual initialization
cd action/<system-name>
mkdir -p skills tools workflows hooks config
```

Create the standard directory structure:

```
action/<system-name>/
├── README.md           ← System documentation
├── CLAUDE.md           ← Agent configuration (if standalone)
├── skills/             ← Skill definitions
│   └── <skill-name>/
│       └── SKILL.md
├── tools/              ← Python scripts
├── workflows/          ← Workflow definitions
├── hooks/              ← Event handlers
├── config/             ← Configuration files
└── .claude/            ← Claude Code integration (optional)
    └── settings.json
```

### Step 5: Implement Components Using RCSF

Generate components based on requirements:

#### Generate Skills

```bash
python action/RCSF/Core/generator/skill_gen.py \
  --name "<skill-name>" \
  --description "<description>" \
  --output "action/<system-name>/skills/<skill-name>"
```

#### Generate Tools

```bash
python action/RCSF/Core/generator/tool_gen.py \
  --name "<tool-name>" \
  --description "<description>" \
  --output "action/<system-name>/tools"
```

#### Generate Workflows

```bash
python action/RCSF/Core/generator/workflow_gen.py \
  --name "<workflow-name>" \
  --description "<description>" \
  --output "action/<system-name>/workflows"
```

### Step 6: Configure Claude Integration

If the system needs standalone Claude Code support, create `.claude/settings.json`:

```json
{
  "projectRoot": ".",
  "hooks": {
    "preToolCall": "hooks/pre_tool_call.py",
    "postToolCall": "hooks/post_tool_call.py"
  }
}
```

### Step 7: Register System

Register the new system in RCSF Registry:

```bash
python action/RCSF/Core/verifier.py --system action/<system-name> --register
```

Or manually update `action/RCSF/Registry/systems.json`:

```json
{
  "systems": [
    {
      "name": "<system-name>",
      "path": "action/<system-name>",
      "created": "YYYY-MM-DD",
      "status": "active",
      "components": ["skills", "tools", "workflows"]
    }
  ]
}
```

### Step 8: Verification Checklist

Before considering the system complete, verify:

- [ ] README.md exists with clear documentation
- [ ] At least one skill is implemented
- [ ] All skills have valid SKILL.md with frontmatter
- [ ] Tools are executable and have docstrings
- [ ] System is registered in RCSF Registry
- [ ] Git submodule is properly committed

## Quick Reference Commands

```bash
# Create repo + submodule (one-liner)
gh repo create <org>/<name> --private && git submodule add git@github.com:<org>/<name>.git action/<name>

# Verify system
python action/RCSF/Core/verifier.py --system action/<name>

# List all action systems
ls -la action/ | grep -E "^d"

# Update all submodules
git submodule update --remote --merge
```

## System Templates

Reference templates are available at:
- `action/RCSF/Templates/base-system/` - Minimal starter template
- `action/RCSF/Templates/kn-system/` - Knowledge network template

See `references/system-template.md` for detailed template documentation.

## Troubleshooting

### Submodule Issues

```bash
# Reset submodule to remote state
git submodule update --init --force action/<system-name>

# Remove and re-add submodule
git rm action/<system-name>
rm -rf .git/modules/action/<system-name>
git submodule add <repo-url> action/<system-name>
```

### GitHub Authentication

```bash
# Check GitHub CLI auth status
gh auth status

# Re-authenticate
gh auth login
```

## Related Resources

- [[action/RCSF/README.md]] - RCSF Meta-system documentation
- [[cognition/agentic-software/README]] - Agentic Software Paradigm
- [[cognition/RCSF/rules.md]] - RCSF Design Principles
