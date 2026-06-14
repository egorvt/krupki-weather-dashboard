import streamlit as st
import requests
import pandas as pd
from collections import Counter

# -----------------------------
# Page
# -----------------------------
st.set_page_config(
    page_title="Погода в Крупках",
    page_icon="🌤️",
    layout="wide"
)

# -----------------------------
# Clean, light styling
# -----------------------------
st.markdown("""
<style>
    .stApp {
        background: #ffffff;
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    html, body, [class*="css"] {
        font-size: 18px;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #111111;
    }

    .page-title {
        font-size: 42px !important;
        font-weight: 800;
        margin-bottom: 0.15rem;
        line-height: 1.1;
    }

    .page-subtitle {
        font-size: 18px !important;
        color: #555555;
        margin-bottom: 1rem;
    }

    .panel {
        border: 1px solid #e8e8e8;
        border-radius: 16px;
        padding: 16px 18px;
        background: #ffffff;
    }

    .current-emoji {
        font-size: 72px;
        line-height: 1;
        margin: 0;
    }

    .current-text {
        font-size: 24px;
        font-weight: 800;
        margin-top: 6px;
        margin-bottom: 0;
    }

    .small-muted {
        font-size: 15px;
        color: #666666;
    }

    div[data-testid="stMetric"] {
        background: #fbfbfb;
        border: 1px solid #ededed;
        border-radius: 14px;
        padding: 12px 14px;
    }

    div[data-testid="stMetricValue"] {
        font-size: 30px !important;
        font-weight: 800;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 15px !important;
        color: #444444;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #ededed;
        border-radius: 14px;
        overflow: hidden;
    }

    div[data-testid="stDataFrame"] * {
        font-size: 17px !important;
    }

    .section-title {
        font-size: 24px;
        font-weight: 800;
        margin-top: 0.3rem;
        margin-bottom: 0.5rem;
    }

    .rule {
        border-top: 1px solid #ededed;
        margin: 0.9rem 0 1rem 0;
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

# -----------------------------
# Helpers
# -----------------------------
def get_meta(code: int):
    return WMO_CODES.get(code, {"text": "Неопределено", "emoji": "🌈", "arrow": "→"})

def symbol_for(meta: dict, mode: str) -> str:
    if mode == "Эмодзи":
        return meta["emoji"]
    if mode == "Стрелочки":
        return meta["arrow"]
    return meta["text"]

def dominant_code(series: pd.Series) -> int:
    counts = Counter(series.tolist())
    return counts.most_common(1)[0][0]

def get_weather(lat, lon):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m,weather_code",
        "hourly": "temperature_2m,apparent_temperature,relative_humidity_2m,precipitation_probability,wind_speed_10m,weather_code",
        "daily": "weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max,windspeed_10m_max",
        "timezone": TIMEZONE,
        "forecast_days": 7
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()

def build_hourly_df(raw):
    hourly = raw["hourly"]
    df = pd.DataFrame({
        "time": pd.to_datetime(hourly["time"]),
        "temp": hourly["temperature_2m"],
        "feels": hourly["apparent_temperature"],
        "humidity": hourly["relative_humidity_2m"],
        "rain": hourly["precipitation_probability"],
        "wind": hourly["wind_speed_10m"],
        "code": hourly["weather_code"],
    })
    df["meta"] = df["code"].apply(get_meta)
    df["condition"] = df["code"].apply(lambda x: get_meta(x)["text"])
    df["symbol"] = df["meta"].apply(lambda x: x["emoji"])
    df["date"] = df["time"].dt.date
    df["hour"] = df["time"].dt.hour

    def part_of_day(h):
        if 6 <= h < 12:
            return "Утро"
        if 12 <= h < 18:
            return "День"
        if 18 <= h < 24:
            return "Вечер"
        return "Ночь"

    df["part"] = df["hour"].apply(part_of_day)
    return df

def build_daily_df(raw):
    daily = raw["daily"]
    df = pd.DataFrame({
        "date": pd.to_datetime(daily["time"]),
        "code": daily["weather_code"],
        "tmax": daily["temperature_2m_max"],
        "tmin": daily["temperature_2m_min"],
        "rain": daily["precipitation_probability_max"],
        "wind": daily["windspeed_10m_max"],
    })
    df["condition"] = df["code"].apply(lambda x: get_meta(x)["text"])
    df["symbol"] = df["code"].apply(lambda x: get_meta(x)["emoji"])
    return df

def build_view(hourly_df, daily_df, granularity):
    weekday_ru = {
        0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт",
        4: "Пт", 5: "Сб", 6: "Вс"
    }

    if granularity == "Почасово":
        view = hourly_df.copy().head(24).copy()
        view["Время"] = view["time"].dt.strftime("%d.%m %H:%M")
        view["Погода"] = view["code"].apply(lambda x: get_meta(x)["text"])
        view["Значок"] = view["code"].apply(lambda x: get_meta(x)["emoji"])
        view = view[["Время", "Значок", "Погода", "temp", "feels", "rain", "wind", "humidity"]]
        view = view.rename(columns={
            "temp": "Темп.",
            "feels": "Ощущ.",
            "rain": "Осадки %",
            "wind": "Ветер км/ч",
            "humidity": "Влажн. %"
        })
        return view, {
            "Темп.": st.column_config.NumberColumn("Темп.", format="%.1f °C"),
            "Ощущ.": st.column_config.NumberColumn("Ощущ.", format="%.1f °C"),
            "Осадки %": st.column_config.NumberColumn("Осадки %", format="%d%%"),
            "Ветер км/ч": st.column_config.NumberColumn("Ветер км/ч", format="%.0f"),
            "Влажн. %": st.column_config.NumberColumn("Влажн. %", format="%d%%"),
        }

    if granularity == "Утро / день / вечер":
        view = hourly_df.copy()
        view = view[view["part"].isin(["Утро", "День", "Вечер"])].copy()
        view["День"] = view["time"].dt.strftime("%d.%m")
        agg = view.groupby(["date", "part"], as_index=False).agg({
            "temp": "mean",
            "feels": "mean",
            "rain": "max",
            "wind": "mean",
            "humidity": "mean",
            "code": dominant_code
        })
        agg["День"] = pd.to_datetime(agg["date"]).dt.strftime("%d.%m")
        agg["Погода"] = agg["code"].apply(lambda x: get_meta(x)["text"])
        agg["Значок"] = agg["code"].apply(lambda x: get_meta(x)["emoji"])
        order = pd.CategoricalDtype(["Утро", "День", "Вечер"], ordered=True)
        agg["part"] = agg["part"].astype(order)
        agg = agg.sort_values(["date", "part"])
        agg = agg[["День", "part", "Значок", "Погода", "temp", "feels", "rain", "wind", "humidity"]]
        agg = agg.rename(columns={
            "part": "Часть дня",
            "temp": "Темп.",
            "feels": "Ощущ.",
            "rain": "Осадки %",
            "wind": "Ветер км/ч",
            "humidity": "Влажн. %"
        })
        return agg, {
            "Темп.": st.column_config.NumberColumn("Темп.", format="%.1f °C"),
            "Ощущ.": st.column_config.NumberColumn("Ощущ.", format="%.1f °C"),
            "Осадки %": st.column_config.NumberColumn("Осадки %", format="%d%%"),
            "Ветер км/ч": st.column_config.NumberColumn("Ветер км/ч", format="%.1f"),
            "Влажн. %": st.column_config.NumberColumn("Влажн. %", format="%.1f%%"),
        }

    if granularity == "По дням":
        view = daily_df.copy()
        view["День"] = view["date"].dt.day_name(locale=None)  # fallback, we remap below
        view["Дата"] = view["date"].dt.strftime("%d.%m")
        view["День"] = view["date"].dt.weekday.map(weekday_ru)
        view = view[["День", "Дата", "symbol", "condition", "tmax", "tmin", "rain", "wind"]]
        view = view.rename(columns={
            "symbol": "Значок",
            "condition": "Погода",
            "tmax": "Макс. °C",
            "tmin": "Мин. °C",
            "rain": "Осадки %",
            "wind": "Ветер км/ч"
        })
        return view, {
            "Макс. °C": st.column_config.NumberColumn("Макс. °C", format="%.0f °C"),
            "Мин. °C": st.column_config.NumberColumn("Мин. °C", format="%.0f °C"),
            "Осадки %": st.column_config.NumberColumn("Осадки %", format="%d%%"),
            "Ветер км/ч": st.column_config.NumberColumn("Ветер км/ч", format="%.0f"),
        }

    # По неделе
    row = {
        "Период": "Ближайшая неделя",
        "Значок": "📅",
        "Погода": "Краткий обзор",
        "Макс. °C": float(daily_df["tmax"].mean()),
        "Мин. °C": float(daily_df["tmin"].mean()),
        "Осадки %": float(daily_df["rain"].max()),
        "Ветер км/ч": float(daily_df["wind"].mean()),
    }
    view = pd.DataFrame([row])
    return view, {
        "Макс. °C": st.column_config.NumberColumn("Макс. °C", format="%.0f °C"),
        "Мин. °C": st.column_config.NumberColumn("Мин. °C", format="%.0f °C"),
        "Осадки %": st.column_config.NumberColumn("Осадки %", format="%d%%"),
        "Ветер км/ч": st.column_config.NumberColumn("Ветер км/ч", format="%.0f"),
    }

# -----------------------------
# Header
# -----------------------------
st.markdown('<div class="page-title">Погода в Крупках</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Простой и крупный вид. Без лишней ерунды.</div>', unsafe_allow_html=True)

# Controls
c1, c2 = st.columns([1.6, 1.2])
with c1:
    granularity = st.radio(
        "Гранулярность таблицы",
        ["Почасово", "Утро / день / вечер", "По дням", "По неделе"],
        horizontal=True,
        index=2
    )
with c2:
    symbol_style = st.radio(
        "Как показывать погоду",
        ["Эмодзи", "Стрелочки", "Текст"],
        horizontal=True,
        index=0
    )

# -----------------------------
# Data fetch
# -----------------------------
with st.spinner("Загружаю погоду..."):
    try:
        raw = get_weather(LAT, LON)
    except Exception as e:
        st.error(f"Не удалось получить данные: {e}")
        st.stop()

if "current" not in raw:
    st.error("Неожиданная структура ответа от погодного сервиса.")
    st.stop()

hourly_df = build_hourly_df(raw)
daily_df = build_daily_df(raw)

current = raw["current"]
current_meta = get_meta(current["weather_code"])

# -----------------------------
# Current conditions panel
# -----------------------------
with st.container(border=True):
    left, right = st.columns([1.2, 3.0], vertical_alignment="center")

    with left:
        st.markdown(
            f'<div class="current-emoji">{symbol_for(current_meta, symbol_style)}</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="current-text">{current_meta["text"]}</div>',
            unsafe_allow_html=True
        )
        st.markdown(
            f'<div class="small-muted">Сейчас в Крупках</div>',
            unsafe_allow_html=True
        )

    with right:
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Температура", f'{current["temperature_2m"]:.1f} °C')
        with m2:
            st.metric("Ощущается", f'{current["apparent_temperature"]:.1f} °C')
        with m3:
            st.metric("Влажность", f'{current["relative_humidity_2m"]}%')
        with m4:
            st.metric("Ветер", f'{current["wind_speed_10m"]:.0f} км/ч')

        st.markdown(
            f'<div class="small-muted">Обновлено: сейчас · Код погоды: WMO {current["weather_code"]}</div>',
            unsafe_allow_html=True
        )

st.markdown('<div class="rule"></div>', unsafe_allow_html=True)

# -----------------------------
# Table section
# -----------------------------
st.markdown('<div class="section-title">Прогноз</div>', unsafe_allow_html=True)

view_df, col_cfg = build_view(hourly_df, daily_df, granularity)

if granularity == "Почасово":
    table_height = 520
elif granularity == "Утро / день / вечер":
    table_height = 480
elif granularity == "По дням":
    table_height = 360
else:
    table_height = 160

st.dataframe(
    view_df,
    use_container_width=True,
    hide_index=True,
    height=table_height,
    column_config=col_cfg
)
