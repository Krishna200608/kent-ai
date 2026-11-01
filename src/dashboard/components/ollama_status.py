"""Ollama daemon health check and dynamic status telemetry (Phase 14 & UI Overhaul)."""

from __future__ import annotations

import os
import time
import urllib.request
import streamlit as st


@st.cache_data(ttl=2, show_spinner=False)
def get_ollama_latency(api_base: str = "http://127.0.0.1:11434") -> tuple[bool, int]:
    """Check Ollama connectivity and measure round-trip latency in milliseconds.

    Checks 127.0.0.1 (IPv4) first to bypass Windows IPv6 resolution latency.
    Bypasses system proxies for local addresses. Cached for 2s to enable real-time dynamic polling.
    """
    if os.environ.get("KENT_MOCK_PIPELINE", "0") == "1":
        return False, 0

    candidates = ["http://127.0.0.1:11434", api_base]
    seen: set = set()
    unique_candidates = [c for c in candidates if c and not (c in seen or seen.add(c))]
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    for base in unique_candidates:
        try:
            start = time.perf_counter()
            url = f"{base.rstrip('/')}/api/tags"
            req = urllib.request.Request(url, method="GET")
            with opener.open(req, timeout=0.4) as resp:
                if resp.status == 200:
                    ms = max(1, int((time.perf_counter() - start) * 1000))
                    return True, ms
        except Exception:
            continue
    return False, 0


@st.cache_data(ttl=2, show_spinner=False)
def check_ollama_online(api_base: str = "http://127.0.0.1:11434") -> bool:
    """Direct HTTP ping to check if local Ollama daemon is active and responding.

    Checks 127.0.0.1 (IPv4) first to bypass Windows IPv6 resolution latency.
    Bypasses system proxies for local addresses. Cached for 2s to enable real-time dynamic polling.
    """
    online, _ = get_ollama_latency(api_base)
    return online


ollama_online = check_ollama_online

__all__ = ["check_ollama_online", "get_ollama_latency", "ollama_online"]


