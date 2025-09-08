// modals.js — small Bootstrap modal helpers (generic, feature-agnostic)
(function () {
  function qs(sel, root) { return (root || document).querySelector(sel); }
  function qsa(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  // Autofocus the first enabled input (or [autofocus]) when a modal opens
  document.addEventListener('show.bs.modal', function (e) {
    const modal = e.target;
    // Prefer [autofocus]
    let el = qs('[autofocus]:not([disabled])', modal);
    // Else first input/select/textarea
    if (!el) el = qsa('input,select,textarea', modal).find(x => !x.disabled && x.type !== 'hidden');
    if (el) {
      setTimeout(() => { try { el.focus(); el.select?.(); } catch (_) {} }, 75);
    }
  });

  // Reset forms inside the modal when it hides (clears stale values/validation)
  document.addEventListener('hidden.bs.modal', function (e) {
    const modal = e.target;
    qsa('form', modal).forEach(f => {
      try { f.reset(); } catch (_) {}
      // clear simple validation states if any
      qsa('.is-invalid,.is-valid', f).forEach(x => x.classList.remove('is-invalid','is-valid'));
    });
  });

  // Ensure only one modal is visible at a time (hide others if a new one shows)
  document.addEventListener('show.bs.modal', function (e) {
    qsa('.modal.show').forEach(opened => {
      if (opened !== e.target) {
        const instance = bootstrap.Modal.getInstance(opened);
        if (instance) instance.hide();
      }
    });
  });

  // Lightweight confirm support:
  //  - <form data-confirm="Are you sure?">…</form>
  //  - <button data-confirm="Are you sure?">…</button> (prevents default if cancelled)
  document.addEventListener('submit', function (e) {
    const el = e.target;
    if (el.matches('form[data-confirm]')) {
      const msg = el.getAttribute('data-confirm') || 'Are you sure?';
      if (!window.confirm(msg)) e.preventDefault();
    }
  }, true);

  document.addEventListener('click', function (e) {
    const btn = e.target.closest('[data-confirm]');
    if (btn && (btn.tagName === 'A' || btn.tagName === 'BUTTON')) {
      const msg = btn.getAttribute('data-confirm') || 'Are you sure?';
      if (!window.confirm(msg)) e.preventDefault();
    }
  }, true);
})();
