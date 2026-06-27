# Field Reports — Index

Chronological, append-only log of every debriefed session that exercised the `acis-weather` skill or the `acis2llm` package. Written by the agent at the end of a session via the [debrief prompt](DEBRIEF-PROMPT.md). One line per session.

## Entry format

Clean run:

```
- YYYY-MM-DD — query: "<one-line summary>" — clean
```

Issues found (the linked file lives in this same directory):

```
- YYYY-MM-DD — query: "<one-line summary>" — issues: see YYYY-MM-DD-<kebab-topic>.md
```

When a finding gets promoted into a spec/plan/fix, **rename** the linked report file with a `RESOLVED-` prefix (e.g. `RESOLVED-2026-04-28-decade-binning.md`). Don't delete — keeps the historical "we already saw this" trail. The line in this file does not need to change.

## Log

<!-- New entries go below this line, oldest first. -->
- 2026-06-27 — query: "stress-test batch 1 (5 queries, 4 with issues)" — issues: see 2026-06-27-stress-test-1.md
- 2026-06-27 — query: "stress-test batch 2 (5 queries, 5 with issues)" — issues: see 2026-06-27-stress-test-2.md
- 2026-06-27 — query: "stress-test batch 1 (5 queries, 5 with issues)" — issues: see 2026-06-27-stress-test-1.md
