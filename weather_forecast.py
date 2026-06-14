import streamlit as st
import requests
import pandas as pd
from collections import Counter

# -----------------------------
# Page setup
# -----------------------------
st.set_page_config(
    page_title="Погода в Крупках",
    page_icon="🌤️",
    layout="wide"
)

# -----------------------------
# Light, simple styling
# -----------------------------
st.markdown("""
<style>
    .stApp {
        background: #ffffff;
        color: #111111;
    }

    .block-container {
        padding-top: 1.0rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    html, body, [class*="css"] {
        font-size: 18px;
        color: #111111 !important;
    }

    h1, h2, h3, h4, h5, h6,
    p, span, label, div {
        color: #111111 !important;
        opacity: 1 !important;
    }

    .page-title {
        font-size: 42px;
        font-weight: 800;
        line-height: 1.1;
        margin-bottom: 0.15rem;
    }

    .page-subtitle {
        font-size: 18px;
        color: #444444 !important;
        margin-bottom: 1rem;
    }

    .section-title {
        font-size: 24px;
        font-weight: 800;
        margin: 0.5rem 0 0.7rem 0;
    }

    .rule {
        border-top: 1px solid #e9ecef;
        margin: 0.9rem 0 1rem 0;
    }

    .wx-wrap {
        padding: 8px 0 2px 0;
    }

    .wx-icon {
        font-size: 76px;
        line-height: 1;
        margin-bottom: 6px;
    }

    .wx-text {
        font-size: 24px;
        font-weight: 800;
        margin-bottom: 6px;
    }

    .wx-sub {
        font-size: 15px;
        color: #666666 !important;
    }

    div[data-testid="stMetric"] {
        background: #fafbfc;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 10px 12px;
    }

    div[data-testid="stMetricValue"] {
        font-size: 30px !important;
        font-weight: 800;
        color: #111111 !important;
    }

    div[data-testid="stMetricLabel"] {
        font-size: 15px !important;
        color: #444444 !important;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        overflow: hidden;
    }

    div[data-testid="stDataFrame"] * {
        font-size: 17px !important;
    }

    [data-testid="stRadio"] label,
    [data-testid="stRadio"] span {
        color: #111111 !important;
        opacity: 1 !important;
        font-size: 17px !important;
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
# WMO code mapping
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

    # По неделе: one compact summary row
    codes = daily_df["code"].tolist()
    most_common = Counter(codes).most_common(1)[0][0]
    meta = get_meta(most_common)
    view = pd.DataFrame([{
        "Период": "Ближайшая неделя",
        "Значок": meta["emoji"],
        "Погода": meta["text"],
        "Макс. °C": float(daily_df["tmax"].max()),
        "Мин. °C": float(daily_df["tmin"].min()),
        "Осадки %": float(daily_df["rain"].max()),
        "Ветер км/ч": float(daily_df["wind"].mean()),
    }])
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
st.markdown('<div class="page-subtitle">Простой вид. Крупный шрифт. Без лишней ерунды.</div>', unsafe_allow_html=True)

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
# Current weather block
# -----------------------------
left, right = st.columns([1.1, 3.2], vertical_alignment="center")

with left:
    st.markdown(f"""
    <div class="wx-wrap">
        <div class="wx-icon">{symbol_for(current_meta, symbol_style)}</div>
        <div class="wx-text">{current_meta["text"]}</div>
        <div class="wx-sub">Сейчас в Крупках</div>
    </div>
    """, unsafe_allow_html=True)

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

st.markdown(f'<div class="wx-sub">Обновлено сейчас · Код погоды: WMO {current["weather_code"]}</div>', unsafe_allow_html=True)

st.markdown('<div class="rule"></div>', unsafe_allow_html=True)

# -----------------------------
# Forecast table
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
    table_height = 140

st.dataframe(
    view_df,
    use_container_width=True,
    hide_index=True,
    height=table_height,
    column_config=col_cfg
)
