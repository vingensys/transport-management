from flask import request, redirect, url_for, jsonify
from transport.models import db, Route, RouteStop, LocationAuthority
from . import admin_bp


def _redirect_to_tab(tab_hash: str):
    """Send the user back to a specific dashboard tab (e.g., '#route')."""
    return redirect(url_for("admin.view_dashboard") + tab_hash)


# -------------------------
# Route — Create
# -------------------------
@admin_bp.route("/route/add", methods=["POST"])
def add_route():
    name = (request.form.get("name") or "").strip()
    total_km = request.form.get("total_km", type=int)

    if not name:
        return _redirect_to_tab("#route")

    r = Route(name=name, total_km=total_km)
    db.session.add(r)
    db.session.commit()

    # If the form also carried from/to + intermediate stops (from UI),
    # those are added separately via /route/<id>/stop/add. Keeping this
    # endpoint focused makes it reusable for booking.js as well.
    return _redirect_to_tab("#route")


# -------------------------
# Route — Edit (name / total_km)
# -------------------------
@admin_bp.route("/route/edit/<int:route_id>", methods=["POST"])
def edit_route(route_id: int):
    r = Route.query.get_or_404(route_id)

    name = (request.form.get("name") or "").strip()
    total_km = request.form.get("total_km", type=int)

    if name:
        r.name = name
    if total_km is not None:
        r.total_km = total_km

    db.session.commit()
    return _redirect_to_tab("#route")


# -------------------------
# Route Stop — Create (append in order)
# -------------------------
@admin_bp.route("/route/<int:route_id>/stop/add", methods=["POST"])
def add_route_stop(route_id: int):
    r = Route.query.get_or_404(route_id)

    location = (request.form.get("location") or "").strip()
    stop_type = (request.form.get("type") or "").strip()  # 'from' | 'intermediate' | 'to'
    order = request.form.get("order", type=int)
    authority_id = request.form.get("authority_id", type=int)

    if not location or not stop_type or order is None:
        return _redirect_to_tab("#route")

    # Validate authority if provided
    if authority_id:
        _ = LocationAuthority.query.get(authority_id)

    rs = RouteStop(
        route_id=r.id,
        location=location,
        type=stop_type,
        order=order,
        authority_id=authority_id,
    )
    db.session.add(rs)
    db.session.commit()
    return _redirect_to_tab("#route")


# -------------------------
# Route Stop — Edit (location / type / order / authority)
# -------------------------
@admin_bp.route("/route/stop/edit/<int:stop_id>", methods=["POST"])
def edit_route_stop(stop_id: int):
    rs = RouteStop.query.get_or_404(stop_id)

    location = (request.form.get("location") or "").strip()
    stop_type = (request.form.get("type") or "").strip()
    order = request.form.get("order", type=int)
    authority_id = request.form.get("authority_id", type=int)

    if location:
        rs.location = location
    if stop_type:
        rs.type = stop_type
    if order is not None:
        rs.order = order

    # Validate authority if provided (allow clearing with empty value)
    if authority_id is not None:
        if authority_id == 0:
            rs.authority_id = None
        else:
            a = LocationAuthority.query.get(authority_id)
            rs.authority_id = a.id if a else rs.authority_id

    db.session.commit()
    return _redirect_to_tab("#route")


# -------------------------
# Routes API (used by route_builder.js / booking.js)
# -------------------------
@admin_bp.route("/api/routes")
def api_routes():
    items = Route.query.with_entities(Route.id, Route.name).order_by(Route.id.desc()).all()
    return jsonify([{"id": i.id, "name": i.name} for i in items])
