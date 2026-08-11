import streamlit as st
import pandas as pd
import requests
import re
from datetime import datetime, timezone

st.set_page_config(
    page_title="GLOBAL STRATEGIC RADAR",
    page_icon="🌐",
    layout="wide",
)

# =========================================================
# DATA SOURCES
# =========================================================
GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_QUERY = '"China" "Taiwan""

MND_SOURCE = "https://www.mnd.gov.tw/en/news/plaact"
MND_NOTE = (
    "Republic of China Ministry of National Defense (MND) "
    "daily PLA activity reports"
)

# =========================================================
# LIVE INFORMATION ACTIVITY — GDELT
# =========================================================
@st.cache_data(ttl=900)
def fetch_gdelt():
    params = {
        "query": GDELT_QUERY,
        "mode": "artlist",
        "maxrecords": 25,
        "format": "json",
        "timespan": "24h",
        "sort": "datedesc",
    }

    try:
        r = requests.get(
            GDELT_URL,
            params=params,
            timeout=20,
            headers={"User-Agent": "GlobalStrategicRadar/0.3"},
        )
        r.raise_for_status()
        data = r.json()

        rows = []
        for a in data.get("articles", []):
            rows.append({
                "title": a.get("title", "Untitled"),
                "domain": a.get("domain", ""),
                "url": a.get("url", ""),
                "published": a.get("seendate", ""),
            })

        return pd.DataFrame(rows), None

    except Exception as e:
        return pd.DataFrame(
            columns=["title", "domain", "url", "published"]
        ), str(e)


articles, gdelt_error = fetch_gdelt()
article_count = len(articles)

# Information activity is deliberately NOT military risk.
information_score = min(100, 25 + article_count * 3)

# =========================================================
# MILITARY ACTIVITY — SOURCE-BASED INPUT
# =========================================================
# IMPORTANT:
# We do NOT fabricate a current PLA count.
# The MND publishes daily observations. Until automated
# extraction is validated, the latest observation is entered
# explicitly by the analyst with its source/date.

st.sidebar.header("⚙️ Military Data")

st.sidebar.markdown(
    f"**Source:** [ROC MND PLA Activities]({MND_SOURCE})"
)

st.sidebar.caption(
    "Enter the latest observation from the official MND daily report. "
    "This is intentionally separated from GDELT."
)

mnd_date = st.sidebar.date_input(
    "Observation date",
    value=datetime.now().date()
)

aircraft = st.sidebar.number_input(
    "PLA aircraft sorties",
    min_value=0,
    max_value=500,
    value=0,
    step=1,
)

median_crossings = st.sidebar.number_input(
    "Aircraft crossing median line",
    min_value=0,
    max_value=500,
    value=0,
    step=1,
)

plan_ships = st.sidebar.number_input(
    "PLAN ships",
    min_value=0,
    max_value=200,
    value=0,
    step=1,
)

official_ships = st.sidebar.number_input(
    "PRC official ships",
    min_value=0,
    max_value=200,
    value=0,
    step=1,
)

mnd_source_url = st.sidebar.text_input(
    "Exact MND report URL",
    value=MND_SOURCE
)

# Military activity score is only calculated after analyst
# enters a source-backed observation.
military_data_entered = aircraft > 0 or median_crossings > 0 or plan_ships > 0 or official_ships > 0

if military_data_entered:
    # Transparent indicator, not a probability of war.
    aircraft_component = min(50, aircraft * 1.5)
    crossing_component = min(30, median_crossings * 3)
    maritime_component = min(20, (plan_ships + official_ships) * 1.5)
    military_score = int(round(
        min(100, aircraft_component + crossing_component + maritime_component)
    ))
else:
    military_score = None

# =========================================================
# DEMO STRATEGIC STRUCTURE
# =========================================================
hotspots = pd.DataFrame([
    ["Taiwan Strait", 78, "↑↑", "Medium"],
    ["Middle East", 81, "↑", "Medium"],
    ["Ukraine", 73, "→", "Medium"],
    ["South China Sea", 67, "↑", "Medium"],
    ["Korean Peninsula", 59, "→", "Medium"],
], columns=["Hotspot", "Score", "Momentum", "Confidence"])

domains = pd.DataFrame([
    ["Military", 74, "↑"],
    ["Nuclear", 63, "↑"],
    ["Geoeconomics", 69, "↑"],
    ["Technology", 77, "↑"],
    ["Space", 66, "→"],
    ["Cyber", 61, "↑"],
    ["Maritime", 72, "↑"],
    ["Energy", 58, "→"],
    ["Political", 64, "→"],
    ["Infrastructure", 62, "↑"],
], columns=["Domain", "Score", "Momentum"])

# =========================================================
# STYLE
# =========================================================
st.markdown("""
<style>
.block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
.metric-card {
    padding: 18px 20px;
    border: 1px solid rgba(128,128,128,.25);
    border-radius: 14px;
    background: rgba(128,128,128,.06);
}
.big-score {font-size: 4.2rem; font-weight: 800; line-height: 1;}
.small-label {
    font-size: .85rem;
    opacity: .72;
    text-transform: uppercase;
    letter-spacing: .08em;
}
.section-title {font-size: 1.35rem; font-weight: 750; margin-top: 1.2rem;}
.assessment {
    padding: 20px;
    border-left: 4px solid #888;
    border-radius: 8px;
    background: rgba(128,128,128,.08);
}
.live {
    display: inline-block;
    padding: 5px 10px;
    border-radius: 12px;
    background: rgba(0,180,100,.12);
    font-weight: 700;
}
</style>
""", unsafe_allow_html=True)

# =========================================================
# HEADER
# =========================================================
st.title("🌐 GLOBAL STRATEGIC RADAR")
st.caption(
    "Strategic change detection • Early warning • Evidence-based assessment"
)

now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
st.markdown(
    f'<span class="live">● LIVE DATA</span> Last refresh: {now}',
    unsafe_allow_html=True
)

if gdelt_error:
    st.warning("GDELT live feed unavailable. The information layer is in fallback mode.")
else:
    st.success(
        f"GDELT live feed connected — {article_count} relevant articles "
        "found in the last 24 hours."
    )

# =========================================================
# TOP METRICS
# =========================================================
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        '<div class="metric-card">'
        '<div class="small-label">Global Strategic Pressure</div>'
        '<div class="big-score">68 ↑</div>'
        '<div>Demo index — not yet model-derived</div>'
        '</div>',
        unsafe_allow_html=True
    )

with c2:
    st.metric(
        "Information Activity",
        information_score,
        f"{article_count} articles / 24h"
    )

with c3:
    if military_score is None:
        st.metric("Military Activity", "N/A", "source input required")
    else:
        st.metric(
            "Military Activity",
            military_score,
            f"MND observation: {mnd_date.isoformat()}"
        )

with c4:
    st.metric("Critical Alerts", "0")

st.divider()

# =========================================================
# SIGNAL CONVERGENCE
# =========================================================
st.markdown(
    '<div class="section-title">⚠️ Signal Convergence</div>',
    unsafe_allow_html=True
)

s1, s2, s3 = st.columns(3)

with s1:
    st.metric("Information Signal", information_score)

with s2:
    st.metric(
        "Military Signal",
        military_score if military_score is not None else "N/A"
    )

with s3:
    if military_score is None:
        st.metric("Convergence", "INSUFFICIENT DATA")
    else:
        # Conservative rule: convergence is high only when both
        # signals are elevated.
        if information_score >= 70 and military_score >= 60:
            convergence = "HIGH"
        elif information_score >= 55 and military_score >= 40:
            convergence = "MEDIUM"
        else:
            convergence = "LOW"
        st.metric("Convergence", convergence)

st.info(
    "Convergence means independent signal streams point in the same direction. "
    "It is not a probability of conflict and should not be interpreted as one."
)

# =========================================================
# MILITARY ACTIVITY
# =========================================================
st.markdown(
    '<div class="section-title">✈️ PLA Military Activity Around Taiwan</div>',
    unsafe_allow_html=True
)

if military_score is None:
    st.warning(
        "No source-backed military observation has been entered yet. "
        "Use the sidebar and enter the figures from the latest official MND report."
    )
else:
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("PLA aircraft sorties", aircraft)
    m2.metric("Median-line crossings", median_crossings)
    m3.metric("PLAN ships", plan_ships)
    m4.metric("PRC official ships", official_ships)

    st.caption(
        f"Observation date: {mnd_date.isoformat()} • "
        f"Source: ROC MND • {mnd_source_url}"
    )

    st.progress(military_score / 100)
    st.write(f"Military activity indicator: **{military_score}/100**")

    st.warning(
        "This is a transparent composite indicator based on the entered MND "
        "observation. It is NOT a validated war-risk probability."
    )

# =========================================================
# HOTSPOTS
# =========================================================
left, right = st.columns([1.35, 1])

with left:
    st.markdown(
        '<div class="section-title">🌍 Strategic Hotspots</div>',
        unsafe_allow_html=True
    )
    st.dataframe(
        hotspots,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Pressure",
                min_value=0,
                max_value=100,
                format="%d"
            )
        },
    )

with right:
    st.markdown(
        '<div class="section-title">🔥 What Changed — Last 24 Hours</div>',
        unsafe_allow_html=True
    )

    if gdelt_error:
        st.warning("Live news feed unavailable.")
    else:
        st.warning(
            f"China–Taiwan information activity: {article_count} relevant articles."
        )

    if military_score is None:
        st.info("Military signal awaiting official MND observation.")
    else:
        st.success(
            f"MND military signal entered for {mnd_date.isoformat()}: "
            f"{military_score}/100."
        )

# =========================================================
# DOMAINS
# =========================================================
st.markdown(
    '<div class="section-title">📊 Strategic Domains</div>',
    unsafe_allow_html=True
)

st.dataframe(
    domains,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Score": st.column_config.ProgressColumn(
            "Score",
            min_value=0,
            max_value=100,
            format="%d"
        )
    },
)

# =========================================================
# LIVE ARTICLES
# =========================================================
st.markdown(
    '<div class="section-title">📰 Live China–Taiwan News Signals</div>',
    unsafe_allow_html=True
)

if not articles.empty:
    display = articles[["title", "domain", "published", "url"]].copy()
    display["title"] = display.apply(
        lambda x: f"[{x['title']}]({x['url']})"
        if x["url"] else x["title"],
        axis=1,
    )
    st.dataframe(
        display[["title", "domain", "published"]],
        use_container_width=True,
        hide_index=True,
        column_config={
            "title": st.column_config.TextColumn("Article", width="large"),
            "domain": "Source",
            "published": "Published",
        },
    )
else:
    st.info("No live articles available.")

# =========================================================
# ASSESSMENT
# =========================================================
st.markdown(
    '<div class="section-title">🇨🇳 China → 🇹🇼 Taiwan Strategic Assessment</div>',
    unsafe_allow_html=True
)

if military_score is None:
    st.markdown("""
    <div class="assessment">
    <b>Assessment status: INCOMPLETE</b><br><br>
    The information stream is live, but the military stream has not yet received
    a source-backed observation. No military-risk conclusion is generated.
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="assessment">
    <b>Assessment status: TWO-STREAM MVP</b><br><br>
    Information activity: <b>{information_score}/100</b><br>
    Military activity: <b>{military_score}/100</b><br><br>
    The system can now test whether information and military indicators
    converge. This is an analytical signal, not a forecast of conflict.
    </div>
    """, unsafe_allow_html=True)

st.markdown(
    '<div class="section-title">🚀 Development Roadmap</div>',
    unsafe_allow_html=True
)
st.write(
    "GDELT information → MND military observations → historical baseline "
    "→ signal convergence → maritime indicators → AI assessment → alerts"
)

st.caption(
    "GLOBAL STRATEGIC RADAR v0.3 • Source-separated information and military layers."
)

