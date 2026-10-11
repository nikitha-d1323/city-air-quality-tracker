import pandas as pd, matplotlib.pyplot as plt, plotly.express as px
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller

df = pd.read_csv("data/coimbatore_clean.csv", parse_dates=["time"], index_col="time")
s = df["pm2_5"]

# 1. Hourly series with 24h rolling mean + daily average
plt.figure(figsize=(12, 4))
s.plot(alpha=0.4, label="Hourly")
s.rolling(24).mean().plot(label="24h rolling mean", linewidth=2)
plt.title("PM2.5 over time"); plt.legend()
plt.tight_layout(); plt.savefig("reports/ts_trend.png", dpi=150); plt.close()

# 2. Decomposition: trend + daily seasonality + residual
res = seasonal_decompose(s, model="additive", period=24)
res.plot().set_size_inches(12, 8)
plt.tight_layout(); plt.savefig("reports/ts_decomposition.png", dpi=150); plt.close()

# 3. Autocorrelation and partial autocorrelation
fig, ax = plt.subplots(1, 2, figsize=(13, 4))
plot_acf(s, lags=72, ax=ax[0]); plot_pacf(s, lags=48, ax=ax[1])
plt.tight_layout(); plt.savefig("reports/ts_acf_pacf.png", dpi=150); plt.close()

# 4. Lag correlations
for lag in [1, 6, 12, 24, 48]:
    print(f"Lag {lag}h correlation: {s.corr(s.shift(lag)):.2f}")

# 5. Stationarity test (ADF)
p = adfuller(s.dropna())[1]
print(f"ADF p-value: {p:.4f} ->", "stationary" if p < 0.05 else "not stationary")

# 6. Weekday vs weekend
wk = df.assign(day=df.index.day_name()).groupby("day")["pm2_5"].mean()
wk = wk.reindex(["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
wk.plot(kind="bar", figsize=(8, 4), title="Average PM2.5 by weekday")
plt.tight_layout(); plt.savefig("reports/ts_weekday.png", dpi=150); plt.close()
print(wk.round(1))

# 7. Interactive version (reused later in the dashboard)
fig = px.line(df.reset_index(), x="time", y=["pm2_5", "pm10"], title="PM2.5 and PM10 over time")
fig.write_html("reports/ts_interactive.html")
print("Saved to reports/")