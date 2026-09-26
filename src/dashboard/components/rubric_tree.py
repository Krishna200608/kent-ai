"""Reusable Kent rubric tree widget for Streamlit."""

import streamlit as st
from typing import Any, Dict, List


def render_rubric_tree(nodes: List[Dict[str, Any]]) -> None:
    """Render hierarchical tree structure in Streamlit sidebar or container."""
    st.write("Rubric tree renderer initialized.")
