import pandas as pd
import openmeteo_requests
import requests_cache
from retry_requests import retry
from datetime import date, timedelta
from sqlalchemy import create_engine
import urllib

print("--- Starting Data Collector for SQL Server ---")

# --- DATABASE CONFIGURATION ---
SERVER_NAME = r"JASH-PC\SQLEXPRESS"
DATABASE_NAME = "WeatherDB"

# --- API CONFIGURATION ---
CITIES = {
    "New Delhi": {"latitude": 28.61, "longitude": 77.23},
    "Mumbai": {"latitude": 19.08, "longitude": 72.88},
    "Bengaluru": {"latitude": 12.97, "longitude": 77.59},
    "Chennai": {"latitude": 13.08, "longitude": 80.27},
    "Kolkata": {"latitude": 22.57, "longitude": 88.36},
    "Hyderabad": {"latitude": 17.38, "longitude": 78.48},
    "Pune": {"latitude": 18.52, "longitude": 73.86},
    "Ahmedabad": {"latitude": 23.02, "longitude": 72.57}
}
end_date = date.today() - timedelta(days=1)
start_date = end_date - timedelta(days=1094) # 3 years
START_DATE_STR = start_date.strftime("%Y-%m-%d")
END_DATE_STR = end_date.strftime("%Y-%m-%d")

# --- SCRIPT LOGIC ---
# Setup the Open-Meteo API client
cache_session = requests_cache.CachedSession('.cache', expire_after=-1)
retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
openmeteo = openmeteo_requests.Client(session=retry_session)

all_city_dfs = []

print(f"Starting data collection for {len(CITIES)} cities...")

for city_name, coords in CITIES.items():
    print(f"\nGetting 3 years of data for {city_name}...")
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = { "latitude": coords["latitude"], "longitude": coords["longitude"], "start_date": START_DATE_STR, "end_date": END_DATE_STR, "daily": ["temperature_2m_max", "temperature_2m_min", "relative_humidity_2m_mean", "surface_pressure_mean", "precipitation_sum"], "timezone": "auto" }
    responses = openmeteo.weather_api(url, params=params)
    response = responses[0]
    daily = response.Daily()
    data = { "MaxTemp": daily.Variables(0).ValuesAsNumpy(), "MinTemp": daily.Variables(1).ValuesAsNumpy(), "Humidity": daily.Variables(2).ValuesAsNumpy(), "Pressure": daily.Variables(3).ValuesAsNumpy(), "ChanceOfRain": daily.Variables(4).ValuesAsNumpy() }
    city_df = pd.DataFrame(data=data)
    date_range = pd.date_range(start=START_DATE_STR, end=END_DATE_STR, freq='D')
    city_df['Date'] = date_range
    city_df["City"] = city_name
    all_city_dfs.append(city_df)
    print(f"  Successfully processed data for {city_name}")

# --- SAVE THE DATA TO SQL SERVER ---
print("\nConnecting to SQL Server and saving data...")
final_df = pd.concat(all_city_dfs, ignore_index=True)
final_df = final_df[['Date', 'City', 'MaxTemp', 'MinTemp', 'Humidity', 'Pressure', 'ChanceOfRain']]

try:
    # Create the connection string for Windows Authentication
    params = urllib.parse.quote_plus(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER_NAME};DATABASE={DATABASE_NAME};Trusted_Connection=yes;TrustServerCertificate=yes;")
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

    # Write the DataFrame to a SQL table named 'HistoricalWeather'
    final_df.to_sql('HistoricalWeather', con=engine, if_exists='replace', index=False)
    
    print("Successfully saved historical data to 'HistoricalWeather' table in SQL Server.")

except Exception as e:
    print(f"An error occurred while connecting to SQL Server: {e}")

print("\n--- Data Collection Script Finished ---")
