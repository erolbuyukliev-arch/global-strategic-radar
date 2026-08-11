import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone

st.set_page_config(
    page_title="GLOBAL STRATEGIC RADAR",
    page_icon="🌐",
    layout="wide",
)

# ---------------- LIVE DATA ----------------
@st.cache_data(ttl=900)
def fetch_gdelt():
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    params = {
        "query": '"China" "Taiwan"',
        "mode": "artlist",
        "maxrecords": 25,
        "format": "json",
        "timespan": "24h",
        "sort": "datedesc",
    }

    try:
        r = requests.get(
            url,
            params=params,
            timeout=20,
            headers={"User-Agent": "GlobalStrategicRadar/0.2"},
        )
        r.raise_for_status()
        data = r.json()
        articles = data.get("articles", [])

        rows = []
        for a in articles:
            rows.append({
                "title": a.get("title", "Untitled"),
                "domain": a.get("domain", ""),
                "url": a.get("url", ""),
                "published": a.get("seendate", ""),
            })

        return pd.DataFrame(rows), None
    except Exception as e:
        return pd.DataFrame(columns=["title", "domain", "url", "published"]), str(e)

articles, error = fetch_gdelt()
article_count = len(articles)

# Information activity only — NOT military risk.
information_score = min(100, 25 + article_count * 3)

# Demo strategic indicators remain clearly labelled.
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

# ---------------- STYLE ----------------
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

# ---------------- HEADER ----------------
st.title("🌐 GLOBAL STRATEGIC RADAR")
st.caption("Strategic change detection • Early warning • Evidence-based assessment")

now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
st.markdown(
    f'<span class="live">● LIVE DATA</span>  Last refresh: {now}',
    unsafe_allow_html=True
)

if error:
    st.warning("GDELT live feed could not be reached. Showing the dashboard with fallback data.")
else:
    st.success(
        f"GDELT live feed connected — {article_count} relevant articles found in the last 24 hours."
    )

# ---------------- TOP METRICS ----------------
c1, c2, c3, c4 = st.columns(4)

with c1:
    st.markdown(
        '<div class="metric-card"><div class="small-label">Global Strategic Pressure</div>'
        '<div class="big-score">68 ↑</div><div>Demo strategic index</div></div>',
        unsafe_allow_html=True
    )

with c2:
    st.metric("Taiwan information activity", information_score, f"{article_count} articles")

with c3:
    st.metric("Signals monitored", "30", "MVP")

with c4:
    st.metric("Critical alerts", "0")

st.divider()

# ---------------- HOTSPOTS + WHAT CHANGED ----------------
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
    st.markdown('<div class="section-title">🔥 What Changed — Last 24 Hours</div>', unsafe_allow_html=True)

    if error:
        st.warning("Live news feed unavailable.")
    elif article_count == 0:
        st.info("No matching English-language GDELT articles were returned.")
    else:
        st.warning(f"Taiwan/China information activity: {article_count} relevant articles.")
        st.info("This is an information-activity indicator, not a military-risk estimate.")
        st.success("Next layer: connect primary military sources and historical baselines.")

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

# ---------------- LIVE ARTICLES ----------------
st.markdown('<div class="section-title">📰 Live China–Taiwan News Signals</div>', unsafe_allow_html=True)

if not articles.empty:
    display = articles[["title", "domain", "published", "url"]].copy()
    display["title"] = display.apply(
        lambda x: f"[{x['title']}]({x['url']})" if x["url"] else x["title"],
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

# ---------------- ASSESSMENT ----------------
st.markdown('<div class="section-title">🇨🇳 China → 🇹🇼 Taiwan Strategic Assessment</div>', unsafe_allow_html=True)

a, b, c = st.columns(3)
a.metric("Strategic Pressure", "78", "↑↑")
b.metric("Signal Convergence", "47", "+3")
c.metric("Assessment Confidence", "Medium")

st.markdown("""
<div class="assessment">
<b>Current MVP assessment</b><br><br>
Information activity around China–Taiwan is being monitored using a live GDELT feed.
The current information signal must not be interpreted as direct evidence of military
preparation. Primary-source military indicators and historical baselines are required
before assigning a military-risk assessment.
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-title">🚀 Development Roadmap</div>', unsafe_allow_html=True)
st.write(
    "LIVE news feed → primary-source military indicators → 7/30/90-day baselines "
    "→ signal convergence → AI strategic assessment → alerts"
)

st.caption(
    "GLOBAL STRATEGIC RADAR v0.2 • Live information layer • "
    "Strategic scores remain demo data until validated against primary sources."
)

