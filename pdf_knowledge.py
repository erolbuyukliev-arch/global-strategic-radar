
import io
import re
from typing import List, Dict

import streamlit as st
from pypdf import PdfReader


# ============================================================
# PDF KNOWLEDGE MODULE
# ============================================================

def extract_pdf(pdf_file):
    """
    Extract text from an uploaded PDF.

    Returns:
        document: dict
        error: str | None
    """

    try:
        pdf_bytes = pdf_file.getvalue()

        reader = PdfReader(
            io.BytesIO(pdf_bytes)
        )

        pages = []

        for page_number, page in enumerate(
            reader.pages,
            start=1
        ):

            try:
                text = page.extract_text() or ""
            except Exception:
                text = ""

            text = clean_text(text)

            if text:
                pages.append(
                    {
                        "page": page_number,
                        "text": text,
                    }
                )

        full_text = "\n\n".join(
            [
                p["text"]
                for p in pages
            ]
        )

        document = {
            "filename": pdf_file.name,
            "pages": len(reader.pages),
            "text_pages": len(pages),
            "text": full_text,
            "page_data": pages,
            "characters": len(full_text),
            "words": len(
                full_text.split()
            ),
        }

        return document, None

    except Exception as exc:

        return None, str(exc)


def clean_text(text: str) -> str:
    """
    Normalize extracted PDF text.
    """

    text = text.replace(
        "\x00",
        " "
    )

    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


def split_into_chunks(
    document: Dict,
    max_words: int = 900
) -> List[Dict]:
    """
    Split PDF text into chunks while preserving
    page provenance.
    """

    chunks = []

    current_text = []
    current_words = 0
    start_page = None
    end_page = None

    for page in document["page_data"]:

        words = page["text"].split()

        if not words:
            continue

        if start_page is None:
            start_page = page["page"]

        if (
            current_words + len(words)
            > max_words
            and current_text
        ):

            chunks.append(
                {
                    "chunk_id": len(chunks) + 1,
                    "start_page": start_page,
                    "end_page": end_page,
                    "text": " ".join(
                        current_text
                    ),
                }
            )

            current_text = []
            current_words = 0
            start_page = page["page"]

        current_text.extend(words)
        current_words += len(words)
        end_page = page["page"]

    if current_text:

        chunks.append(
            {
                "chunk_id": len(chunks) + 1,
                "start_page": start_page,
                "end_page": end_page,
                "text": " ".join(
                    current_text
                ),
            }
        )

    return chunks


def search_document(
    document: Dict,
    query: str,
    max_results: int = 8
) -> List[Dict]:
    """
    Simple evidence retrieval from the PDF.

    This is deliberately deterministic:
    it finds pages containing the query terms.
    """

    if not query.strip():
        return []

    query_terms = [
        term.lower()
        for term in re.findall(
            r"\b\w+\b",
            query
        )
        if len(term) > 2
    ]

    if not query_terms:
        return []

    results = []

    for page in document["page_data"]:

        text_lower = page[
            "text"
        ].lower()

        score = 0

        for term in query_terms:

            score += text_lower.count(
                term
            )

        if score > 0:

            results.append(
                {
                    "page": page["page"],
                    "score": score,
                    "text": page["text"],
                }
            )

    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return results[:max_results]


def render_pdf_knowledge_section():
    """
    Render the complete PDF Knowledge Base section
    inside the Streamlit application.
    """

    st.header(
        "📚 PDF Strategic Knowledge Base"
    )

    st.caption(
        "Upload a book, academic paper, strategic report "
        "or official document and build an evidence base "
        "for strategic analysis."
    )

    uploaded_file = st.file_uploader(
        "Upload PDF document",
        type=["pdf"],
        accept_multiple_files=False,
        key="strategic_pdf_upload",
    )

    if uploaded_file is None:

        st.info(
            "Upload a PDF to begin."
        )

        return

    document, error = extract_pdf(
        uploaded_file
    )

    if error:

        st.error(
            f"PDF extraction failed: {error}"
        )

        return

    # --------------------------------------------------------
    # DOCUMENT METADATA
    # --------------------------------------------------------

    st.success(
        f"Document loaded: {document['filename']}"
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "PDF pages",
            document["pages"]
        )

    with c2:
        st.metric(
            "Pages with text",
            document["text_pages"]
        )

    with c3:
        st.metric(
            "Words",
            f"{document['words']:,}"
        )

    with c4:
        st.metric(
            "Characters",
            f"{document['characters']:,}"
        )

    # --------------------------------------------------------
    # OCR WARNING
    # --------------------------------------------------------

    if document["text_pages"] == 0:

        st.error(
            "No machine-readable text was extracted. "
            "This PDF is probably scanned and will require OCR."
        )

        return

    if (
        document["text_pages"]
        < document["pages"] * 0.5
    ):

        st.warning(
            "Only part of the PDF contains extractable text. "
            "Some pages may be scanned images."
        )

    # --------------------------------------------------------
    # CHUNKING
    # --------------------------------------------------------

    chunks = split_into_chunks(
        document
    )

    st.session_state[
        "pdf_document"
    ] = document

    st.session_state[
        "pdf_chunks"
    ] = chunks

    st.divider()

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    st.subheader(
        "🔎 Search the document"
    )

    query = st.text_input(
        "Search question or concept",
        placeholder=(
            "e.g. strategic competition with China"
        ),
        key="pdf_search_query",
    )

    if query:

        results = search_document(
            document,
            query
        )

        if not results:

            st.warning(
                "No matching evidence found."
            )

        else:

            st.write(
                f"Found {len(results)} relevant "
                "evidence segments."
            )

            for result in results:

                with st.expander(
                    f"📄 Page {result['page']} "
                    f"— relevance {result['score']}"
                ):

                    st.write(
                        result["text"]
                    )

    # --------------------------------------------------------
    # DOCUMENT PREVIEW
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "📖 Document preview"
    )

    preview_page = st.number_input(
        "Page",
        min_value=1,
        max_value=max(
            1,
            document["pages"]
        ),
        value=1,
        step=1,
        key="pdf_preview_page",
    )

    selected_pages = [
        p
        for p in document["page_data"]
        if p["page"] == preview_page
    ]

    if selected_pages:

        st.text_area(
            "Extracted text",
            selected_pages[0]["text"],
            height=350,
            key="pdf_preview_text",
        )

    # --------------------------------------------------------
    # ANALYSIS INTERFACE
    # --------------------------------------------------------

    st.divider()

    st.subheader(
        "🧠 Strategic Analysis from PDF"
    )

    analysis_question = st.text_area(
        "What do you want to analyze?",
        placeholder=(
            "Example: What are the main strategic "
            "implications of China's military modernization?"
        ),
        height=120,
        key="pdf_analysis_question",
    )

    if st.button(
        "Analyze PDF Evidence",
        type="primary",
        key="analyze_pdf_button",
    ):

        if not analysis_question.strip():

            st.warning(
                "Enter an analytical question first."
            )

        else:

            evidence = search_document(
                document,
                analysis_question,
                max_results=10,
            )

            if not evidence:

                st.warning(
                    "No directly relevant evidence "
                    "was found in the document."
                )

            else:

                st.markdown(
                    "### Evidence identified"
                )

                for item in evidence:

                    st.markdown(
                        f"**Page {item['page']}**"
                    )

                    st.write(
                        item["text"]
                    )

                    st.caption(
                        f"Source: "
                        f"{document['filename']} "
                        f"— p. {item['page']}"
                    )

                st.info(
                    "The current version retrieves and "
                    "cites evidence from the PDF. "
                    "The next module will connect this "
                    "evidence layer to an AI analytical engine."
                )
