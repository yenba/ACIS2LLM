prompts = [
    # Temperature Extremes & Records
    "Has {city} ever reached 110 degrees?",
    "What was the longest streak of days over 90°F in {city}?",
    "When was the last time {city} dropped below zero?",
    "What is the coldest day ever recorded in {city} in November?",
    "How many 100-degree days did {city} experience in 2023?",
    "What's the highest temperature recorded in {city} during the month of May?",
    "Did {city} break any high temperature records this past summer?",
    "When does {city} typically experience its first 90-degree day of the year?",
    "What was the lowest high temperature ever recorded in {city}?",
    "How many days stayed below freezing in {city} last winter?",
    
    # Snowfall
    "What was the total snowfall in {city} during the winter of 2010?",
    "Has {city} ever had a white Christmas? If so, when was the last one?",
    "What's the most snow {city} has ever received in a single day?",
    "What was the earliest date of measurable snowfall in {city}?",
    "How does the snowfall in {city} for 2020 compare to 2021?",
    "What is the average annual snowfall for {city}?",
    "How many days with measurable snow did {city} have last year?",
    "What was the snowiest month ever recorded in {city}?",
    "Has {city} ever received snow in October?",
    "What was the greatest snow depth recorded in {city}?",
    
    # Precipitation & Rain
    "What is the normal annual precipitation for {city}?",
    "How many days with over an inch of rain did {city} have last year?",
    "What's the most rain {city} has ever received in a 24-hour period?",
    "What was the wettest year on record for {city}?",
    "How long was the longest dry spell (no rain) in {city}?",
    "Did {city} have a wetter than normal spring this year?",
    "What is the average rainfall for {city} in April?",
    "How many consecutive days did it rain in {city} last month?",
    "What was the driest summer on record for {city}?",
    "How much precipitation did {city} get during the year 2005?",
    
    # Seasons & Normals
    "What is the average first freeze date in {city}?",
    "When is the average last spring frost in {city}?",
    "What are the normal daily high temperatures for {city} in October?",
    "How much does {city} warm up on average between March and May?",
    "What is the typical nighttime low temperature in {city} during August?",
    "Is {city} typically warmer than average in El Niño years?",
    "What was the hottest summer on record for {city}?",
    "What was the coldest winter on record for {city}?",
    "What is the average temperature in {city} for the month of September?",
    "How many days are in the typical growing season for {city}?",
    
    # Degree Days & Agriculture
    "How many cooling degree days did {city} have last July?",
    "What was the total heating degree days for {city} last winter?",
    "Does {city} accumulate more heating or cooling degree days annually?",
    "What was the base 50 growing degree day accumulation in {city} last year?",
    "How do the heating degree days in {city} for 2023 compare to the 30-year normal?",
    "What month has the highest cooling demand (CDD) in {city}?",
    
    # Anomalies & Departures
    "How far above normal were the temperatures in {city} last month?",
    "Was {city} cooler or warmer than normal during 2022?",
    "How much of a precipitation deficit did {city} have during the 2012 drought?",
    "What was the largest positive temperature anomaly for a single month in {city}?",
    "Did {city} experience any record-breaking cold departures last February?",
    
    # Decadal & Long-term Trends
    "Has the average summer temperature in {city} increased since 1980?",
    "What was the snowiest decade on record for {city}?",
    "Are 100-degree days becoming more frequent in {city}?",
    "Compare the average rainfall in {city} from 1990-2000 to 2010-2020.",
    "What year had the most extreme weather swings in {city}?",
    
    # Fun & Trivia
    "Has {city} ever recorded a temperature exactly at 0°F?",
    "What's the rarest weather event recorded in {city}'s ACIS data?",
    "Did it rain in {city} on July 4th, 1776? (Or the earliest July 4th on record)?",
    "What was the weather like in {city} on January 1, 2000?",
    "Has {city} ever had a high temperature lower than its average low?",
    
    # Monthly Deep Dives
    "What was the warmest January ever recorded in {city}?",
    "What was the coldest February ever recorded in {city}?",
    "What was the wettest March ever recorded in {city}?",
    "What was the driest April ever recorded in {city}?",
    "What was the snowiest May ever recorded in {city}?",
    "What was the hottest June ever recorded in {city}?",
    "What was the coolest July ever recorded in {city}?",
    "What was the rainiest August ever recorded in {city}?",
    "What was the driest September ever recorded in {city}?",
    "What was the earliest freeze in October for {city}?",
    "What was the warmest November ever recorded in {city}?",
    "What was the snowiest December ever recorded in {city}?",
    
    # Specific thresholds
    "How many days did the temperature fail to reach 32°F in {city} last year?",
    "How many days had a low temperature above 80°F in {city}?",
    "How many times did {city} get more than 2 inches of rain in a single day last year?",
    "How many days had at least 0.1 inches of snow in {city} last winter?",
    "What is the probability of precipitation in {city} on Halloween based on historical data?",
    
    # Comparisons
    "Was 1993 wetter than 1998 in {city}?",
    "Which was colder in {city}: the winter of 1977 or the winter of 2014?",
    "Did {city} get more snow in January or February last year?",
    
    "What is the highest minimum temperature ever recorded in {city}?",
    "What is the lowest maximum temperature ever recorded in {city}?",
    "How many days in a row did {city} stay below freezing during the 2021 polar vortex?",
    "What is the daily temperature range (high minus low) on average for {city} in spring?"
]

assert len(prompts) == 85, f"Only had {len(prompts)}"

with open("desktop/src/App.tsx", "r") as f:
    text = f.read()

target = "  ];\n\n  const DEFAULT_CITIES ="
replacement = ",\n" + ",\n".join([f'    (city: string) => `{p}`' for p in prompts]) + "\n" + target

text = text.replace(target, replacement)

with open("desktop/src/App.tsx", "w") as f:
    f.write(text)
