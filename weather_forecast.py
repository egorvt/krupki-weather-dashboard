import streamlit as st
import requests
import pandas as pd
from collections import Counter

# -----------------------------
# Page config
# -----------------------------
st.set_page_config(
    page_title="Погода в Крупках",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# Light, clean styling
# -----------------------------
st.markdown("""
<style>
    /* Hide Streamlit top bar / header */
    header[data-testid="stHeader"] {
        display: none !important;
    }
    [data-testid="stToolbar"] {
        display: none !important;
    }
    #MainMenu {
        visibility: hidden !important;
    }
    footer {
        visibility: hidden !important;
    }

    /* Force white page */
    .stApp {
        background: #ffffff !important;
        color: #111111 !important;
    }

    .block-container {
        padding-top: 0.8rem;
        padding-bottom: 1.5rem;
        max-width: 1200px;
        background: #ffffff !important;
    }

    html, body, [class*="css"] {
        font-size: 18px;
        color: #111111 !important;
        background: #ffffff !important;
    }

    /* Make all text visible on white */
    h1, h2, h3, h4, h5, h6,
    p, span, label, div {
        color: #111111 !important;
        opacity: 1 !important;
    }

    .page-title {
        font-size: 42px;
        font-weight: 800;
        line-height: 1.05;
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

    /* Metrics */
    div[data-testid="stMetric"] {
        background: #fafbfc !important;
        border: 1px solid #e5e7eb !important;
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

    /* Force dataframe white */
    div[data-testid="stDataFrame"],
    div[data-testid="stDataFrame"] div,
    div[data-testid="stDataFrame"] section,
    div[data-testid="stDataFrame"] [role="table"] {
        background: #ffffff !important;
        color: #111111 !important;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid #e5e7eb !important;
        border-radius: 14px;
        overflow: hidden;
    }

    div[data-testid="stDataFrame"] * {
        font-size: 17px !important;
        color: #111111 !important;
    }

    /* Radio */
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
# WMO mapping
# -----------------------------
WMO_CODES = {
    0: {"text": "Ясно", "emoji": "☀️"},
    1: {"text": "Почти ясно", "emoji": "🌤️"},
    2: {"text": "Переменная облачность", "emoji": "⛅"},
    3: {"text": "Пасмурно", "emoji": "☁️"},
    45: {"text": "Туман", "emoji": "🌫️"},
    48: {"text": "Туман", "emoji": "🌫️"},
    51: {"text": "Морось", "emoji": "🌦️"},
    53: {"text": "Морось", "emoji": "🌧️"},
    55: {"text": "Морось", "emoji": "🌧️"},
    61: {"text": "Дождь", "emoji": "🌦️"},
    63: {"text": "Дождь", "emoji": "🌧️"},
    65: {"text": "Сильный дождь", "emoji": "⛈️"},
    71: {"text": "Снег", "emoji": "🌨️"},
    73: {"text": "Снег", "emoji": "❄️"},
    75: {"text": "Сильный снег", "emoji": "🏔️"},
    80: {"text": "Ливни", "emoji": "🌦️"},
    81: {"text": "Ливни", "emoji": "🌧️"},
    82: {"text": "Сильные ливни", "emoji": "⛈️"},
    95: {"text": "Гроза", "emoji": "🌩️"},
    96: {"text": "Гроза с градом", "emoji": "⛈️"},
    99: {"text": "Сильная гроза", "emoji": "⛈️"},
}

# -----------------------------
# Helpers
# -----------------------------
def get_meta(code: int):
    return WMO_CODES.get(code, {"text": "Неизвестно", "emoji": "🌈"})

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
    df["condition"] = df["code"].apply(lambda x: get_meta(x)["text"])
    df["emoji"] = df["code"].apply(lambda x: get_meta(x)["emoji"])
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
    df["emoji"] = df["code"].apply(lambda x: get_meta(x)["emoji"])
    return df

def build_view(hourly_df, daily_df, granularity):
    weekday_ru = {
        0: "Пн", 1: "Вт", 2: "Ср", 3: "Чт",
        4: "Пт", 5: "Сб", 6: "Вс"
    }

    if granularity == "Почасово":
        view = hourly_df.copy().head(24).copy()
        view["Время"] = view["time"].dt.strftime("%d.%m %H:%M")
        view = view[["Время", "emoji", "condition", "temp", "feels", "rain", "wind", "humidity"]]
        view = view.rename(columns={
            "emoji": "Значок",
            "condition": "Погода",
            "temp": "Темп.",
            "feels": "Ощущ.",
            "rain": "Осадки %",
            "wind": "Ветер км/ч",
            "humidity": "Влажн. %"
        })
        cfg = {
            "Темп.": st.column_config.NumberColumn("Темп.", format="%.1f °C"),
            "Ощущ.": st.column_config.NumberColumn("Ощущ.", format="%.1f °C"),
            "Осадки %": st.column_config.NumberColumn("Осадки %", format="%d%%"),
            "Ветер км/ч": st.column_config.NumberColumn("Ветер км/ч", format="%.0f"),
            "Влажн. %": st.column_config.NumberColumn("Влажн. %", format="%d%%"),
        }
        return view, cfg

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
        agg["Часть дня"] = agg["part"]
        agg["Погода"] = agg["code"].apply(lambda x: get_meta(x)["text"])
        agg["Значок"] = agg["code"].apply(lambda x: get_meta(x)["emoji"])

        order = pd.CategoricalDtype(["Утро", "День", "Вечер"], ordered=True)
        agg["Часть дня"] = agg["Часть дня"].astype(order)
        agg = agg.sort_values(["date", "Часть дня"])

        agg = agg[["День", "Часть дня", "Значок", "Погода", "temp", "feels", "rain", "wind", "humidity"]]
        agg = agg.rename(columns={
            "temp": "Темп.",
            "feels": "Ощущ.",
            "rain": "Осадки %",
            "wind": "Ветер км/ч",
            "humidity": "Влажн. %"
        })

        cfg = {
            "Темп.": st.column_config.NumberColumn("Темп.", format="%.1f °C"),
            "Ощущ.": st.column_config.NumberColumn("Ощущ.", format="%.1f °C"),
            "Осадки %": st.column_config.NumberColumn("Осадки %", format="%d%%"),
            "Ветер км/ч": st.column_config.NumberColumn("Ветер км/ч", format="%.1f"),
            "Влажн. %": st.column_config.NumberColumn("Влажн. %", format="%.1f%%"),
        }
        return agg, cfg

    if granularity == "По дням":
        view = daily_df.copy()
        view["День"] = view["date"].dt.weekday.map(weekday_ru)
        view["Дата"] = view["date"].dt.strftime("%d.%m")
        view = view[["День", "Дата", "emoji", "condition", "tmax", "tmin", "rain", "wind"]]
        view = view.rename(columns={
            "emoji": "Значок",
            "condition": "Погода",
            "tmax": "Макс. °C",
            "tmin": "Мин. °C",
            "rain": "Осадки %",
            "wind": "Ветер км/ч"
        })
        cfg = {
            "Макс. °C": st.column_config.NumberColumn("Макс. °C", format="%.0f °C"),
            "Мин. °C": st.column_config.NumberColumn("Мин. °C", format="%.0f °C"),
            "Осадки %": st.column_config.NumberColumn("Осадки %", format="%d%%"),
            "Ветер км/ч": st.column_config.NumberColumn("Ветер км/ч", format="%.0f"),
        }
        return view, cfg

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
    cfg = {
        "Макс. °C": st.column_config.NumberColumn("Макс. °C", format="%.0f °C"),
        "Мин. °C": st.column_config.NumberColumn("Мин. °C", format="%.0f °C"),
        "Осадки %": st.column_config.NumberColumn("Осадки %", format="%d%%"),
        "Ветер км/ч": st.column_config.NumberColumn("Ветер км/ч", format="%.0f"),
    }
    return view, cfg

# -----------------------------
# Header
# -----------------------------
st.markdown('<div class="page-title">Погода в Крупках</div>', unsafe_allow_html=True)
st.markdown('<div class="page-subtitle">Простой и крупный вид.</div>', unsafe_allow_html=True)

# Controls: only granularity stays
granularity = st.radio(
    "Гранулярность таблицы",
    ["Почасово", "Утро / день / вечер", "По дням", "По неделе"],
    horizontal=True,
    index=2
)

# -----------------------------
# Data loading
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
with st.container(border=True):
    left, right = st.columns([1.1, 3.2], vertical_alignment="center")

    with left:
        st.markdown(f"""
        <div class="wx-wrap">
            <div class="wx-icon">{current_meta["emoji"]}</div>
            <div class="wx-text">{current_meta["text"]}</div>
            <div class="wx-sub">Сейчас в Крупках</div>
        </div>
        """, unsafe_allow_html=True)

    with right:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("Температура", f'{current["temperature_2m"]:.1f} °C')
        with c2:
            st.metric("Ощущается", f'{current["apparent_temperature"]:.1f} °C')
        with c3:
            st.metric("Влажность", f'{current["relative_humidity_2m"]}%')
        with c4:
            st.metric("Ветер", f'{current["wind_speed_10m"]:.0f} км/ч')

        st.markdown(
            f'<div class="wx-sub">Обновлено сейчас · Код погоды: WMO {current["weather_code"]}</div>',
            unsafe_allow_html=True
        )

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
    table_height = 160

st.dataframe(
    view_df,
    use_container_width=True,
    hide_index=True,
    height=table_height,
    column_config=col_cfg
)
