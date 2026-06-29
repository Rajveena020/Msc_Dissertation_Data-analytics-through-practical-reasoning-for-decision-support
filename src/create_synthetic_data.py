# ============================================================
# create_synthetic_data.py
# Creates synthetic datasets for CC-BY-NC and CC-BY-SA scenarios
# ============================================================

import pandas as pd
import numpy as np
import os

np.random.seed(42)

# NHS Admissions (CC-BY-NC) 
nhs_data = {
    "admission_id": range(1001, 1101),
    "hospital_code": np.random.choice(
        ["RJ1", "RQM", "RRV", "RYJ", "RAX"], 100),
    "admission_date": pd.date_range(
        start="2025-01-01", periods=100, freq="3D").strftime("%Y-%m-%d"),
    "diagnosis_code": np.random.choice(
        ["J45", "I10", "E11", "J44", "F32"], 100),
    "length_of_stay_days": np.random.randint(1, 14, 100),
    "region": np.random.choice(
        ["London", "South East", "South West",
         "East of England", "Midlands"], 100),
    "age_group": np.random.choice(
        ["0-17", "18-34", "35-54", "55-74", "75+"], 100),
    "admission_type": np.random.choice(
        ["Emergency", "Elective", "Maternity"], 100),
}

nhs_df = pd.DataFrame(nhs_data)
nhs_path = os.path.join("data", "nhs_admissions.csv")
nhs_df.to_csv(nhs_path, index=False)
print(f"Created: {nhs_path} ({len(nhs_df)} rows)")

# Met Office Weather (CC-BY-SA) 
weather_data = {
    "station_id": np.random.choice(
        ["WS001", "WS002", "WS003", "WS004", "WS005"], 100),
    "date": pd.date_range(
        start="2025-01-01", periods=100, freq="D").strftime("%Y-%m-%d"),
    "region": np.random.choice(
        ["London", "South East", "South West",
         "East of England", "Midlands"], 100),
    "max_temp_c": np.round(np.random.uniform(2, 32, 100), 1),
    "min_temp_c": np.round(np.random.uniform(-2, 20, 100), 1),
    "rainfall_mm": np.round(np.random.uniform(0, 25, 100), 1),
    "wind_speed_kmh": np.round(np.random.uniform(5, 80, 100), 1),
    "humidity_pct": np.random.randint(40, 95, 100),
    "sunshine_hours": np.round(np.random.uniform(0, 12, 100), 1),
}

weather_data["max_temp_c"] = np.where(
    weather_data["max_temp_c"] < weather_data["min_temp_c"],
    weather_data["min_temp_c"] + 2,
    weather_data["max_temp_c"]
)

weather_df = pd.DataFrame(weather_data)
weather_path = os.path.join("data", "met_office_weather.csv")
weather_df.to_csv(weather_path, index=False)
print(f"Created: {weather_path} ({len(weather_df)} rows)")

print("\nDone! Both synthetic datasets created successfully.")
print("Licence notes:")
print("  nhs_admissions.csv    - synthetic data, CC-BY-NC licence")
print("  met_office_weather.csv - synthetic data, CC-BY-SA licence")