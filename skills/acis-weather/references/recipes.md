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
