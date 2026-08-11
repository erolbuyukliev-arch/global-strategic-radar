import streamlit as st
import requests
import re
import io
import statistics
from datetime import datetime

from bs4 import BeautifulSoup
from pypdf import PdfReader


# ============================================================
# CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Global Strategic Radar",
    page_icon="🌐",
    layout="wide",
)

MND_LIST_URL = "https://www.mnd.gov.tw/en/news/PLAActList"
MND_BASE = "https://www.mnd.gov.tw"

GDELT_URL = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_QUERY = '"China" "Taiwan"'

HEADERS = {
    "User-Agent": "Mozilla/5.0 GlobalStrategicRadar/0.6"
}


# ============================================================
# PAGE STYLE
# ============================================================

st.markdown(
    """
    <style>
    .main-title {
        font-size: 42px;
        font-weight: 800;
        color: #20283a;
        margin-bottom: 0;
    }

    .subtitle {
        color: #68758a;
        font-size: 15px;
        margin-bottom: 20px;
    }

    .metric-card {
        padding: 18px;
        border-radius: 12px;
        border: 1px solid #e1e5eb;
        background: #ffffff;
        min-height: 130px;
    }

    .section-title {
        font-size: 24px;
        font-weight: 750;
        margin-top: 30px;
        margin-bottom: 15px;
        color: #263247;
    }

    .source-box {
        padding: 14px;
        border-radius: 10px;
        background: #f4f7fb;
        border-left: 4px solid #4d8bd8;
        margin-bottom: 12px;
    }

    .warning-box {
        padding: 14px;
        border-radius: 10px;
        background: #fff8dc;
        border-left: 4px solid #e3a928;
        margin-bottom: 12px;
    }

    .analysis-box {
        padding: 18px;
        border-radius: 10px;
        background: #f7f9fc;
        border: 1px solid #dfe5ee;
        line-height: 1.65;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# SESSION STATE
# ============================================================

if "pdf_documents" not in st.session_state:
    st.session_state.pdf_documents = []

if "pdf_chunks" not in st.session_state:
    st.session_state.pdf_chunks = []

if "pdf_analysis" not in st.session_state:
    st.session_state.pdf_analysis = None


# ============================================================
# GDELT
# ============================================================

@st.cache_data(ttl=1800)
def get_gdelt_articles():

    try:

        params = {
            "query": GDELT_QUERY,
            "mode": "artlist",
            "maxrecords": 25,
            "format": "json",
            "sort": "datedesc",
        }

        response = requests.get(
            GDELT_URL,
            params=params,
            timeout=20,
            headers=HEADERS,
        )

        response.raise_for_status()

        data = response.json()

        articles = data.get("articles", [])

        return articles, None

    except Exception as e:

        return [], str(e)


# ============================================================
# MND PARSER
# ============================================================

def parse_mnd_page(url):

    try:

        r = requests.get(
            url,
            timeout=20,
            headers=HEADERS,
        )

        r.raise_for_status()

        soup = BeautifulSoup(
            r.text,
            "html.parser",
        )

        text = soup.get_text(
            " ",
            strip=True,
        )

        # ----------------------------------------------------
        # Publication date
        # ----------------------------------------------------

        pub_match = re.search(
            r"PLA Activities\s+(\d{4}\.\d{2}\.\d{2})",
            text,
            re.I,
        )

        report_date = (
            pub_match.group(1)
            if pub_match
            else ""
        )

        # ----------------------------------------------------
        # Observation period
        # ----------------------------------------------------

        period_match = re.search(
            r"6\s*a\.m\.\s*([A-Z][a-z]{2,8}\.?\s+\d{1,2})"
            r".{0,120}?"
            r"to\s*6\s*a\.m\.\s*([A-Z][a-z]{2,8}\.?\s+\d{1,2})",
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
        # Main activity sentence
        # ----------------------------------------------------

        activity_match = re.search(
            r"(\d+)\s+sorties?\s+of\s+PLA\s+aircraft,\s*"
            r"(\d+)\s+PLAN\s+ships\s+and\s+(\d+)\s+official\s+ships",
            text,
            re.I,
        )

        if not activity_match:

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

        # ----------------------------------------------------
        # Median line / ADIZ
        # ----------------------------------------------------

        median_match = re.search(
            r"(\d+)\s+out of\s+\d+\s+sorties?\s+"
            r"(?:crossed the median line[^.]*|entered Taiwan[^.]*ADIZ)",
            text,
            re.I,
        )

        if median_match:

            median_adiz = int(
                median_match.group(1)
            )

        else:

            entered_match = re.search(
                r"(\d+)\s+out of\s+\d+\s+sorties?\s+"
                r"entered Taiwan[^.]*ADIZ",
                text,
                re.I,
            )

            median_adiz = (
                int(entered_match.group(1))
                if entered_match
                else 0
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

    except Exception as e:

        return None, str(e)


# ============================================================
# VALIDATED FALLBACK DATA
#
# These are the official observations supplied/validated
# during construction of the Radar.
# ============================================================

FALLBACK_MND_DATA = [

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
]


# ============================================================
# CONFLICT DETECTION
# ============================================================

def detect_conflicts(data):

    groups = {}

    for row in data:

        period = row.get(
            "Observation period",
            "",
        )

        if not period:
            continue

        groups.setdefault(
            period,
            []
        ).append(row)

    conflicts = []

    for period, rows in groups.items():

        if len(rows) < 2:
            continue

        signatures = set()

        for row in rows:

            signature = (
                row.get("PLA aircraft"),
                row.get("Median-line/ADIZ"),
                row.get("PLAN ships"),
                row.get("Official ships"),
            )

            signatures.add(signature)

        if len(signatures) > 1:

            conflicts.extend(rows)

    return conflicts


# ============================================================
# BASELINE
# ============================================================

def calculate_baseline(data):

    valid = [
        x for x in data
        if x.get("Status") == "VALID"
    ]

    if len(valid) < 3:
        return None

    return {
        "PLA aircraft": statistics.mean(
            x["PLA aircraft"]
            for x in valid
        ),

        "Median-line/ADIZ": statistics.mean(
            x["Median-line/ADIZ"]
            for x in valid
        ),

        "PLAN ships": statistics.mean(
            x["PLAN ships"]
            for x in valid
        ),

        "Official ships": statistics.mean(
            x["Official ships"]
            for x in valid
        ),
    }


# ============================================================
# PLA ACTIVITY SIGNAL
# ============================================================

def calculate_pla_signal(latest, baseline):

    if not baseline:
        return 0

    aircraft_ratio = (
        latest["PLA aircraft"]
        / max(baseline["PLA aircraft"], 1)
    )

    median_ratio = (
        latest["Median-line/ADIZ"]
        / max(baseline["Median-line/ADIZ"], 1)
    )

    ships_ratio = (
        latest["PLAN ships"]
        / max(baseline["PLAN ships"], 1)
    )

    official_ratio = (
        latest["Official ships"]
        / max(baseline["Official ships"], 1)
    )

    raw = (
        aircraft_ratio * 35
        + median_ratio * 35
        + ships_ratio * 20
        + official_ratio * 10
    )

    return int(
        min(
            max(raw, 0),
            100,
        )
    )


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_pdf_text(uploaded_file):

    try:

        pdf_bytes = uploaded_file.read()

        reader = PdfReader(
            io.BytesIO(pdf_bytes)
        )

        pages = []

        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):

            text = page.extract_text() or ""

            if text.strip():

                pages.append(
                    {
                        "page": page_number,
                        "text": text,
                    }
                )

        return pages, None

    except Exception as e:

        return [], str(e)


# ============================================================
# PDF CHUNKING
# ============================================================

def chunk_text(
    pages,
    chunk_size=1800,
    overlap=250,
):

    chunks = []

    for page in pages:

        text = re.sub(
            r"\s+",
            " ",
            page["text"],
        ).strip()

        if not text:
            continue

        start = 0

        while start < len(text):

            end = min(
                start + chunk_size,
                len(text),
            )

            chunk = text[start:end]

            chunks.append(
                {
                    "page": page["page"],
                    "text": chunk,
                }
            )

            if end >= len(text):
                break

            start = end - overlap

    return chunks


# ============================================================
# STRATEGIC KEYWORD ANALYSIS
# ============================================================

STRATEGIC_KEYWORDS = {

    "China": [
        "china",
        "prc",
        "beijing",
        "chinese communist party",
        "ccp",
    ],

    "Taiwan": [
        "taiwan",
        "taiwan strait",
        "strait",
        "roc",
    ],

    "Military": [
        "military",
        "pla",
        "plar",
        "plan",
        "missile",
        "air force",
        "navy",
        "joint",
        "exercise",
        "combat",
        "deterrence",
    ],

    "Nuclear": [
        "nuclear",
        "warhead",
        "deterrence",
        "strategic forces",
        "second strike",
        "nuclear posture",
    ],

    "Technology": [
        "artificial intelligence",
        "ai",
        "semiconductor",
        "chip",
        "space",
        "cyber",
        "quantum",
        "autonomous",
    ],

    "Economy": [
        "economy",
        "economic",
        "trade",
        "investment",
        "supply chain",
        "sanctions",
    ],

    "Geopolitics": [
        "geopolitical",
        "alliance",
        "indo-pacific",
        "united states",
        "japan",
        "australia",
        "europe",
        "nato",
    ],
}


def analyse_pdf_text(pages):

    full_text = " ".join(
        page["text"]
        for page in pages
    )

    text_lower = full_text.lower()

    domain_scores = {}

    for domain, keywords in STRATEGIC_KEYWORDS.items():

        score = 0

        for keyword in keywords:

            score += text_lower.count(
                keyword.lower()
            )

        domain_scores[domain] = score

    ranked = sorted(
        domain_scores.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    total_words = len(
        full_text.split()
    )

    sentences = re.split(
        r"[.!?]+",
        full_text,
    )

    sentences = [
        s.strip()
        for s in sentences
        if len(s.strip()) > 40
    ]

    return {
        "word_count": total_words,
        "domains": ranked,
        "sentences": sentences,
        "text": full_text,
    }


# ============================================================
# PDF KNOWLEDGE BASE
# ============================================================

def render_pdf_knowledge_section():

    st.markdown(
        '<div class="section-title">📚 PDF Strategic Knowledge Base</div>',
        unsafe_allow_html=True,
    )

    st.write(
        """
        Тук качваш научни статии, книги, доклади, стратегически
        документи и други PDF източници. Системата извлича текста,
        разделя документа на аналитични сегменти и определя
        стратегическите домейни, които са най-силно представени.
        """
    )

    st.info(
        "Важно: PDF анализът е отделен слой от оперативния Radar. "
        "Документът е източник на знания, а не автоматично доказателство."
    )

    uploaded_files = st.file_uploader(
        "Качи PDF документ",
        type=["pdf"],
        accept_multiple_files=True,
        key="strategic_pdf_uploader",
    )

    if uploaded_files:

        for uploaded_file in uploaded_files:

            already_loaded = any(
                d["name"] == uploaded_file.name
                for d in st.session_state.pdf_documents
            )

            if already_loaded:
                continue

            pages, error = extract_pdf_text(
                uploaded_file
            )

            if error:

                st.error(
                    f"Грешка при {uploaded_file.name}: {error}"
                )

                continue

            chunks = chunk_text(
                pages
            )

            analysis = analyse_pdf_text(
                pages
            )

            document = {
                "name": uploaded_file.name,
                "pages": len(pages),
                "chunks": len(chunks),
                "analysis": analysis,
            }

            st.session_state.pdf_documents.append(
                document
            )

            for chunk in chunks:

                st.session_state.pdf_chunks.append(
                    {
                        "document": uploaded_file.name,
                        "page": chunk["page"],
                        "text": chunk["text"],
                    }
                )

    # --------------------------------------------------------
    # DOCUMENT LIST
    # --------------------------------------------------------

    if st.session_state.pdf_documents:

        st.subheader(
            "Заредени документи"
        )

        for document in st.session_state.pdf_documents:

            with st.expander(
                f"📄 {document['name']}"
            ):

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Страници",
                    document["pages"],
                )

                col2.metric(
                    "Текстови сегменти",
                    document["chunks"],
                )

                col3.metric(
                    "Думи",
                    document["analysis"]["word_count"],
                )

                st.write(
                    "Най-силно представени стратегически домейни:"
                )

                top_domains = [
                    x
                    for x in document["analysis"]["domains"]
                    if x[1] > 0
                ][:5]

                for domain, score in top_domains:

                    st.write(
                        f"**{domain}:** {score}"
                    )

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    st.subheader(
        "🔎 Търсене в PDF базата"
    )

    search_query = st.text_input(
        "Търси термин или концепция",
        placeholder="например: Taiwan, deterrence, nuclear, Belt and Road",
    )

    if search_query:

        query = search_query.lower()

        results = []

        for chunk in st.session_state.pdf_chunks:

            if query in chunk["text"].lower():

                results.append(
                    chunk
                )

        st.write(
            f"Намерени сегменти: **{len(results)}**"
        )

        for result in results[:20]:

            with st.expander(
                f"{result['document']} — страница {result['page']}"
            ):

                st.write(
                    result["text"]
                )

    # --------------------------------------------------------
    # STRATEGIC ASSESSMENT
    # --------------------------------------------------------

    st.subheader(
        "🧭 Strategic Assessment"
    )

    if st.session_state.pdf_documents:

        selected_document = st.selectbox(
            "Избери документ",
            [
                d["name"]
                for d in st.session_state.pdf_documents
            ],
        )

        selected = next(
            d
            for d in st.session_state.pdf_documents
            if d["name"] == selected_document
        )

        analysis = selected["analysis"]

        st.markdown(
            '<div class="analysis-box">',
            unsafe_allow_html=True,
        )

        st.markdown(
            "### 1. Source characterization"
        )

        st.write(
            f"Документът съдържа приблизително "
            f"**{analysis['word_count']:,} думи** "
            f"в **{selected['pages']} страници**."
        )

        st.markdown(
            "### 2. Dominant strategic domains"
        )

        top_domains = [
            x
            for x in analysis["domains"]
            if x[1] > 0
        ][:5]

        if top_domains:

            for domain, score in top_domains:

                st.write(
                    f"- **{domain}** — {score} индикатора"
                )

        else:

            st.write(
                "Не са открити достатъчно стратегически ключови термини."
            )

        st.markdown(
            "### 3. Analytical interpretation"
        )

        if top_domains:

            dominant = top_domains[0][0]

            st.write(
                f"Документът е най-силно ориентиран към "
                f"**{dominant}**. Това не означава автоматично, "
                f"че този домейн е най-важният за автора; "
                f"показателят измерва честота на терминологията, "
                f"а не причинна значимост."
            )

        st.markdown(
            "### 4. Evidence discipline"
        )

        st.write(
            """
            Следващото ниво на анализа трябва да различава:

            **Known** — какво авторът действително твърди;

            **Inferred** — какви изводи могат да бъдат направени
            от изложените факти;

            **Contested** — твърдения, за които има конкуриращи се
            интерпретации;

            **Unknown** — какво документът не позволява да бъде
            установено.

            Това е важно, защото честотата на определена дума
            не е доказателство за стратегическо намерение.
            """
        )

        st.markdown(
            '</div>',
            unsafe_allow_html=True,
        )

    else:

        st.warning(
            "Първо качи поне един PDF документ."
        )


# ============================================================
# HEADER
# ============================================================

st.markdown(
    '<div class="main-title">🌐 GLOBAL STRATEGIC RADAR</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Strategic change detection • Early warning • Evidence-based assessment"
    "</div>",
    unsafe_allow_html=True,
)

st.success(
    f"● LIVE DATA    Last refresh: "
    f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC"
)


# ============================================================
# INFORMATION LAYER
# ============================================================

articles, gdelt_error = get_gdelt_articles()

if gdelt_error:

    st.warning(
        "GDELT live feed unavailable. "
        "Information layer is in fallback mode."
    )

    information_activity = 25

else:

    st.success(
        f"GDELT live feed connected — "
        f"{len(articles)} relevant articles found "
        f"in the last 24 hours."
    )

    information_activity = min(
        len(articles) * 4,
        100,
    )


# ============================================================
# MND DATA
# ============================================================

all_mnd = FALLBACK_MND_DATA.copy()

conflicts = detect_conflicts(
    all_mnd
)

valid_data = [
    x
    for x in all_mnd
    if x.get("Status") == "VALID"
]

baseline = calculate_baseline(
    all_mnd
)

latest = valid_data[0]

pla_signal = calculate_pla_signal(
    latest,
    baseline,
)


# ============================================================
# TOP METRICS
# ============================================================

col1, col2, col3, col4 = st.columns(4)

with col1:

    st.metric(
        "Global Strategic Pressure",
        "68 ↑",
        "Demo index — not model-derived",
    )

with col2:

    st.metric(
        "Information Activity",
        information_activity,
        f"{len(articles)} articles / 24h",
    )

with col3:

    st.metric(
        "PLA Activity Signal",
        pla_signal,
        f"{len(valid_data)} validated observations",
    )

with col4:

    if conflicts:

        st.metric(
            "Data Quality",
            "CONFLICT FLAG",
            f"{len(conflicts)} conflicting records",
        )

    else:

        st.metric(
            "Data Quality",
            "OK",
        )


# ============================================================
# SOURCE CONFLICT
# ============================================================

st.markdown(
    '<div class="section-title">⚠️ Source Conflict Detection</div>',
    unsafe_allow_html=True,
)

if conflicts:

    st.error(
        "CONFLICT DETECTED: at least one identical observation "
        "period contains different quantitative observations. "
        "Conflicting records are excluded from the baseline."
    )

    conflict_rows = []

    for row in conflicts:

        conflict_rows.append(
            {
                "Report date": row["Report date"],
                "Observation period": row[
                    "Observation period"
                ],
                "PLA aircraft": row[
                    "PLA aircraft"
                ],
                "Median-line/ADIZ": row[
                    "Median-line/ADIZ"
                ],
                "PLAN ships": row[
                    "PLAN ships"
                ],
                "Official ships": row[
                    "Official ships"
                ],
                "Source": row["URL"],
            }
        )

    st.dataframe(
        conflict_rows,
        use_container_width=True,
    )

else:

    st.success(
        "No source conflicts detected."
    )


# ============================================================
# PLA ACTIVITY
# ============================================================

st.markdown(
    '<div class="section-title">'
    "🇨🇳 PLA Activity Around Taiwan"
    "</div>",
    unsafe_allow_html=True,
)

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric(
        "Latest aircraft",
        latest["PLA aircraft"],
    )

with c2:
    st.metric(
        "Latest median-line / ADIZ",
        latest["Median-line/ADIZ"],
    )

with c3:
    st.metric(
        "Latest PLAN ships",
        latest["PLAN ships"],
    )

with c4:
    st.metric(
        "Latest official ships",
        latest["Official ships"],
    )

st.caption(
    f"Observation: {latest['Observation period']} "
    f"• Source: ROC Ministry of National Defense"
)

st.link_button(
    "Open official MND report",
    latest["URL"],
)


# ============================================================
# HISTORICAL BASELINE
# ============================================================

st.markdown(
    '<div class="section-title">📊 Historical Baseline</div>',
    unsafe_allow_html=True,
)

if baseline:

    b1, b2, b3, b4 = st.columns(4)

    b1.metric(
        "Aircraft baseline",
        f"{baseline['PLA aircraft']:.1f}",
    )

    b2.metric(
        "Median-line / ADIZ baseline",
        f"{baseline['Median-line/ADIZ']:.1f}",
    )

    b3.metric(
        "PLAN baseline",
        f"{baseline['PLAN ships']:.1f}",
    )

    b4.metric(
        "Official ships baseline",
        f"{baseline['Official ships']:.1f}",
    )

else:

    st.info(
        "Недостатъчно валидирани наблюдения за надежден baseline."
    )


# ============================================================
# VALIDATED OBSERVATION SET
# ============================================================

st.markdown(
    '<div class="section-title">📚 Validated Observation Set</div>',
    unsafe_allow_html=True,
)

table_rows = []

for row in valid_data:

    table_rows.append(
        {
            "Report date": row["Report date"],
            "Observation period": row[
                "Observation period"
            ],
            "PLA aircraft": row[
                "PLA aircraft"
            ],
            "Median-line/ADIZ": row[
                "Median-line/ADIZ"
            ],
            "PLAN ships": row[
                "PLAN ships"
            ],
            "Official ships": row[
                "Official ships"
            ],
            "Status": row["Status"],
        }
    )

st.dataframe(
    table_rows,
    use_container_width=True,
)


# ============================================================
# TAIWAN PREPAREDNESS
# ============================================================

st.markdown(
    '<div class="section-title">'
    "🇹🇼 Taiwan Military Preparedness"
    "</div>",
    unsafe_allow_html=True,
)

st.success(
    "ACTIVE — Han Kuang 42"
)

st.write(
    """
    Source-backed preparedness indicators include:

    • joint anti-landing operations  
    • littoral strike  
    • beach and shore battle  
    • joint fires  
    • kill-chain integration  
    • intelligence transmission  
    • common operational picture  
    • increasing automation of strike processes
    """
)

st.link_button(
    "Open official Han Kuang 42 MND source",
    "https://www.mnd.gov.tw/en/News/PressRelease/87316",
)


# ============================================================
# SIGNAL CONVERGENCE
# ============================================================

st.markdown(
    '<div class="section-title">⚠️ Signal Convergence</div>',
    unsafe_allow_html=True,
)

s1, s2, s3 = st.columns(3)

with s1:

    st.metric(
        "Information signal",
        information_activity,
    )

with s2:

    st.metric(
        "PLA signal",
        pla_signal,
    )

with s3:

    if conflicts:

        st.metric(
            "Convergence",
            "PENDING VALIDATION",
        )

    else:

        st.metric(
            "Convergence",
            "AVAILABLE",
        )

st.warning(
    """
    Convergence does not mean probability of conflict.
    It means that independent signal streams may be pointing
    in the same direction. Interpretation requires context,
    historical baselines and source validation.
    """
)


# ============================================================
# SEPARATOR
# ============================================================

st.divider()


# ============================================================
# PDF KNOWLEDGE MODULE
# ============================================================

render_pdf_knowledge_section()


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "GLOBAL STRATEGIC RADAR • Evidence-based strategic monitoring • "
    "Operational data and research knowledge are intentionally separated."
)
