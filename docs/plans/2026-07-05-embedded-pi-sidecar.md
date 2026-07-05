# Embedded pi Sidecar Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the external `omp` CLI with upstream pi (`@earendil-works/pi-coding-agent`) embedded via its SDK in a bun-compiled sidecar binary, with Seatbelt-sandboxed bash, bundled uv Python runtime, and Keychain-stored API keys.

**Architecture:** A thin TypeScript CLI (`desktop/sidecar/`) wraps pi's `createAgentSession()`, forwards pi's native JSON events (`tool_execution_start`, `agent_end`) to stdout — the exact protocol `lib.rs` already parses, because omp is a pi fork. Rust changes are confined to sidecar path resolution, env plumbing, and Keychain key commands. Spec: `docs/specs/2026-07-04-embedded-pi-sidecar-design.md`.

**Tech Stack:** bun ≥ 1.3.14, `@earendil-works/pi-coding-agent` ^0.80.3, `typebox` (re-exported by pi), Rust `keyring` crate v3, Tauri v2 `externalBin`/`resources`, macOS `sandbox-exec`, `uv`.

## Global Constraints

- Package is `@earendil-works/pi-coding-agent` (NOT `@mariozechner/...`, which is stale at 0.73.1).
- stdout in `--mode json` carries ONLY JSON event lines. `lib.rs` consumes exactly: `{"type":"tool_execution_start","toolName":"..."}` and `{"type":"agent_end","messages":[{"role":"assistant","content":[{"type":"text","text":"..."}]}]}`. Diagnostics go to stderr.
- `--list-models` prints exactly `{"models":[{"id":"...","selector":"...","name":"...","provider":"..."}]}` on stdout.
- API keys NEVER appear in logs, CLI args, or stdout — env vars only.
- Existing IPC names stay: `ask_omp`, `stop_omp`, `get_models`, `generate_title`, `omp-output`, `omp-status`, `omp-done`.
- Sidecar env var contract (set by Rust, all optional with `~/.acis-sidecar/*` defaults for standalone testing): `ACIS_WORKSPACE_DIR`, `ACIS_DATA_DIR`, `ACIS_UV_DIR`, `ACIS_SKILL_DIR`.
- macOS arm64 only for packaging (`aarch64-apple-darwin`).
- The pi SDK is newer than your training data. When a compile error suggests an API drifted from this plan, check `desktop/sidecar/node_modules/@earendil-works/pi-coding-agent/dist/index.d.ts` and the package's `docs/sdk.md`, adapt, and note the deviation in your report.
- Per repo CLAUDE.md: after desktop changes are complete (final task only), run `npm run release` from `desktop/`.

---

### Task 1: Sidecar scaffold, CLI parsing, and `--list-models`

**Files:**
- Create: `desktop/sidecar/package.json`, `desktop/sidecar/tsconfig.json`, `desktop/sidecar/src/main.ts`, `desktop/sidecar/src/cli.ts`, `desktop/sidecar/src/models.ts`
- Test: `desktop/sidecar/test/cli.test.ts`

**Interfaces:**
- Produces: `parseArgs(argv: string[]): CliArgs` where `CliArgs = { prompt?: string; model?: string; mode: "text" | "json"; listModels: boolean }`; `listModels(): Promise<{ models: ModelEntry[] }>` where `ModelEntry = { id: string; selector: string; name: string; provider: string }`. `main.ts` dispatches: `--list-models` → print JSON; else requires `-p` and `--model` (missing → stderr message, exit 1).

- [ ] **Step 1: Scaffold the project**

```bash
mkdir -p desktop/sidecar/src desktop/sidecar/test
cd desktop/sidecar
```

`desktop/sidecar/package.json`:
```json
{
  "name": "pi-sidecar",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "start": "bun run src/main.ts",
    "test": "bun test",
    "compile": "bun build --compile src/main.ts --outfile ../src-tauri/binaries/pi-sidecar-aarch64-apple-darwin"
  }
}
```

`desktop/sidecar/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ESNext",
    "module": "ESNext",
    "moduleResolution": "bundler",
    "strict": true,
    "skipLibCheck": true,
    "types": ["bun-types"]
  },
  "include": ["src", "test"]
}
```

```bash
bun add @earendil-works/pi-coding-agent
bun add -d bun-types
```

- [ ] **Step 2: Write failing tests for arg parsing**

`desktop/sidecar/test/cli.test.ts`:
```typescript
import { describe, expect, test } from "bun:test";
import { parseArgs } from "../src/cli";

describe("parseArgs", () => {
  test("parses json chat invocation", () => {
    expect(parseArgs(["-p", "hi there", "--model", "anthropic/claude-sonnet-5", "--mode", "json"])).toEqual({
      prompt: "hi there",
      model: "anthropic/claude-sonnet-5",
      mode: "json",
      listModels: false,
    });
  });

  test("defaults to text mode", () => {
    const args = parseArgs(["-p", "title please", "--model", "anthropic/claude-haiku-4-5"]);
    expect(args.mode).toBe("text");
  });

  test("parses --list-models", () => {
    expect(parseArgs(["--list-models"]).listModels).toBe(true);
  });

  test("accepts --prompt long form", () => {
    expect(parseArgs(["--prompt", "x", "--model", "m"]).prompt).toBe("x");
  });
});
```

- [ ] **Step 3: Run tests, verify they fail**

Run: `cd desktop/sidecar && bun test`
Expected: FAIL — cannot resolve `../src/cli`.

- [ ] **Step 4: Implement `src/cli.ts`**

```typescript
export interface CliArgs {
  prompt?: string;
  model?: string;
  mode: "text" | "json";
  listModels: boolean;
}

export function parseArgs(argv: string[]): CliArgs {
  const args: CliArgs = { mode: "text", listModels: false };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    switch (a) {
      case "-p":
      case "--prompt":
        args.prompt = argv[++i];
        break;
      case "--model":
        args.model = argv[++i];
        break;
      case "--mode":
        args.mode = argv[++i] === "json" ? "json" : "text";
        break;
      case "--list-models":
        args.listModels = true;
        break;
    }
  }
  return args;
}
```

- [ ] **Step 5: Run tests, verify pass**

Run: `cd desktop/sidecar && bun test`
Expected: PASS (4 tests).

- [ ] **Step 6: Implement `src/models.ts`**

```typescript
import { AuthStorage, ModelRegistry } from "@earendil-works/pi-coding-agent";

export interface ModelEntry {
  id: string;
  selector: string;
  name: string;
  provider: string;
}

export async function listModels(): Promise<{ models: ModelEntry[] }> {
  const authStorage = AuthStorage.create();
  const registry = ModelRegistry.create(authStorage);
  // Only models whose provider has a usable API key (env var or ~/.pi auth).
  const available = await registry.getAvailable();
  const models = available.map((m: any) => ({
    id: m.id,
    selector: `${m.provider}/${m.id}`,
    name: m.name ?? m.id,
    provider: m.provider,
  }));
  return { models };
}
```

If `AuthStorage.create()` / `ModelRegistry.create()` / `getAvailable()` don't exist under those names, check `dist/index.d.ts` per Global Constraints and adapt.

- [ ] **Step 7: Implement `src/main.ts` dispatch**

```typescript
import { parseArgs } from "./cli";
import { listModels } from "./models";

async function main() {
  const args = parseArgs(process.argv.slice(2));

  if (args.listModels) {
    const result = await listModels();
    console.log(JSON.stringify(result));
    return;
  }

  if (!args.prompt || !args.model) {
    console.error("Error: --prompt and --model are required");
    process.exit(1);
  }

  // Chat modes are implemented in Task 2.
  console.error("Error: chat mode not implemented yet");
  process.exit(1);
}

main().catch((err) => {
  console.error(err instanceof Error ? err.message : String(err));
  process.exit(1);
});
```

- [ ] **Step 8: Live check `--list-models`**

Run: `cd desktop/sidecar && bun run src/main.ts --list-models`
Expected: one JSON line `{"models":[...]}`. With an `ANTHROPIC_API_KEY` in env (or existing `~/.pi` auth) the array is non-empty and every entry has `id`, `selector`, `name`, `provider`. Without any key, `{"models":[]}` is acceptable. Verify with: `bun run src/main.ts --list-models | python3 -m json.tool`.

- [ ] **Step 9: Commit**

```bash
git add desktop/sidecar
git commit -m "feat(sidecar): scaffold pi sidecar with CLI parsing and --list-models"
```

---

### Task 2: Agent session, event forwarding, JSON and text modes

**Files:**
- Create: `desktop/sidecar/src/events.ts`, `desktop/sidecar/src/session.ts`, `desktop/sidecar/src/run.ts`
- Modify: `desktop/sidecar/src/main.ts` (replace the "not implemented" branch)
- Test: `desktop/sidecar/test/events.test.ts`

**Interfaces:**
- Consumes: `CliArgs` from Task 1.
- Produces: `serializeEvent(event: { type: string; [k: string]: unknown }): string | null`; `buildSession(modelSelector: string, opts: { withTools: boolean }): Promise<AgentSession>` (Task 3 modifies its tool wiring; Task 4 its env wiring); `runJson(prompt: string, model: string): Promise<void>`; `runText(prompt: string, model: string): Promise<void>`.

- [ ] **Step 1: Write failing tests for event serialization**

`desktop/sidecar/test/events.test.ts`:
```typescript
import { describe, expect, test } from "bun:test";
import { serializeEvent } from "../src/events";

describe("serializeEvent", () => {
  test("forwards tool_execution_start with toolName", () => {
    const line = serializeEvent({ type: "tool_execution_start", toolCallId: "t1", toolName: "bash", args: { command: "ls" } });
    expect(JSON.parse(line!)).toEqual({ type: "tool_execution_start", toolName: "bash" });
  });

  test("forwards agent_end with messages", () => {
    const messages = [
      { role: "assistant", content: [{ type: "text", text: "It rained 3 inches." }] },
    ];
    const line = serializeEvent({ type: "agent_end", messages });
    const parsed = JSON.parse(line!);
    expect(parsed.type).toBe("agent_end");
    expect(parsed.messages[0].content[0].text).toBe("It rained 3 inches.");
  });

  test("drops unconsumed event types", () => {
    expect(serializeEvent({ type: "message_update" })).toBeNull();
    expect(serializeEvent({ type: "turn_start" })).toBeNull();
  });

  test("drops non-serializable payload fields safely", () => {
    // agent_end events may carry extra fields; only type + messages are emitted.
    const line = serializeEvent({ type: "agent_end", messages: [], internal: () => {} });
    expect(JSON.parse(line!)).toEqual({ type: "agent_end", messages: [] });
  });
});
```

- [ ] **Step 2: Run tests, verify fail**

Run: `cd desktop/sidecar && bun test test/events.test.ts`
Expected: FAIL — cannot resolve `../src/events`.

- [ ] **Step 3: Implement `src/events.ts`**

```typescript
interface PiEvent {
  type: string;
  [key: string]: unknown;
}

/**
 * Map pi session events to the JSON-line protocol lib.rs parses.
 * Only two event types are consumed by the Rust side; everything else is dropped.
 */
export function serializeEvent(event: PiEvent): string | null {
  switch (event.type) {
    case "tool_execution_start":
      return JSON.stringify({ type: "tool_execution_start", toolName: event.toolName ?? "tool" });
    case "agent_end":
      return JSON.stringify({ type: "agent_end", messages: event.messages ?? [] });
    default:
      return null;
  }
}
```

- [ ] **Step 4: Run tests, verify pass**

Run: `cd desktop/sidecar && bun test test/events.test.ts`
Expected: PASS (4 tests).

- [ ] **Step 5: Implement `src/session.ts`**

```typescript
import {
  AuthStorage,
  ModelRegistry,
  SessionManager,
  createAgentSession,
} from "@earendil-works/pi-coding-agent";

export interface SessionOptions {
  withTools: boolean;
}

export async function buildSession(modelSelector: string, opts: SessionOptions) {
  const authStorage = AuthStorage.create();
  const modelRegistry = ModelRegistry.create(authStorage);

  const slash = modelSelector.indexOf("/");
  if (slash < 1) {
    throw new Error(`model not found: ${modelSelector} (expected provider/model-id)`);
  }
  const provider = modelSelector.slice(0, slash);
  const modelId = modelSelector.slice(slash + 1);
  const model = modelRegistry.find(provider, modelId);
  if (!model) {
    throw new Error(`model not found: ${modelSelector}`);
  }

  const { session } = await createAgentSession({
    authStorage,
    modelRegistry,
    model,
    sessionManager: SessionManager.inMemory(),
    ...(opts.withTools ? { tools: ["read", "bash"] } : { noTools: "all" as const }),
  });
  return session;
}
```

(Task 3 replaces `tools: ["read", "bash"]` with the sandboxed custom bash; Task 4 adds `cwd`/`agentDir`.)

- [ ] **Step 6: Implement `src/run.ts`**

```typescript
import { serializeEvent } from "./events";
import { buildSession } from "./session";

export async function runJson(prompt: string, model: string): Promise<void> {
  const session = await buildSession(model, { withTools: true });
  session.subscribe((event: any) => {
    const line = serializeEvent(event);
    if (line) console.log(line);
  });
  await session.prompt(prompt);
}

export async function runText(prompt: string, model: string): Promise<void> {
  const session = await buildSession(model, { withTools: false });
  await session.prompt(prompt);
  // Extract the last assistant text from session state.
  const messages: any[] = session.agent?.state?.messages ?? [];
  for (let i = messages.length - 1; i >= 0; i--) {
    const msg = messages[i];
    if (msg.role !== "assistant") continue;
    const text = (Array.isArray(msg.content) ? msg.content : [])
      .filter((c: any) => c.type === "text")
      .map((c: any) => c.text)
      .join("");
    if (text) {
      console.log(text.trim());
      return;
    }
  }
  throw new Error("model returned no text");
}
```

If `session.agent.state.messages` isn't the state path in this SDK version, subscribe to `agent_end` and read `event.messages` instead — same extraction logic.

- [ ] **Step 7: Wire into `src/main.ts`**

Replace the "not implemented" branch:
```typescript
  if (args.mode === "json") {
    const { runJson } = await import("./run");
    await runJson(args.prompt, args.model);
  } else {
    const { runText } = await import("./run");
    await runText(args.prompt, args.model);
  }
```

- [ ] **Step 8: Full test suite + typecheck**

Run: `cd desktop/sidecar && bun test && bunx tsc --noEmit`
Expected: all tests PASS, no type errors.

- [ ] **Step 9: Live smoke test (needs a real API key)**

Requires `ANTHROPIC_API_KEY` in env or existing `~/.pi` auth. If neither is available, mark this step skipped and flag it in your report — do not fake it.

```bash
cd desktop/sidecar
bun run src/main.ts -p "Reply with exactly the word: pong" --model anthropic/claude-haiku-4-5 --mode json
```
Expected: stdout ends with an `agent_end` JSON line whose assistant text contains "pong".

```bash
bun run src/main.ts -p "Say exactly: ping" --model anthropic/claude-haiku-4-5
```
Expected: plain text output containing "ping", no JSON.

- [ ] **Step 10: Commit**

```bash
git add desktop/sidecar
git commit -m "feat(sidecar): pi SDK session with JSON event forwarding and text mode"
```

---

### Task 3: Seatbelt-sandboxed bash tool

**Files:**
- Create: `desktop/sidecar/src/sandbox.ts`, `desktop/sidecar/src/bash-tool.ts`
- Modify: `desktop/sidecar/src/session.ts` (swap built-in bash for the custom tool)
- Test: `desktop/sidecar/test/sandbox.test.ts`

**Interfaces:**
- Consumes: `buildSession` from Task 2.
- Produces: `buildProfile(writablePaths: string[]): string`; `truncateOutput(s: string, max?: number): string`; `createSandboxedBash(cfg: BashConfig)` where `BashConfig = { profilePath: string; workspaceDir: string; env: Record<string, string> }`. `buildSession` gains a `bash?: BashConfig` field on `SessionOptions`: when `withTools` is true and `bash` is set, session gets `tools: ["read"]` + `customTools: [createSandboxedBash(cfg)]`.

- [ ] **Step 1: Write failing tests**

`desktop/sidecar/test/sandbox.test.ts`:
```typescript
import { describe, expect, test } from "bun:test";
import { mkdtempSync, existsSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { buildProfile, truncateOutput } from "../src/sandbox";

describe("buildProfile", () => {
  test("allows default, denies writes except listed subpaths", () => {
    const p = buildProfile(["/tmp/ws", "/tmp/uv"]);
    expect(p).toContain("(version 1)");
    expect(p).toContain("(allow default)");
    expect(p).toContain("(deny file-write*)");
    expect(p).toContain('(subpath "/tmp/ws")');
    expect(p).toContain('(subpath "/tmp/uv")');
    // deny must come before the allow-list so the allow wins (SBPL: later rules take precedence)
    expect(p.indexOf("(deny file-write*)")).toBeLessThan(p.indexOf('(subpath "/tmp/ws")'));
  });
});

describe("truncateOutput", () => {
  test("passes short output through", () => {
    expect(truncateOutput("hello")).toBe("hello");
  });
  test("truncates long output with marker", () => {
    const out = truncateOutput("x".repeat(60_000), 50_000);
    expect(out.length).toBeLessThan(51_000);
    expect(out).toContain("[output truncated]");
  });
});

// Integration: real sandbox-exec (macOS only)
describe("sandbox-exec enforcement", () => {
  test("blocks writes outside allowed paths, permits inside", async () => {
    const ws = mkdtempSync(join(tmpdir(), "sbx-ws-"));
    const outside = mkdtempSync(join(tmpdir(), "sbx-outside-"));
    // Only ws is writable; outside is not listed.
    const profile = buildProfile([ws]);
    const profilePath = join(ws, "test.sb");
    writeFileSync(profilePath, profile);

    const inside = Bun.spawnSync(
      ["sandbox-exec", "-f", profilePath, "/bin/bash", "-c", `touch ${ws}/ok.txt`],
    );
    expect(inside.exitCode).toBe(0);
    expect(existsSync(`${ws}/ok.txt`)).toBe(true);

    const blocked = Bun.spawnSync(
      ["sandbox-exec", "-f", profilePath, "/bin/bash", "-c", `touch ${outside}/nope.txt`],
    );
    expect(blocked.exitCode).not.toBe(0);
    expect(existsSync(`${outside}/nope.txt`)).toBe(false);
  });
});
```

Note: `mkdtempSync(join(tmpdir(), ...))` returns `/var/folders/...`; seatbelt canonicalizes to `/private/var/...`. `buildProfile` must canonicalize input paths with `realpathSync` (see Step 3) or the "inside" write will be denied.

- [ ] **Step 2: Run tests, verify fail**

Run: `cd desktop/sidecar && bun test test/sandbox.test.ts`
Expected: FAIL — cannot resolve `../src/sandbox`.

- [ ] **Step 3: Implement `src/sandbox.ts`**

```typescript
import { realpathSync } from "node:fs";

const DEFAULT_MAX_OUTPUT = 50_000;

/**
 * SBPL profile: everything allowed except file writes, which are limited to
 * the given directories (plus /dev for tty/null). Later rules take precedence,
 * so the allow-list must follow the deny.
 */
export function buildProfile(writablePaths: string[]): string {
  const canonical = writablePaths.map((p) => {
    try {
      return realpathSync(p);
    } catch {
      return p;
    }
  });
  const subpaths = [...canonical, "/dev"].map((p) => `  (subpath "${p}")`).join("\n");
  return [
    "(version 1)",
    "(allow default)",
    "(deny file-write*)",
    "(allow file-write*",
    subpaths,
    ")",
  ].join("\n");
}

export function truncateOutput(s: string, max: number = DEFAULT_MAX_OUTPUT): string {
  if (s.length <= max) return s;
  return s.slice(0, max) + "\n[output truncated]";
}
```

- [ ] **Step 4: Run tests, verify pass**

Run: `cd desktop/sidecar && bun test test/sandbox.test.ts`
Expected: PASS (4 tests, including the live sandbox-exec integration test).

- [ ] **Step 5: Implement `src/bash-tool.ts`**

```typescript
import { defineTool } from "@earendil-works/pi-coding-agent";
import { Type } from "@sinclair/typebox";
import { truncateOutput } from "./sandbox";

const DEFAULT_TIMEOUT_MS = 120_000;

export interface BashConfig {
  profilePath: string;
  workspaceDir: string;
  env: Record<string, string>;
}

export function createSandboxedBash(cfg: BashConfig) {
  return defineTool({
    name: "bash",
    label: "bash",
    description:
      "Execute a bash command in the sandboxed workspace. Writes are only permitted inside the workspace and Python cache directories.",
    parameters: Type.Object({
      command: Type.String({ description: "The bash command to run" }),
      timeout: Type.Optional(Type.Number({ description: "Timeout in seconds" })),
    }),
    execute: async (_toolCallId: string, params: { command: string; timeout?: number }) => {
      const timeoutMs = params.timeout ? params.timeout * 1000 : DEFAULT_TIMEOUT_MS;
      const proc = Bun.spawn(
        ["sandbox-exec", "-f", cfg.profilePath, "/bin/bash", "-c", params.command],
        { cwd: cfg.workspaceDir, env: cfg.env, stdout: "pipe", stderr: "pipe" },
      );

      const killer = setTimeout(() => proc.kill(), timeoutMs);
      const [stdout, stderr, exitCode] = await Promise.all([
        new Response(proc.stdout).text(),
        new Response(proc.stderr).text(),
        proc.exited,
      ]);
      clearTimeout(killer);

      let text = stdout;
      if (exitCode !== 0) {
        text += `${text ? "\n" : ""}[exit code ${exitCode}]\n${stderr}`;
      }
      return {
        content: [{ type: "text" as const, text: truncateOutput(text) || "(no output)" }],
        details: {},
      };
    },
  });
}
```

If `defineTool`'s `execute` signature differs (extra `signal`/context params), match the `.d.ts` — extra unused trailing params are fine.
Note: pi re-exports typebox; if `@sinclair/typebox` isn't already a transitive dependency, import `Type` from the pi package if it re-exports it, else `bun add @sinclair/typebox`.

- [ ] **Step 6: Wire into `buildSession`**

In `desktop/sidecar/src/session.ts`, extend `SessionOptions` and the session call:
```typescript
import { createSandboxedBash, type BashConfig } from "./bash-tool";

export interface SessionOptions {
  withTools: boolean;
  bash?: BashConfig;
}
```
and replace the tools spread in `createAgentSession(...)`:
```typescript
    ...(opts.withTools
      ? opts.bash
        ? { tools: ["read"], customTools: [createSandboxedBash(opts.bash)] }
        : { tools: ["read", "bash"] }
      : { noTools: "all" as const }),
```

- [ ] **Step 7: Full suite + typecheck**

Run: `cd desktop/sidecar && bun test && bunx tsc --noEmit`
Expected: PASS, no type errors.

- [ ] **Step 8: Commit**

```bash
git add desktop/sidecar
git commit -m "feat(sidecar): seatbelt-sandboxed bash custom tool"
```

---

### Task 4: Environment wiring — workspace, uv, skill registration

**Files:**
- Create: `desktop/sidecar/src/env.ts`
- Modify: `desktop/sidecar/src/session.ts`, `desktop/sidecar/src/run.ts`
- Test: `desktop/sidecar/test/env.test.ts`

**Interfaces:**
- Consumes: `buildProfile` (Task 3), `BashConfig` (Task 3), `buildSession`/`runJson` (Task 2).
- Produces: `initEnv(): SidecarEnv` where
  ```typescript
  interface SidecarEnv {
    workspaceDir: string;   // ACIS_WORKSPACE_DIR || ~/.acis-sidecar/workspace
    dataDir: string;        // ACIS_DATA_DIR || ~/.acis-sidecar/data
    agentDir: string;       // <dataDir>/pi-agent   (skills live in <agentDir>/skills)
    profilePath: string;    // <dataDir>/sandbox.sb (written by initEnv)
    bashEnv: Record<string, string>; // PATH (uv prepended), UV_CACHE_DIR, UV_PYTHON_INSTALL_DIR, HOME, TMPDIR
  }
  ```
  `initEnv()` creates all dirs, copies the skill from `ACIS_SKILL_DIR` (when set and existing) into `<agentDir>/skills/acis-weather`, writes the sandbox profile (writable: workspaceDir, dataDir, TMPDIR), and returns the struct. `runJson` calls it and passes `cwd: workspaceDir`, `agentDir`, and the `BashConfig` into `buildSession`.

- [ ] **Step 1: Write failing tests**

`desktop/sidecar/test/env.test.ts`:
```typescript
import { afterEach, describe, expect, test } from "bun:test";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { initEnv } from "../src/env";

const saved: Record<string, string | undefined> = {};
const KEYS = ["ACIS_WORKSPACE_DIR", "ACIS_DATA_DIR", "ACIS_UV_DIR", "ACIS_SKILL_DIR"];

function setEnv(vars: Record<string, string>) {
  for (const k of KEYS) {
    saved[k] = process.env[k];
    delete process.env[k];
  }
  Object.assign(process.env, vars);
}

afterEach(() => {
  for (const k of KEYS) {
    if (saved[k] === undefined) delete process.env[k];
    else process.env[k] = saved[k]!;
  }
});

describe("initEnv", () => {
  test("creates dirs, writes profile, syncs skill, prepends uv to PATH", () => {
    const base = mkdtempSync(join(tmpdir(), "acis-env-"));
    const skillSrc = join(base, "skill-src");
    mkdirSync(skillSrc, { recursive: true });
    writeFileSync(join(skillSrc, "SKILL.md"), "---\nname: acis-weather\n---\n");
    const uvDir = join(base, "uv");
    mkdirSync(uvDir);

    setEnv({
      ACIS_WORKSPACE_DIR: join(base, "ws"),
      ACIS_DATA_DIR: join(base, "data"),
      ACIS_UV_DIR: uvDir,
      ACIS_SKILL_DIR: skillSrc,
    });

    const env = initEnv();
    expect(existsSync(env.workspaceDir)).toBe(true);
    expect(existsSync(join(env.agentDir, "skills", "acis-weather", "SKILL.md"))).toBe(true);
    expect(readFileSync(env.profilePath, "utf8")).toContain("(deny file-write*)");
    expect(env.bashEnv.PATH!.startsWith(uvDir)).toBe(true);
    expect(env.bashEnv.UV_CACHE_DIR).toBe(join(env.dataDir, "uv-cache"));
    rmSync(base, { recursive: true, force: true });
  });

  test("works without optional env vars", () => {
    setEnv({});
    const env = initEnv();
    expect(env.workspaceDir).toContain(".acis-sidecar");
    expect(existsSync(env.profilePath)).toBe(true);
  });
});
```

- [ ] **Step 2: Run tests, verify fail**

Run: `cd desktop/sidecar && bun test test/env.test.ts`
Expected: FAIL — cannot resolve `../src/env`.

- [ ] **Step 3: Implement `src/env.ts`**

```typescript
import { cpSync, existsSync, mkdirSync, writeFileSync } from "node:fs";
import { homedir, tmpdir } from "node:os";
import { join } from "node:path";
import { buildProfile } from "./sandbox";

export interface SidecarEnv {
  workspaceDir: string;
  dataDir: string;
  agentDir: string;
  profilePath: string;
  bashEnv: Record<string, string>;
}

export function initEnv(): SidecarEnv {
  const fallback = join(homedir(), ".acis-sidecar");
  const workspaceDir = process.env.ACIS_WORKSPACE_DIR || join(fallback, "workspace");
  const dataDir = process.env.ACIS_DATA_DIR || join(fallback, "data");
  const agentDir = join(dataDir, "pi-agent");
  const skillsDir = join(agentDir, "skills");

  for (const d of [workspaceDir, dataDir, skillsDir]) {
    mkdirSync(d, { recursive: true });
  }

  const skillSrc = process.env.ACIS_SKILL_DIR;
  if (skillSrc && existsSync(skillSrc)) {
    cpSync(skillSrc, join(skillsDir, "acis-weather"), { recursive: true });
  }

  const profilePath = join(dataDir, "sandbox.sb");
  writeFileSync(profilePath, buildProfile([workspaceDir, dataDir, process.env.TMPDIR || tmpdir()]));

  const uvDir = process.env.ACIS_UV_DIR;
  const basePath = process.env.PATH || "/usr/bin:/bin:/usr/sbin:/sbin";
  const bashEnv: Record<string, string> = {
    HOME: homedir(),
    TMPDIR: process.env.TMPDIR || tmpdir(),
    PATH: uvDir ? `${uvDir}:${basePath}` : basePath,
    UV_CACHE_DIR: join(dataDir, "uv-cache"),
    UV_PYTHON_INSTALL_DIR: join(dataDir, "uv-python"),
  };
  return { workspaceDir, dataDir, agentDir, profilePath, bashEnv };
}
```

- [ ] **Step 4: Run tests, verify pass**

Run: `cd desktop/sidecar && bun test test/env.test.ts`
Expected: PASS (2 tests).

- [ ] **Step 5: Wire env into session and run**

`src/session.ts` — add to `SessionOptions`:
```typescript
export interface SessionOptions {
  withTools: boolean;
  bash?: BashConfig;
  cwd?: string;
  agentDir?: string;
}
```
and pass through in `createAgentSession({ ... , cwd: opts.cwd, agentDir: opts.agentDir })`. Skills in `<agentDir>/skills` are auto-discovered by pi's resource loader; verify against the SDK docs (`docs/sdk.md` in the package) — if discovery requires a `DefaultResourceLoader` with explicit paths, construct one and pass it as `resourceLoader`.

`src/run.ts` — in `runJson` only (text mode needs no tools/workspace):
```typescript
import { initEnv } from "./env";

export async function runJson(prompt: string, model: string): Promise<void> {
  const env = initEnv();
  const session = await buildSession(model, {
    withTools: true,
    cwd: env.workspaceDir,
    agentDir: env.agentDir,
    bash: { profilePath: env.profilePath, workspaceDir: env.workspaceDir, env: env.bashEnv },
  });
  session.subscribe((event: any) => {
    const line = serializeEvent(event);
    if (line) console.log(line);
  });
  await session.prompt(prompt);
}
```

- [ ] **Step 6: Full suite + typecheck**

Run: `cd desktop/sidecar && bun test && bunx tsc --noEmit`
Expected: PASS.

- [ ] **Step 7: Live end-to-end weather query (needs API key + network)**

Skip-and-flag if no key available.
```bash
cd desktop/sidecar
ACIS_SKILL_DIR=$(git rev-parse --show-toplevel)/skills/acis-weather \
bun run src/main.ts -p "Use the acis-weather skill. What was the total snowfall at KDEN in January 2023? Cite the number." --model anthropic/claude-sonnet-5 --mode json
```
Expected: at least one `tool_execution_start` line with `"toolName":"bash"`, then an `agent_end` whose text contains a snowfall figure. First run may take minutes while uv bootstraps Python packages into `~/.acis-sidecar/data/uv-cache`.

- [ ] **Step 8: Commit**

```bash
git add desktop/sidecar
git commit -m "feat(sidecar): workspace/uv/skill environment wiring"
```

---

### Task 5: Keychain API key storage (Rust)

**Files:**
- Create: `desktop/src-tauri/src/keys.rs`
- Modify: `desktop/src-tauri/Cargo.toml`, `desktop/src-tauri/src/lib.rs` (register commands only — spawn wiring is Task 6)

**Interfaces:**
- Produces (Rust): `keys::PROVIDERS: [(&str, &str); 6]` mapping provider → env var; `keys::collect_api_keys() -> Vec<(String, String)>` (env-var name, key) for spawn env; Tauri commands `set_api_key(provider: String, key: String)`, `delete_api_key(provider: String)`, `get_api_key_status() -> Vec<KeyStatus>` where `KeyStatus { provider: String, configured: bool }`.
- Produces (frontend contract): `invoke("set_api_key", { provider, key })`, `invoke("delete_api_key", { provider })`, `invoke<KeyStatus[]>("get_api_key_status")`.

- [ ] **Step 1: Add the keyring dependency**

In `desktop/src-tauri/Cargo.toml` under `[dependencies]`:
```toml
keyring = { version = "3", features = ["apple-native"] }
```

- [ ] **Step 2: Write `src/keys.rs` with unit tests**

```rust
use keyring::Entry;

const SERVICE: &str = "com.yenba.acis-weather-bot";

/// Providers we surface in Settings, with the env var pi's AuthStorage reads.
pub const PROVIDERS: [(&str, &str); 6] = [
    ("anthropic", "ANTHROPIC_API_KEY"),
    ("openai", "OPENAI_API_KEY"),
    ("google", "GEMINI_API_KEY"),
    ("xai", "XAI_API_KEY"),
    ("groq", "GROQ_API_KEY"),
    ("openrouter", "OPENROUTER_API_KEY"),
];

fn env_var_for(provider: &str) -> Option<&'static str> {
    PROVIDERS
        .iter()
        .find(|(p, _)| *p == provider)
        .map(|(_, v)| *v)
}

fn entry(provider: &str) -> Result<Entry, String> {
    Entry::new(SERVICE, provider).map_err(|e| format!("keychain error: {}", e))
}

#[derive(serde::Serialize)]
pub struct KeyStatus {
    pub provider: String,
    pub configured: bool,
}

#[tauri::command]
pub fn set_api_key(provider: String, key: String) -> Result<(), String> {
    if env_var_for(&provider).is_none() {
        return Err(format!("unknown provider: {}", provider));
    }
    let trimmed = key.trim();
    if trimmed.is_empty() {
        return Err("key is empty".to_string());
    }
    entry(&provider)?
        .set_password(trimmed)
        .map_err(|e| format!("keychain error: {}", e))
}

#[tauri::command]
pub fn delete_api_key(provider: String) -> Result<(), String> {
    match entry(&provider)?.delete_credential() {
        Ok(()) => Ok(()),
        Err(keyring::Error::NoEntry) => Ok(()),
        Err(e) => Err(format!("keychain error: {}", e)),
    }
}

#[tauri::command]
pub fn get_api_key_status() -> Result<Vec<KeyStatus>, String> {
    Ok(PROVIDERS
        .iter()
        .map(|(provider, _)| KeyStatus {
            provider: provider.to_string(),
            configured: entry(provider)
                .and_then(|e| e.get_password().map_err(|err| err.to_string()))
                .is_ok(),
        })
        .collect())
}

/// (ENV_VAR, key) pairs for every configured provider — used when spawning the sidecar.
/// Keys must never be logged.
pub fn collect_api_keys() -> Vec<(String, String)> {
    PROVIDERS
        .iter()
        .filter_map(|(provider, env_var)| {
            let key = entry(provider).ok()?.get_password().ok()?;
            Some((env_var.to_string(), key))
        })
        .collect()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn env_var_mapping() {
        assert_eq!(env_var_for("anthropic"), Some("ANTHROPIC_API_KEY"));
        assert_eq!(env_var_for("google"), Some("GEMINI_API_KEY"));
        assert_eq!(env_var_for("bogus"), None);
    }

    #[test]
    fn rejects_unknown_provider_and_empty_key() {
        assert!(set_api_key("bogus".into(), "k".into()).is_err());
        assert!(set_api_key("anthropic".into(), "   ".into()).is_err());
    }
}
```

Verify pi's Google env var: `grep -ri "GEMINI_API_KEY\|GOOGLE_API_KEY" desktop/sidecar/node_modules/@earendil-works/pi-coding-agent/dist/ | head -3` — if pi reads a different name, use pi's.

- [ ] **Step 3: Register in `lib.rs`**

Add `mod keys;` at top of `desktop/src-tauri/src/lib.rs` and extend the handler list:
```rust
        .invoke_handler(tauri::generate_handler![
            get_models,
            ask_omp,
            generate_title,
            stop_omp,
            open_log_folder,
            keys::set_api_key,
            keys::delete_api_key,
            keys::get_api_key_status
        ])
```
(`lib.rs` needs no `main.rs` change; `keys.rs` sits beside `lib.rs`.)

- [ ] **Step 4: Test and build**

Run: `cd desktop/src-tauri && cargo test && cargo build`
Expected: tests pass (the two unit tests don't touch the real keychain), clean build.

- [ ] **Step 5: Commit**

```bash
git add desktop/src-tauri
git commit -m "feat(desktop): keychain-backed API key storage commands"
```

---

### Task 6: Rust spawn rewiring — sidecar resolution and env plumbing

**Files:**
- Modify: `desktop/src-tauri/src/lib.rs`

**Interfaces:**
- Consumes: `keys::collect_api_keys()` (Task 5); sidecar CLI + env contract (Global Constraints).
- Produces: `resolve_sidecar() -> (String, Vec<String>)` (program + base args, before per-call args); `sidecar_env(app: &AppHandle) -> Vec<(String, String)>`. `get_models` and `generate_title` gain an `app: AppHandle` first parameter (frontend `invoke` calls need no change — Tauri injects it).

- [ ] **Step 1: Replace `get_omp_path` and `get_expanded_env`**

Delete `get_omp_path()`. Replace `get_expanded_env()` usage with two new helpers:

```rust
/// Locate the sidecar. Release builds use the bundled binary next to the app
/// executable (Tauri externalBin). Debug builds run the TypeScript source via bun.
fn resolve_sidecar() -> (String, Vec<String>) {
    if cfg!(debug_assertions) {
        let sidecar_main = concat!(env!("CARGO_MANIFEST_DIR"), "/../sidecar/src/main.ts");
        ("bun".to_string(), vec!["run".to_string(), sidecar_main.to_string()])
    } else {
        let exe_dir = std::env::current_exe()
            .ok()
            .and_then(|p| p.parent().map(|d| d.to_path_buf()))
            .unwrap_or_default();
        (exe_dir.join("pi-sidecar").to_string_lossy().to_string(), vec![])
    }
}

/// Environment for the sidecar: expanded PATH (so bun/uv resolve in dev),
/// workspace/data dirs, bundled resources, and API keys from the keychain.
/// Keys must never be logged.
fn sidecar_env(app: &AppHandle) -> Vec<(String, String)> {
    let mut env = get_expanded_env(); // keep the existing PATH-expansion helper

    if let Ok(data_dir) = app.path().app_data_dir() {
        env.push(("ACIS_DATA_DIR".into(), data_dir.join("sidecar").to_string_lossy().into()));
        env.push(("ACIS_WORKSPACE_DIR".into(), data_dir.join("workspace").to_string_lossy().into()));
    }
    if let Ok(resource_dir) = app.path().resource_dir() {
        let uv = resource_dir.join("uv");
        if uv.exists() {
            env.push(("ACIS_UV_DIR".into(), uv.to_string_lossy().into()));
        }
        let skill = resource_dir.join("skills/acis-weather");
        if skill.exists() {
            env.push(("ACIS_SKILL_DIR".into(), skill.to_string_lossy().into()));
        }
    }
    if cfg!(debug_assertions) {
        // Dev: use the repo skill directly.
        let skill = concat!(env!("CARGO_MANIFEST_DIR"), "/../../skills/acis-weather");
        env.push(("ACIS_SKILL_DIR".into(), skill.to_string()));
    }

    for (var, key) in keys::collect_api_keys() {
        env.push((var, key));
    }
    env
}
```

- [ ] **Step 2: Update the four commands**

- `get_models(app: AppHandle)`: build `let (prog, mut args) = resolve_sidecar(); args.push("--list-models".into());` then `Command::new(&prog).args(&args).envs(sidecar_env(&app))...` — output handling unchanged.
- `ask_omp(...)`: same substitution; the arg list becomes `args.extend(["-p", &full_prompt, "--model", &model, "--mode", "json"].map(String::from))`. Prompt assembly, event parsing, threads, and emits unchanged.
- `generate_title(app: AppHandle, message: String, model: String)`: same substitution, no `--mode json` (text mode).
- Update log lines that print the spawned program to log only the program path, never env.

- [ ] **Step 3: Update `classify_omp_error` copy**

The omp-specific message becomes settings-oriented:
```rust
        "Missing API key for this model's provider. Add it in Settings → AI, then try again."
```
Update the corresponding assertion in the `#[cfg(test)]` module (`classifies_missing_api_key`, `api_key_takes_priority_over_generic_not_found`). Also update the stderr trigger check: pi's missing-key error may not contain "no api key" verbatim — run the sidecar with no keys and an explicitly-keyed model to capture the real message:
`cd desktop/sidecar && env -u ANTHROPIC_API_KEY bun run src/main.ts -p hi --model anthropic/claude-haiku-4-5 --mode json; echo "exit=$?"` — add the observed phrase (lowercased) to the `classify_omp_error` conditions alongside `"no api key"`.

- [ ] **Step 4: Test and build**

Run: `cd desktop/src-tauri && cargo test && cargo build`
Expected: all tests pass (including updated copy assertions), clean build.

- [ ] **Step 5: Dev-mode smoke test (needs a key in keychain or env)**

Run: `cd desktop && npm run tauri dev` — in the app: model dropdown populates, a chat message produces status + answer, Stop works. If no API key is available, verify the friendly missing-key message appears instead, then close.

- [ ] **Step 6: Commit**

```bash
git add desktop/src-tauri
git commit -m "feat(desktop): spawn embedded pi sidecar instead of external omp"
```

---

### Task 7: Settings UI — API keys section

**Files:**
- Modify: `desktop/src/App.tsx` (the `activeSettingsTab === 'ai'` block, around line 881)

**Interfaces:**
- Consumes: `invoke("get_api_key_status")` → `{ provider: string; configured: boolean }[]`; `invoke("set_api_key", { provider, key })`; `invoke("delete_api_key", { provider })` (Task 5).

- [ ] **Step 1: Add state and handlers**

Near the other state hooks in the `App` component:
```tsx
interface KeyStatus { provider: string; configured: boolean; }

const PROVIDER_LABELS: Record<string, string> = {
  anthropic: "Anthropic", openai: "OpenAI", google: "Google (Gemini)",
  xai: "xAI", groq: "Groq", openrouter: "OpenRouter",
};

const [keyStatus, setKeyStatus] = useState<KeyStatus[]>([]);
const [keyDrafts, setKeyDrafts] = useState<Record<string, string>>({});
const [keyBusy, setKeyBusy] = useState<string | null>(null);

const refreshKeyStatus = async () => {
  try { setKeyStatus(await invoke<KeyStatus[]>("get_api_key_status")); }
  catch (e) { logError("get_api_key_status failed", e); }
};

useEffect(() => { if (isSettingsOpen) refreshKeyStatus(); }, [isSettingsOpen]);

const saveKey = async (provider: string) => {
  const key = (keyDrafts[provider] || "").trim();
  if (!key) return;
  setKeyBusy(provider);
  try {
    await invoke("set_api_key", { provider, key });
    setKeyDrafts((d) => ({ ...d, [provider]: "" }));
    await refreshKeyStatus();
  } catch (e) { logError("set_api_key failed", e); }
  finally { setKeyBusy(null); }
};

const removeKey = async (provider: string) => {
  setKeyBusy(provider);
  try { await invoke("delete_api_key", { provider }); await refreshKeyStatus(); }
  catch (e) { logError("delete_api_key failed", e); }
  finally { setKeyBusy(null); }
};
```
Use the existing logging helper in `desktop/src/logging.ts` (check its exported name — adjust `logError` accordingly). Never log the key value.

- [ ] **Step 2: Render the section in the AI tab**

Inside the `activeSettingsTab === 'ai'` block, above the existing model content, following the tab's existing styling conventions:
```tsx
<div className="mb-6">
  <h3 className="text-sm font-medium mb-2">API Keys</h3>
  <p className="text-xs text-muted-foreground mb-3">
    Stored securely in the macOS Keychain. Required for the embedded assistant.
  </p>
  <div className="space-y-2">
    {keyStatus.map(({ provider, configured }) => (
      <div key={provider} className="flex items-center gap-2">
        <span className="w-32 text-sm">{PROVIDER_LABELS[provider] ?? provider}</span>
        {configured ? (
          <>
            <span className="text-xs text-green-600 flex items-center gap-1">
              <CheckCircle className="w-3 h-3" /> Configured
            </span>
            <button
              onClick={() => removeKey(provider)}
              disabled={keyBusy === provider}
              className="text-xs text-destructive hover:underline ml-2"
            >
              Remove
            </button>
          </>
        ) : (
          <>
            <input
              type="password"
              value={keyDrafts[provider] ?? ""}
              onChange={(e) => setKeyDrafts((d) => ({ ...d, [provider]: e.target.value }))}
              placeholder="Paste API key"
              className="flex-1 px-2 py-1 text-sm rounded-md border border-input bg-background"
            />
            <button
              onClick={() => saveKey(provider)}
              disabled={keyBusy === provider || !(keyDrafts[provider] || "").trim()}
              className="px-2 py-1 text-xs rounded-md bg-primary text-primary-foreground disabled:opacity-50"
            >
              Save
            </button>
          </>
        )}
      </div>
    ))}
  </div>
</div>
```
Match surrounding class conventions in the file; reuse already-imported lucide icons (`CheckCircle` is imported).

- [ ] **Step 3: Typecheck and build**

Run: `cd desktop && npx tsc --noEmit && npm run build`
Expected: no type errors, vite build succeeds.

- [ ] **Step 4: Manual verify in dev**

Run: `cd desktop && npm run tauri dev` — Settings → AI shows the six providers; saving a dummy key flips it to Configured (approve the keychain prompt); Remove flips it back; model list refreshes to include that provider's models after reopening settings.

- [ ] **Step 5: Commit**

```bash
git add desktop/src
git commit -m "feat(desktop): API keys settings UI backed by keychain"
```

---

### Task 8: Packaging, cleanup, and release

**Files:**
- Create: `desktop/scripts/fetch-uv.sh`
- Modify: `desktop/src-tauri/tauri.conf.json`, `desktop/package.json`, `docs/architecture-embedded-pi.md`
- Delete: `desktop/backend/pi_harness.py`, `todo.txt` (repo root)

**Interfaces:**
- Consumes: sidecar `compile` script (Task 1), resource paths expected by `sidecar_env` (Task 6): `<resources>/uv/uv`, `<resources>/skills/acis-weather`.

- [ ] **Step 1: uv fetch script**

`desktop/scripts/fetch-uv.sh`:
```bash
#!/usr/bin/env bash
# Download the static uv binary into src-tauri resources (skips if present).
set -euo pipefail
DEST="$(cd "$(dirname "$0")/.." && pwd)/src-tauri/resources/uv"
if [[ -x "$DEST/uv" ]]; then
  echo "uv already present at $DEST/uv"
  exit 0
fi
mkdir -p "$DEST"
TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
curl -fsSL "https://github.com/astral-sh/uv/releases/latest/download/uv-aarch64-apple-darwin.tar.gz" \
  | tar -xz -C "$TMP"
mv "$TMP"/uv-aarch64-apple-darwin/uv "$DEST/uv"
chmod +x "$DEST/uv"
echo "uv installed to $DEST/uv"
```
Run: `chmod +x desktop/scripts/fetch-uv.sh && desktop/scripts/fetch-uv.sh`
Expected: `desktop/src-tauri/resources/uv/uv --version` prints a version.
Add `desktop/src-tauri/resources/uv/` and `desktop/src-tauri/binaries/` to `.gitignore` (build artifacts, not source).

- [ ] **Step 2: Compile the sidecar binary**

Run: `cd desktop/sidecar && bun run compile`
Expected: `desktop/src-tauri/binaries/pi-sidecar-aarch64-apple-darwin` exists; verify:
```bash
../src-tauri/binaries/pi-sidecar-aarch64-apple-darwin --list-models
```
prints the models JSON (empty list fine without keys).

- [ ] **Step 3: Tauri bundle config**

In `desktop/src-tauri/tauri.conf.json`, add to the `bundle` object:
```json
    "externalBin": ["binaries/pi-sidecar"],
    "resources": {
      "resources/uv/uv": "uv/uv",
      "../../skills/acis-weather": "skills/acis-weather"
    }
```
(Tauri appends the target triple to `externalBin` entries at build time and strips it inside the bundle, which is why release-mode `resolve_sidecar()` looks for plain `pi-sidecar` next to the executable.)

- [ ] **Step 4: Build pipeline hooks**

In `desktop/package.json`, read the existing `release` script first, then prepend sidecar steps so they run before the Tauri build, e.g.:
```json
"sidecar:build": "bash scripts/fetch-uv.sh && cd sidecar && bun install && bun run compile",
```
and make `release` (and any `tauri build` path in `rebuild_app.py` if that's what release invokes — read it) run `npm run sidecar:build` first. Keep the existing version-bump/deploy behavior intact.

- [ ] **Step 5: Delete the obsolete prototype and stale plan files**

```bash
git rm desktop/backend/pi_harness.py
git rm todo.txt
rmdir desktop/backend 2>/dev/null || true
```
Replace the body of `docs/architecture-embedded-pi.md` with:
```markdown
# Embedded Pi Harness (superseded)

This plan is superseded by the implemented design:
see `docs/specs/2026-07-04-embedded-pi-sidecar-design.md`.
The app embeds upstream pi (`@earendil-works/pi-coding-agent`) via a
bun-compiled sidecar in `desktop/sidecar/`.
```

- [ ] **Step 6: Full verification + release**

```bash
cd desktop/sidecar && bun test && bunx tsc --noEmit
cd ../src-tauri && cargo test
cd .. && npx tsc --noEmit
npm run release
```
Expected: all green; release builds, bumps version, deploys to /Applications (per CLAUDE.md). Launch the installed app: model list populates from keychain-configured providers, a weather query streams status then an answer, title generation works, Stop cancels.

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "feat(desktop): bundle pi sidecar, uv runtime, and skill; remove python harness prototype"
```
