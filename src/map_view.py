import ast, requests, pandas as pd, folium
import plotly.express as px

CENTER = [11.0168, 76.9558]

def aqi_color(a):
    if pd.isna(a): return "#999999"
    for limit, c in [(50, "#2c7bb6"), (100, "#ffd92f"), (150, "#fc8d59"),
                     (200, "#d7191c"), (300, "#7b3294")]:
        if a <= limit: return c
    return "#4d004b"

# 1. Live stations near Coimbatore
st = pd.read_csv("data/live_stations.csv")
st["geo"] = st["station.geo"].apply(ast.literal_eval)
st["lat"], st["lon"] = st["geo"].str[0], st["geo"].str[1]
st["aqi_num"] = pd.to_numeric(st["aqi"], errors="coerce")
st = st[(abs(st.lat - CENTER[0]) < 0.5) & (abs(st.lon - CENTER[1]) < 0.5)]
print("Stations used on map:", len(st))
print(st[["station.name", "aqi_num", "lat", "lon"]])

m = folium.Map(location=CENTER, zoom_start=11, tiles="CartoDB positron")
for _, r in st.iterrows():
    label = "n/a" if pd.isna(r.aqi_num) else int(r.aqi_num)
    folium.CircleMarker(
        [r.lat, r.lon], radius=14, color="black", weight=1,
        fill=True, fill_color=aqi_color(r.aqi_num), fill_opacity=0.85,
        popup=folium.Popup(f"<b>{r['station.name']}</b><br>AQI: {label}", max_width=250),
        tooltip=f"{r['station.name']}: {label}",
    ).add_to(m)

legend = """
<div style="position:fixed;bottom:30px;left:30px;z-index:9999;background:white;
padding:10px;border:1px solid grey;font-size:13px;">
<b>AQI</b><br>
<span style="color:#2c7bb6">&#9679;</span> 0-50 Good<br>
<span style="color:#ffd92f">&#9679;</span> 51-100 Moderate<br>
<span style="color:#fc8d59">&#9679;</span> 101-150 Unhealthy (sensitive)<br>
<span style="color:#d7191c">&#9679;</span> 151-200 Unhealthy<br>
<span style="color:#7b3294">&#9679;</span> 201-300 Very unhealthy<br>
<span style="color:#999999">&#9679;</span> No data</div>"""
m.get_root().html.add_child(folium.Element(legend))
m.save("reports/coimbatore_map.html")

# 2. Compare Coimbatore with other Tamil Nadu cities (current AQI, modelled)
cities = {"Coimbatore": (11.0168, 76.9558), "Chennai": (13.0827, 80.2707),
          "Madurai": (9.9252, 78.1198), "Tiruchirappalli": (10.7905, 78.7047),
          "Salem": (11.6643, 78.1460), "Tiruppur": (11.1085, 77.3411),
          "Erode": (11.3410, 77.7172), "Tirunelveli": (8.7139, 77.7567)}
rows = []
for name, (lat, lon) in cities.items():
    r = requests.get("https://air-quality-api.open-meteo.com/v1/air-quality",
                     params={"latitude": lat, "longitude": lon,
                             "current": "us_aqi,pm2_5", "timezone": "Asia/Kolkata"}).json()["current"]
    rows.append({"city": name, "us_aqi": r["us_aqi"], "pm2_5": r["pm2_5"]})
cmp_df = pd.DataFrame(rows).sort_values("us_aqi", ascending=False)
cmp_df.to_csv("data/tn_city_comparison.csv", index=False)
print(cmp_df)

fig = px.bar(cmp_df, x="city", y="us_aqi", color="us_aqi",
             color_continuous_scale="YlOrRd", title="Current US AQI: Tamil Nadu cities")
fig.write_html("reports/tn_comparison.html")
print("Saved map and comparison to reports/")