// route_builder.js — add routes with ordered stops via existing endpoints
// Uses:
//   POST /admin/route/add
//   POST /admin/route/<id>/stop/add
//   GET  /admin/api/routes

(function () {
  function qs(sel) { return document.querySelector(sel); }
  function qsa(sel) { return Array.from(document.querySelectorAll(sel)); }

  // Build a stop-card HTML using the hidden <select> options as source
  function buildStopCard(index) {
    const options = (qs('#rbAuthorityOptionsSource') || {}).innerHTML || '<option value="">Select</option>';
    return `
      <div class="stop-card">
        <div class="row g-3">
          <div class="col-md-6">
            <label class="form-label">Stop Location</label>
            <input class="form-control" name="stop_location_${index}" placeholder="Location">
          </div>
          <div class="col-md-4">
            <label class="form-label">Authority</label>
            <select name="stop_authority_id_${index}" class="form-select">
              ${options}
            </select>
          </div>
        </div>
      </div>
    `;
  }

  async function createRoute(name, totalKm) {
    const fd = new FormData();
    fd.append('name', name);
    if (totalKm !== null && totalKm !== '' && !Number.isNaN(Number(totalKm))) {
      fd.append('total_km', String(totalKm));
    }
    const res = await fetch('/admin/route/add', { method: 'POST', body: fd, credentials: 'same-origin' });
    if (!res.ok) throw new Error('Failed to create route');
  }

  async function findCreatedRouteByName(name) {
    const res = await fetch('/admin/api/routes', { credentials: 'same-origin' });
    if (!res.ok) throw new Error('Failed to fetch routes');
    const routes = await res.json();
    // If multiple with same name, pick the newest (max id)
    const matches = routes.filter(r => r.name === name);
    if (!matches.length) throw new Error('Created route not found');
    return matches.sort((a, b) => b.id - a.id)[0];
  }

  async function addStop(routeId, stop, order) {
    const fd = new FormData();
    fd.append('location', stop.location);
    fd.append('type', stop.type); // 'from' | 'intermediate' | 'to'
    fd.append('order', String(order));
    if (stop.authority_id) fd.append('authority_id', stop.authority_id);
    const res = await fetch(`/admin/route/${routeId}/stop/add`, { method: 'POST', body: fd, credentials: 'same-origin' });
    if (!res.ok) throw new Error('Failed to add a stop');
  }

  document.addEventListener('DOMContentLoaded', function () {
    const form = qs('#routeForm');
    const addStopBtn = qs('#addStopBtn');
    const stopsContainer = qs('#intermediateStops');

    if (addStopBtn && stopsContainer) {
      addStopBtn.addEventListener('click', function () {
        const index = stopsContainer.children.length + 1;
        stopsContainer.insertAdjacentHTML('beforeend', buildStopCard(index));
      });
    }

    if (form) {
      form.addEventListener('submit', async function (e) {
        e.preventDefault();

        const fd = new FormData(form);
        const name = (fd.get('name') || '').toString().trim();
        const totalKm = fd.get('total_km');

        const fromLoc = (fd.get('from_location') || '').toString().trim();
        const toLoc = (fd.get('to_location') || '').toString().trim();
        if (!fromLoc || !toLoc) {
          alert('From and To locations are required.');
          return;
        }

        try {
          // 1) Create route
          await createRoute(name, totalKm);

          // 2) Find the route we just created
          const route = await findCreatedRouteByName(name);

          // 3) Build stops array in order
          const stops = [];
          stops.push({
            location: fromLoc,
            type: 'from',
            authority_id: (fd.get('from_authority_id') || '').toString()
          });

          // Intermediate stops (scan dynamically added cards)
          qsa('#intermediateStops .stop-card').forEach((card, idx) => {
            const locInput = card.querySelector('input[name^="stop_location_"]');
            const sel = card.querySelector('select[name^="stop_authority_id_"]');
            const loc = (locInput?.value || '').trim();
            const auth = (sel?.value || '').toString();
            if (loc) {
              stops.push({ location: loc, type: 'intermediate', authority_id: auth });
            }
          });

          stops.push({
            location: toLoc,
            type: 'to',
            authority_id: (fd.get('to_authority_id') || '').toString()
          });

          // 4) POST stops sequentially
          for (let i = 0; i < stops.length; i++) {
            await addStop(route.id, stops[i], i + 1);
          }

          alert('Route created with stops!');
          // Reset form and UI, keep user on Route tab
          form.reset();
          if (stopsContainer) stopsContainer.innerHTML = '';
          if (window.location.hash !== '#route') {
            history.replaceState(null, '', '#route');
          }
          window.location.reload();
        } catch (err) {
          console.error(err);
          alert(err.message || 'Failed to save route and stops');
        }
      });
    }
  });
})();
