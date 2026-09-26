"""Rubric Explorer View: Interactive Kent hierarchical repertory navigator."""

import streamlit as st


def render_page() -> None:
    st.header("🌳 Kent Repertory Rubric Explorer")
    st.write("Browse and search the 37 anatomical and symptom sections.")


if __name__ == "__main__":
    render_page()
