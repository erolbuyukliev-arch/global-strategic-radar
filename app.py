import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone

st.set_page_config(page_title="GLOBAL STRATEGIC RADAR", page_icon="🌐", layout="wide")

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_QUERY = '"China" "Taiwan"'
MND_REPORT = "https://www.mnd.gov.tw/en/News/PLAAct/87306"
MND_PREP = "https://www.mnd.gov.tw/en/News/PressRelease/87316"

@st.cache_data(ttl=900)
def fetch_gdelt():
    params = {
        "query": GDELT_QUERY, "mode": "artlist", "maxrecords": 25,
        "format": "json", "timespan": "24h", "sort": "datedesc"
    }
    try:
        r = requests.get(GDELT_URL, params=params, timeout=20,
                          headers={"User-Agent": "GlobalStrategicRadar/0.4"})
        r.raise_for_status()
        data = r.json()
        rows = [{
            "title": a.get("title", "Untitled"),
            "domain": a.get("domain", ""),
            "url": a.get("url", ""),
            "published": a.get("seendate", "")
        } for a in data.get("articles", [])]
        return pd.DataFrame(rows), None
    except Exception as e:
        return pd.DataFrame(columns=["title","domain","url","published"]), str(e)

articles, gdelt_error = fetch_gdelt()
article_count = len(articles)
information_score = min(100, 25 + article_count * 3)

# =========================================================
# VERIFIED MND OBSERVATION — 11 AUG 2026
# =========================================================
pla = {
    "date": "2026-08-11",
    "period": "2026-08-10 06:00 → 2026-08-11 06:00 UTC+8",
    "aircraft": 2,
    "adiz_entries": 2,
    "plan_ships": 7,
    "official_ships": 6,
    "source": MND_REPORT,
}

# One observation is NOT enough to calculate a historical anomaly.
# We therefore keep baseline explicitly unavailable rather than inventing it.
baseline_available = False
baseline_days = 1

st.markdown("""
<style>
.block-container{padding-top:1.5rem;padding-bottom:2rem}
.section-title{font-size:1.35rem;font-weight:750;margin-top:1.2rem}
.assessment{padding:20px;border-left:4px solid #888;border-radius:8px;background:rgba(128,128,128,.08)}
.live{display:inline-block;padding:5px 10px;border-radius:12px;background:rgba(0,180,100,.12);font-weight:700}
</style>
""", unsafe_allow_html=True)

st.title("🌐 GLOBAL STRATEGIC RADAR")
st.caption("Strategic change detection • Early warning • Evidence-based assessment")
now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
st.markdown(f'<span class="live">● LIVE DATA</span> Last refresh: {now}', unsafe_allow_html=True)

if gdelt_error:
    st.warning("GDELT live feed unavailable. Information layer is in fallback mode.")
else:
    st.success(f"GDELT live feed connected — {article_count} relevant articles found in the last 24 hours.")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Global Strategic Pressure", "68 ↑", "Demo — not model-derived")
with c2:
    st.metric("Information Activity", information_score, f"{article_count} articles / 24h")
with c3:
    st.metric("PLA Activity", "OBSERVED", "MND • 11 Aug 2026")
with c4:
    st.metric("Critical Alerts", "0")

st.divider()

# =========================================================
# PLA ACTIVITY
# =========================================================
st.markdown('<div class="section-title">🇨🇳 PLA Activity Around Taiwan</div>', unsafe_allow_html=True)

p1, p2, p3, p4 = st.columns(4)
p1.metric("PLA aircraft", pla["aircraft"])
p2.metric("ADIZ entries", pla["adiz_entries"])
p3.metric("PLAN ships", pla["plan_ships"])
p4.metric("Official ships", pla["official_ships"])

st.caption(
    f"Observation: {pla['period']} • Source: ROC Ministry of National Defense"
)
st.link_button("Open official MND report", MND_REPORT)

st.markdown("### 📈 Historical Baseline")
if not baseline_available:
    st.info(
        "Baseline: NOT YET AVAILABLE. The Radar currently has 1 validated daily "
        "observation. A 7-day baseline requires at least 7 comparable observations."
    )
    st.progress(1/7)
    st.caption("Baseline collection: 1 / 7 days")
else:
    st.success("7-day baseline available.")

# =========================================================
# TAIWAN PREPAREDNESS
# =========================================================
st.markdown('<div class="section-title">🇹🇼 Taiwan Military Preparedness</div>', unsafe_allow_html=True)
st.success("ACTIVE — Han Kuang 42")
st.write("Observation date: **2026-08-09**")
st.write("Source: **ROC Ministry of National Defense — Press Release 87316**")
st.write("Observed indicators: **joint anti-landing, littoral strike, beach/shore battle, joint fires, kill-chain integration, intelligence transmission and common operational picture.**")
st.link_button("Open MND Han Kuang 42 report", MND_PREP)

# =========================================================
# CONVERGENCE
# =========================================================
st.markdown('<div class="section-title">⚠️ Signal Convergence</div>', unsafe_allow_html=True)
x1, x2, x3 = st.columns(3)
x1.metric("Information", information_score)
x2.metric("PLA Observation", "2 aircraft / 7 PLAN / 6 official")
x3.metric("Convergence", "PENDING BASELINE")

st.warning(
    "The system does not infer elevated conflict probability from this single observation. "
    "The next analytical step is comparison against a 7-day baseline."
)

# =========================================================
# HOTSPOTS
# =========================================================
hotspots = pd.DataFrame([
    ["Taiwan Strait",78,"↑↑","Medium"],
    ["Middle East",81,"↑","Medium"],
    ["Ukraine",73,"→","Medium"],
    ["South China Sea",67,"↑","Medium"],
    ["Korean Peninsula",59,"→","Medium"],
], columns=["Hotspot","Score","Momentum","Confidence"])

st.markdown('<div class="section-title">🌍 Strategic Hotspots</div>', unsafe_allow_html=True)
st.dataframe(hotspots, use_container_width=True, hide_index=True,
             column_config={"Score": st.column_config.ProgressColumn("Pressure", min_value=0, max_value=100, format="%d")})

# =========================================================
# LIVE ARTICLES
# =========================================================
st.markdown('<div class="section-title">📰 Live China–Taiwan Information Signals</div>', unsafe_allow_html=True)
if not articles.empty:
    display = articles[["title","domain","published","url"]].copy()
    display["title"] = display.apply(
        lambda x: f"[{x['title']}]({x['url']})" if x["url"] else x["title"], axis=1)
    st.dataframe(display[["title","domain","published"]], use_container_width=True, hide_index=True)
else:
    st.info("No live articles available.")

# =========================================================
# ASSESSMENT
# =========================================================
st.markdown('<div class="section-title">🇨🇳 China → 🇹🇼 Taiwan Strategic Assessment</div>', unsafe_allow_html=True)
st.markdown("""
<div class="assessment">
<b>Assessment: BASELINE BUILDING PHASE</b><br><br>
The Radar now contains a verified PLA observation from the ROC MND and a separate
Taiwan preparedness observation from Han Kuang 42. No anomaly or conflict-risk
judgment is generated until comparable historical observations are collected.
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-title">🚀 Next Layer</div>', unsafe_allow_html=True)
st.write("Collect daily MND observations → 7-day baseline → anomaly detection → signal convergence → alerts")

st.caption("GLOBAL STRATEGIC RADAR v0.4 • Verified observation layer.")

