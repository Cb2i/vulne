---
name: claude-task-master
description: Set up and drive AI-assisted project/task management using Task Master (task-master-ai, https://github.com/eyaltoledano/claude-task-master). Use this skill whenever the user wants to turn a PRD or feature description into a structured, dependency-aware task list for AI-driven development, wants to install or configure "task-master"/"taskmaster", asks to track, expand, or mark development tasks as done, or wants Task Master wired up as an MCP server for Claude Code. Trigger even if they just say "set up task tracking for this project" or "break this PRD into tasks" without naming the tool.
---

# Task Master (task-master-ai)

Task Master is an AI-driven task management CLI/MCP server for development
workflows: it turns a Product Requirements Document (PRD) into a structured,
dependency-aware task list, and lets you expand, reorder, and complete tasks
from the command line or from within Claude Code. Project:
https://github.com/eyaltoledano/claude-task-master

## When to reach for this skill

- The user wants a PRD or feature spec turned into a task breakdown.
- The user mentions "task-master", "taskmaster", or wants AI-driven task
  tracking with dependency management for a coding project.
- The user wants Task Master available as a Claude Code MCP tool rather than
  a standalone CLI.

## Setup

Task Master needs at least one AI provider API key (Anthropic, OpenAI,
Google Gemini, Perplexity, xAI, OpenRouter, or a Claude Code OAuth-based
alternative). Never hardcode a key in a file that gets committed — get it
from the user and put it in the environment or a git-ignored `.env`.

### Option A: CLI, installed in the project

```bash
npm install -g task-master-ai
task-master init
```

(Or without a global install: `npm install task-master-ai && npx task-master init`.)

`task-master init` scaffolds:

```
.taskmaster/
├── docs/
│   └── prd.txt              # your PRD goes here
├── templates/
│   └── example_prd.txt      # reference template
└── config                   # provider/model config
```

### Option B: MCP server for Claude Code

Register Task Master as an MCP server so its tools are callable directly
from a Claude Code session:

```bash
claude mcp add taskmaster-ai -- npx -y task-master-ai
```

To pin which tool subset loads and pass provider keys as env vars:

```bash
claude mcp add task-master-ai --env ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY --env TASK_MASTER_TOOLS="core" -- npx -y task-master-ai@latest
```

Other editors configure the same MCP server via a config file instead of a
CLI command — same `command`/`args`/`env` shape:

| Editor | Config file |
|---|---|
| Cursor (global) | `~/.cursor/mcp.json` |
| Cursor (project) | `<project>/.cursor/mcp.json` |
| VS Code | `<project>/.vscode/mcp.json` |
| Windsurf | `~/.codeium/windsurf/mcp_config.json` |

```json
{
  "mcpServers": {
    "task-master-ai": {
      "command": "npx",
      "args": ["-y", "task-master-ai"],
      "env": {
        "ANTHROPIC_API_KEY": "YOUR_KEY_HERE"
      }
    }
  }
}
```

## Core workflow

1. **Write or import a PRD** at `.taskmaster/docs/prd.txt` — a plain-language
   description of the feature or project (use `templates/example_prd.txt`
   as a starting shape if the user has nothing yet).
2. **Generate tasks from the PRD:**
   ```bash
   task-master parse-prd .taskmaster/docs/prd.txt
   ```
3. **Review and refine:**
   ```bash
   task-master list                 # see all tasks
   task-master expand --id <id>     # break a task into subtasks
   task-master show <id>            # inspect one task in detail
   ```
4. **Track dependencies** between tasks so work happens in the right order —
   Task Master models these explicitly rather than leaving ordering implicit
   in a flat list; use `task-master list` to confirm the dependency graph
   makes sense before starting implementation.
5. **Mark progress as you go:**
   ```bash
   task-master set-status --id <id> --status done
   ```

When Task Master is registered as an MCP server instead, the same
operations (parse a PRD, list/expand tasks, set status) are exposed as MCP
tools callable directly from the conversation — prefer that path if the
user is already working inside Claude Code and wants the loop to stay
in-session rather than shelling out to the CLI.

## Notes

- `.taskmaster/` holds project-specific state (parsed tasks, config); treat
  it like any other project file — commit it if the user wants task state
  shared with collaborators, otherwise `.gitignore` it.
- Don't invent or hardcode API keys. If none is configured yet, ask the
  user which provider they want to use and where the key should come from.
