import streamlit as st
import pandas as pd
import requests
import math
from datetime import datetime, timezone

st.set_page_config(
    page_title="GLOBAL STRATEGIC RADAR",
    page_icon="🌐",
    layout="wide",
)

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
QUERY = '"China" "Taiwan"'

@st.cache_data(ttl=900)
def fetch_articles():
    params = {
        "query": QUERY,
        "mode": "artlist",
        "maxrecords": 50,
        "format": "json",
        "timespan": "24h",
        "sort": "datedesc",
    }
    try:
        r = requests.get(
            GDELT_URL, params=params, timeout=20,
            headers={"User-Agent": "GlobalStrategicRadar/0.2.1"}
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
        return pd.DataFrame(columns=["title", "domain", "url", "published"]), str(e)

@st.cache_data(ttl=1800)
def fetch_7day_timeline():
    params = {
        "query": QUERY,
        "mode": "timelinevolraw",
        "format": "json",
        "timespan": "7d",
        "dateres": "day",
    }
    try:
        r = requests.get(
            GDELT_URL, params=params, timeout=20,
            headers={"User-Agent": "GlobalStrategicRadar/0.2.1"}
        )
        r.raise_for_status()
        data = r.json()
        timeline = data.get("timeline", [])
        if not timeline:
            return pd.DataFrame(columns=["date", "count"]), None

        points = timeline[0].get("data", [])
        rows = []
        for p in points:
            try:
                rows.append({
                    "date": p.get("date", ""),
                    "count": float(p.get("value", 0)),
                })
            except (TypeError, ValueError):
                pass
        return pd.DataFrame(rows), None
    except Exception as e:
        return pd.DataFrame(columns=["date", "count"]), str(e)

articles, article_error = fetch_articles()
timeline, timeline_error = fetch_7day_timeline()

current_count = len(articles)

# Information-activity baseline, deliberately NOT a military-risk baseline.
if len(timeline) >= 2:
    historical = timeline.iloc[:-1]["count"]
    baseline = float(historical.mean()) if len(historical) else 0.0
else:
    baseline = 0.0

if baseline > 0:
    anomaly_pct = ((current_count - baseline) / baseline) * 100
    raw_score = 50 + 25 * math.log2(max(current_count, 1) / baseline)
    information_score = int(max(0, min(100, round(raw_score))))
else:
    anomaly_pct = 0.0
    information_score = 50

# ---------- STYLE ----------
st.markdown("""
<style>
.block-container {padding-top: 1.6rem; padding-bottom: 2rem;}
.metric-card {
    padding: 18px 20px;
    border: 1px solid rgba(128,128,128,.25);
    border-radius: 14px;
    background: rgba(128,128,128,.06);
}
.big-score {font-size: 4.2rem; font-weight: 800; line-height: 1;}
.small-label {font-size: .85rem; opacity: .72; text-transform: uppercase; letter-spacing: .08em;}
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

# ---------- HEADER ----------
st.title("🌐 GLOBAL STRATEGIC RADAR")
st.caption("Strategic change detection • Early warning • Evidence-based assessment")

now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
st.markdown(
    f'<span class="live">● LIVE DATA</span>  Last refresh: {now}',
    unsafe_allow_html=True
)

if article_error:
    st.warning("GDELT article feed unavailable.")
else:
    st.success(
        f"GDELT live feed connected — {current_count} relevant articles "
        "found in the last 24 hours."
    )

# ---------- TOP METRICS ----------
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        '<div class="metric-card">'
        '<div class="small-label">Global Strategic Pressure</div>'
        '<div class="big-score">68 ↑</div>'
        '<div>Demo strategic index</div></div>',
        unsafe_allow_html=True
    )

with c2:
    delta = f"{anomaly_pct:+.0f}% vs baseline" if baseline > 0 else "baseline unavailable"
    st.metric("Taiwan information activity", information_score, delta)

with c3:
    st.metric("Current articles / 24h", current_count)

with c4:
    st.metric("Signals monitored", "30", "MVP")

st.divider()

# ---------- BASELINE ----------
st.markdown(
    '<div class="section-title">📈 China–Taiwan Information Activity Baseline</div>',
    unsafe_allow_html=True
)

if not timeline.empty:
    chart_df = timeline.copy()
    chart_df["date"] = pd.to_datetime(chart_df["date"], errors="coerce")
    chart_df = chart_df.dropna(subset=["date"]).set_index("date")
    st.line_chart(chart_df["count"], height=260)

    b1, b2, b3 = st.columns(3)
    b1.metric("Current 24h", current_count)
    b2.metric(
        "Historical daily baseline",
        f"{baseline:.1f}" if baseline > 0 else "N/A"
    )
    b3.metric(
        "Anomaly",
        f"{anomaly_pct:+.0f}%" if baseline > 0 else "N/A"
    )
else:
    st.info("Seven-day baseline is temporarily unavailable.")

st.warning(
    "⚠️ Information Activity is not Military Risk. "
    "A media spike can reflect reporting intensity rather than a change in military behavior."
)

# ---------- HOTSPOTS ----------
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

left, right = st.columns([1.35, 1])

with left:
    st.markdown('<div class="section-title">🌍 Strategic Hotspots</div>', unsafe_allow_html=True)
    st.dataframe(
        hotspots,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Score": st.column_config.ProgressColumn(
                "Pressure", min_value=0, max_value=100, format="%d"
            )
        },
    )

with right:
    st.markdown(
        '<div class="section-title">🔥 What Changed — Last 24 Hours</div>',
        unsafe_allow_html=True
    )
    if baseline > 0:
        st.warning(
            f"China–Taiwan information activity is "
            f"{anomaly_pct:+.0f}% versus the historical daily baseline."
        )
    else:
        st.info(f"{current_count} relevant articles were returned in the last 24 hours.")
    st.info("This indicator measures information activity, not military activity.")

st.markdown('<div class="section-title">📊 Strategic Domains</div>', unsafe_allow_html=True)
st.dataframe(
    domains,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Score": st.column_config.ProgressColumn(
            "Score", min_value=0, max_value=100, format="%d"
        )
    },
)

# ---------- LIVE ARTICLES ----------
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

# ---------- ASSESSMENT ----------
st.markdown(
    '<div class="section-title">🇨🇳 China → 🇹🇼 Taiwan Strategic Assessment</div>',
    unsafe_allow_html=True
)

a, b, c = st.columns(3)
a.metric("Strategic Pressure", "78", "↑↑")
b.metric("Signal Convergence", "47", "+3")
c.metric("Assessment Confidence", "Medium")

st.markdown("""
<div class="assessment">
<b>Current MVP assessment</b><br><br>
The system now measures China–Taiwan information activity against a
seven-day historical baseline. This is an early-warning information signal,
not a military-risk estimate.
<br><br>
Primary-source military indicators and longer historical baselines are required
before assigning a validated military-risk assessment.
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-title">🚀 Development Roadmap</div>', unsafe_allow_html=True)
st.write(
    "LIVE news feed → primary-source military indicators → 7/30/90-day baselines "
    "→ signal convergence → AI strategic assessment → alerts"
)

st.caption(
    "GLOBAL STRATEGIC RADAR v0.2.1 • Live information layer • "
    "Strategic scores remain demo data until validated against primary sources."
)

