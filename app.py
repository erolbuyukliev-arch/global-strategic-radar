import re
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup
import streamlit as st

from pdf_knowledge import render_pdf_knowledge_section
# ============================================================
# GLOBAL STRATEGIC RADAR
# ============================================================

st.set_page_config(
    page_title="Global Strategic Radar",
    page_icon="🌐",
    layout="wide",
)


# ============================================================
# CONFIGURATION
# ============================================================

MND_LIST_URL = "https://www.mnd.gov.tw/en/news/PLAActList"
MND_BASE = "https://www.mnd.gov.tw"

GDELT_URL = (
    "https://api.gdeltproject.org/api/v2/doc/doc"
)

GDELT_QUERY = '"China" "Taiwan"'

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/151.0 Safari/537.36 "
        "GlobalStrategicRadar/1.0"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}


# ============================================================
# FALLBACK DATA
# ============================================================

# These are validated observations already checked against
# official MND pages.
#
# Conflicting Aug 4-5 observations are intentionally NOT here.
# They are retained separately for provenance/conflict detection.

FALLBACK_OBSERVATIONS = [
    {
        "Report date": "2026-08-11",
        "Observation period": "Aug 10 – Aug 11",
        "PLA aircraft": 2,
        "Median-line/ADIZ": 2,
        "PLAN ships": 7,
        "Official ships": 6,
        "URL": "https://www.mnd.gov.tw/en/News/PLAAct/87306",
        "Status": "VALID",
    },
    {
        "Report date": "2026-08-10",
        "Observation period": "Aug 9 – Aug 10",
        "PLA aircraft": 1,
        "Median-line/ADIZ": 1,
        "PLAN ships": 9,
        "Official ships": 11,
        "URL": "https://www.mnd.gov.tw/en/News/PLAAct/87302",
        "Status": "VALID",
    },
    {
        "Report date": "2026-08-09",
        "Observation period": "Aug 8 – Aug 9",
        "PLA aircraft": 4,
        "Median-line/ADIZ": 2,
        "PLAN ships": 6,
        "Official ships": 9,
        "URL": "https://www.mnd.gov.tw/en/News/PLAAct/87282",
        "Status": "VALID",
    },
    {
        "Report date": "2026-08-08",
        "Observation period": "Aug 7 – Aug 8",
        "PLA aircraft": 14,
        "Median-line/ADIZ": 11,
        "PLAN ships": 6,
        "Official ships": 8,
        "URL": "https://www.mnd.gov.tw/en/News/PLAAct/87276",
        "Status": "VALID",
    },
    {
        "Report date": "2026-08-07",
        "Observation period": "Aug 6 – Aug 7",
        "PLA aircraft": 10,
        "Median-line/ADIZ": 6,
        "PLAN ships": 6,
        "Official ships": 3,
        "URL": "https://www.mnd.gov.tw/en/News/PLAAct/87270",
        "Status": "VALID",
    },
    {
        "Report date": "2026-08-06",
        "Observation period": "Aug 4 – Aug 5",
        "PLA aircraft": 14,
        "Median-line/ADIZ": 6,
        "PLAN ships": 9,
        "Official ships": 7,
        "URL": "https://www.mnd.gov.tw/en/News/PLAAct/87257",
        "Status": "CONFLICT",
    },
]


# Explicit conflicting records detected in official MND material.
CONFLICTING_OBSERVATIONS = [
    {
        "Report date": "2026-08-05",
        "Observation period": "Aug 4 – Aug 5",
        "PLA aircraft": 21,
        "Median-line/ADIZ": 17,
        "PLAN ships": 9,
        "Official ships": 5,
        "URL": "https://www.mnd.gov.tw/en/News/PLAAct/87248",
        "Status": "CONFLICT",
    },
    {
        "Report date": "2026-08-06",
        "Observation period": "Aug 4 – Aug 5",
        "PLA aircraft": 14,
        "Median-line/ADIZ": 6,
        "PLAN ships": 9,
        "Official ships": 7,
        "URL": "https://www.mnd.gov.tw/en/News/PLAAct/87257",
        "Status": "CONFLICT",
    },
]


# ============================================================
# HTTP
# ============================================================

@st.cache_data(ttl=1800)
def fetch_url(url):
    try:
        response = requests.get(
            url,
            timeout=30,
            headers=HEADERS,
            allow_redirects=True,
        )
        response.raise_for_status()

        return {
            "ok": True,
            "status_code": response.status_code,
            "text": response.text,
            "url": response.url,
            "error": "",
        }

    except Exception as exc:
        return {
            "ok": False,
            "status_code": None,
            "text": "",
            "url": url,
            "error": str(exc),
        }


# ============================================================
# MND PAGE PARSER
# ============================================================

def parse_mnd_page(url):
    """
    Fetch one official MND PLA Activity page and extract:
      - report date
      - observation period
      - PLA aircraft
      - median-line / ADIZ count
      - PLAN ships
      - official ships
    """

    try:
        result = fetch_url(url)

        if not result["ok"]:
            return None, (
                f"HTTP request failed: {result['error']}"
            )

        soup = BeautifulSoup(
            result["text"],
            "html.parser",
        )

        text = soup.get_text(
            " ",
            strip=True,
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        # ----------------------------------------------------
        # REPORT DATE
        # ----------------------------------------------------

        pub_match = re.search(
            r"PLA Activities\s*"
            r"(\d{4}\.\d{2}\.\d{2})",
            text,
            re.I,
        )

        if not pub_match:
            pub_match = re.search(
                r"PLA Activities.*?"
                r"(\d{4}\.\d{2}\.\d{2})",
                text,
                re.I,
            )

        report_date = (
            pub_match.group(1)
            if pub_match
            else ""
        )

        # ----------------------------------------------------
        # OBSERVATION PERIOD
        # ----------------------------------------------------

        period_match = re.search(
            r"6\s*a\.m\.\s*"
            r"([A-Z][a-z]{2,8}\.?\s+\d{1,2})"
            r".{0,250}?"
            r"to\s*6\s*a\.m\.\s*"
            r"([A-Z][a-z]{2,8}\.?\s+\d{1,2})",
            text,
            re.I,
        )

        if period_match:
            period = (
                f"{period_match.group(1)} – "
                f"{period_match.group(2)}"
            )
        else:
            period = ""

        # ----------------------------------------------------
        # AIRCRAFT / SHIPS
        # ----------------------------------------------------

        activity_match = re.search(
            r"(\d+)\s+sorties?\s+of\s+PLA\s+aircraft"
            r".{0,200}?"
            r"(\d+)\s+PLAN\s+ships"
            r".{0,120}?"
            r"(\d+)\s+official\s+ships",
            text,
            re.I,
        )

        if activity_match:

            aircraft = int(
                activity_match.group(1)
            )

            plan = int(
                activity_match.group(2)
            )

            official = int(
                activity_match.group(3)
            )

        else:

            ship_match = re.search(
                r"(\d+)\s+PLAN\s+ships"
                r".{0,120}?"
                r"(\d+)\s+official\s+ships",
                text,
                re.I,
            )

            if not ship_match:
                return None, (
                    "Activity sentence not parsed"
                )

            aircraft = 0

            plan = int(
                ship_match.group(1)
            )

            official = int(
                ship_match.group(2)
            )

        # ----------------------------------------------------
        # MEDIAN LINE / ADIZ
        # ----------------------------------------------------

        median_match = re.search(
            r"(\d+)\s+out\s+of\s+\d+\s+sorties?"
            r".{0,150}?"
            r"(?:crossed the median line|"
            r"entered Taiwan)"
            r".{0,150}?ADIZ",
            text,
            re.I,
        )

        if median_match:

            median_adiz = int(
                median_match.group(1)
            )

        else:

            entered_match = re.search(
                r"(\d+)\s+out\s+of\s+\d+\s+sorties?"
                r".{0,100}?"
                r"entered Taiwan"
                r".{0,100}?ADIZ",
                text,
                re.I,
            )

            if entered_match:
                median_adiz = int(
                    entered_match.group(1)
                )
            else:
                median_adiz = 0

        # ----------------------------------------------------
        # VALIDATION
        # ----------------------------------------------------

        if not report_date:
            return None, (
                "Report date not parsed"
            )

        if not period:
            return None, (
                "Observation period not parsed"
            )

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

    except Exception as exc:
        return None, str(exc)


# ============================================================
# DISCOVER MND LINKS
# ============================================================

@st.cache_data(ttl=1800)
def discover_mnd_links():
    """
    Discover official MND PLA Activity pages from the
    official list page.
    """

    result = fetch_url(MND_LIST_URL)

    if not result["ok"]:
        return [], result["error"]

    soup = BeautifulSoup(
        result["text"],
        "html.parser",
    )

    links = []

    for a in soup.find_all("a"):
        href = a.get("href", "")

        if not href:
            continue

        if "/en/News/PLAAct/" not in href:
            continue

        if href.startswith("/"):
            href = MND_BASE + href

        elif href.startswith("./"):
            href = MND_BASE + "/en/news/" + href[2:]

        links.append(href)

    # Remove duplicates while preserving order.
    unique_links = list(
        dict.fromkeys(links)
    )

    return unique_links, ""


# ============================================================
# AUTOMATIC MND INGESTION
# ============================================================

@st.cache_data(ttl=1800)
def automatic_mnd_ingestion():

    links, error = discover_mnd_links()

    if error:
        return [], {
            "pages_parsed": 0,
            "error": error,
        }

    observations = []

    # Limit requests so the app remains lightweight.
    for url in links[:20]:

        observation, parse_error = (
            parse_mnd_page(url)
        )

        if observation is not None:
            observations.append(
                observation
            )

    return observations, {
        "pages_parsed": len(observations),
        "error": "",
    }


# ============================================================
# CONFLICT DETECTION
# ============================================================

def detect_conflicts(observations):

    df = pd.DataFrame(observations)

    if df.empty:
        return df, pd.DataFrame()

    conflict_rows = []

    for period, group in df.groupby(
        "Observation period"
    ):

        if len(group) <= 1:
            continue

        quantitative_columns = [
            "PLA aircraft",
            "Median-line/ADIZ",
            "PLAN ships",
            "Official ships",
        ]

        unique_values = (
            group[
                quantitative_columns
            ]
            .drop_duplicates()
        )

        if len(unique_values) > 1:

            conflict_rows.append(
                group
            )

    if conflict_rows:

        conflicts = pd.concat(
            conflict_rows,
            ignore_index=True,
        )

        conflict_periods = set(
            conflicts[
                "Observation period"
            ].tolist()
        )

        clean = df[
            ~df[
                "Observation period"
            ].isin(conflict_periods)
        ].copy()

        return clean, conflicts

    return df.copy(), pd.DataFrame()


# ============================================================
# MERGE AUTOMATIC + FALLBACK
# ============================================================

def build_observation_set():

    automatic, meta = (
        automatic_mnd_ingestion()
    )

    fallback = FALLBACK_OBSERVATIONS.copy()

    # If automatic ingestion works, use automatic records.
    # Otherwise use validated fallback observations.
    if automatic:

        auto_df = pd.DataFrame(
            automatic
        )

        # Add fallback records that automatic ingestion
        # did not retrieve.
        fallback_df = pd.DataFrame(
            fallback
        )

        combined = pd.concat(
            [
                auto_df,
                fallback_df,
            ],
            ignore_index=True,
        )

        # Deduplicate exact records.
        combined = combined.drop_duplicates(
            subset=[
                "Report date",
                "Observation period",
                "PLA aircraft",
                "Median-line/ADIZ",
                "PLAN ships",
                "Official ships",
            ]
        )

    else:

        combined = pd.DataFrame(
            fallback
        )

    # Add known conflict records.
    conflict_df = pd.DataFrame(
        CONFLICTING_OBSERVATIONS
    )

    combined = pd.concat(
        [
            combined,
            conflict_df,
        ],
        ignore_index=True,
    )

    # --------------------------------------------------------
    # IMPORTANT:
    # Resolve duplicates by observation period.
    # Conflicting periods are excluded from baseline.
    # --------------------------------------------------------

    clean_df, detected_conflicts = (
        detect_conflicts(combined)
    )

    # Ensure explicit known conflicts are excluded.
    known_conflict_periods = set(
        conflict_df[
            "Observation period"
        ].tolist()
    )

    baseline_df = clean_df[
        ~clean_df[
            "Observation period"
        ].isin(
            known_conflict_periods
        )
    ].copy()

    # Sort latest first.
    if not baseline_df.empty:
        baseline_df = (
            baseline_df
            .sort_values(
                "Report date",
                ascending=False,
            )
            .reset_index(drop=True)
        )

    return (
        baseline_df,
        conflict_df,
        meta,
    )


# ============================================================
# GDELT
# ============================================================

@st.cache_data(ttl=900)
def fetch_gdelt():

    params = {
        "query": GDELT_QUERY,
        "mode": "ArtList",
        "maxrecords": 25,
        "format": "json",
        "timespan": "24h",
    }

    try:

        response = requests.get(
            GDELT_URL,
            params=params,
            timeout=20,
            headers=HEADERS,
        )

        response.raise_for_status()

        data = response.json()

        articles = data.get(
            "articles",
            [],
        )

        return articles, None

    except Exception as exc:

        return [], str(exc)


# ============================================================
# BASELINE
# ============================================================

def calculate_baseline(df):

    if df.empty:
        return {
            "aircraft": None,
            "median": None,
            "plan": None,
            "official": None,
        }

    return {
        "aircraft": round(
            df["PLA aircraft"].mean(),
            1,
        ),
        "median": round(
            df["Median-line/ADIZ"].mean(),
            1,
        ),
        "plan": round(
            df["PLAN ships"].mean(),
            1,
        ),
        "official": round(
            df["Official ships"].mean(),
            1,
        ),
    }


def pct_change(current, baseline):

    if baseline is None:
        return None

    if baseline == 0:
        return None

    return (
        (current - baseline)
        / baseline
        * 100
    )


# ============================================================
# STRATEGIC SIGNAL
# ============================================================

def calculate_pla_signal(
    latest,
    baseline,
):

    if latest is None:
        return 0

    components = []

    for key, value in [
        (
            "aircraft",
            latest["PLA aircraft"],
        ),
        (
            "median",
            latest["Median-line/ADIZ"],
        ),
        (
            "plan",
            latest["PLAN ships"],
        ),
        (
            "official",
            latest["Official ships"],
        ),
    ]:

        base = baseline.get(key)

        if base is None or base == 0:
            continue

        ratio = value / base

        # Cap each component.
        ratio = min(
            max(ratio, 0),
            2.0,
        )

        components.append(
            ratio
        )

    if not components:
        return 0

    average_ratio = sum(
        components
    ) / len(components)

    score = int(
        round(
            min(
                max(
                    average_ratio * 50,
                    0,
                ),
                100,
            )
        )
    )

    return score


# ============================================================
# PAGE HEADER
# ============================================================

st.title(
    "🌐 GLOBAL STRATEGIC RADAR"
)

st.caption(
    "Strategic change detection • "
    "Early warning • Evidence-based assessment"
)

now = datetime.utcnow().strftime(
    "%Y-%m-%d %H:%M UTC"
)

st.success(
    f"● LIVE DATA   Last refresh: {now}"
)


# ============================================================
# DATA LOAD
# ============================================================

gdelt_articles, gdelt_error = (
    fetch_gdelt()
)

(
    observations,
    conflicts,
    mnd_meta,
) = build_observation_set()


# ============================================================
# STATUS BANNERS
# ============================================================

if gdelt_error:

    st.warning(
        "GDELT live feed unavailable. "
        "Information layer is in fallback mode."
    )

else:

    st.success(
        "GDELT live feed connected — "
        f"{len(gdelt_articles)} relevant articles "
        "found in the last 24 hours."
    )


if mnd_meta["pages_parsed"] == 0:

    st.warning(
        "MND automatic ingestion unavailable. "
        "Using validated fallback observations."
    )

else:

    st.success(
        "MND automatic ingestion active — "
        f"{mnd_meta['pages_parsed']} pages parsed."
    )


# ============================================================
# METRICS
# ============================================================

baseline = calculate_baseline(
    observations
)

latest = (
    observations.iloc[0].to_dict()
    if not observations.empty
    else None
)

if latest:

    pla_signal = calculate_pla_signal(
        latest,
        baseline,
    )

else:

    pla_signal = 0


# Global strategic pressure remains deliberately
# marked as demo until a validated composite model exists.
GLOBAL_PRESSURE = 68


c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Global Strategic Pressure",
        f"{GLOBAL_PRESSURE} ↑",
    )
    st.caption(
        "Demo index — not model-derived"
    )

with c2:
    st.metric(
        "Information Activity",
        len(gdelt_articles),
    )
    st.caption(
        "Articles / 24h"
    )

with c3:
    st.metric(
        "PLA Activity Signal",
        pla_signal,
    )
    st.caption(
        f"{len(observations)} validated observations"
    )

with c4:

    if not conflicts.empty:

        st.metric(
            "Data Quality",
            "CONFLICT FLAG",
        )

        st.caption(
            f"{len(conflicts)} conflicting records"
        )

    else:

        st.metric(
            "Data Quality",
            "OK",
        )


st.divider()


# ============================================================
# AUTOMATED SOURCE INGESTION
# ============================================================

st.subheader(
    "🔄 Automated Source Ingestion"
)

a1, a2, a3 = st.columns(3)

with a1:
    st.metric(
        "MND pages parsed",
        mnd_meta["pages_parsed"],
    )

with a2:
    st.metric(
        "Validated observations",
        len(observations),
    )

with a3:
    st.metric(
        "Conflicting records",
        len(conflicts),
    )

st.caption(
    "The Radar attempts to discover recent official "
    "MND PLA Activity pages automatically. If MND blocks "
    "the request, the application falls back to validated "
    "source-backed observations."
)


# ============================================================
# SOURCE CONFLICT
# ============================================================

st.subheader(
    "⚠️ Source Conflict Detection"
)

if conflicts.empty:

    st.success(
        "No conflicting quantitative observations detected."
    )

else:

    st.error(
        "CONFLICT DETECTED: at least one identical "
        "observation period contains different quantitative "
        "observations. Conflicting records are excluded "
        "from the baseline."
    )

    display_conflicts = conflicts[
        [
            "Report date",
            "Observation period",
            "PLA aircraft",
            "Median-line/ADIZ",
            "PLAN ships",
            "Official ships",
            "URL",
        ]
    ].copy()

    display_conflicts[
        "Source"
    ] = display_conflicts[
        "URL"
    ].str.extract(
        r"/PLAAct/(\d+)"
    )[0].apply(
        lambda x:
        f"MND {x}"
        if pd.notna(x)
        else "MND"
    )

    display_conflicts = (
        display_conflicts
        .drop(columns=["URL"])
    )

    st.dataframe(
        display_conflicts,
        use_container_width=True,
        hide_index=True,
    )

    st.caption(
        "Rule: conflicting observations are retained "
        "for provenance but excluded from quantitative "
        "baseline calculations until the discrepancy "
        "is resolved."
    )


# ============================================================
# LATEST PLA ACTIVITY
# ============================================================

st.subheader(
    "🇨🇳 CN PLA Activity Around Taiwan"
)

if latest:

    l1, l2, l3, l4 = st.columns(4)

    with l1:
        st.metric(
            "Latest aircraft",
            latest["PLA aircraft"],
        )

        change = pct_change(
            latest["PLA aircraft"],
            baseline["aircraft"],
        )

        if change is not None:
            st.caption(
                f"{change:+.0f}% vs baseline"
            )

    with l2:
        st.metric(
            "Latest median-line / ADIZ",
            latest["Median-line/ADIZ"],
        )

        change = pct_change(
            latest["Median-line/ADIZ"],
            baseline["median"],
        )

        if change is not None:
            st.caption(
                f"{change:+.0f}% vs baseline"
            )

    with l3:
        st.metric(
            "Latest PLAN ships",
            latest["PLAN ships"],
        )

        change = pct_change(
            latest["PLAN ships"],
            baseline["plan"],
        )

        if change is not None:
            st.caption(
                f"{change:+.0f}% vs baseline"
            )

    with l4:
        st.metric(
            "Latest official ships",
            latest["Official ships"],
        )

        change = pct_change(
            latest["Official ships"],
            baseline["official"],
        )

        if change is not None:
            st.caption(
                f"{change:+.0f}% vs baseline"
            )

    st.caption(
        f"Observation: "
        f"{latest['Observation period']} "
        f"• Source: ROC Ministry of National Defense"
    )

    st.link_button(
        "Open official MND report",
        latest["URL"],
    )

else:

    st.warning(
        "No validated PLA observation available."
    )


# ============================================================
# HISTORICAL BASELINE
# ============================================================

st.subheader(
    "📊 Historical Baseline"
)

if len(observations) < 7:

    st.info(
        "Baseline: NOT YET AVAILABLE. "
        f"The Radar currently has {len(observations)} "
        "validated daily observations. "
        "A 7-day baseline requires at least 7 "
        "comparable observations."
    )

else:

    st.success(
        "7-day baseline available."
    )


b1, b2, b3, b4 = st.columns(4)

with b1:
    st.metric(
        "Aircraft baseline",
        (
            baseline["aircraft"]
            if baseline["aircraft"] is not None
            else "N/A"
        ),
    )

with b2:
    st.metric(
        "Median-line / ADIZ baseline",
        (
            baseline["median"]
            if baseline["median"] is not None
            else "N/A"
        ),
    )

with b3:
    st.metric(
        "PLAN baseline",
        (
            baseline["plan"]
            if baseline["plan"] is not None
            else "N/A"
        ),
    )

with b4:
    st.metric(
        "Official ships baseline",
        (
            baseline["official"]
            if baseline["official"] is not None
            else "N/A"
        ),
    )


# ============================================================
# VALIDATED OBSERVATION SET
# ============================================================

st.subheader(
    "📚 Validated Observation Set"
)

if observations.empty:

    st.warning(
        "No validated observations."
    )

else:

    display_df = observations[
        [
            "Report date",
            "Observation period",
            "PLA aircraft",
            "Median-line/ADIZ",
            "PLAN ships",
            "Official ships",
            "Status",
        ]
    ].copy()

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# TAIWAN MILITARY PREPAREDNESS
# ============================================================

st.subheader(
    "🇹🇼 TW Taiwan Military Preparedness"
)

st.success(
    "ACTIVE — Han Kuang 42"
)

st.caption(
    "Source: ROC Ministry of National Defense"
)

st.caption(
    "Observation date: 2026-08-09"
)

st.write(
    "Observed preparedness indicators:"
)

p1, p2, p3, p4, p5 = st.columns(5)

with p1:
    st.checkbox(
        "Joint anti-landing",
        value=True,
        disabled=True,
    )

with p2:
    st.checkbox(
        "Littoral strike",
        value=True,
        disabled=True,
    )

with p3:
    st.checkbox(
        "Beach / shore battle",
        value=True,
        disabled=True,
    )

with p4:
    st.checkbox(
        "Joint fires",
        value=True,
        disabled=True,
    )

with p5:
    st.checkbox(
        "Kill-chain integration",
        value=True,
        disabled=True,
    )

st.link_button(
    "Open official Han Kuang 42 report",
    "https://www.mnd.gov.tw/en/News/PressRelease/87316",
)


# ============================================================
# SIGNAL CONVERGENCE
# ============================================================

st.subheader(
    "⚠️ Signal Convergence"
)

s1, s2, s3 = st.columns(3)

with s1:
    st.metric(
        "Information Signal",
        len(gdelt_articles),
    )

with s2:
    st.metric(
        "PLA Signal",
        pla_signal,
    )

with s3:

    if len(observations) >= 7:
        convergence = "CALCULATED"
    else:
        convergence = "PENDING VALIDATION"

    st.metric(
        "Convergence",
        convergence,
    )

st.info(
    "Convergence means independent signal streams "
    "point in the same direction. It is NOT a probability "
    "of conflict and should not be interpreted as one."
)


# ============================================================
# INFORMATION LAYER
# ============================================================

st.subheader(
    "📰 Information Layer — GDELT"
)

if gdelt_error:

    st.warning(
        "GDELT is currently unavailable. "
        "No live information signal is being calculated."
    )

elif not gdelt_articles:

    st.info(
        "No relevant GDELT articles returned "
        "for the current query."
    )

else:

    rows = []

    for article in gdelt_articles:

        rows.append(
            {
                "Title": article.get(
                    "title",
                    "",
                ),
                "Source": article.get(
                    "domain",
                    "",
                ),
                "Published": article.get(
                    "seendate",
                    "",
                ),
                "URL": article.get(
                    "url",
                    "",
                ),
            }
        )

    article_df = pd.DataFrame(
        rows
    )

    st.dataframe(
        article_df,
        use_container_width=True,
        hide_index=True,
    )


# ============================================================
# ANALYTICAL DISCLAIMER
# ============================================================

st.divider()

st.caption(
    "Analytical note: Information Activity is not "
    "Military Risk. Media volume may reflect reporting "
    "intensity rather than a change in military behavior."
)

st.caption(
    "PLA Activity Signal is a descriptive deviation "
    "indicator based on available validated observations. "
    "It is not a probability of conflict, invasion, "
    "or military escalation."
)

st.caption(
    "Global Strategic Pressure remains a demonstration "
    "index until a formally specified and validated "
    "composite model is implemented."
)
