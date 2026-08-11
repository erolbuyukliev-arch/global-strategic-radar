
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="GLOBAL STRATEGIC RADAR",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Demo data ----------
hotspots = pd.DataFrame([
    ["Taiwan Strait", 78, "↑↑", "High"],
    ["Middle East", 81, "↑", "High"],
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

signals = pd.DataFrame([
    ["PLA aircraft activity", "Military", 72, "↑", "High"],
    ["PLAN presence", "Maritime", 70, "↑", "High"],
    ["China Coast Guard activity", "Maritime", 74, "↑", "High"],
    ["Military exercises", "Military", 76, "↑", "High"],
    ["Logistics indicators", "Logistics", 42, "→", "Medium"],
    ["Political rhetoric", "Political", 76, "→", "High"],
    ["US force posture", "External response", 61, "↑", "Medium"],
], columns=["Signal", "Domain", "Score", "Momentum", "Confidence"])

# ---------- Styling ----------
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
</style>
""", unsafe_allow_html=True)

# ---------- Header ----------
st.title("🌐 GLOBAL STRATEGIC RADAR")
st.caption("Strategic change detection • Early warning • Evidence-based assessment")

# ---------- Top metrics ----------
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.markdown('<div class="metric-card"><div class="small-label">Global Strategic Pressure</div><div class="big-score">68 ↑</div><div>Confidence: 72/100</div></div>', unsafe_allow_html=True)
with c2:
    st.metric("Strategic hotspots", "5", "+2")
with c3:
    st.metric("Signals monitored", "30", "+4")
with c4:
    st.metric("Critical alerts", "0", "0")

st.divider()

# ---------- Main dashboard ----------
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
            ),
        },
    )

with right:
    st.markdown('<div class="section-title">🔥 What Changed — Last 24 Hours</div>', unsafe_allow_html=True)
    st.warning("Taiwan: military activity remains elevated.")
    st.info("China–US: technology competition remains elevated.")
    st.info("South China Sea: maritime pressure increased.")
    st.success("No critical signal convergence detected.")

st.markdown('<div class="section-title">📊 Strategic Domains</div>', unsafe_allow_html=True)
st.dataframe(
    domains,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Score": st.column_config.ProgressColumn(
            "Score", min_value=0, max_value=100, format="%d"
        ),
    },
)

# ---------- Taiwan assessment ----------
st.markdown('<div class="section-title">🇨🇳 China → 🇹🇼 Taiwan Strategic Assessment</div>', unsafe_allow_html=True)

a, b, c = st.columns(3)
a.metric("Strategic Pressure", "78", "↑↑")
b.metric("Signal Convergence", "47", "+3")
c.metric("Assessment Confidence", "71", "Medium")

st.markdown("""
<div class="assessment">
<b>Primary assessment</b><br><br>
Current evidence is more consistent with sustained coercive pressure and
normalization of PLA activity than with imminent preparation for major
military operations.
<br><br>
<b>Confidence:</b> Medium
</div>
""", unsafe_allow_html=True)

# ---------- Hypotheses ----------
st.markdown('<div class="section-title">🧠 Competing Hypotheses</div>', unsafe_allow_html=True)
hyp = pd.DataFrame([
    ["H1", "Coercive pressure", "HIGH"],
    ["H2", "Military preparation", "MEDIUM"],
    ["H3", "Strategic signaling", "HIGH"],
    ["H4", "Normalization", "HIGH"],
], columns=["ID", "Hypothesis", "Current assessment"])
st.dataframe(hyp, use_container_width=True, hide_index=True)

# ---------- Early warning ----------
st.markdown('<div class="section-title">🚨 Early-Warning Indicators</div>', unsafe_allow_html=True)
st.dataframe(
    signals,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Score": st.column_config.ProgressColumn(
            "Current score", min_value=0, max_value=100, format="%d"
        ),
    },
)

st.caption("MVP v0.1 • Demo/seed data. Automated source ingestion and historical baselines are the next development layer.")
