import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone

st.set_page_config(
    page_title="GLOBAL STRATEGIC RADAR",
    page_icon="🌐",
    layout="wide",
)

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_QUERY = '"China" "Taiwan"'
MND_SOURCE = "https://www.mnd.gov.tw/en/News/PressRelease/87316"

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
            headers={"User-Agent": "GlobalStrategicRadar/0.3.1"},
        )
        r.raise_for_status()
        data = r.json()
        rows = [{
            "title": a.get("title", "Untitled"),
            "domain": a.get("domain", ""),
            "url": a.get("url", ""),
            "published": a.get("seendate", ""),
        } for a in data.get("articles", [])]
        return pd.DataFrame(rows), None
    except Exception as e:
        return pd.DataFrame(columns=["title","domain","url","published"]), str(e)

articles, gdelt_error = fetch_gdelt()
article_count = len(articles)
information_score = min(100, 25 + article_count * 3)

st.markdown("""
<style>
.block-container {padding-top:1.5rem;padding-bottom:2rem}
.metric-card {padding:18px 20px;border:1px solid rgba(128,128,128,.25);border-radius:14px;background:rgba(128,128,128,.06)}
.big-score {font-size:4.2rem;font-weight:800;line-height:1}
.small-label {font-size:.85rem;opacity:.72;text-transform:uppercase;letter-spacing:.08em}
.section-title {font-size:1.35rem;font-weight:750;margin-top:1.2rem}
.assessment {padding:20px;border-left:4px solid #888;border-radius:8px;background:rgba(128,128,128,.08)}
.live {display:inline-block;padding:5px 10px;border-radius:12px;background:rgba(0,180,100,.12);font-weight:700}
</style>
""", unsafe_allow_html=True)

st.title("🌐 GLOBAL STRATEGIC RADAR")
st.caption("Strategic change detection • Early warning • Evidence-based assessment")
now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
st.markdown(f'<span class="live">● LIVE DATA</span> Last refresh: {now}', unsafe_allow_html=True)

if gdelt_error:
    st.warning("GDELT live feed unavailable. The information layer is in fallback mode.")
else:
    st.success(f"GDELT live feed connected — {article_count} relevant articles found in the last 24 hours.")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown(
        '<div class="metric-card"><div class="small-label">Global Strategic Pressure</div>'
        '<div class="big-score">68 ↑</div><div>Demo index — not yet model-derived</div></div>',
        unsafe_allow_html=True)
with c2:
    st.metric("Information Activity", information_score, f"{article_count} articles / 24h")
with c3:
    st.metric("Military Layer", "2 sources", "PLA + Taiwan preparedness")
with c4:
    st.metric("Critical Alerts", "0")

st.divider()

# =========================================================
# TWO MILITARY LAYERS
# =========================================================
st.markdown('<div class="section-title">🛡️ Military Situation — Two Separate Layers</div>', unsafe_allow_html=True)

m1, m2 = st.columns(2)

with m1:
    st.subheader("🇨🇳 PLA Activity")
    st.warning("No validated daily PLA activity observation has been entered.")
    st.caption("Next step: connect the official ROC MND PLA Activities daily reports.")
    st.metric("PLA aircraft", "N/A")
    st.metric("PLAN / official ships", "N/A")

with m2:
    st.subheader("🇹🇼 Taiwan Military Preparedness")
    st.success("ACTIVE — Han Kuang 42")
    st.write("**Observation date:** 2026-08-09")
    st.write("**Source:** ROC Ministry of National Defense")
    st.write("**Press Release:** 87316")
    st.write("")
    st.write("**Observed preparedness indicators:**")
    st.checkbox("Joint anti-landing", value=True, disabled=True)
    st.checkbox("Littoral strike", value=True, disabled=True)
    st.checkbox("Beach / shore battle", value=True, disabled=True)
    st.checkbox("Joint fires", value=True, disabled=True)
    st.checkbox("Kill-chain integration", value=True, disabled=True)
    st.checkbox("Intelligence transmission / COP", value=True, disabled=True)
    st.link_button("Open official MND source", MND_SOURCE)

st.info(
    "Analytical distinction: Taiwan preparedness is not PLA activity. "
    "Neither signal alone is evidence of imminent conflict."
)

# =========================================================
# SIGNAL CONVERGENCE
# =========================================================
st.markdown('<div class="section-title">⚠️ Signal Convergence</div>', unsafe_allow_html=True)
s1, s2, s3 = st.columns(3)
with s1:
    st.metric("Information Signal", information_score)
with s2:
    st.metric("PLA Activity Signal", "N/A")
with s3:
    st.metric("Convergence", "INCOMPLETE")

st.caption(
    "Convergence will be assessed only after independent PLA activity data "
    "and information activity have validated observations."
)

# =========================================================
# HOTSPOTS
# =========================================================
hotspots = pd.DataFrame([
    ["Taiwan Strait", 78, "↑↑", "Medium"],
    ["Middle East", 81, "↑", "Medium"],
    ["Ukraine", 73, "→", "Medium"],
    ["South China Sea", 67, "↑", "Medium"],
    ["Korean Peninsula", 59, "→", "Medium"],
], columns=["Hotspot", "Score", "Momentum", "Confidence"])

left, right = st.columns([1.35, 1])
with left:
    st.markdown('<div class="section-title">🌍 Strategic Hotspots</div>', unsafe_allow_html=True)
    st.dataframe(
        hotspots, use_container_width=True, hide_index=True,
        column_config={"Score": st.column_config.ProgressColumn("Pressure", min_value=0, max_value=100, format="%d")}
    )

with right:
    st.markdown('<div class="section-title">🔥 What Changed — Last 24 Hours</div>', unsafe_allow_html=True)
    if gdelt_error:
        st.warning("Live news feed unavailable.")
    else:
        st.warning(f"China–Taiwan information activity: {article_count} relevant articles.")
    st.success("Taiwan preparedness: Han Kuang 42 active on 2026-08-09.")

# =========================================================
# DOMAINS
# =========================================================
domains = pd.DataFrame([
    ["Military", 74, "↑"], ["Nuclear", 63, "↑"], ["Geoeconomics", 69, "↑"],
    ["Technology", 77, "↑"], ["Space", 66, "→"], ["Cyber", 61, "↑"],
    ["Maritime", 72, "↑"], ["Energy", 58, "→"], ["Political", 64, "→"],
    ["Infrastructure", 62, "↑"],
], columns=["Domain", "Score", "Momentum"])

st.markdown('<div class="section-title">📊 Strategic Domains</div>', unsafe_allow_html=True)
st.dataframe(
    domains, use_container_width=True, hide_index=True,
    column_config={"Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d")}
)

# =========================================================
# LIVE ARTICLES
# =========================================================
st.markdown('<div class="section-title">📰 Live China–Taiwan News Signals</div>', unsafe_allow_html=True)
if not articles.empty:
    display = articles[["title", "domain", "published", "url"]].copy()
    display["title"] = display.apply(
        lambda x: f"[{x['title']}]({x['url']})" if x["url"] else x["title"], axis=1)
    st.dataframe(
        display[["title", "domain", "published"]],
        use_container_width=True, hide_index=True,
        column_config={"title": st.column_config.TextColumn("Article", width="large"),
                       "domain": "Source", "published": "Published"}
    )
else:
    st.info("No live articles available.")

# =========================================================
# ASSESSMENT
# =========================================================
st.markdown('<div class="section-title">🇨🇳 China → 🇹🇼 Taiwan Strategic Assessment</div>', unsafe_allow_html=True)
st.markdown("""
<div class="assessment">
<b>Current assessment: INCOMPLETE TWO-SIDED MILITARY PICTURE</b><br><br>
The Taiwan side shows active and realistic defensive preparedness during Han Kuang 42.
The independent PLA activity layer is not yet populated with a validated daily observation.
Therefore the system does not infer an elevated conflict probability.
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-title">🚀 Development Roadmap</div>', unsafe_allow_html=True)
st.write(
    "GDELT information → PLA daily activity → Taiwan preparedness → "
    "historical baseline → signal convergence → maritime indicators → AI assessment → alerts"
)
st.caption("GLOBAL STRATEGIC RADAR v0.3.1 • Source-separated military layers.")

