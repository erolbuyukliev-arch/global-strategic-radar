import re
from typing import List, Dict

import streamlit as st
from pypdf import PdfReader


# ============================================================
# PDF STRATEGIC KNOWLEDGE MODULE
# ============================================================

MAX_FILE_SIZE_MB = 200
CHUNK_SIZE = 4500
CHUNK_OVERLAP = 500


# ============================================================
# PDF TEXT EXTRACTION
# ============================================================

def extract_pdf_text(uploaded_file) -> List[Dict]:
    """
    Extract text from a PDF while preserving page numbers.
    Returns:
        [
            {
                "page": 1,
                "text": "..."
            },
            ...
        ]
    """

    reader = PdfReader(uploaded_file)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""

        text = re.sub(r"\s+", " ", text).strip()

        if text:
            pages.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )

    return pages


# ============================================================
# CHUNKING
# ============================================================

def chunk_pages(
    pages: List[Dict],
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> List[Dict]:

    chunks = []

    for page in pages:
        text = page["text"]
        page_number = page["page"]

        if len(text) <= chunk_size:
            chunks.append(
                {
                    "page": page_number,
                    "text": text,
                }
            )
            continue

        start = 0

        while start < len(text):
            end = start + chunk_size

            chunk_text = text[start:end]

            chunks.append(
                {
                    "page": page_number,
                    "text": chunk_text,
                }
            )

            if end >= len(text):
                break

            start = end - overlap

    return chunks


# ============================================================
# SEARCH
# ============================================================

def search_pdf(
    chunks: List[Dict],
    query: str,
    max_results: int = 8,
) -> List[Dict]:

    if not query.strip():
        return []

    query_terms = [
        term.lower()
        for term in re.findall(r"\b[\w-]+\b", query)
        if len(term) > 2
    ]

    if not query_terms:
        return []

    results = []

    for chunk in chunks:

        text_lower = chunk["text"].lower()

        score = 0

        for term in query_terms:

            occurrences = text_lower.count(term)

            if occurrences:
                score += min(occurrences, 10)

                # Extra weight if the term occurs near the beginning
                if text_lower.find(term) < 500:
                    score += 1

        if score > 0:

            results.append(
                {
                    "page": chunk["page"],
                    "text": chunk["text"],
                    "score": score,
                }
            )

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[:max_results]


# ============================================================
# STRATEGIC KEYWORDS
# ============================================================

STRATEGIC_KEYWORDS = {

    "Military": [
        "military",
        "armed forces",
        "army",
        "navy",
        "air force",
        "missile",
        "force posture",
        "deterrence",
        "combat",
        "warfare",
    ],

    "Geopolitics": [
        "geopolitical",
        "geostrategic",
        "alliance",
        "rivalry",
        "great power",
        "influence",
        "regional order",
        "international order",
    ],

    "China": [
        "china",
        "chinese",
        "pla",
        "prc",
        "beijing",
        "taiwan",
        "south china sea",
        "indo-pacific",
    ],

    "Technology": [
        "artificial intelligence",
        "ai",
        "semiconductor",
        "cyber",
        "space",
        "technology",
        "dual-use",
        "quantum",
    ],

    "Economics": [
        "economy",
        "economic",
        "trade",
        "investment",
        "supply chain",
        "sanctions",
        "energy",
        "industrial policy",
    ],

    "Nuclear": [
        "nuclear",
        "strategic forces",
        "nuclear weapons",
        "warhead",
        "icbm",
        "deterrence",
        "second strike",
    ],

    "Information": [
        "information warfare",
        "disinformation",
        "propaganda",
        "influence operation",
        "information environment",
        "psychological",
    ],
}


# ============================================================
# STRATEGIC ANALYSIS
# ============================================================

def analyse_pdf_text(pages: List[Dict]) -> Dict:

    full_text = " ".join(
        page["text"] for page in pages
    ).lower()

    findings = {}

    for category, keywords in STRATEGIC_KEYWORDS.items():

        matches = []

        for keyword in keywords:

            count = full_text.count(keyword.lower())

            if count > 0:
                matches.append(
                    {
                        "keyword": keyword,
                        "count": count,
                    }
                )

        matches.sort(
            key=lambda x: x["count"],
            reverse=True,
        )

        findings[category] = matches[:8]

    return findings


# ============================================================
# EXECUTIVE ASSESSMENT
# ============================================================

def build_executive_assessment(
    pages: List[Dict],
    findings: Dict,
) -> str:

    total_words = sum(
        len(page["text"].split())
        for page in pages
    )

    active_domains = []

    for category, matches in findings.items():

        if matches:
            active_domains.append(category)

    if not active_domains:
        return (
            "The document does not contain sufficient searchable "
            "evidence to generate a domain-level strategic assessment."
        )

    domains = ", ".join(active_domains)

    return (
        f"The document contains approximately {total_words:,} "
        f"extractable words across {len(pages)} pages. "
        f"The strongest identifiable strategic domains are: "
        f"{domains}. "
        f"This assessment is derived from textual frequency and "
        f"document evidence only. Keyword frequency does not by "
        f"itself establish strategic importance, causality, intent, "
        f"or probability."
    )


# ============================================================
# PDF KNOWLEDGE SECTION
# ============================================================

def render_pdf_knowledge_section():

    st.markdown(
        """
        <div class="section-title">
        📚 PDF Strategic Knowledge Base
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.write(
        """
        Upload academic papers, books, research reports, strategic
        documents, policy papers, or other PDF sources.

        The system extracts the document text, preserves page
        references, creates searchable knowledge chunks, and
        generates an evidence-based strategic assessment.
        """
    )

    st.info(
        "Research documents are treated as knowledge sources and "
        "are intentionally separated from operational monitoring data."
    )

    # ========================================================
    # UPLOAD
    # ========================================================

    uploaded_file = st.file_uploader(
        "Upload a PDF document",
        type=["pdf"],
        key="strategic_pdf_uploader",
        help="Maximum recommended file size: 200 MB.",
    )

    if uploaded_file is None:

        st.markdown(
            """
            ### 📄 No document loaded

            Upload a PDF to create a searchable strategic
            knowledge source.
            """
        )

        return

    # ========================================================
    # FILE SIZE
    # ========================================================

    file_size_mb = uploaded_file.size / (
        1024 * 1024
    )

    if file_size_mb > MAX_FILE_SIZE_MB:

        st.error(
            f"The selected file is {file_size_mb:.1f} MB. "
            f"The maximum supported size is "
            f"{MAX_FILE_SIZE_MB} MB."
        )

        return

    # ========================================================
    # EXTRACT
    # ========================================================

    try:

        with st.spinner(
            "Extracting text from the PDF..."
        ):

            pages = extract_pdf_text(
                uploaded_file
            )

    except Exception as exc:

        st.error(
            "The PDF could not be processed."
        )

        st.exception(exc)

        return

    if not pages:

        st.warning(
            "No extractable text was found in this PDF. "
            "The document may contain scanned images rather "
            "than machine-readable text."
        )

        return

    # ========================================================
    # CHUNK
    # ========================================================

    chunks = chunk_pages(pages)

    # Store in session state
    st.session_state["pdf_pages"] = pages
    st.session_state["pdf_chunks"] = chunks
    st.session_state["pdf_filename"] = uploaded_file.name

    # ========================================================
    # DOCUMENT SUMMARY
    # ========================================================

    total_words = sum(
        len(page["text"].split())
        for page in pages
    )

    st.success(
        f"Document loaded successfully: "
        f"{uploaded_file.name}"
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Pages",
            len(pages),
        )

    with col2:
        st.metric(
            "Extracted Words",
            f"{total_words:,}",
        )

    with col3:
        st.metric(
            "Knowledge Chunks",
            len(chunks),
        )

    st.divider()

    # ========================================================
    # STRATEGIC ASSESSMENT
    # ========================================================

    st.subheader(
        "🎯 Strategic Assessment"
    )

    findings = analyse_pdf_text(
        pages
    )

    assessment = build_executive_assessment(
        pages,
        findings,
    )

    st.write(
        assessment
    )

    st.caption(
        "Analytical caution: keyword frequency is an "
        "indicator of document emphasis, not a measure "
        "of strategic importance or probability."
    )

    # ========================================================
    # STRATEGIC DOMAINS
    # ========================================================

    st.subheader(
        "📊 Strategic Domains"
    )

    domain_rows = []

    for category, matches in findings.items():

        if matches:

            total = sum(
                item["count"]
                for item in matches
            )

            top_keyword = matches[0]["keyword"]

            domain_rows.append(
                {
                    "Domain": category,
                    "Signal Count": total,
                    "Leading Term": top_keyword,
                }
            )

    if domain_rows:

        st.dataframe(
            domain_rows,
            use_container_width=True,
            hide_index=True,
        )

    else:

        st.info(
            "No predefined strategic-domain signals "
            "were detected."
        )

    # ========================================================
    # SEARCH
    # ========================================================

    st.divider()

    st.subheader(
        "🔎 Search the PDF Knowledge Base"
    )

    query = st.text_input(
        "Search query",
        placeholder=(
            "Example: Taiwan deterrence, Chinese military "
            "modernization, nuclear strategy..."
        ),
        key="pdf_search_query",
    )

    max_results = st.slider(
        "Maximum results",
        min_value=1,
        max_value=20,
        value=8,
    )

    if query:

        results = search_pdf(
            chunks,
            query,
            max_results=max_results,
        )

        if not results:

            st.warning(
                "No matching passages were found."
            )

        else:

            st.success(
                f"{len(results)} relevant passages found."
            )

            for index, result in enumerate(
                results,
                start=1,
            ):

                with st.expander(
                    f"Result {index} — Page {result['page']} "
                    f"— Relevance {result['score']}"
                ):

                    st.markdown(
                        f"**Source page:** "
                        f"{result['page']}"
                    )

                    st.write(
                        result["text"]
                    )

    # ========================================================
    # DOCUMENT EVIDENCE
    # ========================================================

    st.divider()

    st.subheader(
        "📑 Document Evidence"
    )

    page_number = st.number_input(
        "Open page",
        min_value=1,
        max_value=len(pages),
        value=1,
        step=1,
        key="pdf_page_number",
    )

    selected_page = next(
        (
            page
            for page in pages
            if page["page"] == page_number
        ),
        None,
    )

    if selected_page:

        st.markdown(
            f"**Page {selected_page['page']}**"
        )

        st.text_area(
            "Extracted text",
            selected_page["text"],
            height=300,
            key=f"pdf_page_text_{page_number}",
        )

    # ========================================================
    # KNOWLEDGE BASE STATUS
    # ========================================================

    st.divider()

    st.subheader(
        "🧠 Knowledge Base Status"
    )

    st.write(
        f"**Document:** {uploaded_file.name}"
    )

    st.write(
        f"**Pages indexed:** {len(pages)}"
    )

    st.write(
        f"**Searchable chunks:** {len(chunks)}"
    )

    st.write(
        "**Evidence model:** page-level source preservation"
    )

    st.caption(
        "This module currently performs document extraction, "
        "search, evidence retrieval, and structured analytical "
        "screening. It does not claim that keyword frequency "
        "constitutes an intelligence assessment."
    )
