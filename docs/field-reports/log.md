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
- 2026-06-27 — query: "stress-test batch 1 (5 queries, 3 with issues)" — issues: see 2026-06-27-stress-test-1.md
- 2026-06-27 — query: "stress-test batch 2 (5 queries, 4 with issues)" — issues: see 2026-06-27-stress-test-2.md
- 2026-06-27 — query: "stress-test batch 3 (5 queries, 4 with issues)" — issues: see 2026-06-27-stress-test-3.md
- 2026-06-27 — query: "stress-test batch 1 (1 queries)" — clean
- 2026-06-27 — query: "stress-test batch 2 (1 queries)" — clean
- 2026-06-27 — query: "stress-test batch 3 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-3.md
- 2026-06-27 — query: "stress-test batch 4 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-4.md
- 2026-06-27 — query: "stress-test batch 5 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-5.md
- 2026-06-27 — query: "stress-test batch 6 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-6.md
- 2026-06-27 — query: "stress-test batch 7 (1 queries)" — clean
- 2026-06-27 — query: "stress-test batch 8 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-8.md
- 2026-06-27 — query: "stress-test batch 9 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-9.md
- 2026-06-27 — query: "stress-test batch 10 (1 queries)" — clean
- 2026-06-27 — query: "stress-test batch 11 (1 queries)" — clean
- 2026-06-27 — query: "stress-test batch 12 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-12.md
- 2026-06-27 — query: "stress-test batch 13 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-13.md
- 2026-06-27 — query: "stress-test batch 14 (1 queries)" — clean
- 2026-06-27 — query: "stress-test batch 15 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-15.md
- 2026-06-27 — query: "stress-test batch 16 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-16.md
- 2026-06-27 — query: "stress-test batch 17 (1 queries)" — clean
- 2026-06-27 — query: "stress-test batch 18 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-18.md
- 2026-06-27 — query: "stress-test batch 19 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-19.md
- 2026-06-27 — query: "stress-test batch 20 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-20.md
- 2026-06-27 — query: "stress-test batch 21 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-21.md
- 2026-06-27 — query: "stress-test batch 22 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-22.md
- 2026-06-27 — query: "stress-test batch 23 (1 queries)" — clean
- 2026-06-27 — query: "stress-test batch 24 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-24.md
- 2026-06-27 — query: "stress-test batch 25 (1 queries)" — clean
- 2026-06-27 — query: "stress-test batch 26 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-26.md
- 2026-06-27 — query: "stress-test batch 27 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-27.md
- 2026-06-27 — query: "stress-test batch 28 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-28.md
- 2026-06-27 — query: "stress-test batch 29 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-29.md
- 2026-06-27 — query: "stress-test batch 30 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-30.md
- 2026-06-27 — query: "stress-test batch 31 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-31.md
- 2026-06-27 — query: "stress-test batch 32 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-32.md
- 2026-06-27 — query: "stress-test batch 33 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-33.md
- 2026-06-27 — query: "stress-test batch 34 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-34.md
- 2026-06-27 — query: "stress-test batch 35 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-35.md
- 2026-06-27 — query: "stress-test batch 36 (1 queries)" — clean
- 2026-06-27 — query: "stress-test batch 37 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-37.md
- 2026-06-27 — query: "stress-test batch 38 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-38.md
- 2026-06-27 — query: "stress-test batch 39 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-39.md
- 2026-06-27 — query: "stress-test batch 40 (1 queries)" — clean
- 2026-06-27 — query: "stress-test batch 41 (1 queries)" — clean
- 2026-06-27 — query: "stress-test batch 42 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-42.md
- 2026-06-27 — query: "stress-test batch 43 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-43.md
- 2026-06-27 — query: "stress-test batch 44 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-44.md
- 2026-06-27 — query: "stress-test batch 45 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-45.md
- 2026-06-27 — query: "stress-test batch 46 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-46.md
- 2026-06-27 — query: "stress-test batch 47 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-47.md
- 2026-06-27 — query: "stress-test batch 48 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-48.md
- 2026-06-27 — query: "stress-test batch 49 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-49.md
- 2026-06-27 — query: "stress-test batch 50 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-50.md
- 2026-06-27 — query: "stress-test batch 51 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-51.md
- 2026-06-27 — query: "stress-test batch 52 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-52.md
- 2026-06-27 — query: "stress-test batch 53 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-53.md
- 2026-06-27 — query: "stress-test batch 54 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-54.md
- 2026-06-27 — query: "stress-test batch 55 (1 queries)" — clean
- 2026-06-27 — query: "stress-test batch 56 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-56.md
- 2026-06-27 — query: "stress-test batch 57 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-57.md
- 2026-06-27 — query: "stress-test batch 58 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-58.md
- 2026-06-27 — query: "stress-test batch 59 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-59.md
- 2026-06-27 — query: "stress-test batch 60 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-60.md
- 2026-06-27 — query: "stress-test batch 61 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-61.md
- 2026-06-27 — query: "stress-test batch 62 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-62.md
- 2026-06-27 — query: "stress-test batch 63 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-63.md
- 2026-06-27 — query: "stress-test batch 64 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-64.md
- 2026-06-27 — query: "stress-test batch 65 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-65.md
- 2026-06-27 — query: "stress-test batch 66 (1 queries)" — clean
- 2026-06-27 — query: "stress-test batch 67 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-67.md
- 2026-06-27 — query: "stress-test batch 68 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-68.md
- 2026-06-27 — query: "stress-test batch 69 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-69.md
- 2026-06-27 — query: "stress-test batch 70 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-70.md
- 2026-06-27 — query: "stress-test batch 71 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-71.md
- 2026-06-27 — query: "stress-test batch 72 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-72.md
- 2026-06-27 — query: "stress-test batch 73 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-73.md
- 2026-06-27 — query: "stress-test batch 74 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-74.md
- 2026-06-27 — query: "stress-test batch 75 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-75.md
- 2026-06-27 — query: "stress-test batch 76 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-76.md
- 2026-06-27 — query: "stress-test batch 77 (1 queries)" — clean
- 2026-06-27 — query: "stress-test batch 78 (1 queries, 1 with issues)" — issues: see 2026-06-27-stress-test-78.md
