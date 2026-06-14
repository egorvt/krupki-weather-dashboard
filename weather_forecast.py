import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime

# Page Configuration
st.set_page_config(page_title="Krupki Weather Dashboard", layout="wide")

# Modern Styling Overrides
st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 12px;
        border-left: 5px solid #0068C9;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    div[data-testid="stMetricValue"] {
        font-size: 32px !important;
        font-weight: bold;
    }
    /* Custom style for the massive emoji display */
    .giant-weather-emoji {
        font-size: 90px;
        line-height: 1;
        margin: 0;
        padding: 0;
        text-align: center;
    }
    .condition-text {
        font-size: 20px;
        font-weight: bold;
        text-align: center;
        color: #31333F;
        margin-top: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🌤️ Krupki Group Weather Telemetry")
st.markdown("High-accuracy predictive metrics using direct ECMWF/GFS weather model pipelines for Krupki, Belarus.")

# Strict Coordinates for Krupki, RB
LAT = 54.3178
LON = 29.1374

# Advanced WMO Code Mapping
WMO_CODES = {
    0: {"text": "Clear Sky", "emoji": "☀️"},
    1: {"text": "Mainly Clear", "emoji": "🌤️"},
    2: {"text": "Partly Cloudy", "emoji": "⛅️"},
    3: {"text": "Overcast", "emoji": "☁️"},
    45: {"text": "Foggy", "emoji": "🌫️"},
    48: {"text": "Depositing Rime Fog", "emoji": "🌫️"},
    51: {"text": "Light Drizzle", "emoji": "🌦️"},
    53: {"text": "Moderate Drizzle", "emoji": "🌦️"},
    55: {"text": "Dense Drizzle", "emoji": "🌧️"},
    61: {"text": "Slight Rain", "emoji": "🌦️"},
    63: {"text": "Moderate Rain", "emoji": "🌧️"},
    65: {"text": "Heavy Rain", "emoji": "⛈️"},
    71: {"text": "Slight Snowfall", "emoji": "🌨️"},
    73: {"text": "Moderate Snowfall", "emoji": "❄️"},
    75: {"text": "Heavy Snowfall", "emoji": "🏔️"},
    80: {"text": "Slight Rain Showers", "emoji": "🌦️"},
    81: {"text": "Moderate Rain Showers", "emoji": "🌧️"},
    82: {"text": "Violent Rain Showers", "emoji": "⛈️"},
    95: {"text": "Thunderstorm", "emoji": "🌩️"},
    96: {"text": "Thunderstorm with Slight Hail", "emoji": "⛈️"},
    99: {"text": "Thunderstorm with Heavy Hail", "emoji": "🚨"}
}

# Fetching Data from Open-Meteo
@st.cache_data(ttl=900)
def get_high_accuracy_weather(lat, lon):
    url = (
        f"https://open-meteo.com?"
        f"latitude={lat}&longitude={lon}"
        f"&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,wind_speed_10m,weather_code"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code"
        f"&timezone=Europe%2FMinsk&forecast_days=3"
    )
    response = requests.get(url)
    return response.json()

with st.spinner("Streaming data from Open-Meteo servers..."):
    try:
        raw_data = get_high_accuracy_weather(LAT, LON)
    except Exception as e:
        st.error(f"Failed to communicate with the data node: {e}")
        st.stop()

if "current" in raw_data:
    # --- 1. CURRENT SNAPSHOT WITH GIANT EMOJI ---
    current = raw_data["current"]
    
    # Get condition attributes from our dictionary safely
    current_code = current["weather_code"]
    condition_meta = WMO_CODES.get(current_code, {"text": "Variable Conditions", "emoji": "🌀"})
    
    st.subheader("📍 Live Telemetry Station: Krupki")
    
    # Custom 5-column layout to accommodate the big weather display cleanly
    col_img, col1, col2, col3, col4 = st.columns([1.2, 1, 1, 1, 1])

    with col_img:
        # Render the large weather emoji and condition text using secure HTML components
        st.markdown(f'<p class="giant-weather-emoji">{condition_meta["emoji"]}</p>', unsafe_allow_html=True)
        st.markdown(f'<p class="condition-text">{condition_meta["text"]}</p>', unsafe_allow_html=True)
        
    with col1:
        st.metric("Temperature", f"{current['temperature_2m']} °C", f"Feels like {current['apparent_temperature']} °C")
    with col2:
        st.metric("Weather Code", f"WMO {current_code}")
    with col3:
        st.metric("Relative Humidity", f"{current['relative_humidity_2m']}%")
    with col4:
        st.metric("Wind Velocity", f"{current['wind_speed_10m']} km/h")
        
    st.divider()
    
    # --- 2. TIMELINE PROCESSING ---
    hourly = raw_data["hourly"]
    df = pd.DataFrame({
        "Time": pd.to_datetime(hourly["time"]),
        "Temperature (°C)": hourly["temperature_2m"],
        "Feels Like (°C)": hourly["apparent_temperature"],
        "Humidity (%)": hourly["relative_humidity_2m"],
        "Precipitation Probability (%)": hourly["precipitation_probability"],
        "Wind Speed (km/h)": hourly["wind_speed_10m"],
        "ConditionCode": hourly["weather_code"]
    })
    
    # Map the text descriptions and emojis into the table columns
    df["Condition"] = df["ConditionCode"].apply(lambda x: WMO_CODES.get(x, {"text": "Unknown"})["text"])
    df["Sign"] = df["ConditionCode"].apply(lambda x: WMO_CODES.get(x, {"emoji": "❓"})["emoji"])

    # --- 3. ADVANCED GROUP VISUALIZATIONS ---
    st.subheader("📊 Cluster Visual Analytics")
    
    tab1, tab2 = st.tabs(["🌡️ Thermal Profile", "🌧️ Moisture & Velocity Index"])
    
    with tab1:
        st.markdown("#### High-Fidelity Temperature Discrepancy (Actual vs Perceived)")
        fig_thermal = go.Figure()
        fig_thermal.add_trace(go.Scatter(
            x=df["Time"], y=df["Temperature (°C)"],
            mode='lines+markers', name='Actual Temp',
            line=dict(color='#FF4B4B', width=3),
            hovertemplate='%{y}°C'
        ))
        fig_thermal.add_trace(go.Scatter(
            x=df["Time"], y=df["Feels Like (°C)"],
            mode='lines', name='Perceived Comfort',
            line=dict(color='#0068C9', width=2, dash='dot'),
            hovertemplate='%{y}°C'
        ))
        fig_thermal.update_layout(
            hovermode="x unified",
            xaxis_title="Timeline",
            yaxis_title="Scale (°C)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig_thermal, use_container_width=True)

    with tab2:
        col_c1, col_c2 = st.columns(2)
        
        with col_c1:
            st.markdown("#### Precipitation Risk Projections")
            fig_precip = px.area(
                df, x="Time", y="Precipitation Probability (%)",
                color_discrete_sequence=["#1A73E8"],
                markers=True
            )
            fig_precip.update_layout(yaxis_range=[0, 105], margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_precip, use_container_width=True)
            
        with col_c2:
            st.markdown("#### Group Dynamics Wind Assessment")
            fig_wind = px.bar(
                df, x="Time", y="Wind Speed (km/h)",
                color="Wind Speed (km/h)",
                color_continuous_scale="Purples"
            )
            fig_wind.update_layout(margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_wind, use_container_width=True)

    st.divider()

    # --- 4. RAW MATRIX FOR EXPORT ---
    st.subheader("📋 Chronological Weather Log Matrix")
    
    # Reordering and prepping clean presentation columns
    display_df = df.copy()
    display_df["Time"] = display_df["Time"].dt.strftime('%a %b %d, %H:%M')
    
    # Merge Sign + Condition for slick display row (e.g., "☀️ Clear Sky")
    display_df["Forecast status"] = display_df["Sign"] + " " + display_df["Condition"]
    display_df = display_df.drop(columns=["ConditionCode", "Condition", "Sign"])
        
        # Put status column upfront
    cols = ['Forecast status'] + [col for col in display_df.columns if col != 'Forecast status']
    display_df = display_df[cols]
        
    st.dataframe(
        display_df.set_index("Time"),
        column_config={
            "Temperature (°C)": st.column_config.NumberColumn(format="%.1f °C"),
            "Feels Like (°C)": st.column_config.NumberColumn(format="%.1f °C"),
            "Humidity (%)": st.column_config.NumberColumn(format="%d%%"),
            "Precipitation Probability (%)": st.column_config.NumberColumn(format="%d%%"),
            "Wind Speed (km/h)": st.column_config.NumberColumn(format="%.1f km/h"),
        },
        use_container_width=True
    )
else:
     st.error("Encountered unexpected dataset schema from weather array node.")