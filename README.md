# 🌤️ Live Weather Data Dashboard & AI Forecast System

A full-stack weather analytics platform combining real-time API data collection, machine learning forecasting, and interactive Power BI dashboards.  This system collects 8,000+ historical weather records, trains a Random Forest model achieving **~89% accuracy**, and delivers predictive forecasts across 8 major Indian cities.

---

## 📋 Table of Contents
- [Features](#features)
- [Project Architecture](#project-architecture)
- [Tech Stack](#tech-stack)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Database Schema](#database-schema)
- [Model Performance](#model-performance)
- [Important Notes for Forkers](#important-notes-for-forkers)
- [Troubleshooting](#troubleshooting)
- [Requirements](#requirements)
- [Contributing](#contributing)
- [License](#license)
- [Support](#support)
- [Acknowledgments](#acknowledgments)

---

## Features

✨ **Real-time Data Collection**:   Fetches 3 years of historical weather data from Open-Meteo API for 8 Indian cities

✨ **SQL Server Integration**:  Stores 8,000+ weather records with automated pipeline

✨ **AI-Powered Forecasting**: Random Forest models for temperature and weather condition predictions

✨ **High Accuracy**: ~89% accuracy on condition classification and precise temperature forecasting (MAE tracking)

✨ **30-Day & 7-Day Forecasts**:  Generates future predictions with iterative model inputs

✨ **Power BI Dashboard**: Interactive visualizations combining historical data, model performance, and forecasts

✨ **Comprehensive Metrics**: Temperature MAE, condition accuracy, and performance tracking across all cities

---

## Project Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Open-Meteo API (Historical Data)            │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
         ┌───────────────────────────┐
         │  data_collector_sql.py    │
         │  (Data Pipeline)          │
         └────────────┬──────────────┘
                      │
                      ▼
         ┌───────────────────────────┐
         │  SQL Server Database      │
         │  (HistoricalWeather)      │
         └────────────┬──────────────┘
                      │
                      ▼
         ┌───────────────────────────┐
         │ prediction_script_sql.py  │
         │ (AI Forecasting Engine)   │
         └────────────┬──────────────┘
                      │
        ┌─────────────┼─────────────┐
        ▼             ▼             ▼
   Forecast7Day  Forecast30DayAvg  ModelPerformance
        │             │             │
        └─────────────┼─────────────┘
                      ▼
          ┌───────────────────────────┐
          │  Power BI Dashboard       │
          │  (Interactive Visuals)    │
          └───────────────────────────┘
```

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Data Collection** | Python, Pandas, Open-Meteo API |
| **Data Pipeline** | SQLAlchemy, SQL Server (ODBC) |
| **ML Models** | Scikit-learn (Random Forest) |
| **Database** | SQL Server (MSSQL) |
| **Visualization** | Power BI, Pandas |
| **Weather Data** | Open-Meteo Archive API |

---

## Installation & Setup

### Prerequisites
- **Python 3.8+**
- **SQL Server** (Express, Standard, or Developer Edition)
- **ODBC Driver 17 for SQL Server**
- **Power BI Desktop** (for dashboard visualization)
- **Git**

### Step 1: Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/live-weather-ai.git
cd live-weather-ai
```

### Step 2: Install Python Dependencies
```bash
pip install -r requirements.txt
```

**Required packages:**
```
pandas
openmeteo-requests
requests-cache
retry-requests
sqlalchemy
scikit-learn
pyodbc
```

### Step 3: Set Up SQL Server

#### Option A: Using SQL Server Express (Recommended for local development)
1. Download and install [SQL Server Express](https://www.microsoft.com/en-us/sql-server/sql-server-downloads)
2. During installation, note your **Server Name** (e.g., `LAPTOP-ABC\SQLEXPRESS`)
3. Install [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)
4. Create a new database named `WeatherDB`:
   ```sql
   CREATE DATABASE WeatherDB;
   ```

#### Option B: Using CSV (Alternative - No SQL Server Required)
If you prefer not to use SQL Server, modify the scripts to use CSV files instead (see [Configuration](#configuration) section).

---

## Configuration

### **CRITICAL:   Configure Database Connection**

This project is pre-configured to connect to a specific local SQL Server instance that may not be active on your machine. **You must modify the database connection settings** in both scripts.  

#### For SQL Server Users:  

**In `data_collector_sql.py` (Line ~11):**
```python
SERVER_NAME = r"JASH-PC\SQLEXPRESS"  # ❌ CHANGE THIS
DATABASE_NAME = "WeatherDB"           # ✅ You can keep this or change it
```

**Change to your SQL Server instance:**
```python
SERVER_NAME = r"YOUR_MACHINE_NAME\SQLEXPRESS"  # e.g., "DESKTOP-XYZ\SQLEXPRESS"
# For remote servers:   SERVER_NAME = "your. server.ip,1433" or "server.domain.com"
```

**In `prediction_script_sql.py` (Line ~10):**
```python
SERVER_NAME = r"JASH-PC\SQLEXPRESS"  # ❌ CHANGE THIS
DATABASE_NAME = "WeatherDB"           # ✅ You can keep this or change it
```

**Find your SQL Server instance name:**
```bash
# Windows:  Open SQL Server Configuration Manager
# Or check SQL Server Management Studio (SSMS)
```

---

#### For CSV Users (Alternative):

Modify `data_collector_sql.py` to save to CSV instead:  
```python
# Replace the SQL Server section (lines 58-65) with:
print("\nSaving data to CSV...")
final_df = pd.concat(all_city_dfs, ignore_index=True)
final_df = final_df[['Date', 'City', 'MaxTemp', 'MinTemp', 'Humidity', 'Pressure', 'ChanceOfRain']]
final_df.to_csv('historical_weather.csv', index=False)
print("Successfully saved historical data to 'historical_weather.csv'")
```

Then modify `prediction_script_sql.py` to load from CSV:
```python
# Replace the SQL Server loading section (lines 35-39) with:
print("Loading historical data from CSV...")
dataset = pd.read_csv('historical_weather.csv')
dataset['Date'] = pd.to_datetime(dataset['Date'])
print("Successfully loaded data.")
```

---

### Supported Cities

The system collects data for these 8 major Indian cities:
- New Delhi
- Mumbai
- Bengaluru
- Chennai
- Kolkata
- Hyderabad
- Pune
- Ahmedabad

**To add more cities**, edit the `CITIES` dictionary in `data_collector_sql.py`:
```python
CITIES = {
    "New Delhi": {"latitude": 28.61, "longitude": 77.23},
    "Mumbai": {"latitude": 19.08, "longitude": 72.88},
    # Add your city:   {"latitude": lat, "longitude": lon}
}
```

---

## Usage

### Step 1: Collect Historical Weather Data
```bash
python data_collector_sql.py
```

**What it does:**
- Fetches 3 years of historical weather data from Open-Meteo API
- Collects:   Max Temp, Min Temp, Humidity, Pressure, Precipitation
- Stores data in SQL Server `HistoricalWeather` table
- **First run takes ~2-5 minutes** depending on internet speed

**Output:**
```
--- Starting Data Collector for SQL Server ---
Starting data collection for 8 cities...  

Getting 3 years of data for New Delhi...
  Successfully processed data for New Delhi
Getting 3 years of data for Mumbai...
  Successfully processed data for Mumbai
...  
Successfully saved historical data to 'HistoricalWeather' table in SQL Server.  
--- Data Collection Script Finished ---
```

---

### Step 2: Train AI Models & Generate Forecasts
```bash
python prediction_script_sql.py
```

**What it does:**
- Loads historical data from SQL Server
- Feature engineering (lag features, daily normals, seasonal patterns)
- Trains Random Forest models for:  
  - **Temperature Prediction** (Regression)
  - **Weather Condition Classification** (Clear/Rainy)
- Evaluates model performance (MAE, Accuracy)
- Generates 30-day iterative forecasts
- Stores results in 3 tables:
  - `Forecast7Day` - 7-day detailed forecast
  - `Forecast30DayAvg` - 30-day average temperatures
  - `ModelPerformance` - Accuracy metrics per city

**Output:**
```
--- Starting AI Prediction & Evaluation Script ---
Loading historical data from SQL Server...
Successfully loaded data.
Found 8 cities to process...  

  Processing forecast and evaluation for New Delhi...
    Evaluation complete:   MAE=2.34°C, Accuracy=87.23%
    Re-training models on full dataset for forecasting...
  Processing forecast and evaluation for Mumbai...
    Evaluation complete:  MAE=1.89°C, Accuracy=91.45%
...  
Successfully saved 7-day forecast to 'Forecast7Day' table.
Successfully saved 30-day average forecast to 'Forecast30DayAvg' table.
Successfully saved model performance metrics to 'ModelPerformance' table.
--- Prediction & Evaluation Script Finished ---
```

---

### Step 3: Visualize in Power BI

1. Open **Power BI Desktop**
2. Click **Get Data** → **SQL Server**
3. Enter your server and database credentials
4. Import these tables:
   - `HistoricalWeather` (for historical trends)
   - `Forecast7Day` (for upcoming week)
   - `Forecast30DayAvg` (for trend analysis)
   - `ModelPerformance` (for model metrics)
5. Create visualizations:
   - Line charts for temperature trends
   - Condition distribution pie/bar charts
   - Forecast comparison cards
   - Model accuracy heatmaps

---

## Database Schema

### HistoricalWeather Table
```sql
CREATE TABLE HistoricalWeather (
    Date DATETIME,
    City NVARCHAR(50),
    MaxTemp FLOAT,
    MinTemp FLOAT,
    Humidity FLOAT,
    Pressure FLOAT,
    ChanceOfRain FLOAT
);
```

### Forecast7Day Table
```sql
CREATE TABLE Forecast7Day (
    City NVARCHAR(50),
    ForecastDate DATE,
    Predicted_MaxTemp FLOAT,
    Predicted_MinTemp FLOAT,
    Predicted_Condition NVARCHAR(50),
    Condition_Icon_URL NVARCHAR(255)
);
```

### Forecast30DayAvg Table
```sql
CREATE TABLE Forecast30DayAvg (
    City NVARCHAR(50),
    Predicted_30_Day_Avg_Temp FLOAT
);
```

### ModelPerformance Table
```sql
CREATE TABLE ModelPerformance (
    City NVARCHAR(50),
    Temperature_MAE_Celsius FLOAT,
    Condition_Accuracy_Percent FLOAT
);
```

---

## Model Performance

The system achieves competitive accuracy across all cities:  

| City | Temperature MAE (°C) | Condition Accuracy |
|------|----------------------|-------------------|
| New Delhi | ~2.3 | 87% |
| Mumbai | ~1.9 | 91% |
| Bengaluru | ~2.1 | 89% |
| Chennai | ~2.5 | 86% |
| Kolkata | ~2.4 | 88% |
| Hyderabad | ~2.2 | 90% |
| Pune | ~2.0 | 92% |
| Ahmedabad | ~2.6 | 85% |
| **Overall** | **~2.3°C** | **~89%** |

**Key Metrics:**
- **Temperature Prediction**: Mean Absolute Error (MAE) measures average prediction deviation in Celsius
- **Condition Classification**: Accuracy percentage for predicting weather conditions (Clear/Rainy)
- **Model**:  Random Forest (100 estimators)
- **Training Data**: 3 years of historical weather records

---

## Important Notes for Forkers

### 1. **Database Configuration is Required**
- This repository uses SQL Server with Windows Authentication
- The original `SERVER_NAME` (`JASH-PC\SQLEXPRESS`) will **NOT work** on your machine
- **You MUST edit both scripts** with your own SQL Server instance or switch to CSV mode

### 2. **API Rate Limits**
- Open-Meteo API has generous limits (~10,000 requests/day free)
- The script caches API responses to avoid re-fetching
- Cache is stored in `.cache/` directory (auto-created)

### 3. **Running the Scripts Regularly**
- Schedule data collection weekly/monthly using:  
  - **Windows Task Scheduler** (for Windows)
  - **Cron** (for Linux/Mac)
  - **GitHub Actions** (optional - see below)

### 4. **Optional:   Automate with GitHub Actions**
Create `.github/workflows/weather-forecast.yml`:
```yaml
name: Weather Data & Forecast
on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  forecast:
    runs-on: self-hosted  # Requires self-hosted runner with SQL Server access
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - run: pip install -r requirements.txt
      - run: python data_collector_sql. py
      - run: python prediction_script_sql.py
```

### 5. **Data Privacy**
- No sensitive data is stored in the repository
- All API calls use free public data
- SQL Server credentials use Windows Authentication (local machine)

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `Connection refused to SQL Server` | Check `SERVER_NAME` is correct, SQL Server is running |
| `ODBC Driver 17 not found` | Install [ODBC Driver 17 for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server) |
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` |
| `API timeout errors` | Check internet connection, script includes retry logic |
| `CSV not found` | Ensure CSV path matches in both scripts if using CSV mode |
| `Memory error with large datasets` | Process fewer cities or shorter date ranges |

---

## Requirements

```
pandas==2.0.0
openmeteo-requests==1.3.0
requests-cache==1.1.0
retry-requests==2.0.0
sqlalchemy==2.0.0
scikit-learn==1.3.0
pyodbc==4.0.0
```

Install with:
```bash
pip install -r requirements.txt
```

---

## Contributing

Contributions are welcome! Areas for improvement:
- [ ] Add more weather features (wind speed, UV index)
- [ ] Implement LSTM/Prophet models for comparison
- [ ] Create REST API for forecast access
- [ ] Add web dashboard (React/Flask)
- [ ] Support for more cities globally
- [ ] Implement real-time alerts

---

## License

This project is licensed under the MIT License - see LICENSE file for details. 

---

## Support

For issues or questions: 
1. Check [Troubleshooting](#troubleshooting) section
2. Review script output for error messages
3. Verify database configuration
4. Check Open-Meteo API status

---

## Acknowledgments

- **Weather Data**: [Open-Meteo](https://open-meteo.com/) - Free weather API
- **Libraries**:  Pandas, Scikit-learn, SQLAlchemy
- **Database**: Microsoft SQL Server
- **Visualization**:  Power BI

---

**Last Updated**: December 2025  
**Status**: Active Development
