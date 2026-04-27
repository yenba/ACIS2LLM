# acis2llm

> Agent-friendly helpers for the [xmACIS2Py](https://github.com/edrewitz/xmACIS2Py) climate library — **plus** the [`acis-weather`](skills/acis-weather/SKILL.md) skill that teaches an LLM how to use them.

`acis2llm` adds three things on top of `xmacis2py`:

1. **Station discovery** — resolve `"10001"` (ZIP) / `"KNYC"` (station ID) / `"4600 Silver Hill Rd, Washington, DC"` (street address) → ACIS station ID
2. **Multi-station fetch** — comma-aggregate (`"KNYC,KJFK"`) and plus-backfill (`"KNYC+OLDER"`) syntax
3. **Composite analyses** — seasonal/monthly aggregates and threshold frequencies, computed across many years in one call

The bulk of the value lives in [`skills/acis-weather/`](skills/acis-weather/) — a complete agent skill with an [`agentskills.io`](https://agentskills.io)-compliant `SKILL.md` and 5 reference docs covering xmACIS2Py + the helpers + worked recipes.

---

## Install

This project uses [uv](https://docs.astral.sh/uv/). [Install it first](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it.

```bash
uv pip install xmacis2py acis2llm
```

Or for one-off scripts without managing a venv:

```bash
uv run --with xmacis2py --with acis2llm python your_script.py
```

Requires Python 3.10+ and network access to `data.rcc-acis.org`, `geocoding.geo.census.gov`, and `api.zippopotam.us`. No API keys.

---

## Use the skill (the agent path)

If you're driving an LLM agent (Claude Code, Cursor, Gemini CLI, OpenCode, etc.), point it at the skill and it will know what to do:

```bash
# Copy or symlink skills/acis-weather into your client's skills directory.
# For Claude Code:
ln -s "$PWD/skills/acis-weather" ~/.claude/skills/acis-weather

# For project-scoped use, drop it under .claude/skills/ in your repo:
ln -s "$(pwd)/skills/acis-weather" /path/to/project/.claude/skills/acis-weather
```

The skill is a single `SKILL.md` (under 500 lines) plus `references/` files the agent loads on demand. See the [agentskills.io spec](https://agentskills.io/specification) for the format.

---

## Use the library directly (the human path)

```python
import xmacis2py
import acis2llm

# 1. Resolve a ZIP / station ID / street address → station metadata
stn = acis2llm.find_best_station("80202")
# {'station_id': 'KDEN', 'name': 'DENVER INTL ARPT, CO', 'data_start': 1948, ...}
# Note: "City, State" alone does not resolve — pass a ZIP, a station ID
# (e.g. "KDEN"), or a full street address.

# 2. Single-station fetch
df = xmacis2py.get_single_station_acis_data(
    stn["station_id"],
    start_date="2023-06-01",
    end_date="2023-08-31",
)

# 3. Multi-station aggregate (comma) or backfill (plus)
df = acis2llm.fetch_stations(
    "KNYC,KBOS,KORD",
    start_date="2024-06-01",
    end_date="2024-06-30",
)

# 4. Cross-year composite — "snowiest winters in Buffalo"
result = acis2llm.seasonal_summary(
    station="KBUF",
    variable="snow",
    season="winter",
    aggregation="sum",
)
top5 = sorted(result["table"], key=lambda r: r["value"] or 0, reverse=True)[:5]

# 5. Threshold frequency — "100°F+ days each summer at Phoenix"
result = acis2llm.frequency_of_occurrence(
    station="KPHX",
    variable="tmax",
    threshold=100,
    comparison=">=",          # also accepts "at_or_above"
    season="summer",
    start_year=2015,
    end_year=2023,
)
```

For the full API surface see [`skills/acis-weather/references/acis2llm-api.md`](skills/acis-weather/references/acis2llm-api.md). For end-to-end recipes see [`skills/acis-weather/references/recipes.md`](skills/acis-weather/references/recipes.md).

---

## Variables

| Short | Full xmACIS2Py column | Unit |
|---|---|---|
| `tmax` | Maximum Temperature | °F |
| `tmin` | Minimum Temperature | °F |
| `tavg` | Average Temperature | °F |
| `tdpa` | Average Temperature Departure | °F |
| `prcp` | Precipitation | inches |
| `snow` | Snowfall | inches |
| `snow_depth` | Snow Depth | inches |
| `hdd` / `cdd` / `gdd` | Heating / Cooling / Growing Degree Days | base 65/65/32°F |
| `awdb` | Average Daily Water Balance | inches |

`acis2llm`'s composite functions accept short codes; xmACIS2Py's analysis functions take the full column names. `acis2llm.VARIABLE_COLUMN_MAP` exports the mapping.

---

## Development

```bash
uv sync --extra dev
uv run pytest
```

---

## Layout

```
.
├── src/acis2llm/
│   ├── __init__.py             public API re-exports
│   ├── geocoding.py            find_best_station, geocode_census, is_zip_code
│   ├── composites.py           seasonal_summary, monthly_totals_by_year, ...
│   └── multi_station.py        fetch_stations (comma + plus syntax)
├── skills/acis-weather/
│   ├── SKILL.md                agent-facing playbook (agentskills.io v1)
│   └── references/             vendored xmACIS2Py docs + recipes + API ref
└── tests/
    ├── test_composites.py
    └── test_multi_station.py
```

---

## Credits

- Data: [Regional Climate Centers](https://www.rcc-acis.org/overview) via the Applied Climate Information System.
- Engine: [xmACIS2Py](https://github.com/edrewitz/xmACIS2Py) by Eric J. Drewitz ([@edrewitz](https://github.com/edrewitz)) — MIT-licensed. Documentation in `skills/acis-weather/references/xmacis2py-*.md` is vendored from upstream and reformatted; original copyright preserved.

**License**: MIT — see [LICENSE](LICENSE).
