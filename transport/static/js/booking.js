// booking.js — compose a booking using existing endpoints
// Flow:
//   1) POST /admin/route/add
//   2) POST /admin/route/<id>/stop/add  (from → [intermediates] → to)
//   3) POST /admin/letter/add           (ELS flags, lorry, placement date, computed far_end_action)

(function () {
  function qs(sel) { return document.querySelector(sel); }
  function qsa(sel) { return Array.from(document.querySelectorAll(sel)); }

  // Build an intermediate stop card using the hidden <select> options as source
  function buildStopCard(index) {
    const options = (qs('#authorityOptionsSource') || {}).innerHTML || '<option value="">Select</option>';
    return `
      <div class="stop-card">
        <div class="row g-3 align-items-end">
          <div class="col-md-6">
            <label class="form-label">Stop Location</label>
            <input class="form-control" name="stop_location_${index}" placeholder="Intermediate stop">
          </div>
          <div class="col-md-4">
            <label class="form-label">Authority</label>
            <select class="form-select" name="stop_authority_id_${index}">
              ${options}
            </select>
          </div>
          <div class="col-md-2 d-grid">
            <button type="button" class="btn btn-outline-danger" title="Remove" onclick="this.closest('.stop-card').remove()">✕ Remove</button>
          </div>
        </div>
      </div>
    `;
  }

  async function createRoute(name) {
    const fd = new FormData();
    fd.append('name', name);
    const res = await fetch('/admin/route/add', { method: 'POST', body: fd, credentials: 'same-origin' });
    if (!res.ok) throw new Error('Failed to create route');
  }

  async function findCreatedRouteByName(name) {
    const res = await fetch('/admin/api/routes', { credentials: 'same-origin' });
    if (!res.ok) throw new Error('Failed to fetch routes');
    const routes = await res.json();
    const matches = routes.filter(r => r.name === name);
    if (!matches.length) throw new Error('Created route not found');
    return matches.sort((a, b) => b.id - a.id)[0]; // newest if duplicates
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

  // Compute far-end action from "Loading at ELS/ED?"
  function computeFarEndAction(loadAtHomeVal /* '1' or '0' */) {
    return loadAtHomeVal === '1' ? 'unload' : 'load';
  }

  document.addEventListener('DOMContentLoaded', function () {
    const form = qs('#bookingForm');
    const addStopBtn = qs('#addBookingStopBtn');
    const stopsContainer = qs('#bookingIntermediateStops');
    const loadAtHomeSel = qs('#letter select[name="load_at_home"]');

    // Add Stop button
    if (addStopBtn && stopsContainer) {
      addStopBtn.addEventListener('click', function () {
        const index = stopsContainer.children.length + 1;
        stopsContainer.insertAdjacentHTML('beforeend', buildStopCard(index));
      });
    }

    // Optional: live preview of computed far-end action (console or future UI label)
    if (loadAtHomeSel) {
      loadAtHomeSel.addEventListener('change', function () {
        const action = computeFarEndAction(this.value || '1');
        // You can show this in the UI later if desired.
        console.debug('[booking] far_end_action =', action);
      });
    }

    if (form) {
      form.addEventListener('submit', async function (e) {
        e.preventDefault();
        const fd = new FormData(form);

        // Required fields
        const fromLoc = (fd.get('from_location') || '').toString().trim();
        const toLoc = (fd.get('to_location') || '').toString().trim();
        if (!fromLoc || !toLoc) { alert('From and To are required.'); return; }

        // 1) Create a temporary route name (unique-ish)
        const routeName = `${fromLoc} → ${toLoc} @ ${new Date().toISOString().slice(0,16).replace('T',' ')}`;

        try {
          await createRoute(routeName);
          const route = await findCreatedRouteByName(routeName);

          // 2) Build stops (ordered)
          const stops = [];
          stops.push({
            location: fromLoc,
            type: 'from',
            authority_id: (fd.get('from_authority_id') || '').toString()
          });

          // Intermediate stops
          qsa('#bookingIntermediateStops .stop-card').forEach((card) => {
            const loc = (card.querySelector('input[name^="stop_location_"]')?.value || '').trim();
            const auth = (card.querySelector('select[name^="stop_authority_id_"]')?.value || '').toString();
            if (loc) stops.push({ location: loc, type: 'intermediate', authority_id: auth });
          });

          stops.push({
            location: toLoc,
            type: 'to',
            authority_id: (fd.get('to_authority_id') || '').toString()
          });

          for (let i = 0; i < stops.length; i++) {
            await addStop(route.id, stops[i], i + 1);
          }

          // 3) Create letter (booking) — compute far_end_action from load_at_home
          const fL = new FormData();
          fL.append('lorry_id', fd.get('lorry_id') || '');
          fL.append('route_id', route.id);
          const isHome = (fd.get('is_home_depot') || '1');
          const loadAtHome = (fd.get('load_at_home') || '1');
          fL.append('is_home_depot', isHome);
          fL.append('load_at_home', loadAtHome);
          fL.append('far_end_action', computeFarEndAction(loadAtHome));
          fL.append('remarks', fd.get('remarks') || '');
          const placement = (fd.get('placement_date') || '').toString();
          if (placement) fL.append('placement_date', placement); // backend may ignore if not supported

          const rL = await fetch('/admin/letter/add', { method: 'POST', body: fL, credentials: 'same-origin' });
          if (!rL.ok) throw new Error('Failed to create booking');

          alert('Booking created!');
          if (window.location.hash !== '#letter') {
            history.replaceState(null, '', '#letter');
          }
          window.location.reload();
        } catch (err) {
          console.error(err);
          alert(err.message || 'Failed to create booking');
        }
      });
    }
  });
})();
