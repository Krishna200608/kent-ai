"""Reusable chat transcript viewer component."""

import streamlit as st
from typing import Any, Dict, List


def render_chat_transcript(turns: List[Dict[str, str]]) -> None:
    """Render conversation history between patient and clinical intake agent."""
    for turn in turns:
        role = turn.get("role", "user")
        with st.chat_message(role):
            st.write(turn.get("content", ""))
