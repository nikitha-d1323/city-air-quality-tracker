import pandas as pd, numpy as np

df = pd.read_csv("data/coimbatore_clean.csv", parse_dates=["time"], index_col="time")
fc = pd.read_csv("data/forecast_next7d.csv", index_col=0, parse_dates=True)

hourly = df.groupby(df.index.hour)["pm2_5"].mean()
weekday = df.groupby(df.index.day_name())["pm2_5"].mean()
corr = df.corr()["us_aqi"].drop("us_aqi").sort_values(key=abs, ascending=False)

print("Period:", df.index.min().date(), "to", df.index.max().date(), "| rows:", len(df))
print(f"Mean PM2.5: {df['pm2_5'].mean():.1f} | Max PM2.5: {df['pm2_5'].max():.1f}")
print(f"Mean AQI: {df['us_aqi'].mean():.0f}")
print(f"Peak hour: {hourly.idxmax()}:00 ({hourly.max():.1f}) | Cleanest: {hourly.idxmin()}:00 ({hourly.min():.1f})")
print(f"Peak/cleanest ratio: {hourly.max()/hourly.min():.1f}x")
print("Worst weekday:", weekday.idxmax(), "| Best weekday:", weekday.idxmin())
print(f"% hours with AQI > 100: {(df['us_aqi'] > 100).mean()*100:.1f}%")
print(f"% hours with PM2.5 above WHO 24h guideline (15): {(df['pm2_5'] > 15).mean()*100:.1f}%")
print("Top correlations with AQI:\n", corr.head(4).round(2))
print(f"Corr wind vs PM2.5: {df['wind_speed_10m'].corr(df['pm2_5']):.2f}")
print(f"Forecast next 7d: mean {fc.iloc[:,0].mean():.1f}, max {fc.iloc[:,0].max():.1f}")