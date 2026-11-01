(() => {
  if (window.__kentBusy) return;
  window.__kentBusy = true;
  const root = document.documentElement;
  const GRACE = 700, MIN_VISIBLE = 450, SPIN_DELAY = 120, SLOW_AFTER = 3000, USER_WINDOW = 1500;
  let lastInput = 0, btn = null, t0 = 0, sawRun = false, rootOwned = false, tGrace, tSlow, tRelease;
  const app = () => document.querySelector('[data-testid="stApp"]');
  const live = document.createElement('div');
  live.className = 'sr-only'; live.setAttribute('role', 'status'); live.setAttribute('aria-live', 'polite');
  document.body.appendChild(live);

  const mark = () => { lastInput = performance.now(); };
  document.addEventListener('pointerdown', mark, true);
  document.addEventListener('keydown', (e) => {
    const typing = e.target.matches && e.target.matches('input, textarea, [contenteditable="true"]');
    if (e.key === 'Enter' || e.key === 'Tab' || (e.key === ' ' && !typing)) mark();
  }, true);

  function begin(b) {
    finish(true);
    btn = b; rootOwned = true; t0 = performance.now(); sawRun = false;
    if (b) { b.setAttribute('data-kent-busy', 'true'); b.setAttribute('aria-busy', 'true'); }
    root.setAttribute('data-kent-busy', 'true');
    live.textContent = 'Working';
    // If the script never starts, the click did not rerun (download ignore, popover, etc.)
    tGrace = setTimeout(() => { if (!sawRun) finish(true); }, GRACE);
    tSlow = setTimeout(() => root.setAttribute('data-kent-slow', 'true'), SLOW_AFTER);
  }
  function finish(now) {
    clearTimeout(tGrace); clearTimeout(tSlow); clearTimeout(tRelease);
    const b = btn; btn = null;
    const done = () => {
      if (b) { b.removeAttribute('data-kent-busy'); b.removeAttribute('aria-busy'); }
      root.removeAttribute('data-kent-busy'); root.removeAttribute('data-kent-slow');
      rootOwned = false; live.textContent = '';
    };
    const shown = performance.now() - t0;
    if (now || !rootOwned || shown < SPIN_DELAY) done();
    else tRelease = setTimeout(done, Math.max(0, MIN_VISIBLE - shown));
  }
  document.addEventListener('click', (e) => {
    const b = e.target.closest && e.target.closest('button[data-testid^="stBaseButton-"]');
    if (!b || b.disabled || b.closest('header, [data-testid="stHeader"], [data-kent-nobusy]')) return;
    begin(b);
  }, true);

  // Orphan tooltip safety net: hide (never remove; React owns the node) tooltips whose trigger is gone.
  function sweepTooltips() {
    document.querySelectorAll('[data-testid="stTooltipContent"]').forEach((tip) => {
      const host = tip.closest('[id]');
      if (host && !document.querySelector('[aria-describedby="' + host.id + '"]'))
        host.setAttribute('data-kent-orphan', 'true');
    });
  }
  document.addEventListener('pointerdown', () => setTimeout(sweepTooltips, 150), true);

  (function hook() {
    const a = app();
    if (!a) return void setTimeout(hook, 200);
    new MutationObserver((records) => {
      const s = a.getAttribute('data-test-script-state');
      if (s === 'running' || records.some((r) => r.oldValue === 'running')) sawRun = true;
      if (s === 'running') {
        // Non-button user actions (Enter in input, checkbox, selectbox): only if user just interacted.
        if (!rootOwned && performance.now() - lastInput < USER_WINDOW) { begin(null); sawRun = true; }
      } else if (s === 'notRunning' && rootOwned) { finish(false); sweepTooltips(); }
    }).observe(a, { attributes: true, attributeFilter: ['data-test-script-state'], attributeOldValue: true });
  })();
})();
