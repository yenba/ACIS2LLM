# Debrief Prompt

> **For the human:** copy everything below the `---` line and paste it into the same chat that just used the `acis-weather` skill, **before clearing context**. Works in any LLM host (Claude Code, opencode, Gemini CLI, pi, etc.). The agent will write report files to `docs/field-reports/` but will not edit code or commit anything.

---

You just finished using the `acis-weather` skill (and/or the `acis2llm` Python package) to answer one or more weather queries. Before this conversation ends, write a structured debrief about how the run went so future agents can do better.

## Step 1 — Self-assess

Look back over the work you just did. Did anything in this list happen?

- A tool/function call errored or returned an unexpected shape.
- The skill docs (`SKILL.md` or anything in `skills/acis-weather/references/`) were ambiguous, contradicted the code, or were missing info you needed mid-task.
- You retried with different arguments, or you guessed and got lucky.
- You looked for a reference doc or a recipe that didn't exist.
- You returned a result that turned out to be wrong or misleading (wrong unit, wrong season window, wrong station, etc.).
- The user had to correct you, clarify the skill, or escape into raw library calls.

If **none** of those apply, the run was clean — go to Step 2A.
If **any** applies, the run had issues — go to Step 2B.

## Step 2A — Clean run

Append exactly **one line** to `docs/field-reports/log.md`, in this format:

```
- YYYY-MM-DD — query: "<one-line summary of what was asked>" — clean
```

Use today's date. Keep the query summary under ~80 chars. Do not create any other files. Stop after this step.

## Step 2B — Issues found

Do these two writes, **in this order**:

### 1. Create the report file

Path: `docs/field-reports/YYYY-MM-DD-<kebab-topic>.md`

- Use today's date.
- `<kebab-topic>` is a short kebab-case slug describing the *primary* issue (e.g. `decade-binning`, `comparison-symbols`, `missing-snow-recipe`). If a file with that exact name already exists today, append `-2` (then `-3`, etc.).

Fill in this template. Keep each section tight — a triager will skim. Omit any section that genuinely has nothing to say (except the header and *What broke*, which are required):

```markdown
# <Short title — what went wrong>

**Date:** YYYY-MM-DD
**Host:** <Claude Code / opencode / Gemini CLI / pi / other — best guess is fine>
**Model:** <model name if you know it, else "unknown">

## Query

<What the user asked, verbatim if short. Otherwise paraphrase in one or two sentences.>

## Path through the skill

<Which `references/*.md` files you loaded, in order. Which `acis2llm` / `xmacis2py` functions you called, with the args that mattered. A bulleted timeline is fine.>

## What broke

### <Issue 1 — short title>

- **Symptom:** <what you saw>
- **Expected:** <what you thought would happen>
- **Actual:** <what actually happened>
- **Recovery:** <how you got past it, or "did not recover">

### <Issue 2 — short title>

<Same shape. Add as many subsections as needed.>

## Pointers

<For each issue, point to the most relevant location with a `file:line` reference. Examples:>

- Issue 1 → `src/acis2llm/composites.py:142` (threshold parsing)
- Issue 2 → `skills/acis-weather/references/recipes.md:88` (no recipe for decade binning)

## Suggested direction

<Short prose per issue. High-level only — no diffs, no full code blocks. If you're not sure whether something is a real bug or your own confusion, **say so explicitly**. Triage signal matters more than confidence theatre.>

- Issue 1: <one or two sentences>
- Issue 2: <one or two sentences>

## Verbatim excerpts

<Paste the user/assistant/tool-result lines that show each issue concretely. Trim aggressively — keep only what a triager actually needs to see. Use fenced code blocks. If nothing here adds signal beyond what's already above, omit this whole section.>

## What worked well

<Short bullet list of things in the docs or code that were clear and helpful on this run. This prevents future agents from "improving" things that are actually fine. Optional but encouraged — even one bullet helps.>

- <e.g. "comparison alias map in `composites.py` saved a guess">
- <e.g. "`recipes.md` example for seasonal_summary was directly applicable">
```

### 2. Append to `docs/field-reports/log.md`

After the report file is written, append exactly **one line** to `docs/field-reports/log.md`:

```
- YYYY-MM-DD — query: "<one-line summary>" — issues: see <filename you just wrote>.md
```

## Hard rules

- **Do not edit** `src/acis2llm/`, `skills/acis-weather/`, or `pyproject.toml`. Debrief output goes only into `docs/field-reports/`.
- **Do not commit** anything. Leave the new files on disk; the human will review and commit.
- **Do not draft diffs or full code rewrites** in *Suggested direction*. Describe the problem and the rough fix direction in prose. Detailed fixes belong in a follow-up session.
- If the report file already exists with the same name (and you didn't create it this turn), append `-2`/`-3` to the slug instead of overwriting.
- Be honest about uncertainty. "I'm not sure if this was a bug or my misreading the docs" is more useful than a confident wrong claim.
