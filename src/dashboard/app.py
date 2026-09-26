"""Streamlit Doctor Clinical Dashboard — Entry Point."""

import streamlit as st


def main() -> None:
    st.set_page_config(
        page_title="Kent-AI Clinical Assistant",
        page_icon="🌿",
        layout="wide",
    )
    st.title("🌿 Kent-AI Clinical Assistant")
    st.markdown("AI-Powered Homeopathic Repertorization & Clinical Consultation")
    st.info("System initialized. Navigation available via sidebar pages.")


if __name__ == "__main__":
    main()
