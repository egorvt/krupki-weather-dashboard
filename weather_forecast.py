import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="Погода в Крупках",
    page_icon="🌤️",
    layout="wide"
)

# -----------------------------
# Simple, big-font styling
# -----------------------------
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-size: 20px;
    }

    .title-big {
        font-size: 44px !important;
        font-weight: 800;
        margin-bottom: 0.2rem;
    }

    .subtitle-big {
        font-size: 22px !important;
        color: #444;
        margin-bottom: 1rem;
    }

    .weather-card {
        background: #f8f9fa;
        padding: 22px;
        border-radius: 18px;
        border: 1px solid #e9ecef;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
    }

    .big-emoji {
        font-size: 88px;
        line-height: 1;
        text-align: center;
        margin: 0;
    }

    .big-condition {
        font-size: 24px;
        font-weight: 700;
        text-align: center;
        margin-top: 8px;
    }

    .day-card {
        background: #ffffff;
        border: 1px solid #e9ecef;
        border-radius: 16px;
        padding: 18px;
        margin-bottom: 12px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.05);
    }

    .day-name {
        font-size: 24px;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .day-temp {
        font-size: 30px;
        font-weight: 800;
        margin: 6px 0;
    }

    .small-line {
        font-size: 18px;
        margin: 2px 0;
        color: #333;
    }

    div[data-testid="stMetricValue"] {
        font-size: 34px !important;
        font-weight: 800;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 18px !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Location
# -----------------------------
LAT = 54.3178
LON = 29.1374
TIMEZONE = "Europe/Minsk"

# -----------------------------
# WMO mapping
# -----------------------------
WMO_CODES = {
    0: {"text": "Ясно", "emoji": "☀️", "arrow": "↑"},
    1: {"text": "Почти ясно", "emoji": "🌤️", "arrow": "↗"},
    2: {"text": "Переменная облачность", "emoji": "⛅", "arrow": "→"},
    3: {"text": "Пасмурно", "emoji": "☁️", "arrow": "↓"},
    45: {"text": "Туман", "emoji": "🌫️", "arrow": "↓"},
    48: {"text": "Туман", "emoji": "🌫️", "arrow": "↓"},
    51: {"text": "Морось", "emoji": "🌦️", "arrow": "↘"},
    53: {"text": "Морось", "emoji": "🌧️", "arrow": "↘"},
    55: {"text": "Морось", "emoji": "🌧️", "arrow": "↘"},
    61: {"text": "Дождь", "emoji": "🌦️", "arrow": "↘"},
    63: {"text": "Дождь", "emoji": "🌧️", "arrow": "↘"},
    65: {"text": "Сильный дождь", "emoji": "⛈️", "arrow": "↓↓"},
    71: {"text": "Снег", "emoji": "🌨️", "arrow": "↘"},
    73: {"text": "Снег", "emoji": "❄️", "arrow": "↘"},
    75: {"text": "Сильный снег", "emoji": "🏔️", "arrow": "↓↓"},
    80: {"text": "Ливни", "emoji": "🌦️", "arrow": "↘"},
    81: {"text": "Ливни", "emoji": "🌧️", "arrow": "↘"},
    82: {"text": "Сильные ливни", "emoji": "⛈️", "arrow": "↓↓"},
    95: {"text": "Гроза", "emoji": "🌩️", "arrow": "⚡"},
    96: {"text": "Гроза с градом", "emoji": "⛈️", "arrow": "⚡"},
    99: {"text": "Сильная гроза", "emoji": "⛈️", "arrow": "⚡"},
}

def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,windspeed_10m_max",
        "timezone": TIMEZONE,
        "forecast_days": 3
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def get_meta(code):
    return WMO_CODES.get(code, {"text": "Погода меняется", "emoji": "🌈", "arrow": "→"})

# -----------------------------
# Header
# -----------------------------
st.markdown('<div class="title-big">🌤️ Погода в Крупках</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle-big">Простой прогноз для бабушки: крупно, понятно, без лишнего.</div>', unsafe_allow_html=True)

# Choose symbol style
symbol_style = st.radio(
    "Как показывать значки:",
    ["Эмодзи", "Стрелочки", "Текст"],
    horizontal=True
)

# -----------------------------
# Data loading
# -----------------------------
with st.spinner("Загружаю погоду..."):
    try:
        raw = get_weather(LAT, LON)
    except Exception as e:
        st.error(f"Не удалось получить погоду: {e}")
        st.stop()

if "current" not in raw or "daily" not in raw:
    st.error("Структура ответа от погодного сервиса неожиданная.")
    st.stop()

current = raw["current"]
daily = raw["daily"]

current_meta = get_meta(current["weather_code"])

# -----------------------------
# Current weather block
# -----------------------------
st.markdown('<div class="weather-card">', unsafe_allow_html=True)
col_a, col_b, col_c, col_d = st.columns([1.1, 1, 1, 1])

with col_a:
    if symbol_style == "Эмодзи":
        st.markdown(f'<div class="big-emoji">{current_meta["emoji"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="big-condition">{current_meta["text"]}</div>', unsafe_allow_html=True)
    elif symbol_style == "Стрелочки":
        st.markdown(f'<div class="big-emoji">{current_meta["arrow"]}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="big-condition">{current_meta["text"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="big-emoji">●</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="big-condition">{current_meta["text"]}</div>', unsafe_allow_html=True)

with col_b:
    st.metric("Температура", f"{current['temperature_2m']:.1f} °C")

with col_c:
    st.metric("Ощущается", f"{current['apparent_temperature']:.1f} °C")

with col_d:
    st.metric("Ветер", f"{current['wind_speed_10m']:.0f} км/ч")

st.markdown("</div>", unsafe_allow_html=True)

st.write("")
st.markdown("### Сегодня сейчас")
st.write(f"Влажность: **{current['relative_humidity_2m']}%**")

# -----------------------------
# Simple daily forecast
# -----------------------------
st.markdown("### Прогноз на 3 дня")

days = pd.DataFrame({
    "date": pd.to_datetime(daily["time"]),
    "code": daily["weather_code"],
    "tmax": daily["temperature_2m_max"],
    "tmin": daily["temperature_2m_min"],
    "rain": daily["precipitation_probability_max"],
    "wind": daily["windspeed_10m_max"]
})

weekday_ru = {
    0: "Понедельник", 1: "Вторник", 2: "Среда", 3: "Четверг",
    4: "Пятница", 5: "Суббота", 6: "Воскресенье"
}

for _, row in days.iterrows():
    meta = get_meta(int(row["code"]))
    day_name = weekday_ru[row["date"].weekday()]
    date_str = row["date"].strftime("%d.%m")

    if symbol_style == "Эмодзи":
        marker = meta["emoji"]
    elif symbol_style == "Стрелочки":
        marker = meta["arrow"]
    else:
        marker = meta["text"]

    st.markdown(f"""
    <div class="day-card">
        <div class="day-name">{day_name}, {date_str} {marker}</div>
        <div class="small-line">Состояние: <b>{meta["text"]}</b></div>
        <div class="day-temp">{row["tmax"]:.0f}° / {row["tmin"]:.0f}°</div>
        <div class="small-line">Осадки: <b>{int(row["rain"])}%</b></div>
        <div class="small-line">Ветер: <b>{row["wind"]:.0f} км/ч</b></div>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# Very simple trend chart
# -----------------------------
st.markdown("### Температура по дням")
fig = go.Figure()
fig.add_trace(go.Scatter(
    x=days["date"],
    y=days["tmax"],
    mode="lines+markers",
    name="Днём",
))
fig.add_trace(go.Scatter(
    x=days["date"],
    y=days["tmin"],
    mode="lines+markers",
    name="Ночью",
))
fig.update_layout(
    height=350,
    margin=dict(l=10, r=10, t=20, b=10),
    xaxis_title="День",
    yaxis_title="°C",
    legend_title_text=""
)
st.plotly_chart(fig, use_container_width=True)
