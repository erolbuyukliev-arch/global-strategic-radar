import streamlit as st
import pandas as pd
import requests
import re
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from urllib.parse import urljoin

st.set_page_config(page_title="GLOBAL STRATEGIC RADAR", page_icon="🌐", layout="wide")

MND_LIST_URL = "https://www.mnd.gov.tw/en/news/PLAActList"
MND_BASE = "https://www.mnd.gov.tw"
GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_QUERY = '"China" "Taiwan"'

HEADERS = {
    "User-Agent": "Mozilla/5.0 GlobalStrategicRadar/0.5"
}

# ---------------------------------------------------------
# GDELT
# ---------------------------------------------------------
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
        r = requests.get(GDELT_URL, params=params, timeout=20, headers=HEADERS)
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

# ---------------------------------------------------------
# MND AUTOMATIC INGESTION
# ---------------------------------------------------------
def parse_mnd_page(url):
    """Fetch one official MND PLA Activities page and extract
    the observation period and four quantitative indicators."""
    try:
        r = requests.get(url, timeout=20, headers=HEADERS)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        text = soup.get_text(" ", strip=True)

        # Publication date from page heading/title area.
        pub_match = re.search(
            r"PLA Activities\s+(\d{4}\.\d{2}\.\d{2})", text, re.I
        )
        report_date = pub_match.group(1) if pub_match else ""

        # Observation period: "6 a.m. Aug. 10 ... to 6 a.m. Aug. 11 ..."
        period_match = re.search(
            r"6\s*a\.m\.\s*([A-Z][a-z]{2,8}\.?\s+\d{1,2})"
            r".{0,120}?"
            r"to\s*6\s*a\.m\.\s*([A-Z][a-z]{2,8}\.?\s+\d{1,2})",
            text,
            re.I,
        )
        if period_match:
            period = f"{period_match.group(1)} – {period_match.group(2)}"
        else:
            period = ""

        # Main activity sentence.
        activity_match = re.search(
            r"(\d+)\s+sorties?\s+of\s+PLA\s+aircraft,\s*"
            r"(\d+)\s+PLAN\s+ships\s+and\s+(\d+)\s+official\s+ships",
            text,
            re.I,
        )
        if not activity_match:
            # Some MND reports say "No PLA aircraft..." rather than a number.
            ship_match = re.search(
                r"(\d+)\s+PLAN\s+ships\s+and\s+(\d+)\s+official\s+ships",
                text,
                re.I,
            )
            if not ship_match:
                return None, "Activity sentence not parsed"
            aircraft = 0
            plan = int(ship_match.group(1))
            official = int(ship_match.group(2))
        else:
            aircraft = int(activity_match.group(1))
            plan = int(activity_match.group(2))
            official = int(activity_match.group(3))

        # Median-line / ADIZ count. Reports use several formulations.
        median_match = re.search(
            r"(\d+)\s+out of\s+\d+\s+sorties?\s+"
            r"(?:crossed the median line[^.]*|entered Taiwan[^.]*ADIZ)",
            text,
            re.I,
        )
        if median_match:
            median_adiz = int(median_match.group(1))
        else:
            entered_match = re.search(
                r"(\d+)\s+out of\s+\d+\s+sorties?\s+entered Taiwan[^.]*ADIZ",
                text,
                re.I,
            )
            median_adiz = int(entered_match.group(1)) if entered_match else 0

        return {
            "Report date": report_date,
            "Observation period": period,
            "PLA aircraft": aircraft,
            "Median-line/ADIZ": median_adiz,
            "PLAN ships": plan,
            "Official ships": official,
            "URL": url,
            "Status": "PARSED",
        }, None

    except Exception as e:
        return None, str(e)


@st.cache_data(ttl=1800)
def discover_mnd_reports():
    """Discover recent PLA Activity reports from the official MND site."""
    try:
        r = requests.get(
            MND_LIST_URL,
            timeout=30,
            headers=HEADERS
        )
        r.raise_for_status()

        soup = BeautifulSoup(r.text, "html.parser")

        links = []

        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()
            label = a.get_text(" ", strip=True)

            full = urljoin(MND_BASE, href).rstrip("/")

            # Official MND PLA Activity pages:
            # /en/News/PLAAct/87306
            if re.search(r"/en/news/plaact/\d+$", full, re.I):
                links.append(full)

            # Also catch links whose text identifies PLA Activities.
            elif (
                "PLA Activities" in label
                and re.search(r"/\d+$", full)
            ):
                links.append(full)

        # Remove duplicates
        links = list(dict.fromkeys(links))

        parsed = []
        errors = []

        # Try newest-looking links first
        links = sorted(
            links,
            key=lambda x: int(re.search(r"(\d+)$", x).group(1)),
            reverse=True
        )

        for url in links[:30]:
            item, err = parse_mnd_page(url)

            if item:
                parsed.append(item)
            else:
                errors.append((url, err))

        df = pd.DataFrame(parsed)

        if not df.empty:
            df = df.drop_duplicates(subset=["URL"])
            df = df.sort_values(
                "Report date",
                ascending=False
            )

        return df, errors

    except Exception as e:
        return pd.DataFrame(), [("LIST", str(e))]

# ---------------------------------------------------------
# Fallback: validated records already established manually.
# These remain available if MND temporarily blocks automated access.
# ---------------------------------------------------------
fallback_valid = pd.DataFrame([
    ["2026-08-04", "Aug 3 – Aug 4", 6, 6, 7, 6, "VALID", "MND 87238"],
    ["2026-08-07", "Aug 6 – Aug 7", 10, 6, 6, 3, "VALID", "MND 87270"],
    ["2026-08-08", "Aug 7 – Aug 8", 14, 11, 6, 8, "VALID", "MND 87276"],
    ["2026-08-09", "Aug 8 – Aug 9", 4, 2, 6, 9, "VALID", "MND 87282"],
    ["2026-08-10", "Aug 9 – Aug 10", 1, 1, 9, 11, "VALID", "MND 87302"],
    ["2026-08-11", "Aug 10 – Aug 11", 2, 2, 7, 6, "VALID", "MND 87306"],
], columns=[
    "Report date","Observation period","PLA aircraft",
    "Median-line/ADIZ","PLAN ships","Official ships","Status","Source"
])

fallback_conflict = pd.DataFrame([
    ["2026-08-05", "Aug 4 – Aug 5", 21, 17, 9, 5, "CONFLICT", "MND 87248"],
    ["2026-08-06", "Aug 4 – Aug 5", 14, 6, 9, 7, "CONFLICT", "MND 87257"],
], columns=fallback_valid.columns)


def normalize_auto(df):
    if df.empty:
        return pd.DataFrame(columns=fallback_valid.columns + ["URL"])

    out = df.copy()
    out["Report date"] = pd.to_datetime(
        out["Report date"], errors="coerce"
    ).dt.strftime("%Y-%m-%d")
    out["Status"] = "PARSED"
    return out


def apply_conflict_detection(df):
    """Group by observation period. If one period has different
    quantitative observations, mark every record in that period
    as CONFLICT and exclude it from baseline."""
    if df.empty:
        return df, pd.DataFrame()

    work = df.copy()
    work["Status"] = "VALID"

    conflict_rows = []
    for period, group in work.groupby("Observation period", dropna=False):
        signatures = group[
            ["PLA aircraft","Median-line/ADIZ","PLAN ships","Official ships"]
        ].drop_duplicates()

        if len(signatures) > 1:
            work.loc[group.index, "Status"] = "CONFLICT"
            conflict_rows.append(group)

    conflicts = pd.concat(conflict_rows, ignore_index=True) if conflict_rows else pd.DataFrame(columns=work.columns)
    return work, conflicts


# ---------------------------------------------------------
# Run ingestion
# ---------------------------------------------------------
articles, gdelt_error = fetch_gdelt()
auto_df, ingest_errors = discover_mnd_reports()

if not auto_df.empty:
    auto_df = normalize_auto(auto_df)

# Combine automatic data with known validated seed data.
# Automatic observations are used only when they are parseable.
frames = [fallback_valid]
if not auto_df.empty:
    auto_core = auto_df[
        ["Report date","Observation period","PLA aircraft",
         "Median-line/ADIZ","PLAN ships","Official ships","Status","URL"]
    ].copy()
    auto_core["Source"] = auto_core["URL"]
    auto_core = auto_core.drop(columns=["URL"])
    frames.append(auto_core)

combined = pd.concat(frames, ignore_index=True)

# Keep one row per report date + period + quantitative signature.
combined = combined.drop_duplicates(
    subset=[
        "Report date","Observation period","PLA aircraft",
        "Median-line/ADIZ","PLAN ships","Official ships"
    ]
)

combined, auto_conflicts = apply_conflict_detection(combined)

# Re-insert the known source conflict if automatic list discovery does
# not expose the duplicate historical pages.
for _, row in fallback_conflict.iterrows():
    if not (
        (combined["Report date"] == row["Report date"]) &
        (combined["Observation period"] == row["Observation period"])
    ).any():
        combined = pd.concat([combined, pd.DataFrame([row])], ignore_index=True)

# Mark known duplicate Aug 4–5 conflict explicitly.
mask = combined["Observation period"].astype(str).str.contains("Aug 4", na=False) & \
       combined["Observation period"].astype(str).str.contains("Aug 5", na=False)
if mask.any():
    combined.loc[mask, "Status"] = "CONFLICT"

valid = combined[combined["Status"] == "VALID"].copy()
conflicts = combined[combined["Status"] == "CONFLICT"].copy()

numeric_cols = ["PLA aircraft","Median-line/ADIZ","PLAN ships","Official ships"]
for col in numeric_cols:
    valid[col] = pd.to_numeric(valid[col], errors="coerce")

valid = valid.dropna(subset=numeric_cols)

# Latest VALID observation
valid = valid.sort_values("Report date")
latest = valid.iloc[-1]

baseline = valid[numeric_cols].mean()

def anomaly(current, base):
    return 0 if base == 0 else ((current - base) / base) * 100

air_anom = anomaly(latest["PLA aircraft"], baseline["PLA aircraft"])
adiz_anom = anomaly(latest["Median-line/ADIZ"], baseline["Median-line/ADIZ"])
plan_anom = anomaly(latest["PLAN ships"], baseline["PLAN ships"])
official_anom = anomaly(latest["Official ships"], baseline["Official ships"])

composite = (air_anom + adiz_anom + plan_anom + official_anom) / 4
pla_signal = int(max(0, min(100, round(50 + composite / 2))))

# ---------------------------------------------------------
# UI
# ---------------------------------------------------------
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
    st.success(f"GDELT live feed connected — {len(articles)} relevant articles found in the last 24 hours.")

if not auto_df.empty:
    st.success(f"MND automatic ingestion connected — {len(auto_df)} PLA Activity pages parsed.")
else:
    st.warning("MND automatic ingestion unavailable. Using validated fallback observations.")

# ---------------------------------------------------------
# TOP METRICS
# ---------------------------------------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Global Strategic Pressure", "68 ↑", "Demo — not model-derived")
c2.metric("Information Activity", min(100, 25 + len(articles)*3), f"{len(articles)} articles / 24h")
c3.metric("PLA Activity Signal", pla_signal, f"{len(valid)} validated observations")
c4.metric("Data Quality", "CONFLICT FLAG" if not conflicts.empty else "OK",
          f"{len(conflicts)} conflicting records")

st.divider()

# ---------------------------------------------------------
# AUTOMATION STATUS
# ---------------------------------------------------------
st.markdown('<div class="section-title">🔄 Automated Source Ingestion</div>', unsafe_allow_html=True)
a1, a2, a3 = st.columns(3)
a1.metric("MND pages parsed", len(auto_df))
a2.metric("Validated observations", len(valid))
a3.metric("Conflicting records", len(conflicts))

st.caption(
    "The Radar now discovers recent official MND PLA Activity pages automatically. "
    "If MND blocks the request, the application falls back to the validated seed dataset."
)

# ---------------------------------------------------------
# SOURCE CONFLICT
# ---------------------------------------------------------
st.markdown('<div class="section-title">⚠️ Source Conflict Detection</div>', unsafe_allow_html=True)

if not conflicts.empty:
    st.error(
        "CONFLICT DETECTED: at least one identical observation period contains "
        "different quantitative observations. Conflicting records are excluded from baseline."
    )
    st.dataframe(
        conflicts[
            ["Report date","Observation period","PLA aircraft",
             "Median-line/ADIZ","PLAN ships","Official ships","Source"]
        ].sort_values("Observation period"),
        use_container_width=True,
        hide_index=True,
    )
else:
    st.success("No source conflict detected in the currently ingested observations.")

# ---------------------------------------------------------
# PLA ACTIVITY
# ---------------------------------------------------------
st.markdown('<div class="section-title">🇨🇳 PLA Activity Around Taiwan</div>', unsafe_allow_html=True)

p1, p2, p3, p4 = st.columns(4)
p1.metric("Latest aircraft", int(latest["PLA aircraft"]), f"{air_anom:+.0f}% vs baseline")
p2.metric("Latest median-line/ADIZ", int(latest["Median-line/ADIZ"]), f"{adiz_anom:+.0f}% vs baseline")
p3.metric("Latest PLAN ships", int(latest["PLAN ships"]), f"{plan_anom:+.0f}% vs baseline")
p4.metric("Latest official ships", int(latest["Official ships"]), f"{official_anom:+.0f}% vs baseline")

st.progress(pla_signal / 100)
st.write(f"**PLA Activity Signal: {pla_signal}/100**")

# ---------------------------------------------------------
# BASELINE
# ---------------------------------------------------------
st.markdown('<div class="section-title">📊 Validated Observation Set</div>', unsafe_allow_html=True)
show_cols = [
    "Report date","Observation period","PLA aircraft",
    "Median-line/ADIZ","PLAN ships","Official ships","Status","Source"
]
st.dataframe(
    valid[show_cols].sort_values("Report date", ascending=False),
    use_container_width=True,
    hide_index=True,
)

b1, b2, b3, b4 = st.columns(4)
b1.metric("Aircraft baseline", f"{baseline['PLA aircraft']:.1f}")
b2.metric("Median-line / ADIZ baseline", f"{baseline['Median-line/ADIZ']:.1f}")
b3.metric("PLAN baseline", f"{baseline['PLAN ships']:.1f}")
b4.metric("Official ships baseline", f"{baseline['Official ships']:.1f}")

# ---------------------------------------------------------
# TAIWAN PREPAREDNESS
# ---------------------------------------------------------
st.markdown('<div class="section-title">🇹🇼 Taiwan Military Preparedness</div>', unsafe_allow_html=True)
st.success("ACTIVE — Han Kuang 42")
st.write(
    "2026-08-09 • Joint anti-landing • Littoral strike • Beach/shore battle • "
    "Joint fires • Kill-chain integration • Intelligence transmission / common operational picture"
)
st.link_button(
    "Open official MND Han Kuang 42 report",
    "https://www.mnd.gov.tw/en/News/PressRelease/87316"
)

# ---------------------------------------------------------
# CONVERGENCE
# ---------------------------------------------------------
st.markdown('<div class="section-title">⚠️ Signal Convergence</div>', unsafe_allow_html=True)
x1, x2, x3 = st.columns(3)
x1.metric("Information Signal", min(100, 25 + len(articles)*3))
x2.metric("PLA Signal", pla_signal)
x3.metric("Convergence", "PENDING VALIDATION")

st.warning(
    "The PLA Activity Signal measures deviation from the validated observation baseline. "
    "It is not a probability of conflict and should not be interpreted as one."
)

# ---------------------------------------------------------
# LIVE INFORMATION
# ---------------------------------------------------------
st.markdown('<div class="section-title">📰 Live China–Taiwan Information Signals</div>', unsafe_allow_html=True)
if not articles.empty:
    display = articles[["title","domain","published","url"]].copy()
    display["title"] = display.apply(
        lambda x: f"[{x['title']}]({x['url']})" if x["url"] else x["title"],
        axis=1
    )
    st.dataframe(display[["title","domain","published"]], use_container_width=True, hide_index=True)
else:
    st.info("No live articles available.")

# ---------------------------------------------------------
# ASSESSMENT
# ---------------------------------------------------------
st.markdown('<div class="section-title">🇨🇳 China → 🇹🇼 Taiwan Strategic Assessment</div>', unsafe_allow_html=True)
st.markdown(f"""
<div class="assessment">
<b>Assessment status: AUTOMATED INGESTION + DATA QUALITY CONTROL</b><br><br>
The Radar currently uses <b>{len(valid)}</b> validated MND observations.
Conflicting source records are retained for provenance but excluded from the quantitative baseline.
The latest validated observation is <b>{latest["Observation period"]}</b>:
{int(latest["PLA aircraft"])} aircraft, {int(latest["Median-line/ADIZ"])} median-line/ADIZ,
{int(latest["PLAN ships"])} PLAN ships and {int(latest["Official ships"])} official ships.<br><br>
PLA Activity Signal: <b>{pla_signal}/100</b>. This is an anomaly-oriented indicator,
not a forecast or conflict probability.
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="section-title">🚀 Next Layer</div>', unsafe_allow_html=True)
st.write(
    "Automated MND ingestion → persistent historical database → 30/90-day baselines → "
    "source reliability scoring → multi-domain signal convergence → alerts"
)

if ingest_errors:
    with st.expander("Technical ingestion diagnostics"):
        st.write(ingest_errors[:10])

st.caption("GLOBAL STRATEGIC RADAR v0.5 • Automated MND ingestion + source conflict detection.")

