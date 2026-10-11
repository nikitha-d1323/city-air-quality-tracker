import ast, requests, pandas as pd, plotly.express as px, plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output

LAT, LON = 11.0168, 76.9558
BLUE, ORANGE = "#0072B2", "#E69F00"   # colourblind-safe pair

# ---------- Data ----------
df = pd.read_csv("data/coimbatore_clean.csv", parse_dates=["time"])
fc = pd.read_csv("data/forecast_next7d.csv", index_col=0, parse_dates=True).reset_index()
fc.columns = ["time", "pm2_5_forecast"]
cmp_df = pd.read_csv("data/tn_city_comparison.csv")

st = pd.read_csv("data/live_stations.csv")
st["geo"] = st["station.geo"].apply(ast.literal_eval)
st["lat"], st["lon"] = st["geo"].str[0], st["geo"].str[1]
st["aqi_num"] = pd.to_numeric(st["aqi"], errors="coerce")
st = st[(abs(st.lat - LAT) < 0.5) & (abs(st.lon - LON) < 0.5)].dropna(subset=["aqi_num"])
st["size"] = 15

POLLUTANTS = {"PM2.5": "pm2_5", "PM10": "pm10", "NO2": "nitrogen_dioxide",
              "SO2": "sulphur_dioxide", "Ozone": "ozone", "CO": "carbon_monoxide",
              "US AQI": "us_aqi"}

def category(a):
    for limit, name, advice in [
        (50, "Good", "Air is clean. Enjoy outdoor activities."),
        (100, "Moderate", "Sensitive people should limit long outdoor exertion."),
        (150, "Unhealthy for sensitive groups", "Children, elderly and asthma patients should reduce outdoor activity."),
        (200, "Unhealthy", "Everyone should reduce prolonged outdoor exertion. Consider a mask."),
        (300, "Very unhealthy", "Avoid outdoor exercise. Wear an N95 mask outdoors.")]:
        if a <= limit: return name, advice
    return "Hazardous", "Stay indoors with windows closed."

def card(title, value, sub=""):
    return html.Div([html.Div(title, style={"fontSize": 13, "color": "#666"}),
                     html.Div(value, style={"fontSize": 28, "fontWeight": "bold"}),
                     html.Div(sub, style={"fontSize": 12, "color": "#666"})],
                    style={"flex": "1", "minWidth": 180, "padding": 14, "margin": 6,
                           "background": "white", "borderRadius": 8,
                           "boxShadow": "0 1px 4px rgba(0,0,0,.15)"})

# ---------- Static figures ----------
fc_fig = go.Figure()
recent = df.tail(14 * 24)
fc_fig.add_trace(go.Scatter(x=recent["time"], y=recent["pm2_5"], name="Recent actual", line=dict(color=BLUE)))
fc_fig.add_trace(go.Scatter(x=fc["time"], y=fc["pm2_5_forecast"], name="Forecast (7 days)", line=dict(color=ORANGE, dash="dash")))
fc_fig.update_layout(title="PM2.5 forecast: next 7 days", yaxis_title="µg/m³", template="plotly_white")

if len(st):
    map_fig = px.scatter_mapbox(st, lat="lat", lon="lon", color="aqi_num", size="size",
                                hover_name="station.name", zoom=10, height=420,
                                color_continuous_scale="YlOrRd", range_color=(0, 200),
                                labels={"aqi_num": "AQI"})
    map_fig.update_layout(mapbox_style="open-street-map", margin=dict(l=0, r=0, t=30, b=0),
                          title=f"Monitoring stations in Coimbatore ({len(st)})")
else:
    map_fig = go.Figure().update_layout(title="No live station data available")

cmp_fig = px.bar(cmp_df, x="city", y="us_aqi", color="us_aqi", color_continuous_scale="YlOrRd",
                 title="Current US AQI: Tamil Nadu cities (modelled)", template="plotly_white")

# ---------- App ----------
app = Dash(__name__)
app.title = "Coimbatore Air Quality Tracker"

app.layout = html.Div(style={"fontFamily": "Arial", "background": "#f4f6f8", "padding": 16}, children=[
    html.H2("Coimbatore Air Quality Tracker"),
    html.Div("Live readings, trends, forecast and station coverage", style={"color": "#555"}),
    dcc.Interval(id="tick", interval=10 * 60 * 1000, n_intervals=0),
    html.Div(id="live", style={"display": "flex", "flexWrap": "wrap", "marginTop": 10}),
    html.Div(id="advice", style={"padding": 12, "margin": 6, "background": "#fff8e1",
                                 "borderLeft": f"5px solid {ORANGE}", "borderRadius": 4}),
    html.Div([
        dcc.Dropdown(id="pollutant", options=[{"label": k, "value": v} for k, v in POLLUTANTS.items()],
                     value="pm2_5", clearable=False, style={"width": 220}),
        dcc.DatePickerRange(id="dates", min_date_allowed=df["time"].min().date(),
                            max_date_allowed=df["time"].max().date(),
                            start_date=df["time"].min().date(), end_date=df["time"].max().date()),
    ], style={"display": "flex", "gap": 16, "margin": "12px 6px", "flexWrap": "wrap"}),
    dcc.Graph(id="trend"),
    dcc.Graph(id="hourly"),
    dcc.Graph(figure=fc_fig),
    dcc.Graph(figure=map_fig),
    dcc.Graph(figure=cmp_fig),
    html.Div("Data: Open-Meteo / CAMS (modelled, city-level), WAQI station network (sensor readings). "
             "Coimbatore has very few official monitors, so station coverage is limited.",
             style={"fontSize": 12, "color": "#666", "margin": 8}),
])

@app.callback(Output("live", "children"), Output("advice", "children"), Input("tick", "n_intervals"))
def live(_):
    try:
        c = requests.get("https://air-quality-api.open-meteo.com/v1/air-quality",
                         params={"latitude": LAT, "longitude": LON, "current": "us_aqi,pm2_5,pm10",
                                 "timezone": "Asia/Kolkata"}, timeout=10).json()["current"]
        aqi, pm25, pm10, when = c["us_aqi"], c["pm2_5"], c["pm10"], c["time"]
    except Exception:
        last = df.iloc[-1]; aqi, pm25, pm10, when = last["us_aqi"], last["pm2_5"], last["pm10"], str(last["time"])
    cat, advice = category(aqi)
    cards = [card("Current AQI", f"{aqi:.0f}", cat), card("PM2.5", f"{pm25:.1f}", "µg/m³"),
             card("PM10", f"{pm10:.1f}", "µg/m³"), card("Updated", when[-5:], when[:10])]
    return cards, f"Health advice: {advice}"

@app.callback(Output("trend", "figure"), Output("hourly", "figure"),
              Input("pollutant", "value"), Input("dates", "start_date"), Input("dates", "end_date"))
def update(col, start, end):
    d = df[(df["time"] >= start) & (df["time"] <= pd.to_datetime(end) + pd.Timedelta(days=1))]
    label = [k for k, v in POLLUTANTS.items() if v == col][0]
    trend = px.line(d, x="time", y=col, title=f"{label} over time", template="plotly_white")
    trend.update_traces(line_color=BLUE)
    hr = d.groupby(d["time"].dt.hour)[col].mean().reset_index()
    hourly = px.bar(hr, x="time", y=col, title=f"Average {label} by hour of day",
                    labels={"time": "Hour"}, template="plotly_white")
    hourly.update_traces(marker_color=ORANGE)
    return trend, hourly

if __name__ == "__main__":
    app.run(debug=True)