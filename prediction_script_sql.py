import pandas as pd
from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, accuracy_score
from datetime import date, timedelta
from sqlalchemy import create_engine
import urllib

print("--- Starting AI Prediction & Evaluation Script with SQL Server ---")

# --- DATABASE CONFIGURATION ---
SERVER_NAME = r"JASH-PC\SQLEXPRESS" 
DATABASE_NAME = "WeatherDB"

# --- **NEW**: ICON MAPPING ---
# Define a dictionary to map your conditions to the icon URLs
CONDITION_TO_ICON_URL = {
    'Heavy Rain': 'https://cdn.weatherapi.com/weather/64x64/day/308.png',
    'Moderate Rain': 'https://cdn.weatherapi.com/weather/64x64/day/302.png',
    'Cloudy / Light Rain': 'https://cdn.weatherapi.com/weather/64x64/day/176.png',
    'Clear/Sunny': 'https://cdn.weatherapi.com/weather/64x64/day/113.png',
}
# Define a fallback URL for any conditions not in the map
DEFAULT_ICON_URL = 'https://cdn.weatherapi.com/weather/64x64/day/113.png'


# --- SCRIPT LOGIC ---
try:
    # Create the connection string and engine
    params = urllib.parse.quote_plus(f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={SERVER_NAME};DATABASE={DATABASE_NAME};Trusted_Connection=yes;TrustServerCertificate=yes;")
    engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

    # --- 1. Load Historical Data from SQL Server ---
    print("Loading historical data from SQL Server...")
    dataset = pd.read_sql("SELECT * FROM HistoricalWeather", con=engine)
    dataset['Date'] = pd.to_datetime(dataset['Date'])
    print("Successfully loaded data.")

except Exception as e:
    print(f"An error occurred while connecting to SQL Server: {e}")
    exit()

# --- 2. Initialize lists to store final results ---
seven_day_forecasts = []
thirty_day_averages = []
model_performance_results = []

# --- 3. Get a list of unique cities ---
unique_cities = dataset['City'].unique()
print(f"Found {len(unique_cities)} cities to process...")

# --- 4. Loop through each city ---
for city in unique_cities:
    print(f"\n  Processing forecast and evaluation for {city}...")
    
    city_df = dataset[dataset['City'] == city].copy().sort_values(by='Date')
    
    if len(city_df) < 365:
        print(f"  Skipping {city}, not enough data.")
        continue

    # --- a. Feature Engineering ---
    city_df['day_of_year'] = city_df['Date'].dt.dayofyear
    daily_normals = city_df.groupby('day_of_year')[['MaxTemp', 'MinTemp']].mean().rename(columns={"MaxTemp": "Normal_MaxTemp", "MinTemp": "Normal_MinTemp"})
    city_df = city_df.merge(daily_normals, on='day_of_year', how='left')
    city_df['Lag_MaxTemp'] = city_df['MaxTemp'].shift(1)
    city_df['Lag_MinTemp'] = city_df['MinTemp'].shift(1)
    
    # Use your specified, more accurate categorization
    def categorize_weather_detailed(precipitation_mm):
        if precipitation_mm < 0.3: return 'Clear/Sunny'
        elif precipitation_mm <= 3: return 'Cloudy / Light Rain'
        elif precipitation_mm <= 25: return 'Moderate Rain'
        elif precipitation_mm > 25: return 'Heavy Rain'
        else: return 'Clear/Sunny'
    
    precip_column = 'Precipitation' if 'Precipitation' in city_df.columns else 'ChanceOfRain'
    city_df['Condition'] = city_df[precip_column].apply(categorize_weather_detailed)
    
    # Simplified categories just for the evaluation part
    def categorize_weather_simple(precipitation_mm):
        if precipitation_mm < 0.3: return 'Clear/Sunny'
        else: return 'Rainy'
    city_df['Condition_Simple'] = city_df[precip_column].apply(categorize_weather_simple)
    
    condition_mapping = {'Clear/Sunny': 0, 'Cloudy / Light Rain': 1, 'Moderate Rain': 2, 'Heavy Rain': 3}
    city_df['Condition_Num'] = city_df['Condition'].map(condition_mapping)

    city_df.dropna(inplace=True)

    # --- b. Prepare data for training and testing ---
    condition_features = ['Lag_MaxTemp', 'Lag_MinTemp', 'Normal_MaxTemp', 'Normal_MinTemp']
    X_condition = city_df[condition_features]
    y_condition_simple = city_df['Condition_Simple']

    temp_features = ['Lag_MaxTemp', 'Lag_MinTemp', 'Normal_MaxTemp', 'Normal_MinTemp', 'Condition_Num']
    X_temp = city_df[temp_features]
    y_maxtemp = city_df['MaxTemp']

    X_cond_train, X_cond_test, y_cond_train, y_cond_test = train_test_split(X_condition, y_condition_simple, test_size=0.2, random_state=42, shuffle=False)
    X_temp_train, X_temp_test, y_temp_train, y_temp_test = train_test_split(X_temp, y_maxtemp, test_size=0.2, random_state=42, shuffle=False)

    # --- c. Train Models for EVALUATION ---
    eval_maxtemp_model = RandomForestRegressor(n_estimators=100, random_state=42).fit(X_temp_train, y_temp_train)
    eval_condition_model = RandomForestClassifier(n_estimators=100, random_state=42).fit(X_cond_train, y_cond_train)

    # --- d. Make Predictions on test data ---
    temp_predictions = eval_maxtemp_model.predict(X_temp_test)
    condition_predictions = eval_condition_model.predict(X_cond_test)

    # --- e. Calculate and Store Performance Metrics ---
    mae = mean_absolute_error(y_temp_test, temp_predictions)
    accuracy = accuracy_score(y_cond_test, condition_predictions)
    model_performance_results.append({
        "City": city,
        "Temperature_MAE_Celsius": mae,
        "Condition_Accuracy_Percent": accuracy * 100
    })
    print(f"    Evaluation complete: MAE={mae:.2f}°C, Accuracy={accuracy:.2%}")

    # --- f. Re-train Models on ALL data for final forecast ---
    print("    Re-training models on full dataset for forecasting...")
    final_condition_model = RandomForestClassifier(n_estimators=100, random_state=42).fit(X_condition, city_df['Condition_Num'])
    final_maxtemp_model = RandomForestRegressor(n_estimators=100, random_state=42).fit(X_temp, y_maxtemp)
    final_mintemp_model = RandomForestRegressor(n_estimators=100, random_state=42).fit(X_temp, city_df['MinTemp'])


    # --- g. Iterative Forecasting ---
    future_predictions = []
    last_known_max = city_df['MaxTemp'].iloc[-1]
    last_known_min = city_df['MinTemp'].iloc[-1]
    reverse_condition_mapping = {v: k for k, v in condition_mapping.items()}
    
    for day in range(30):
        forecast_date = date.today() + timedelta(days=day + 1)
        day_of_year = forecast_date.timetuple().tm_yday
        if day_of_year > 365 and day_of_year not in daily_normals.index: day_of_year = 1
        elif day_of_year not in daily_normals.index: day_of_year = 365
        normal_max = daily_normals.loc[day_of_year]['Normal_MaxTemp']
        normal_min = daily_normals.loc[day_of_year]['Normal_MinTemp']
        
        condition_input_df = pd.DataFrame([[last_known_max, last_known_min, normal_max, normal_min]], columns=condition_features)
        pred_condition_num = final_condition_model.predict(condition_input_df)[0]
        
        temp_input_df = pd.DataFrame([[last_known_max, last_known_min, normal_max, normal_min, pred_condition_num]], columns=temp_features)
        pred_maxtemp = final_maxtemp_model.predict(temp_input_df)[0]
        pred_mintemp = final_mintemp_model.predict(temp_input_df)[0]
        
        # Get the text for the predicted condition
        predicted_condition_text = reverse_condition_mapping.get(pred_condition_num, 'Unknown')
        # Get the corresponding icon URL
        predicted_icon_url = CONDITION_TO_ICON_URL.get(predicted_condition_text, DEFAULT_ICON_URL)

        future_predictions.append({
            "City": city, 
            "ForecastDate": forecast_date, 
            "Predicted_MaxTemp": pred_maxtemp, 
            "Predicted_MinTemp": pred_mintemp, 
            "Predicted_Condition": predicted_condition_text,
            "Condition_Icon_URL": predicted_icon_url # NEW COLUMN
        })
        last_known_max, last_known_min = pred_maxtemp, pred_mintemp

    # --- h. Process results ---
    predictions_df = pd.DataFrame(future_predictions)
    seven_day_forecasts.append(predictions_df.head(7))
    thirty_day_averages.append({"City": city, "Predicted_30_Day_Avg_Temp": predictions_df['Predicted_MaxTemp'].mean()})

# --- 5. SAVE ALL RESULTS TO SQL SERVER ---
print("\nConnecting to SQL Server and saving all results...")
try:
    seven_day_df = pd.concat(seven_day_forecasts)
    seven_day_df.to_sql('Forecast7Day', con=engine, if_exists='replace', index=False)
    print("Successfully saved 7-day forecast to 'Forecast7Day' table.")

    thirty_day_df = pd.DataFrame(thirty_day_averages)
    thirty_day_df.to_sql('Forecast30DayAvg', con=engine, if_exists='replace', index=False)
    print("Successfully saved 30-day average forecast to 'Forecast30DayAvg' table.")

    performance_df = pd.DataFrame(model_performance_results)
    performance_df.to_sql('ModelPerformance', con=engine, if_exists='replace', index=False)
    print("Successfully saved model performance metrics to 'ModelPerformance' table.")

except Exception as e:
    print(f"An error occurred while saving results to SQL Server: {e}")

print("\n--- Prediction & Evaluation Script Finished ---")
