# Embedded pi Sidecar — Progress log

Spec: `docs/specs/2026-07-04-embedded-pi-sidecar-design.md`
Plan: `docs/plans/2026-07-05-embedded-pi-sidecar.md` (8 tasks; execute via superpowers:subagent-driven-development — briefs/reports/ledger in `.superpowers/sdd/`, gitignored)
Branch: `experiment/embedded-pi-harness`

## Status (updated 2026-07-05)

- [x] **Task 1** — sidecar scaffold, CLI parsing, `--list-models` (commits `43d5633..eea87e5`, review approved)
- [x] **Task 2** — pi agent session, JSON event forwarding, text mode (commits `eea87e5..518e70e`, review approved; live-tested against OpenRouter)
- [ ] **Task 3** — Seatbelt-sandboxed bash tool ← **NEXT**
- [ ] **Task 4** — env wiring: workspace, uv, skill sync
- [ ] **Task 5** — Keychain API key storage (Rust)
- [ ] **Task 6** — Rust spawn rewiring to sidecar
- [ ] **Task 7** — Settings UI: API keys
- [ ] **Task 8** — packaging, cleanup, `npm run release`

## Decisions & non-obvious facts a fresh session needs

- `omp` is a pi fork (`@oh-my-pi/pi-coding-agent`), which is why the frontend already speaks pi's event protocol. We embed **upstream** pi: `@earendil-works/pi-coding-agent` **0.80.3** (NOT `@mariozechner/...`, stale).
- SDK deviations from the plan discovered so far (plan code is otherwise accurate):
  - `ModelRegistry.getAvailable()` is **synchronous**.
  - Last assistant text comes from `session.getLastAssistantText()`, not `session.agent.state.messages`.
  - Provider/model selector split must be on the **first** slash (OpenRouter ids contain slashes).
- Live testing: user supplies an OpenRouter key (session-scratchpad env file, never in repo/args/logs — ask user for the key again in a new session). Test model per user instruction: **`openrouter/openrouter/free`** (OpenRouter's free router).
- Task 3 live test must trigger a real tool call — `tool_execution_start` forwarding is only unit-tested so far.
- Deferred to Task 8: audit pi's transitive deps and the two blocked bun postinstall scripts (`bun pm untrusted` in `desktop/sidecar`).
- Minor findings queue for the final whole-branch review: dead `m.name ?? m.id` fallback (models.ts); trailing bare CLI flags unvalidated (cli.ts); `any`-typed event param in run.ts subscribe.
- Version is now 0.1.21 (Task 2's agent ran `npm run release` per CLAUDE.md; harmless).
