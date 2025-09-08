// tabs.js — persist active tab via URL hash + localStorage

(function () {
  // Wait for Bootstrap to be ready
  document.addEventListener('DOMContentLoaded', function () {
    // If we have a hash in the URL, prefer it
    if (window.location.hash) {
      const trigger = document.querySelector(
        `#adminTabs button[data-bs-target="${window.location.hash}"]`
      );
      if (trigger && window.bootstrap?.Tab) {
        new bootstrap.Tab(trigger).show();
      }
    }

    // When a tab is shown, save it and update hash
    document.querySelectorAll('#adminTabs button[data-bs-toggle="tab"]').forEach(function (btn) {
      btn.addEventListener('shown.bs.tab', function (e) {
        const target = e.target.getAttribute('data-bs-target');
        if (target) {
          try {
            localStorage.setItem('activeTab', target);
          } catch (_) {}
          if (history.replaceState) {
            history.replaceState(null, '', target);
          } else {
            // Fallback
            window.location.hash = target;
          }
        }
      });
    });

    // If no hash, restore last active tab from localStorage
    if (!window.location.hash) {
      const saved = (function () {
        try { return localStorage.getItem('activeTab'); } catch (_) { return null; }
      })();
      if (saved) {
        const trigger = document.querySelector(
          `#adminTabs button[data-bs-target="${saved}"]`
        );
        if (trigger && window.bootstrap?.Tab) {
          new bootstrap.Tab(trigger).show();
        }
      }
    }
  });
})();
