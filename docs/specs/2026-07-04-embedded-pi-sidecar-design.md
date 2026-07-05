# Embedded pi Sidecar — Design

**Date:** 2026-07-04
**Branch:** `experiment/embedded-pi-harness`
**Status:** Approved direction — supersedes the "clean-room Python litellm harness" approach in `docs/architecture-embedded-pi.md` and the `desktop/backend/pi_harness.py` prototype (both to be removed/rewritten).

## Goal

Embed the real **upstream pi** coding agent (`@mariozechner/pi-coding-agent`, pi.dev) inside the Tauri desktop app, replacing the external `omp` CLI dependency. Users install nothing: no bun, no omp, no Python. The agent answers historical-weather questions by running Python (`xmacis2py` + `acis2llm`) through pi's `bash` tool and the bundled `acis-weather` skill, sandboxed via macOS Seatbelt.

Key insight making this cheap: `omp` **is** a pi fork, so the JSON event protocol the React frontend and `lib.rs` already parse (`tool_execution_start`, `agent_end`) is pi's native event stream. No contract translation is needed.

## Components

### 1. Sidecar — `desktop/sidecar/` (new, TypeScript on bun)

A thin CLI entry over pi's embedding SDK.

- **CLI contract** (drop-in for today's omp invocation):
  - `-p <prompt> --model <selector> --mode json` — one-shot agent run, JSON events on stdout.
  - `-p <prompt> --model <selector>` (no `--mode json`) — plain text on stdout (used by `generate_title`; runs with **no tools**).
  - `--list-models` — prints `{"models":[{"id":"...","selector":"...","name":"...","provider":"..."}]}`, from pi's `ModelRegistry`, filtered to providers that have an API key available.
- **Session setup:** `createAgentSession()` with:
  - `SessionManager.inMemory()` — conversation history continues to be replayed inside the prompt by `lib.rs` (unchanged).
  - Tools: `read` + `bash` only. Bash execution is wrapped in the Seatbelt sandbox (below).
  - System prompt override passed through from the app.
  - The bundled `acis-weather` skill registered via pi's resource loader.
- **Event output:** `session.subscribe()` forwards pi events as JSON lines. `lib.rs` consumes `tool_execution_start` and `agent_end`; other events are harmless passthrough.
- **Working directory:** a dedicated agent workspace under app data (`~/Library/Application Support/<app>/workspace/`).
- **Packaging:** `bun build --compile` → single self-contained binary per arch (e.g. `pi-sidecar-aarch64-apple-darwin`), declared as a Tauri `externalBin` sidecar. Dev mode runs `bun run` against the TS source.

### 2. Sandbox — Seatbelt (`sandbox-exec`)

Every bash-tool command runs under `sandbox-exec` with a bundled profile:

- **Write access:** agent workspace + uv cache/python dirs only.
- **Read access:** system, bundled resources, uv toolchain.
- **Network:** allowed (required for `data.rcc-acis.org`, `geocoding.geo.census.gov`, `api.zippopotam.us`, and uv package downloads).
- Implemented by replacing pi's built-in `bash` tool with a custom tool (same name/description/schema, via `customTools`) whose executor prefixes commands with `sandbox-exec -f <profile>`, so the boundary is kernel-enforced regardless of what the model writes.
- Trust model: the untrusted actor is model-generated code; inputs are user weather questions. Container-based isolation (Docker/OrbStack) stays a possible later opt-in, not in scope.

### 3. Python runtime — bundled `uv`

- Static `uv` binary shipped as a Tauri resource; sidecar prepends it to the bash tool's PATH.
- `UV_CACHE_DIR` and `UV_PYTHON_INSTALL_DIR` pointed at app-data, so the first query bootstraps a managed Python + `xmacis2py`/`acis2llm` without touching the user's system. Subsequent queries hit the cache.
- `skills/acis-weather/` bundled as a resource and registered with pi.

### 4. Rust seam — `desktop/src-tauri/src/lib.rs` (small changes)

- `get_omp_path()` → resolve the sidecar: Tauri sidecar path in production, `desktop/sidecar` dev invocation otherwise.
- Spawn-per-request lifecycle, `stop_omp` kill semantics, stdout JSON parsing, and the `omp-output` / `omp-status` / `omp-done` events all stay as-is.
- IPC/command names keep their `omp` naming for now; renaming to `pi` is a separate cosmetic pass done atomically across `lib.rs` + `App.tsx` later.
- Env plumbing: API keys injected as env vars (`ANTHROPIC_API_KEY`, etc.) into the sidecar process per spawn. Keys never appear in logs or CLI args.

### 5. API keys — Keychain-backed settings

- New settings section in the frontend for provider API keys (Anthropic, OpenAI, others pi supports as needed).
- Stored in the **macOS Keychain** via the `keyring` crate; Tauri commands `set_api_key(provider, key)` / `get_api_key_status(provider)` (status only — the key itself is never sent back to the frontend beyond a masked indicator).
- Fallback: if pi's own auth store (`~/.pi`) or ambient env vars exist, they still work — bundled keys take precedence.

## Removals

- `desktop/backend/pi_harness.py` — deleted.
- `docs/architecture-embedded-pi.md` — rewritten to reflect this design (or replaced by a pointer to this spec).
- `todo.txt` at repo root — superseded by the implementation plan.

## Error handling

- Sidecar exits non-zero with a clear stderr message for: missing API key for selected model, unknown model selector, network failure. `classify_omp_error()` in `lib.rs` gets its patterns checked against pi's actual error strings (drop the omp-specific wording like "Configure it in omp").
- Sandbox denials surface as tool errors to the model (it can retry within policy), not silent failures.

## Testing

- **Sidecar unit tests (bun test):** CLI arg parsing, `--list-models` shape, event-to-stdout forwarding with a mocked session, no-tools text mode.
- **Sandbox test:** a bash command attempting to write outside the workspace fails; writing inside succeeds.
- **Live smoke test:** run the sidecar CLI directly with a real key — a known weather query produces `tool_execution_start` events and a final `agent_end` with a plausible answer.
- **End-to-end:** `npm run release`, launch the installed app, verify model list, a weather chat, title generation, and stop/cancel.

## Phases (implementation order)

1. **Sidecar core:** TS project, CLI contract, SDK session, event forwarding, model listing. Runs via bun in dev; `lib.rs` pointed at it.
2. **Sandbox + runtime:** Seatbelt wrapper, bundled uv, workspace dirs, skill registration.
3. **Keys UX:** Keychain storage, settings UI, env injection.
4. **Packaging:** `bun build --compile`, `tauri.conf.json` externalBin/resources, release script, cleanup of pi_harness.py and stale docs.
