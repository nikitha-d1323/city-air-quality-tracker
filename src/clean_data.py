import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("data/coimbatore_history.csv", parse_dates=["time"])

# 1. Drop forecast hours (keep only past/observed time)
now = pd.Timestamp.now().floor("h")
df = df[df["time"] <= now].sort_values("time").drop_duplicates("time")
df = df.set_index("time")
print("Rows:", len(df))
print("Missing values:\n", df.isna().sum())

# 2. Fill short gaps (up to 3 hours), drop the rest
df = df.interpolate(limit=3).dropna()

# 3. Detect outliers with the IQR rule
cols = ["pm2_5", "pm10", "us_aqi"]
raw = df.copy()
for c in cols:
    q1, q3 = df[c].quantile([0.25, 0.75])
    iqr = q3 - q1
    lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
    n = ((df[c] < lo) | (df[c] > hi)).sum()
    print(f"{c}: {n} outliers (bounds {lo:.1f} to {hi:.1f})")
    df[c] = df[c].clip(lo, hi)   # cap extreme values instead of deleting

# 4. Before vs after plots
fig, ax = plt.subplots(2, 2, figsize=(12, 8))
raw["pm2_5"].plot(ax=ax[0, 0], title="PM2.5 before cleaning")
df["pm2_5"].plot(ax=ax[0, 1], title="PM2.5 after cleaning")
ax[1, 0].boxplot(raw["pm2_5"].dropna()); ax[1, 0].set_title("Boxplot before")
ax[1, 1].boxplot(df["pm2_5"]); ax[1, 1].set_title("Boxplot after")
plt.tight_layout()
plt.savefig("reports/cleaning_before_after.png", dpi=150)

# 5. Save
df.to_csv("data/coimbatore_clean.csv")
print("Saved data/coimbatore_clean.csv")