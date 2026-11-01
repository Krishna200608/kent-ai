/**
 * busy.js – Kent-AI button busy / loading feedback runtime.
 *
 * Contract:
 *  - Runs once per page load (guarded by window.__kentBusy).
 *  - On any primary/secondary button click (not download, not form-submit twin)
 *    adds data-kent-busy="true" within GRACE ms and raises html[data-kent-busy].
 *  - Clears on the next Streamlit notRunning transition (MIN_VISIBLE enforced).
 *  - Adds html[data-kent-slow] when the run exceeds SLOW_THRESHOLD ms.
 *  - Sweeps orphan [data-tip] tooltip nodes that JS injected but Streamlit pruned.
 *  - Never keys on script-state alone for global indicator (header fragment polls
 *    every 2 s and also sets "running"); we track a user-click flag separately.
 */
(() => {
  if (window.__kentBusy) return;
  window.__kentBusy = true;

  const GRACE = 700;        // ms before showing busy state (avoids flash on fast ops)
  const MIN_VISIBLE = 450;  // ms minimum spinner visibility once shown
  const SPIN_DELAY = 150;   // ms from click to first visual feedback
  const SLOW_THRESHOLD = 4000; // ms before showing slow-operation overlay

  const root = document.documentElement;
  let _userClickPending = false;
  let _busyShownAt = 0;
  let _graceTimer = null;
  let _slowTimer = null;
  let _clearTimer = null;

  /** Show global busy indicator. */
  function _showBusy() {
    _busyShownAt = Date.now();
    root.setAttribute('data-kent-busy', 'true');
    _slowTimer = setTimeout(() => {
      root.setAttribute('data-kent-slow', 'true');
    }, SLOW_THRESHOLD);
  }

  /** Clear global busy indicator, honouring MIN_VISIBLE. */
  function _clearBusy() {
    clearTimeout(_graceTimer);
    clearTimeout(_slowTimer);
    root.removeAttribute('data-kent-slow');
    const elapsed = Date.now() - _busyShownAt;
    const remaining = Math.max(0, MIN_VISIBLE - elapsed);
    _clearTimer = setTimeout(() => {
      if (!_userClickPending) {
        root.removeAttribute('data-kent-busy');
        // Also clear any data-kent-busy on individual buttons
        document.querySelectorAll('button[data-kent-busy="true"]').forEach(b => {
          b.removeAttribute('data-kent-busy');
        });
      }
    }, remaining);
  }

  /** Mark a button as locally busy. */
  function _markButton(btn) {
    if (!btn) return;
    btn.setAttribute('data-kent-busy', 'true');
    btn.setAttribute('aria-busy', 'true');
  }

  /** Clear a button's busy state. */
  function _clearButton(btn) {
    if (!btn) return;
    btn.removeAttribute('data-kent-busy');
    btn.removeAttribute('aria-busy');
  }

  /** Determine if a button is a download button (heuristic: its ancestor has data-testid="stDownloadButton"). */
  function _isDownloadButton(btn) {
    return !!btn.closest('[data-testid="stDownloadButton"]');
  }

  /** Determine if a button is a form-submit twin (has class containing "__busy"). */
  function _isBusyTwin(btn) {
    return btn.id && btn.id.includes('__busy');
  }

  /** Determine if a button is a popover trigger. */
  function _isPopoverTrigger(btn) {
    return !!btn.closest('[data-testid="stPopoverButton"]') || btn.getAttribute('data-testid') === 'stPopoverButton';
  }

  /** Global click handler — attach on first user gesture. */
  document.addEventListener('click', (e) => {
    const btn = e.target.closest('button[data-testid^="stBaseButton-"]');
    if (!btn) return;
    if (_isDownloadButton(btn)) return;
    if (_isBusyTwin(btn)) return;
    if (_isPopoverTrigger(btn)) return;

    _userClickPending = true;
    _markButton(btn);

    clearTimeout(_graceTimer);
    _graceTimer = setTimeout(() => {
      _showBusy();
    }, GRACE);
  }, { capture: true, passive: true });

  /**
   * Watch Streamlit's data-test-script-state transitions.
   * We ONLY clear busy when we see notRunning AND a user click was pending
   * (prevents the header fragment's polling from toggling the indicator).
   */
  const appEl = document.querySelector('[data-testid="stApp"]');
  if (appEl) {
    const observer = new MutationObserver(() => {
      const state = appEl.getAttribute('data-test-script-state');
      if (state === 'notRunning' && _userClickPending) {
        _userClickPending = false;
        _clearBusy();
      }
    });
    observer.observe(appEl, { attributes: true, attributeFilter: ['data-test-script-state'] });
  }

  /**
   * Orphan tooltip sweeper: every 3 s, hide any [data-kent-orphan] nodes
   * that have been detached from their anchor (Streamlit re-render pruned them).
   */
  setInterval(() => {
    document.querySelectorAll('[data-kent-orphan="true"]').forEach(el => {
      if (!el.offsetParent) el.style.display = 'none';
    });
  }, 3000);

  // Expose for test/debug
  window.__kentBusyAPI = { showBusy: _showBusy, clearBusy: _clearBusy };
})();
