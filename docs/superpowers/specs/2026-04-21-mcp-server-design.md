# MCP Server for acis2LLM — Design Spec

## Overview

Add an MCP (Model Context Protocol) server to acis2LLM so that any MCP-compatible client (Claude Code, Claude Desktop, Cursor, Windsurf, VS Code Copilot, etc.) can use the weather/climate tools natively. The server runs locally on the user's machine as a stdio subprocess — no hosted infrastructure.

## Decisions

- **Same repo** — MCP server lives alongside the existing CLI
- **One package, two entry points** — `acis2llm` (CLI) and `acis2llm-mcp` (MCP server), both from the same PyPI package
- **All 26+ tools exposed individually** — no consolidation
- **Thin wrapper over execute_tool_call** — no new execution logic, no refactoring

## Architecture

```
MCP Client (Claude Code, Cursor, etc.)
    │
    │  stdio (stdin/stdout)
    │
    ▼
mcp_server.py  ←  new file (~100-150 lines)
    │
    │  calls execute_tool_call(name, args)
    │
    ▼
execution.py  (existing, unchanged)
    │
    ├──► xmacis2py (get_data, analysis functions)
    └──► composite_tools.py (monthly_totals, seasonal, frequency, find_best_station)
    │
    ▼
formatter.py  (existing, unchanged)
    │
    ▼
TextContent response back to MCP client
```

## New File: `mcp_server.py`

### Responsibilities

1. Create an MCP `Server` instance (name: `"acis2llm"`)
2. Convert `TOOL_DEFINITIONS` from `tools.py` (OpenAI function-calling format) into MCP tool registrations
3. Handle `list_tools` — return all tools with their schemas
4. Handle `call_tool` — validate the tool name, delegate to `execute_tool_call(name, args)`, return result as `TextContent`
5. Run via stdio transport (`mcp.server.stdio`)

### Schema Conversion

OpenAI format (current):
```json
{
  "type": "function",
  "function": {
    "name": "period_mean",
    "description": "Calculate the mean...",
    "parameters": {
      "type": "object",
      "properties": { ... },
      "required": [ ... ]
    }
  }
}
```

MCP format (target):
```json
{
  "name": "period_mean",
  "description": "Calculate the mean...",
  "inputSchema": {
    "type": "object",
    "properties": { ... },
    "required": [ ... ]
  }
}
```

The conversion is a trivial field rename — extract `function.name`, `function.description`, and `function.parameters` → `inputSchema`.

### Error Handling

- If `execute_tool_call` returns a string starting with `"ERROR:"`, set `is_error=True` on the MCP response
- All exceptions caught and returned as error text (same pattern as existing CLI)

## Changes to `pyproject.toml`

### New dependency

```toml
dependencies = [
    ...existing...,
    "mcp>=1.0",
]
```

### New entry point

```toml
[project.scripts]
acis2llm = "main:main"
acis2llm-mcp = "mcp_server:main"
```

### New module in setuptools

```toml
[tool.setuptools]
py-modules = [
    ...existing...,
    "mcp_server",
]
```

## User Installation

### Claude Code
```bash
claude mcp add acis2llm -- uvx acis2llm
```
This tells Claude Code to launch the MCP server via `uvx`, which auto-installs the package and runs the `acis2llm-mcp` entry point.

Note: Need to verify the exact `uvx` invocation — it may need to be:
```bash
claude mcp add acis2llm -- uvx --from acis2llm acis2llm-mcp
```

### Claude Desktop (settings JSON)
```json
{
  "mcpServers": {
    "acis2llm": {
      "command": "uvx",
      "args": ["--from", "acis2llm", "acis2llm-mcp"]
    }
  }
}
```

### Local development
```bash
claude mcp add acis2llm -- uv run mcp_server.py
```

## README Updates

Add an "MCP Server" section to README.md documenting:
- What MCP is (one sentence)
- Installation commands for Claude Code, Claude Desktop, and generic MCP clients
- Note that the ACIS API is public/free — no API keys needed on the user's end

## What Does NOT Change

- `execution.py` — untouched
- `composite_tools.py` — untouched
- `formatter.py` — untouched
- `tools.py` — untouched (read-only, used as the schema source)
- `cli.py` / `main.py` — untouched
- `config.py` / `acis2llm_setup.py` — not needed by MCP server (no LLM config needed since the host client provides the LLM)
- `system_prompt.py` — not needed by MCP server

## Testing

- Manual test: run `uv run mcp_server.py` and verify it starts and accepts stdio
- Use `mcp dev` or Claude Code's MCP inspector to verify tools are listed correctly
- Test one tool call end-to-end (e.g., `find_best_station` with `{"location": "Denver"}`)
- Verify error handling by calling a tool with missing required args
