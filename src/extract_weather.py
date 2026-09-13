import requests
import pandas as pd
import duckdb
import time
from datetime import datetime, timedelta

# Connect to MotherDuck
con = duckdb.connect('md:')

# 1. Expanded City List (Spellings corrected for Geocoding API)
cities = [
    "Istanbul", "Izmir", "Ankara", "London", "Tokyo", "New York",
    "Beijing", "New Delhi", "Jakarta", "Moscow", "Sydney", 
    "Baku", "Tehran", "Berlin", "Stockholm"
]

# 2. Date Setup (10 Years)
end_date = (datetime.now() - timedelta(days=7)).date()
start_date = end_date - timedelta(days=3652)

weather_data = []
air_quality_data = []

print(f"Fetching 10 years of hourly data from {start_date} to {end_date}...")

for city in cities:
    print(f"Extracting {city}...")
    
    # A. Dynamic Geocoding
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
    geo_resp = requests.get(geo_url).json()
    
    if 'results' not in geo_resp:
        print(f"  Geocoding failed for {city}. Skipping.")
        continue
        
    lat = geo_resp['results'][0]['latitude']
    lon = geo_resp['results'][0]['longitude']

    # B. Weather API (Hourly)
    weather_url = (f"https://archive-api.open-meteo.com/v1/archive?"
                   f"latitude={lat}&longitude={lon}&"
                   f"start_date={start_date}&end_date={end_date}&"
                   f"hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m&"
                   f"timezone=auto")
    
    w_resp = requests.get(weather_url)
    if w_resp.status_code == 200:
        w_data = w_resp.json()
        if 'hourly' in w_data:
            w_df = pd.DataFrame(w_data['hourly'])
            w_df['city'] = city
            w_df['latitude'] = lat
            w_df['longitude'] = lon
            weather_data.append(w_df)
    else:
        print(f"  Weather API Error: {w_resp.text}")

    time.sleep(2) 

    # C. Air Quality API (Hourly)
    aq_start = max(start_date, datetime.strptime("2022-07-30", "%Y-%m-%d").date())
    aq_url = (f"https://air-quality-api.open-meteo.com/v1/air-quality?"
              f"latitude={lat}&longitude={lon}&"
              f"start_date={aq_start}&end_date={end_date}&"
              f"hourly=pm10,pm2_5,nitrogen_dioxide,european_aqi&"
              f"timezone=auto")
    
    aq_resp = requests.get(aq_url)
    if aq_resp.status_code == 200:
        aq_data = aq_resp.json()
        if 'hourly' in aq_data:
            aq_df = pd.DataFrame(aq_data['hourly'])
            aq_df['city'] = city
            aq_df['latitude'] = lat
            aq_df['longitude'] = lon
            air_quality_data.append(aq_df)
    else:
        print(f"  Air Quality API Error: {aq_resp.text}")

    print("  Sleeping for 15 seconds to respect rate limits...")
    time.sleep(15) 

# 3. Load into MotherDuck Data Warehouse
if weather_data and air_quality_data:
    final_weather = pd.concat(weather_data, ignore_index=True)
    final_aq = pd.concat(air_quality_data, ignore_index=True)
    
    print("Loading hourly raw bronze data into MotherDuck...")
    con.execute("CREATE OR REPLACE TABLE raw_weather AS SELECT * FROM final_weather")
    con.execute("CREATE OR REPLACE TABLE raw_air_quality AS SELECT * FROM final_aq")
    
    w_count = con.execute("SELECT COUNT(*) FROM raw_weather").fetchone()[0]
    aq_count = con.execute("SELECT COUNT(*) FROM raw_air_quality").fetchone()[0]
    
    print(f"Success! Inserted {w_count} rows into 'raw_weather'.")
    print(f"Success! Inserted {aq_count} rows into 'raw_air_quality'.")
else:
    print("Extraction failed. Check the error messages printed above.")