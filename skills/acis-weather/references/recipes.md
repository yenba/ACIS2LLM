# Recipes — Worked end-to-end examples

Each recipe walks from a user question → station resolution → fetch → analysis → answer.

---

## 1. "What was the hottest July in NYC history?"

```python
import xmacis2py
import acis2llm

stn = acis2llm.find_best_station("10001")  # NYC ZIP — city-state strings do NOT resolve
# stn["station_id"] == "KNYC"

result = acis2llm.monthly_totals_by_year(
    station=stn["station_id"],
    parameter="tmax",
    month="july",
    aggregation="max",
)

# result["table"] is a list of {"year", "value", "missing_days"}.
# Find the hottest July by max daily high:
hottest = max(result["table"], key=lambda r: r["value"] or -999)
print(f"Hottest July high in {stn['name']}: "
      f"{hottest['value']}°F in {hottest['year']}")
```

Why `monthly_totals_by_year` with `aggregation="max"`: the user is asking about an extreme single-day high, not a monthly mean. `aggregation="mean"` would give the average July high per year — useful but a different question.

---

## 2. "How many days over 100°F did Phoenix have in 2023?"

```python
import xmacis2py
from xmacis2py import analysis

stn = acis2llm.find_best_station("85001")  # Phoenix ZIP — city-state strings do NOT resolve
df = xmacis2py.get_single_station_acis_data(
    stn["station_id"],
    start_date="2023-01-01",
    end_date="2023-12-31",
)

count = analysis.number_of_days_above_value(df, "Maximum Temperature", 100)
print(f"{stn['name']} had {count} days above 100°F in 2023.")
```

Why fetch first, then analyze: this is a single-period scalar — the xmACIS2Py threshold-count functions take a DataFrame. Use `acis2llm.frequency_of_occurrence` only when the question is *across years* (e.g. "in how many summers...").

---

## 3. "Show me the top 5 snowiest winters in Buffalo."

```python
result = acis2llm.seasonal_summary(
    station=acis2llm.find_best_station("14202")["station_id"],  # Buffalo ZIP
    parameter="snow",
    season="winter",
    aggregation="sum",
)

top5 = sorted(result["table"], key=lambda r: r["value"] or 0, reverse=True)[:5]
for row in top5:
    print(f"  Winter {row['year']}: {row['value']:.1f} in")
```

Why "winter" not "december": meteorological winter spans Dec–Feb across calendar years, and `seasonal_summary` correctly labels each by the *ending* year (Dec 2023 → Winter 2024).

---

## 4. "Is it likely to freeze in Miami during January?"

```python
result = acis2llm.frequency_of_occurrence(
    station=acis2llm.find_best_station("33101")["station_id"],  # Miami ZIP
    parameter="tmin",
    threshold=32,
    comparison="at_or_below",     # also accepts "<="
    month="january",
)

print(result["summary"])
# In January, Minimum Temperature was at_or_below 32 in 7 out of 78 years (9.0%).
```

Why `at_or_below` not `below`: 32°F is the freezing point — inclusive comparison is what the user means by "freeze". Use `below` only when the user explicitly says "below freezing" / "sub-freezing".

---

## 5. "Compare today's temperature in NYC, Boston, and Chicago"

```python
from datetime import date, timedelta
yesterday = (date.today() - timedelta(days=1)).isoformat()
df = acis2llm.fetch_stations(
    "KNYC,KBOS,KORD",
    start_date=yesterday,
    end_date=yesterday,
)

# df has a 'station' column distinguishing the rows
print(df[["station", "Date", "Maximum Temperature", "Minimum Temperature"]])
```

Why `,` not `+`: the user wants three separate readings, not one backfilled record. Use `+` only when the goal is to *extend* one station's history with another's older records.

---

## 6. "Get the longest possible record for downtown LA"

```python
stn = acis2llm.find_best_station("90013")  # downtown LA ZIP
# If a co-located older station exists, station_id will look like "KCQT+OLD_LA_ID"
# That spec is already valid — just pass it through:

df = acis2llm.fetch_stations(
    stn["station_id"],
    start_date=f"{stn['data_start']}-01-01",
    end_date="2026-04-26",
)
```

Why use the threaded ID: `find_best_station` already does the legwork of identifying that an older nearby station can backfill the modern one. You just pass `station_id` straight to `fetch_stations`.

---

## 7. Plotting — when the user asks for a chart

`xmACIS2Py` has `plot_*` helpers (`plot_precipitation_summary`,
`plot_maximum_temperature_summary`, etc.) that render PNGs to disk. They're
heavyweight and opinionated — typically faster and more flexible to plot
yourself:

```python
import matplotlib.pyplot as plt

df = xmacis2py.get_single_station_acis_data("KNYC", start_date="2024-01-01",
                                              end_date="2024-12-31")
df["Date"] = pd.to_datetime(df["Date"])
df.plot(x="Date", y=["Maximum Temperature", "Minimum Temperature"])
plt.title("KNYC daily highs and lows, 2024")
plt.savefig("knyc-2024.png")
```

If the user specifically asks for the upstream plotting style, see the
xmACIS2Py [`plot_*` documentation](https://github.com/edrewitz/xmACIS2Py/tree/main/Documentation/xmACIS2.0).


---

## 8. "Is this a record for this calendar date?"

Two approaches: the manual pattern (works now) and the helper (after `calendar_date_records` ships).

### Manual pattern

```python
import xmacis2py
import pandas as pd
import acis2llm

# Fetch the full record for KLEX (Lexington, KY)
df = acis2llm.fetch_stations(
    "KLEX",
    start_date="1898-01-01",
    end_date="2026-06-27",
)
df["Date"] = pd.to_datetime(df["Date"])
df["Precipitation"] = pd.to_numeric(df["Precipitation"], errors="coerce")

# Filter to June 9 across all years
june9 = df[(df["Date"].dt.month == 6) & (df["Date"].dt.day == 9)].copy()
june9 = june9.dropna(subset=["Precipitation"])
june9 = june9.sort_values("Precipitation", ascending=False)
june9["rank"] = range(1, len(june9) + 1)

print(f"June 9 precipitation record for KLEX ({len(june9)} years):")
print(june9[["Date", "Precipitation", "rank"]].head(5).to_string(index=False))
```

Note the parenthesized conditions in the filter — `&` binds tighter than `==` in Python.

### Using the helper

```python
import acis2llm

result = acis2llm.calendar_date_records(
    station="KLEX",
    month=6,
    day=9,
    parameter="prcp",
)

if result["is_record"]:
    print(f"NEW RECORD! {result['current_value']}\" on June 9")
else:
    print(f"Ranks #{result['current_rank']} of {result['total_years']} years")

print("Top 5:")
for entry in result["top_n"]:
    print(f"  #{entry['rank']}: {entry['year']} — {entry['value']}\"")
```

Why this matters: "is this a record for this date" is a different question from "is this the highest ever" (which `period_rankings` answers). Calendar-date records compare the same day across years, controlling for seasonality.

---

## 9. "Compare snowfall at two stations for a winter season"

```python
import xmacis2py
from xmacis2py import analysis

# Step 1: Fetch data for each station separately
df_ord = xmacis2py.get_single_station_acis_data(
    "KORD", start_date="2020-12-01", end_date="2021-02-28")
df_msp = xmacis2py.get_single_station_acis_data(
    "KMSP", start_date="2020-12-01", end_date="2021-02-28")

# Step 2: Sum snowfall for each station
total_ord = analysis.period_sum(df_ord, "Snowfall")
total_msp = analysis.period_sum(df_msp, "Snowfall")

print(f"KORD: {total_ord:.1f} in")
print(f"KMSP: {total_msp:.1f} in")
print(f"Difference: {abs(total_ord - total_msp):.1f} in")
```

Why separate fetches: `fetch_stations("KORD,KMSP", ...)` returns one combined DataFrame with a `station` column — useful for side-by-side daily comparison, but for simple aggregation (sum, mean), fetching each station separately is clearer. Never use `fetch_stations` alone and expect weather data — it's a convenience wrapper, not a replacement for `get_single_station_acis_data`.

---

## 10. "How much did temperature depart from normal?"

```python
import xmacis2py

# Option 1: Use the departures API directly
# (returns observed-minus-normal as signed deltas)
departures = xmacis2py.get_single_station_departures(
    "KSEA",
    interval="monthly",
    start_date="2021-08-01",
    end_date="2021-08-31",
)
# Column "Average Temperature Departure" has the delta in °F
# Positive = warmer than normal; negative = colder
print(departures[["Date", "Average Temperature Departure"]])

# Option 2: Fetch observations and normals separately, then subtract
obs = xmacis2py.get_single_station_acis_data("KSEA", start_date="2021-08-01", end_date="2021-08-31")
normals = xmacis2py.get_single_station_climate_normals("KSEA", interval="monthly",
    start_date="2021-08-01", end_date="2021-08-31")
# Note: normals columns are "Average Temperature", "Max Temperature", etc. — NO " Normal" suffix
```

Why `get_single_station_departures` over normals: The departures API gives you the signed delta directly — no need to fetch normals and subtract manually. Use `interval="monthly"` for monthly departures, `"daily"` for daily. The column name is `"Average Temperature Departure"` (same as the observation column naming convention).

---

## 11. "Wettest/hottest/snowiest X ever" (cross-year ranking)

```python
import acis2llm

# Wettest summer on record for Miami:
result = acis2llm.seasonal_summary(
    station="KMIA",
    parameter="prcp",           # keyword is parameter=, NOT variable=
    season="summer",
    aggregation="sum",
)

# Sort by value descending to find extremes
ranked = sorted(result["table"], key=lambda r: r["value"] or 0, reverse=True)
print("Top 5 wettest summers:")
for row in ranked[:5]:
    print(f"  Summer {row['year']}: {row['value']:.1f} in")

# For monthly extremes (e.g., snowiest January):
result = acis2llm.monthly_totals_by_year(
    station="KBUR",
    parameter="snow",           # keyword is parameter=
    month="january",
    aggregation="sum",
)
ranked = sorted(result["table"], key=lambda r: r["value"] or 0, reverse=True)
```

Why `seasonal_summary` not `monthly_totals_by_year`: Summers span June–August (one meteorological season), so `seasonal_summary` is the right tool. Use `monthly_totals_by_year` when the question targets a single calendar month. Both return `{"table": [{"year", "value", "missing_days"}, ...], "summary": str}` — sort by `"value"` to rank.

---

## 12. "Heating degree days for a month"

```python
import xmacis2py
from xmacis2py import analysis

# Fetch daily data for Minneapolis, January 1996
df = xmacis2py.get_single_station_acis_data(
    "KMSP",
    start_date="1996-01-01",
    end_date="1996-01-31",
)

# Sum heating degree days for the month
hdd = analysis.period_sum(df, "Heating Degree Days")
print(f"KMSP January 1996: {hdd} HDD")

# Compare two months
df2 = xmacis2py.get_single_station_acis_data(
    "KMSP", start_date="2019-01-01", end_date="2019-01-31")
hdd2 = analysis.period_sum(df2, "Heating Degree Days")
print(f"KMSP January 2019: {hdd2} HDD")
print(f"Difference: {hdd - hdd2} HDD")
```

Why fetch-then-analyze: Degree days (HDD, CDD, GDD) are daily observations in the ACIS DataFrame — there's no composite function for them. Fetch the date range, then use `analysis.period_sum()` for total, `analysis.period_mean()` for average. The column name is the full English name: `"Heating Degree Days"`, `"Cooling Degree Days"`, `"Growing Degree Days"`.
