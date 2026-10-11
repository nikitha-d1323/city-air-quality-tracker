import pandas as pd, seaborn as sns, matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

df = pd.read_csv("data/coimbatore_clean.csv", parse_dates=["time"], index_col="time")
pollutants = ["pm2_5", "pm10", "carbon_monoxide", "nitrogen_dioxide", "sulphur_dioxide", "ozone"]
weather = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m"]

# 1. Summary statistics
print(df[pollutants + ["us_aqi"]].describe().round(1))

# 2. Distributions (histogram + boxplot)
fig, ax = plt.subplots(2, 3, figsize=(14, 7))
for a, c in zip(ax.flat, pollutants):
    sns.histplot(df[c], kde=True, ax=a); a.set_title(c)
plt.tight_layout(); plt.savefig("reports/eda_distributions.png", dpi=150); plt.close()

plt.figure(figsize=(10, 5))
sns.boxplot(data=df[pollutants], orient="h")
plt.xscale("log"); plt.title("Pollutant spread (log scale)")
plt.tight_layout(); plt.savefig("reports/eda_boxplots.png", dpi=150); plt.close()

# 3. Correlation heatmap (pollutants vs weather)
plt.figure(figsize=(9, 7))
sns.heatmap(df[pollutants + weather + ["us_aqi"]].corr(), annot=True, fmt=".2f", cmap="coolwarm", center=0)
plt.title("Correlation heatmap")
plt.tight_layout(); plt.savefig("reports/eda_correlation.png", dpi=150); plt.close()

# 4. Scatter with regression line: wind vs PM2.5
plt.figure(figsize=(7, 5))
sns.regplot(data=df, x="wind_speed_10m", y="pm2_5", scatter_kws={"alpha": 0.3})
plt.title("Wind speed vs PM2.5")
plt.tight_layout(); plt.savefig("reports/eda_wind_vs_pm25.png", dpi=150); plt.close()

# 5. Hour-of-day pattern
df["hour"] = df.index.hour
hourly = df.groupby("hour")["pm2_5"].mean()
plt.figure(figsize=(9, 4)); hourly.plot(marker="o")
plt.title("Average PM2.5 by hour of day"); plt.xlabel("Hour"); plt.ylabel("PM2.5")
plt.tight_layout(); plt.savefig("reports/eda_hourly.png", dpi=150); plt.close()
print("Peak hour:", hourly.idxmax(), "| Cleanest hour:", hourly.idxmin())

# 6. PCA on pollutants
X = StandardScaler().fit_transform(df[pollutants].dropna())
pca = PCA().fit(X)
print("Explained variance:", pca.explained_variance_ratio_.round(2))
print(pd.DataFrame(pca.components_[:2], columns=pollutants, index=["PC1", "PC2"]).round(2))
print("Saved plots to reports/")