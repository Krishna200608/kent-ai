"""Google Stitch Design System & CSS theme injection for Streamlit (Phase 7)."""

from __future__ import annotations

import streamlit as st


def inject_custom_css() -> None:
    """Inject custom Google Stitch clinical dark-mode CSS into Streamlit DOM."""
    css = """
    <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200" />
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

    /* Global Typography & Background */
    html, body {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        background-color: #0A0F1D;
        color: #F9FAFB;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        letter-spacing: -0.02em;
        color: #F9FAFB;
    }

    .stApp {
        background-color: #0A0F1D;
        color: #F9FAFB;
    }

    /* Google Material Symbols Font Enforcer */
    [data-testid="stIconMaterial"], 
    .material-symbols-rounded, 
    .material-symbols-outlined {
        font-family: 'Material Symbols Rounded', 'Material Symbols Outlined' !important;
        font-size: 19px !important;
        font-style: normal !important;
        font-weight: normal !important;
        line-height: 1 !important;
        display: inline-block !important;
        text-transform: none !important;
        letter-spacing: normal !important;
        word-wrap: normal !important;
        white-space: nowrap !important;
        direction: ltr !important;
        -webkit-font-smoothing: antialiased;
        vertical-align: middle !important;
    }

    /* Top Brand Navigation Header */
    .brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 14px 22px;
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        margin-bottom: 22px;
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25);
        flex-wrap: wrap;
        gap: 16px;
    }

    .brand-left {
        display: flex;
        align-items: center;
        gap: 14px;
    }

    .brand-icon-box {
        width: 44px;
        height: 44px;
        border-radius: 10px;
        background: rgba(16, 185, 129, 0.12);
        border: 1px solid rgba(16, 185, 129, 0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.2);
        flex-shrink: 0;
    }

    .brand-title {
        font-size: 22px;
        font-weight: 800;
        font-family: 'Outfit', sans-serif;
        color: #FFFFFF;
        letter-spacing: -0.02em;
        line-height: 1.2;
        margin: 0;
    }

    .brand-subtitle {
        font-size: 12px;
        font-weight: 500;
        color: #9CA3AF;
        margin-top: 2px;
        letter-spacing: 0.01em;
    }

    .brand-pills {
        display: flex;
        gap: 10px;
        align-items: center;
        flex-wrap: wrap;
    }

    /* Glassmorphic Container Cards */
    .stGlassCard {
        background: rgba(17, 24, 39, 0.75);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px 20px;
        margin-bottom: 16px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }

    .stGlassCard:hover {
        border-color: rgba(16, 185, 129, 0.3);
    }

    /* 7-Dimension Pill Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 6px;
        letter-spacing: 0.02em;
    }

    .badge-loc {
        background: rgba(6, 182, 212, 0.15);
        color: #22D3EE;
        border: 1px solid rgba(6, 182, 212, 0.3);
    }

    .badge-sen {
        background: rgba(16, 185, 129, 0.15);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .badge-agg {
        background: rgba(245, 158, 11, 0.15);
        color: #FBBF24;
        border: 1px solid rgba(245, 158, 11, 0.3);
    }

    .badge-amel {
        background: rgba(52, 211, 153, 0.15);
        color: #6EE7B7;
        border: 1px solid rgba(52, 211, 153, 0.3);
    }

    .badge-conc {
        background: rgba(236, 72, 153, 0.15);
        color: #F472B6;
        border: 1px solid rgba(236, 72, 153, 0.3);
    }

    .badge-temp {
        background: rgba(59, 130, 246, 0.15);
        color: #60A5FA;
        border: 1px solid rgba(59, 130, 246, 0.3);
    }

    .badge-ment {
        background: rgba(139, 92, 246, 0.15);
        color: #A78BFA;
        border: 1px solid rgba(139, 92, 246, 0.3);
    }

    .badge-neg {
        background: rgba(239, 68, 68, 0.15);
        color: #F87171;
        border: 1px solid rgba(239, 68, 68, 0.3);
        text-decoration: line-through;
    }

    /* Remedy Grade Indicators */
    .grade-3 {
        color: #10B981;
        font-weight: 800;
        font-size: 13px;
        background: rgba(16, 185, 129, 0.15);
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .grade-2 {
        color: #06B6D4;
        font-style: italic;
        font-weight: 600;
        font-size: 13px;
        background: rgba(6, 182, 212, 0.12);
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid rgba(6, 182, 212, 0.3);
    }

    .grade-1 {
        color: #9CA3AF;
        font-weight: 400;
        font-size: 13px;
        padding: 2px 6px;
    }

    /* Primary Simillimum Hero Card */
    .hero-simillimum {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 182, 212, 0.08) 100%);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 14px;
        padding: 20px 24px;
        margin-top: 15px;
        margin-bottom: 20px;
        box-shadow: 0 0 25px rgba(16, 185, 129, 0.12);
    }

    /* Status Pills */
    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        padding: 6px 13px;
        background: rgba(16, 185, 129, 0.08);
        border: 1px solid rgba(16, 185, 129, 0.25);
        border-radius: 20px;
        color: #34D399;
        font-size: 12px;
        font-weight: 600;
        line-height: 1;
    }
    
    .status-pill-info {
        background: rgba(6, 182, 212, 0.08);
        border-color: rgba(6, 182, 212, 0.3);
        color: #22D3EE;
    }

    .status-pill-purple {
        background: rgba(139, 92, 246, 0.08);
        border-color: rgba(139, 92, 246, 0.3);
        color: #A78BFA;
    }

    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10B981;
        box-shadow: 0 0 8px #10B981;
        animation: pulse-glow 2s infinite ease-in-out;
        flex-shrink: 0;
    }

    .status-dot-cyan {
        background-color: #06B6D4;
        box-shadow: 0 0 8px #06B6D4;
    }

    @keyframes pulse-glow {
        0%, 100% {
            opacity: 1;
            transform: scale(1);
            box-shadow: 0 0 10px #10B981;
        }
        50% {
            opacity: 0.5;
            transform: scale(0.85);
            box-shadow: 0 0 3px #10B981;
        }
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 6px;
        background-color: rgba(17, 24, 39, 0.6);
        padding: 6px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .stTabs [data-baseweb="tab"] {
        height: 40px;
        border-radius: 8px;
        color: #9CA3AF;
        font-weight: 500;
        font-family: 'Outfit', sans-serif;
        padding: 0 16px;
    }

    .stTabs [aria-selected="true"] {
        background: rgba(16, 185, 129, 0.2) !important;
        color: #10B981 !important;
        font-weight: 700;
        border: 1px solid rgba(16, 185, 129, 0.3) !important;
    }

    /* Button Styling */
    .stButton>button[kind="primary"],
    [data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%) !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
        font-family: 'Outfit', sans-serif !important;
        border: none !important;
        border-radius: 9px !important;
        padding: 10px 18px !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3) !important;
    }

    .stButton>button[kind="primary"]:hover,
    [data-testid="stBaseButton-primary"]:hover {
        background: linear-gradient(135deg, #34D399 0%, #10B981 100%) !important;
        box-shadow: 0 6px 18px rgba(16, 185, 129, 0.45) !important;
        transform: translateY(-1px);
    }

    .stButton>button[kind="secondary"],
    [data-testid="stBaseButton-secondary"] {
        background: rgba(31, 41, 55, 0.6) !important;
        color: #E5E7EB !important;
        font-weight: 500 !important;
        font-family: 'Outfit', sans-serif !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 9px !important;
        padding: 10px 18px !important;
        transition: all 0.2s ease !important;
    }

    .stButton>button[kind="secondary"]:hover,
    [data-testid="stBaseButton-secondary"]:hover {
        background: rgba(55, 65, 81, 0.8) !important;
        border-color: rgba(239, 68, 68, 0.4) !important;
        color: #F87171 !important;
    }

    /* Custom Sleek Scrollbar */
    ::-webkit-scrollbar {
        width: 6px;
        height: 6px;
    }
    ::-webkit-scrollbar-track {
        background: #0A0F1D;
    }
    ::-webkit-scrollbar-thumb {
        background: #1F2937;
        border-radius: 4px;
    }
    ::-webkit-scrollbar-thumb:hover {
        background: #374151;
    }

    /* Metric Stat Card */
    .stitch-metric {
        background: rgba(17, 24, 39, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 10px;
        padding: 12px 16px;
        text-align: center;
    }
    .stitch-metric-val {
        font-size: 22px;
        font-weight: 800;
        color: #10B981;
    }
    .stitch-metric-lbl {
        font-size: 11px;
        color: #9CA3AF;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-top: 2px;
    }

    /* Repertory Totality Grid Table */
    .repertory-grid {
        width: 100%;
        border-collapse: separate;
        border-spacing: 0;
        margin-top: 12px;
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.08);
        background: rgba(17, 24, 39, 0.6);
        font-size: 13px;
    }
    .repertory-grid th {
        background: rgba(31, 41, 55, 0.8);
        color: #9CA3AF;
        padding: 10px 12px;
        text-align: left;
        font-weight: 600;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .repertory-grid td {
        padding: 8px 12px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.04);
        color: #E5E7EB;
    }
    .repertory-grid tr:hover td {
        background: rgba(255, 255, 255, 0.02);
    }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)
