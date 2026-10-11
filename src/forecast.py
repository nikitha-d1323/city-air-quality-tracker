import pandas as pd, numpy as np, matplotlib.pyplot as plt
from statsmodels.tsa.holtwinters import ExponentialSmoothing

df = pd.read_csv("data/coimbatore_clean.csv", parse_dates=["time"], index_col="time")
s = df["pm2_5"].asfreq("h").interpolate()

# 1. Train/test split: last 7 days held out for testing
H = 7 * 24
train, test = s.iloc[:-H], s.iloc[-H:]

def metrics(y, p, name):
    mae = np.mean(np.abs(y - p))
    rmse = np.sqrt(np.mean((y - p) ** 2))
    mape = np.mean(np.abs((y - p) / y.clip(lower=1))) * 100
    print(f"{name}: MAE={mae:.2f}  RMSE={rmse:.2f}  MAPE={mape:.1f}%")
    return mae

# 2. Baseline: seasonal naive (repeat the last 24 hours)
last_day = train.iloc[-24:].values
naive = pd.Series(np.tile(last_day, 7), index=test.index)
metrics(test, naive, "Seasonal naive")

# 3. Holt-Winters (trend + 24h seasonality)
model = ExponentialSmoothing(train, trend="add", damped_trend=True,
                             seasonal="add", seasonal_periods=24).fit()
hw = model.forecast(H)
metrics(test, hw, "Holt-Winters")

# 4. Plot test period: actual vs forecasts
plt.figure(figsize=(12, 4))
test.plot(label="Actual"); hw.plot(label="Holt-Winters"); naive.plot(label="Seasonal naive", alpha=0.6)
plt.title("7-day forecast vs actual (PM2.5)"); plt.legend()
plt.tight_layout(); plt.savefig("reports/forecast_test.png", dpi=150); plt.close()

# 5. Refit on all data and forecast the next 7 days
final = ExponentialSmoothing(s, trend="add", damped_trend=True,
                             seasonal="add", seasonal_periods=24).fit()
future = final.forecast(H).clip(lower=0)
future.rename("pm2_5_forecast").to_csv("data/forecast_next7d.csv")

plt.figure(figsize=(12, 4))
s.iloc[-14 * 24:].plot(label="Recent actual"); future.plot(label="Next 7 days")
plt.title("PM2.5 forecast: next 7 days"); plt.legend()
plt.tight_layout(); plt.savefig("reports/forecast_future.png", dpi=150); plt.close()
print("Saved forecast to data/forecast_next7d.csv")