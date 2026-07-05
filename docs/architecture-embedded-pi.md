# Embedded Pi Harness Architecture Plan

## Goal
Replace the external `omp` CLI dependency with an embedded Python AI harness ("pi" based) that natively runs `acis2llm` tools. This provides an "all-in-one" desktop experience without sacrificing orchestration capabilities, avoiding the need for users to configure external tools.

## Phase 0: Discovery & Dependency Resolution ("What is Pi?")
Before implementation, the concrete definition of the "pi" harness must be resolved. The user references "a small pi coding harness" and "an embedded version of pi", but the exact source (PyPI package, local vendor, external repository, or custom minimalist rewrite) is not yet explicitly defined in the project configuration.

*   **Action Required**:
    1.  Determine if "pi" refers to a specific PyPI package (e.g., `pi-agent`, a Google/DeepMind internal lib, or a known community tool) or a specific local CLI.
    2.  If "pi" is an external CLI, evaluate how to import its core orchestration loop as a library rather than shelling out to it.
    3.  If a library version is unavailable, plan for a "clean room" minimalist Python loop (using `litellm` + tool schemas) inspired by the behavior of the `pi` tool.
*   **Acceptance Criteria for Phase 0**: The specific Python dependency/library to be used for the agentic loop is identified, added to `pyproject.toml`, and a "hello world" tool call can be executed natively in Python without shelling out to a binary.

## Core Requirements & Architecture
1.  **Bundled Python Sidecar (Primary)**: Instead of mandating Docker (which complicates desktop distribution), the app will bundle a locked `uv` environment or standalone Python executable as a Tauri sidecar. 
    *   *Optional Container Backend*: A containerized execution path can be an advanced user toggle for stricter sandboxing later.
2.  **Embedded Pi Harness**: A stripped-down, focused agent loop in Python that handles tool routing, LLM API calls, and history management.
3.  **Strict Tauri Frontend Contracts**: The backend must maintain the exact JSON schemas and event shapes expected by `desktop/src/App.tsx`.

## Phase 1: Develop the Pi Harness CLI (The Sidecar)
Create a Python CLI that acts as a drop-in replacement for the `omp` invocation.

*   **File Location**: `desktop/backend/pi_harness.py`
*   **Input Contract**: Accept arguments like `omp`: `-p <prompt>`, `--model <model>`, `--mode json`.
*   **LLM Integration**: Use standard Python SDKs (`litellm`, `openai`, or the specific `pi` orchestrator lib defined in Phase 0) to connect to providers.
*   **Tool Binding**: Import `xmacis2py` wrappers and current tools directly (Note: `composite_tools` is obsolete in this repo; use the current tool modules).
*   **Output Contract (Streaming JSON)**: Stream `stdout` JSON lines that exactly match the current parser in `ask_omp`:
    *   `{"type": "tool_execution_start", "toolName": "...", "intent": "..."}`
    *   `{"type": "agent_end", "messages": [{"role": "assistant", "content": [{"type": "text", "text": "..."}]}]}`

## Phase 2: Tauri Backend Seams (`lib.rs`)
Update the Rust backend to target the new Python sidecar instead of the external `omp` binary.

*   **Path Resolution**: Update `get_omp_path()` to point to the bundled `pi_harness.py` (running via a local bundled `uv` binary) rather than `~/.bun/bin/omp`.
*   **Command `ask_omp`**: 
    *   Maintains the signature: `message: String, model: String, system_prompt: String, history: Vec<Message>`. (Note: Tauri maps the frontend's camelCase `systemPrompt` to `system_prompt`).
    *   Pass environment variables securely to the sidecar.
*   **Command `stop_omp`**: Ensure process termination correctly kills the sidecar process.
*   **Command `get_models`**: 
    *   The sidecar must implement a `--list-models` flag.
    *   **CRITICAL**: `App.tsx` expects the exact JSON shape: `{ "models": [{ "id": "...", "selector": "..." }] }`. The sidecar must return this.
*   **Command `generate_title`**: Update to call the sidecar for quick title generation.

## Phase 3: Tauri Frontend Validation (`App.tsx`)
Verify the frontend-backend contract remains intact. The frontend currently relies on these specific IPC hooks:

*   **Tauri Commands**: `invoke("ask_omp")`, `invoke("stop_omp")`, `invoke("get_models")`, `invoke("generate_title")`.
*   **Tauri Events**: 
    *   `listen<string>("omp-output", ...)` for text chunks.
    *   `listen<string>("omp-status", ...)` for tool execution status.
    *   `listen("omp-done", ...)` for completion.
*   *Migration Note*: If we rename these for clarity (e.g., `ask_pi`, `pi-output`), the Rust signatures in `lib.rs` and the React hooks in `App.tsx` must be updated atomically.

## Phase 4: Sidecar Packaging
*   Use Tauri's `sidecar` configuration in `tauri.conf.json` to bundle the Python environment.
*   Investigate using PyInstaller or a bundled `uv` cache to ensure the harness runs independently of the host's Python installation.