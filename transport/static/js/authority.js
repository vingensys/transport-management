// authority.js — authority address autofill + inline add-authority

(function () {
  let authorityIndex = null; // { [id:number]: {id, location, authority, address} }

  async function loadAuthorities() {
    try {
      const res = await fetch('/admin/api/authorities', { credentials: 'same-origin' });
      if (!res.ok) return;
      const data = await res.json();
      authorityIndex = Object.create(null);
      data.forEach(a => { authorityIndex[Number(a.id)] = a; });
    } catch (_) {
      // ignore network errors silently
    }
  }

  function fillAdjacentAddress(selectEl) {
    if (!authorityIndex) return;
    const id = Number(selectEl.value || 0);
    const a = authorityIndex[id];
    const row = selectEl.closest('.row');
    if (!row) return;
    const addrInput = row.querySelector('.authority-address'); // optional field
    if (addrInput) {
      addrInput.value = (a && a.address) ? a.address : '';
    }
  }

  // Inline Add Authority: submit modal form, then refresh current tab
  async function submitAddAuthority(form) {
    const fd = new FormData(form);
    try {
      const resp = await fetch('/admin/authority/add', { method: 'POST', body: fd, credentials: 'same-origin' });
      if (resp.ok) {
        // keep current tab (tabs.js manages hash/localStorage)
        if (window.location.hash) {
          window.location.reload();
        } else {
          // fallback: try saved tab
          const saved = (() => { try { return localStorage.getItem('activeTab'); } catch { return null; } })();
          if (saved) {
            history.replaceState(null, '', saved);
          }
          window.location.reload();
        }
      } else {
        alert('Failed to add authority');
      }
    } catch (e) {
      alert('Network error adding authority');
    }
  }

  document.addEventListener('DOMContentLoaded', async function () {
    await loadAuthorities();

    // Autofill address when an authority select changes (if an .authority-address field is present)
    document.addEventListener('change', function (e) {
      const el = e.target;
      if (el && el.matches('select[name$="authority_id"]')) {
        fillAdjacentAddress(el);
      }
    });

    // Handle inline Add Authority modal submit (if present on the page)
    const addAuthForm = document.getElementById('addAuthorityForm');
    if (addAuthForm) {
      addAuthForm.addEventListener('submit', function (e) {
        e.preventDefault();
        submitAddAuthority(addAuthForm);
      });
    }
  });
})();
