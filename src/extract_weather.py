import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
import duckdb
import time
from datetime import datetime, timedelta

# Configure a robust session with automatic retries
session = requests.Session()
retries = Retry(
    total=5, 
    backoff_factor=2, 
    status_forcelist=[429, 500, 502, 503, 504]
)
session.mount('https://', HTTPAdapter(max_retries=retries))

con = duckdb.connect('md:')

cities = [
    "Istanbul", "Izmir", "Ankara", "London", "Tokyo", "New York",
    "Beijing", "New Delhi", "Jakarta", "Moscow", "Sydney", 
    "Baku", "Tehran", "Berlin", "Stockholm"
]

end_date = (datetime.now() - timedelta(days=7)).date()
start_date = end_date - timedelta(days=3652)

weather_data = []
air_quality_data = []

print(f"Fetching 10 years of hourly data from {start_date} to {end_date}...", flush=True)

for city in cities:
    print(f"Extracting {city}...", flush=True)
    
    try:
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=en&format=json"
        geo_resp = session.get(geo_url, timeout=45).json()
        
        if 'results' not in geo_resp:
            print(f"  Geocoding failed for {city}. Skipping.", flush=True)
            continue
            
        lat = geo_resp['results'][0]['latitude']
        lon = geo_resp['results'][0]['longitude']

        w_url = (f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&"
                 f"start_date={start_date}&end_date={end_date}&"
                 f"hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m&timezone=auto")
        
        w_resp = session.get(w_url, timeout=90)
        if w_resp.status_code == 200 and 'hourly' in w_resp.json():
            w_df = pd.DataFrame(w_resp.json()['hourly'])
            w_df['city'], w_df['latitude'], w_df['longitude'] = city, lat, lon
            weather_data.append(w_df)

        time.sleep(3) 

        aq_start = max(start_date, datetime.strptime("2022-07-30", "%Y-%m-%d").date())
        aq_url = (f"https://air-quality-api.open-meteo.com/v1/air-quality?latitude={lat}&longitude={lon}&"
                  f"start_date={aq_start}&end_date={end_date}&"
                  f"hourly=pm10,pm2_5,nitrogen_dioxide,european_aqi&timezone=auto")
        
        aq_resp = session.get(aq_url, timeout=90)
        if aq_resp.status_code == 200 and 'hourly' in aq_resp.json():
            aq_df = pd.DataFrame(aq_resp.json()['hourly'])
            aq_df['city'], aq_df['latitude'], aq_df['longitude'] = city, lat, lon
            air_quality_data.append(aq_df)

        print("  Success. Sleeping for 15 seconds...", flush=True)
        time.sleep(15) 

    except Exception as e:
        print(f"  Connection timed out or failed for {city}: {e}", flush=True)

if weather_data and air_quality_data:
    final_weather = pd.concat(weather_data, ignore_index=True)
    final_aq = pd.concat(air_quality_data, ignore_index=True)
    
    con.execute("CREATE OR REPLACE TABLE raw_weather AS SELECT * FROM final_weather")
    con.execute("CREATE OR REPLACE TABLE raw_air_quality AS SELECT * FROM final_aq")
    
    print("Success! Data loaded into MotherDuck.", flush=True)
else:
    print("Extraction failed completely.", flush=True)