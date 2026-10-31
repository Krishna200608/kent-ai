"""Google Stitch Design System & CSS theme injection for Streamlit (Phase 7)."""

from __future__ import annotations

from pathlib import Path
import streamlit as st
import streamlit.components.v1 as components

_CSS_PATH = Path(__file__).resolve().parent / "styles.css"


def inject_custom_css() -> None:
    """Inject custom Google Stitch clinical dark-mode CSS and typography into Streamlit DOM."""
    if _CSS_PATH.is_file():
        css = _CSS_PATH.read_text(encoding="utf-8")
        st.markdown(f"<style id='kent-ai-theme'>\n{css}\n</style>", unsafe_allow_html=True)


def inject_full_screen_layout_js() -> None:
    """Inject a MutationObserver via components.v1.html to force full-width layout.

    Uses window.parent to reach the Streamlit host document from within the
    component iframe. Watches for sidebar aria-expanded changes and applies
    inline styles to the correct parent flex containers so the main content
    area fills the viewport when the sidebar is collapsed.
    """
    _JS = """
    <script>
    (function() {
        var doc = window.parent.document;

        function applyLayout() {
            var sidebar = doc.querySelector('[data-testid="stSidebar"]');
            var appView = doc.querySelector('[data-testid="stAppViewContainer"]');
            var stMain  = doc.querySelector('[data-testid="stMain"]') ||
                          doc.querySelector('.stMain');
            var block   = doc.querySelector('.block-container') ||
                          doc.querySelector('[data-testid="stMainBlockContainer"]');

            if (!appView || !block) return;

            // Sidebar is collapsed when aria-expanded is "false" OR when the
            // expand button is present in the header.
            var expandBtn  = doc.querySelector('[data-testid="stExpandSidebarButton"]');
            var collapsed  = expandBtn !== null ||
                             (sidebar && sidebar.getAttribute('aria-expanded') === 'false');

            if (collapsed) {
                // Force the main section to fill whatever space the sidebar vacated.
                if (stMain) {
                    stMain.style.setProperty('width',    '100%',    'important');
                    stMain.style.setProperty('flex',     '1 1 auto','important');
                    stMain.style.setProperty('min-width','0',       'important');
                    stMain.style.setProperty('max-width','100%',    'important');
                }
                // Also widen the block-container inside it.
                block.style.setProperty('max-width', '100%', 'important');
                block.style.setProperty('width',     '100%', 'important');
                block.style.setProperty('margin-left',  '0', 'important');
                block.style.setProperty('margin-right', '0', 'important');
            } else {
                // Restore managed properties when sidebar re-opens.
                if (stMain) {
                    stMain.style.removeProperty('width');
                    stMain.style.removeProperty('flex');
                    stMain.style.removeProperty('min-width');
                    stMain.style.removeProperty('max-width');
                }
                block.style.removeProperty('max-width');
                block.style.removeProperty('width');
                block.style.removeProperty('margin-left');
                block.style.removeProperty('margin-right');
            }
        }

        // Run once immediately (after a short delay to let Streamlit render).
        setTimeout(applyLayout, 200);

        // Watch for DOM mutations (sidebar toggle, Streamlit reruns).
        var observer = new MutationObserver(function(mutations) {
            applyLayout();
        });

        observer.observe(doc.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['aria-expanded', 'class', 'style']
        });

        // Also respond to window resize.
        window.parent.addEventListener('resize', applyLayout);
    })();
    </script>
    """
    # height=0 + scrolling=False renders a zero-height invisible iframe.
    # The script runs in the iframe context where window.parent is the Streamlit page.
    components.html(_JS, height=0, scrolling=False)
