import os, requests, pandas as pd
from dotenv import load_dotenv

load_dotenv()
LAT, LON = 11.0168, 76.9558  # Coimbatore

def fetch_history(past_days=90):
    aq = requests.get("https://air-quality-api.open-meteo.com/v1/air-quality", params={
        "latitude": LAT, "longitude": LON, "past_days": past_days,
        "hourly": "pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone,us_aqi",
        "timezone": "Asia/Kolkata"}).json()["hourly"]
    wx = requests.get("https://api.open-meteo.com/v1/forecast", params={
        "latitude": LAT, "longitude": LON, "past_days": past_days,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m",
        "timezone": "Asia/Kolkata"}).json()["hourly"]
    df = pd.DataFrame(aq).merge(pd.DataFrame(wx), on="time")
    df["time"] = pd.to_datetime(df["time"])
    return df

def fetch_live_stations():
    r = requests.get("https://api.waqi.info/search/",
                     params={"token": os.getenv("WAQI_TOKEN"), "keyword": "Coimbatore"}).json()
    return pd.json_normalize(r["data"])

if __name__ == "__main__":
    fetch_history().to_csv("data/coimbatore_history.csv", index=False)
    fetch_live_stations().to_csv("data/live_stations.csv", index=False)
    print("Saved to data/")