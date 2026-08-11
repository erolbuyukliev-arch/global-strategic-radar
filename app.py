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
                          headers={"User-Agent": "GlobalStrategicRadar/0.4.1"})
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
# VERIFIED MND OBSERVATIONS + DATA QUALITY
# =========================================================
# IMPORTANT: The two official MND pages dated Aug 5 and Aug 6
# report the same 4–5 Aug observation period with conflicting
# values. Therefore that period is explicitly excluded from the
# baseline rather than silently choosing one value.
#
# Valid comparable observations:
# Aug 4 report: period Aug 3–4
# Aug 7 report: period Aug 6–7
# Aug 8 report: period Aug 7–8
# Aug 9 report: period Aug 8–9
# Aug 10 report: period Aug 9–10
# Aug 11 report: period Aug 10–11

observations = pd.DataFrame([
    ["2026-08-04", "Aug 3–4", 6, 6, 7, 6, "VALID", "MND 87238"],
    ["2026-08-07", "Aug 6–7", 10, 6, 6, 3, "VALID", "MND 87270"],
    ["2026-08-08", "Aug 7–8", 14, 11, 6, 8, "VALID", "MND 87276"],
    ["2026-08-09", "Aug 8–9", 4, 2, 6, 9, "VALID", "MND 87282"],
    ["2026-08-10", "Aug 9–10", 1, 1, 9, 11, "VALID", "MND 87302"],
    ["2026-08-11", "Aug 10–11", 2, 2, 7, 6, "VALID", "MND 87306"],
], columns=[
    "Report date", "Observation period", "PLA aircraft",
    "Median-line/ADIZ", "PLAN ships", "Official ships", "Status", "Source"
])

conflict = pd.DataFrame([
    ["2026-08-05", "Aug 4–5", 21, 17, 9, 5, "CONFLICT", "MND 87248"],
    ["2026-08-06", "Aug 4–5", 14, 6, 9, 7, "CONFLICT", "MND 87257"],
], columns=observations.columns)

# Baseline uses only VALID observations.
baseline = observations[["PLA aircraft","Median-line/ADIZ","PLAN ships","Official ships"]].mean()

latest = observations.iloc[-1]

def anomaly(current, base):
    if base == 0:
        return 0.0
    return ((current - base) / base) * 100

air_anom = anomaly(latest["PLA aircraft"], baseline["PLA aircraft"])
adiz_anom = anomaly(latest["Median-line/ADIZ"], baseline["Median-line/ADIZ"])
plan_anom = anomaly(latest["PLAN ships"], baseline["PLAN ships"])
official_anom = anomaly(latest["Official ships"], baseline["Official ships"])

# Conservative composite: equal weighting of the four observable dimensions.
composite = (air_anom + adiz_anom + plan_anom + official_anom) / 4
pla_signal = int(max(0, min(100, round(50 + composite / 2))))

# =========================================================
# STYLE
# =========================================================
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

# =========================================================
# TOP METRICS
# =========================================================
c1, c2, c3, c4 = st.columns(4)
c1.metric("Global Strategic Pressure", "68 ↑", "Demo — not model-derived")
c2.metric("Information Activity", information_score, f"{article_count} articles / 24h")
c3.metric("PLA Activity Signal", pla_signal, "6 validated observations")
c4.metric("Data Quality", "CONFLICT FLAG", "1 period excluded")

st.divider()

# =========================================================
# DATA QUALITY
# =========================================================
st.markdown('<div class="section-title">⚠️ Source Conflict Detection</div>', unsafe_allow_html=True)
st.error(
    "CONFLICT DETECTED: MND reports 87248 and 87257 both describe Aug 4–5, "
    "2026 but publish different observations. The period is excluded from the baseline."
)

st.dataframe(
    conflict,
    use_container_width=True,
    hide_index=True,
    column_config={
        "PLA aircraft": st.column_config.NumberColumn("Aircraft"),
        "Median-line/ADIZ": st.column_config.NumberColumn("Median-line / ADIZ"),
    },
)

st.caption(
    "Rule: conflicting observations are retained for provenance but excluded from "
    "quantitative baseline calculations until the source discrepancy is resolved."
)

# =========================================================
# PLA ACTIVITY
# =========================================================
st.markdown('<div class="section-title">🇨🇳 PLA Activity Around Taiwan</div>', unsafe_allow_html=True)

p1, p2, p3, p4 = st.columns(4)
p1.metric("Latest aircraft", int(latest["PLA aircraft"]), f"{air_anom:+.0f}% vs baseline")
p2.metric("Latest median-line/ADIZ", int(latest["Median-line/ADIZ"]), f"{adiz_anom:+.0f}% vs baseline")
p3.metric("Latest PLAN ships", int(latest["PLAN ships"]), f"{plan_anom:+.0f}% vs baseline")
p4.metric("Latest official ships", int(latest["Official ships"]), f"{official_anom:+.0f}% vs baseline")

st.progress(pla_signal / 100)
st.write(f"**PLA Activity Signal: {pla_signal}/100**")

# =========================================================
# BASELINE TABLE
# =========================================================
st.markdown('<div class="section-title">📊 Validated Observation Set</div>', unsafe_allow_html=True)
st.dataframe(
    observations,
    use_container_width=True,
    hide_index=True,
)

b1, b2, b3, b4 = st.columns(4)
b1.metric("Aircraft baseline", f"{baseline['PLA aircraft']:.1f}")
b2.metric("Median-line / ADIZ baseline", f"{baseline['Median-line/ADIZ']:.1f}")
b3.metric("PLAN baseline", f"{baseline['PLAN ships']:.1f}")
b4.metric("Official ships baseline", f"{baseline['Official ships']:.1f}")

# =========================================================
# TAIWAN PREPAREDNESS
# =========================================================
st.markdown('<div class="section-title">🇹🇼 Taiwan Military Preparedness</div>', unsafe_allow_html=True)
st.success("ACTIVE — Han Kuang 42")
st.write(
    "2026-08-09 • Joint anti-landing • Littoral strike • Beach/shore battle • "
    "Joint fires • Kill-chain integration • Intelligence transmission / common operational picture"
)
st.link_button("Open official MND Han Kuang 42 report", MND_PREP)

# =========================================================
# CONVERGENCE
# =========================================================
st.markdown('<div class="section-title">⚠️ Signal Convergence</div>', unsafe_allow_html=True)

x1, x2, x3 = st.columns(3)
x1.metric("Information Signal", information_score)
x2.metric("PLA Signal", pla_signal)
x3.metric("Convergence", "PENDING VALIDATION")

st.warning(
    "A higher PLA signal indicates deviation from the validated observation baseline. "
    "It does not represent a probability of conflict."
)

# =========================================================
# LIVE INFORMATION
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
st.markdown(f"""
<div class="assessment">
<b>Assessment status: BASELINE + DATA-QUALITY CONTROL</b><br><br>
The Radar uses {len(observations)} validated MND observations.
The conflicting Aug 4–5 records are retained as provenance but excluded from the baseline.
The latest validated observation is Aug 10–11: 2 aircraft, 2 median-line/ADIZ,
7 PLAN ships and 6 official ships.<br><br>
PLA Activity Signal: <b>{pla_signal}/100</b>. This is an anomaly-oriented indicator,
not a forecast or conflict probability.
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-title">🚀 Next Layer</div>', unsafe_allow_html=True)
st.write(
    "Resolve MND source conflict → automate daily MND ingestion → expand baseline "
    "to 30/90 days → add maritime/geoeconomic signals → validated convergence model"
)

st.caption("GLOBAL STRATEGIC RADAR v0.4.1 • Data provenance + conflict detection.")

