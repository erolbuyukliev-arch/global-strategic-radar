import re
from typing import List, Dict

import streamlit as st


# ============================================================
# PDF STRATEGIC KNOWLEDGE BASE
# PUBLIC VERSION
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
        The Global Strategic Radar Knowledge Base contains
        curated academic papers, books, research reports,
        strategic documents and policy publications.
        """
    )

    st.info(
        "The Knowledge Base is maintained by the administrator. "
        "Public users cannot upload or modify documents."
    )

    st.divider()

    # ========================================================
    # PUBLIC KNOWLEDGE BASE
    # ========================================================

    st.subheader("📚 Research Knowledge")

    st.write(
        """
        The public version of the Knowledge Base is designed
        for reading, research and strategic analysis.
        """
    )

    st.markdown(
        """
        **The Knowledge Base will contain:**

        - Academic research
        - Strategic studies
        - Government and defense documents
        - Think-tank reports
        - Books and monographs
        - Policy papers
        - Research articles
        - Strategic assessments
        """
    )

    st.divider()

    # ========================================================
    # SEARCH
    # ========================================================

    st.subheader("🔎 Search the Knowledge Base")

    query = st.text_input(
        "Search",
        placeholder=(
            "Example: Taiwan deterrence, Chinese military "
            "modernization, nuclear strategy..."
        ),
        key="public_pdf_search",
    )

    if query:

        st.info(
            "Knowledge Base search will become available after "
            "the administrator publishes the first documents."
        )

    else:

        st.caption(
            "Enter a strategic topic, concept or keyword to "
            "search the published Knowledge Base."
        )

    st.divider()

    # ========================================================
    # STRATEGIC ANALYSIS
    # ========================================================

    st.subheader("🎯 Strategic Assessment")

    st.write(
        """
        Published documents will support structured strategic
        analysis covering:
        """
    )

    col1, col2 = st.columns(2)

    with col1:

        st.markdown(
            """
            **Strategic Dimensions**

            - Actors
            - Interests
            - Capabilities
            - Intentions
            - Strategic objectives
            - Military posture
            - Geopolitical dynamics
            """
        )

    with col2:

        st.markdown(
            """
            **Analytical Assessment**

            - Key findings
            - Strategic implications
            - Risks
            - Opportunities
            - Competing interpretations
            - Intelligence gaps
            - Areas of uncertainty
            """
        )

    st.divider()

    # ========================================================
    # EVIDENCE STANDARD
    # ========================================================

    st.subheader("📑 Evidence Standard")

    st.write(
        """
        The Knowledge Base is designed around source traceability.
        Strategic assessments should be linked to the original
        document and, where possible, to specific page-level
        evidence.
        """
    )

    st.caption(
        "Documents are treated as research sources. "
        "Source evidence, analytical inference and uncertainty "
        "should be kept conceptually separate."
    )

    # ========================================================
    # ADMINISTRATOR NOTICE
    # ========================================================

    st.divider()

    st.subheader("🔐 Knowledge Base Administration")

    st.caption(
        "Document upload and knowledge-base management are "
        "restricted to authorized administrators."
    )
