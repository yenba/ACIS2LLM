"""
ACIS Skill Edge-Case Stress Tester
===================================

Automated loop that generates realistic weather queries, tests them against
the acis-weather skill via agent() calls, reviews results for failures, and
documents findings in docs/field-reports/.

Usage (in an opencode/Claude eval cell):
    exec(read("tools/stress_test.py"))
    await run_batch()            # run one batch of 5 queries
    await run_loop(batches=3)    # run 3 batches continuously

Each batch:
  1. Generates 5 diverse weather queries via completion()
  2. Tests each query by dispatching an agent that uses the acis-weather skill
  3. Reviews each test transcript for issues via completion()
  4. Writes findings to docs/field-reports/
"""

from datetime import date
import json
import re

TODAY = date.today().isoformat()

# ---------------------------------------------------------------------------
# Query generation
# ---------------------------------------------------------------------------

QUERY_CATEGORIES = [
    "single-period stat (avg/max/min for a specific month or date range)",
    "cross-year ranking (hottest/coldest/wettest/driest month or season ever)",
    "threshold count (days above/below a value in a period)",
    "frequency of occurrence (how often does X happen in month/season)",
    "multi-station comparison (compare 2-3 cities)",
    "calendar-date record (is today's value a record for this date)",
    "climate normals or departures (what's normal, how far off)",
    "snowfall or winter-specific query (snowiest winter, snow depth, etc.)",
    "long-record or backfill scenario (oldest data for a small station)",
    "ambiguous or tricky location (ZIP code, lesser-known city, vague region)",
    "edge-case time period (partial month, current year, leap year Feb 29)",
    "trace precipitation or zero-value edge case",
    "degree days (heating, cooling, growing) query",
    "unusual phrasing (colloquial, indirect, multi-part question)",
]

GENERATE_PROMPT = """\
You are generating realistic weather queries that a normal person might ask \
an AI assistant. These will be used to stress-test the acis-weather skill \
(which answers historical US weather/climate questions using NOAA ACIS data).

Generate exactly {count} queries. Each should:
- Sound natural — the way a real person would ask, not a developer testing an API
- Cover a DIFFERENT category from this list (pick {count} different ones):
{categories}
- Use a variety of US locations (mix of major cities, smaller towns, ZIP codes, \
  airport codes like KNYC or KLAX)
- Use a variety of time periods (specific years, seasons, decades, "on record", \
  recent vs historical)
- Vary in complexity — some simple, some multi-part or ambiguous
- NOT repeat any query from this list of already-tested queries:
{prior_queries}

Return a JSON array of exactly {count} objects, each with:
- "query": the natural-language question (string)
- "category": which category from the list above it targets (string)
- "expected_difficulty": "easy" | "medium" | "hard" — your estimate of how \
  tricky this is for the skill to handle
"""

# ---------------------------------------------------------------------------
# Test execution
# ---------------------------------------------------------------------------

TEST_AGENT_PROMPT = """\
You are answering a weather question using the acis-weather skill. \
Read skill://acis-weather, then answer this question by writing and \
executing real Python code.

IMPORTANT RULES:
- You MUST read skill://acis-weather before writing any code.
- You MUST actually execute the code (use eval cells), not just show it.
- If a call fails, try to recover — but document what failed and how.
- Report the final answer AND any errors/retries that happened along the way.
- If you cannot answer, explain exactly why (missing capability, bad data, etc).

THE QUESTION:
{query}

After answering, end with a structured summary block exactly like this:

---SUMMARY---
ANSWER: <your final answer, or "COULD NOT ANSWER" if you failed>
ERRORS: <comma-separated list of errors hit, or "none">
RETRIES: <number of times you had to retry a call>
FUNCTIONS_USED: <comma-separated list of acis2llm/xmacis2py functions called>
STATION: <station ID(s) used, or "none">
---END---
"""

# ---------------------------------------------------------------------------
# Review
# ---------------------------------------------------------------------------

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {
            "type": "string",
            "enum": ["clean", "error_recovered", "error_unrecovered",
                     "wrong_answer", "missing_capability"],
            "description": "Overall outcome of the test"
        },
        "issues": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string",
                              "description": "Short title for the issue"},
                    "category": {
                        "type": "string",
                        "enum": ["api_error", "doc_gap", "wrong_api_usage",
                                 "missing_function", "data_quality",
                                 "agent_confusion", "skill_doc_unclear",
                                 "parameter_mismatch", "other"],
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                    },
                    "description": {
                        "type": "string",
                        "description": "What went wrong and why"
                    },
                    "suggestion": {
                        "type": "string",
                        "description": "How to fix or improve the skill/docs"
                    },
                    "code_pointer": {
                        "type": "string",
                        "description": "File:line reference if applicable"
                    },
                },
                "required": ["title", "category", "severity",
                             "description", "suggestion"],
            },
        },
        "what_worked": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Things in the skill/docs that worked well"
        },
        "answer_quality": {
            "type": "string",
            "enum": ["correct", "partially_correct", "incorrect",
                     "no_answer", "cannot_determine"],
        },
    },
    "required": ["status", "issues", "what_worked", "answer_quality"],
}

REVIEW_PROMPT = """\
You are reviewing the output of an AI agent that was asked a weather question \
and attempted to answer it using the acis-weather skill.

ORIGINAL QUERY: {query}
QUERY CATEGORY: {category}
EXPECTED DIFFICULTY: {difficulty}

AGENT'S FULL OUTPUT:
---
{agent_output}
---

Analyze the agent's performance:

1. Did the agent produce a correct answer?
2. Did it hit any errors? If so, were they recovered from?
3. Did it use the right API functions for this type of question?
4. Were there any gotchas in the skill docs that tripped it up?
5. Is there anything in the skill docs (SKILL.md, references/, recipes.md) that \
   could be improved to prevent this failure pattern?
6. Did the agent misuse any API (wrong parameter names, wrong return shape \
   assumptions, etc)?

For each issue found, suggest a concrete improvement — a doc clarification, \
a new gotcha entry, a missing recipe, or a code change direction.

Also note what worked well — things in the docs or code that helped the agent \
succeed. This prevents future "improvements" from breaking things that work.
"""

# ---------------------------------------------------------------------------
# Report writing
# ---------------------------------------------------------------------------

def build_report(batch_num: int, results: list[dict]) -> str:
    """Build a markdown field report from a batch of test results."""
    issues_found = any(r["review"]["issues"] for r in results)

    lines = [
        f"# Stress Test Batch {batch_num}",
        f"",
        f"**Date:** {TODAY}",
        f"**Type:** Automated edge-case stress test",
        f"**Queries tested:** {len(results)}",
        f"**Status:** {'Issues found' if issues_found else 'All clean'}",
        f"",
        f"---",
        f"",
    ]

    # Summary table
    lines.append("## Results Summary")
    lines.append("")
    lines.append("| # | Query | Category | Difficulty | Status | Answer Quality |")
    lines.append("|---|-------|----------|------------|--------|----------------|")
    for i, r in enumerate(results, 1):
        q = r["query"][:60] + ("..." if len(r["query"]) > 60 else "")
        lines.append(
            f"| {i} | {q} | {r['category']} | {r['difficulty']} "
            f"| {r['review']['status']} | {r['review']['answer_quality']} |"
        )
    lines.append("")

    # Detailed findings per query
    for i, r in enumerate(results, 1):
        lines.append(f"## Query {i}: {r['query']}")
        lines.append(f"")
        lines.append(f"**Category:** {r['category']}")
        lines.append(f"**Difficulty:** {r['difficulty']}")
        lines.append(f"**Status:** {r['review']['status']}")
        lines.append(f"**Answer Quality:** {r['review']['answer_quality']}")
        lines.append(f"")

        if r["review"]["issues"]:
            lines.append("### Issues")
            lines.append("")
            for issue in r["review"]["issues"]:
                lines.append(f"#### {issue['title']}")
                lines.append(f"")
                lines.append(f"- **Category:** {issue['category']}")
                lines.append(f"- **Severity:** {issue['severity']}")
                lines.append(f"- **Description:** {issue['description']}")
                lines.append(f"- **Suggestion:** {issue['suggestion']}")
                if issue.get("code_pointer"):
                    lines.append(f"- **Pointer:** `{issue['code_pointer']}`")
                lines.append("")

        if r["review"]["what_worked"]:
            lines.append("### What Worked")
            lines.append("")
            for item in r["review"]["what_worked"]:
                lines.append(f"- {item}")
            lines.append("")

        lines.append("---")
        lines.append("")

    # Deduplicated issue summary
    all_issues = []
    for r in results:
        for issue in r["review"]["issues"]:
            all_issues.append(issue)

    if all_issues:
        lines.append("## Consolidated Issues")
        lines.append("")
        lines.append("| Title | Category | Severity | Suggestion |")
        lines.append("|-------|----------|----------|------------|")
        seen = set()
        for issue in all_issues:
            key = issue["title"].lower().strip()
            if key not in seen:
                seen.add(key)
                lines.append(
                    f"| {issue['title']} | {issue['category']} "
                    f"| {issue['severity']} | {issue['suggestion'][:80]}... |"
                )
        lines.append("")

    return "\n".join(lines)


def build_log_entry(batch_num: int, results: list[dict],
                    filename: str) -> str:
    """Build a log.md entry for this batch."""
    issues = sum(1 for r in results if r["review"]["issues"])
    total = len(results)
    if issues == 0:
        return (f"- {TODAY} — query: \"stress-test batch {batch_num} "
                f"({total} queries)\" — clean")
    return (f"- {TODAY} — query: \"stress-test batch {batch_num} "
            f"({total} queries, {issues} with issues)\" — "
            f"issues: see {filename}")


# ---------------------------------------------------------------------------
# State management
# ---------------------------------------------------------------------------

STATE_FILE = "local://stress-test-state.md"


def parse_state(content: str) -> dict:
    """Parse the state file into a dict."""
    try:
        # Extract JSON block from markdown
        match = re.search(r"```json\n(.*?)\n```", content, re.DOTALL)
        if match:
            return json.loads(match.group(1))
    except Exception:
        pass
    return {"batch_number": 0, "prior_queries": []}


def serialize_state(state: dict) -> str:
    """Serialize state to markdown."""
    return (
        "# Stress Test State\n\n"
        "Tracks batch number and prior queries to avoid repetition.\n\n"
        "```json\n"
        f"{json.dumps(state, indent=2)}\n"
        "```\n"
    )


# ---------------------------------------------------------------------------
# Orchestration (call from eval cells)
# ---------------------------------------------------------------------------

async def run_batch(batch_size=5):
    """Run one batch of stress tests. Call from an eval cell."""
    phase("Loading state")

    # Load or init state
    try:
        state_content = read(STATE_FILE)
        state = parse_state(state_content)
    except Exception:
        state = {"batch_number": 0, "prior_queries": []}

    batch_num = state["batch_number"] + 1
    prior_queries = state["prior_queries"]

    log(f"Starting batch {batch_num} ({batch_size} queries)")

    # ---- Phase 1: Generate queries ----
    phase("Generating queries")

    categories_str = "\n".join(f"  - {c}" for c in QUERY_CATEGORIES)
    prior_str = "\n".join(f"  - {q}" for q in prior_queries[-30:]) or "  (none yet)"

    gen_prompt = GENERATE_PROMPT.format(
        count=batch_size,
        categories=categories_str,
        prior_queries=prior_str,
    )

    gen_result = completion(gen_prompt, schema={
        "type": "object",
        "properties": {
            "queries": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "category": {"type": "string"},
                        "expected_difficulty": {
                            "type": "string",
                            "enum": ["easy", "medium", "hard"],
                        },
                    },
                    "required": ["query", "category", "expected_difficulty"],
                },
            },
        },
        "required": ["queries"],
    })
    queries = gen_result["queries"]

    for q in queries:
        log(f"  [{q['expected_difficulty']}] {q['query'][:70]}")

    # ---- Phase 2: Test each query ----
    phase("Testing queries against skill")

    def make_tester(q):
        def tester():
            prompt = TEST_AGENT_PROMPT.format(query=q["query"])
            result = agent(prompt, label=f"test: {q['query'][:40]}")
            return {"query_obj": q, "output": result}
        return tester

    test_results = parallel([make_tester(q) for q in queries])

    # ---- Phase 3: Review each result ----
    phase("Reviewing results")

    def make_reviewer(tr):
        def reviewer():
            prompt = REVIEW_PROMPT.format(
                query=tr["query_obj"]["query"],
                category=tr["query_obj"]["category"],
                difficulty=tr["query_obj"]["expected_difficulty"],
                agent_output=tr["output"][:8000],  # cap for context
            )
            return completion(prompt, schema=REVIEW_SCHEMA)
        return reviewer

    reviews = parallel([make_reviewer(tr) for tr in test_results])

    # Combine into results
    results = []
    for tr, review in zip(test_results, reviews):
        results.append({
            "query": tr["query_obj"]["query"],
            "category": tr["query_obj"]["category"],
            "difficulty": tr["query_obj"]["expected_difficulty"],
            "agent_output": tr["output"],
            "review": review,
        })

    # ---- Phase 4: Document ----
    phase("Documenting findings")

    filename = f"{TODAY}-stress-test-{batch_num}.md"
    report_path = f"docs/field-reports/{filename}"
    report = build_report(batch_num, results)
    write(report_path, report)
    log(f"Report written to {report_path}")

    # Append to log
    log_entry = build_log_entry(batch_num, results, filename)
    try:
        existing_log = read("docs/field-reports/log.md")
    except Exception:
        existing_log = ""
    write("docs/field-reports/log.md", existing_log.rstrip() + "\n" + log_entry + "\n")
    log(f"Log updated")

    # Update state
    state["batch_number"] = batch_num
    state["prior_queries"].extend(q["query"] for q in queries)
    # Keep only last 50 queries to avoid prompt bloat
    state["prior_queries"] = state["prior_queries"][-50:]
    write(STATE_FILE, serialize_state(state))

    # ---- Summary ----
    phase("Batch complete")

    clean = sum(1 for r in results if r["review"]["status"] == "clean")
    issues = len(results) - clean
    total_issues = sum(len(r["review"]["issues"]) for r in results)

    print(f"\n{'='*60}")
    print(f"BATCH {batch_num} COMPLETE")
    print(f"{'='*60}")
    print(f"Queries tested:  {len(results)}")
    print(f"Clean:           {clean}")
    print(f"With issues:     {issues}")
    print(f"Total issues:    {total_issues}")
    print(f"Report:          {report_path}")
    print(f"{'='*60}\n")

    for r in results:
        status_icon = "✓" if r["review"]["status"] == "clean" else "✗"
        print(f"  {status_icon} [{r['difficulty']}] {r['query'][:65]}")
        if r["review"]["issues"]:
            for issue in r["review"]["issues"]:
                print(f"    └─ [{issue['severity']}] {issue['title']}")
    print()

    return results


async def run_loop(batches=3, batch_size=5):
    """Run multiple batches continuously."""
    all_results = []
    for i in range(batches):
        log(f"Starting batch {i+1} of {batches}")
        results = await run_batch(batch_size=batch_size)
        all_results.extend(results)

    # Final summary
    total = len(all_results)
    clean = sum(1 for r in all_results if r["review"]["status"] == "clean")
    all_issues = []
    for r in all_results:
        all_issues.extend(r["review"]["issues"])

    print(f"\n{'='*60}")
    print(f"LOOP COMPLETE — {batches} batches")
    print(f"{'='*60}")
    print(f"Total queries:   {total}")
    print(f"Clean:           {clean}")
    print(f"With issues:     {total - clean}")
    print(f"Unique issues:   {len(set(i['title'].lower() for i in all_issues))}")
    print(f"{'='*60}")

    return all_results
