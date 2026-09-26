"""Google Stitch Design System & CSS theme injection for Streamlit (Phase 7)."""

from __future__ import annotations

import streamlit as st


def inject_custom_css() -> None:
    """Inject custom Google Stitch clinical dark-mode CSS into Streamlit DOM."""
    css = """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&family=Fira+Code:wght@400;500&display=swap');
    @import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200');

    /* Global Body and Font Settings */
    html, body, [class*="css"], [class*="st-"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    h1, h2, h3, h4, h5, h6 {
        font-family: 'Outfit', sans-serif !important;
        letter-spacing: -0.02em;
    }

    /* Google Material Symbols Font Utility */
    .material-symbols-outlined {
        font-family: 'Material Symbols Outlined' !important;
        font-weight: normal;
        font-style: normal;
        font-size: 20px;
        line-height: 1;
        letter-spacing: normal;
        text-transform: none;
        display: inline-flex;
        vertical-align: middle;
        white-space: nowrap;
        word-wrap: normal;
        direction: ltr;
        -webkit-font-feature-settings: 'liga';
        -webkit-font-smoothing: antialiased;
    }

    /* Main Container Background */
    .stApp {
        background-color: #0A0F1D;
        color: #F9FAFB;
    }

    /* Native Streamlit Bordered Container as Google Stitch Glassmorphic Card */
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: rgba(17, 24, 39, 0.75) !important;
        backdrop-filter: blur(16px) !important;
        -webkit-backdrop-filter: blur(16px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37) !important;
        padding: 4px !important;
        margin-bottom: 16px !important;
        transition: border-color 0.2s ease !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"]:hover {
        border-color: rgba(16, 185, 129, 0.3) !important;
    }

    /* Glassmorphic Container Cards for Pure HTML */
    .stGlassCard {
        background: rgba(17, 24, 39, 0.75);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
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
        font-size: 14px;
        background: rgba(16, 185, 129, 0.12);
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid rgba(16, 185, 129, 0.3);
    }

    .grade-2 {
        color: #06B6D4;
        font-style: italic;
        font-weight: 600;
        background: rgba(6, 182, 212, 0.12);
        padding: 2px 8px;
        border-radius: 4px;
        border: 1px solid rgba(6, 182, 212, 0.3);
    }

    .grade-1 {
        color: #9CA3AF;
        font-weight: 400;
        padding: 2px 6px;
    }

    /* Primary Simillimum Hero Card */
    .hero-simillimum {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(6, 182, 212, 0.08) 100%);
        border: 1px solid rgba(16, 185, 129, 0.4);
        border-radius: 14px;
        padding: 24px;
        margin-top: 15px;
        margin-bottom: 20px;
        box-shadow: 0 0 25px rgba(16, 185, 129, 0.12);
    }

    /* Custom Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        font-family: 'Outfit', sans-serif;
        font-weight: 600;
        border: none;
        border-radius: 8px;
        padding: 8px 24px;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
    }

    .stButton>button:hover {
        background: linear-gradient(135deg, #34D399 0%, #10B981 100%);
        box-shadow: 0 6px 16px rgba(16, 185, 129, 0.4);
        transform: translateY(-1px);
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: rgba(17, 24, 39, 0.6);
        padding: 6px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.05);
    }

    .stTabs [data-baseweb="tab"] {
        height: 42px;
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

    /* Dataframe Table styling */
    .stDataFrame {
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Top Navigation Brand Header */
    .brand-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 12px 0 20px 0;
        border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        margin-bottom: 24px;
    }

    .brand-title {
        font-size: 26px;
        font-weight: 800;
        background: linear-gradient(135deg, #34D399 0%, #06B6D4 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .status-pill {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 4px 12px;
        background: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 20px;
        color: #34D399;
        font-size: 12px;
        font-weight: 600;
    }
    
    .status-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10B981;
        box-shadow: 0 0 8px #10B981;
        animation: pulse-glow 2s infinite ease-in-out;
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
            box-shadow: 0 0 4px #10B981;
        }
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

    /* Conversational Quick Suggestion Chips */
    .stitch-chip {
        display: inline-block;
        background: rgba(31, 41, 55, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #D1D5DB;
        border-radius: 16px;
        padding: 5px 14px;
        font-size: 12px;
        font-weight: 500;
        margin-right: 6px;
        margin-bottom: 6px;
        cursor: pointer;
        transition: all 0.2s ease;
    }

    .stitch-chip:hover {
        background: rgba(16, 185, 129, 0.2);
        border-color: #10B981;
        color: #F9FAFB;
        transform: translateY(-1px);
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

