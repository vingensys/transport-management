from flask import request, redirect, url_for, jsonify
from transport.models import db, LocationAuthority
from . import admin_bp


def _redirect_to_tab(tab_hash: str):
    """Send the user back to a specific dashboard tab (e.g., '#authority')."""
    return redirect(url_for("admin.view_dashboard") + tab_hash)


# -------------------------
# Authority — Create
# -------------------------
@admin_bp.route("/authority/add", methods=["POST"])
def add_authority():
    location = (request.form.get("location") or "").strip()
    authority = (request.form.get("authority") or "").strip()
    address = (request.form.get("address") or "").strip()

    if not location or not authority:
        return _redirect_to_tab("#authority")

    a = LocationAuthority(location=location, authority=authority, address=address)
    db.session.add(a)
    db.session.commit()
    return _redirect_to_tab("#authority")


# -------------------------
# Authority — Update
# -------------------------
@admin_bp.route("/authority/edit/<int:authority_id>", methods=["POST"])
def edit_authority(authority_id: int):
    a = LocationAuthority.query.get_or_404(authority_id)

    location = (request.form.get("location") or "").strip()
    authority = (request.form.get("authority") or "").strip()
    address = (request.form.get("address") or "").strip()

    if location:
        a.location = location
    if authority:
        a.authority = authority
    a.address = address  # may be empty

    db.session.commit()
    return _redirect_to_tab("#authority")


# -------------------------
# Authorities API (used by authority.js & dynamic selects)
# -------------------------
@admin_bp.route("/api/authorities")
def api_authorities():
    items = (
        LocationAuthority.query
        .order_by(LocationAuthority.id.desc())
        .with_entities(
            LocationAuthority.id,
            LocationAuthority.location,
            LocationAuthority.authority,
            LocationAuthority.address,
        )
        .all()
    )
    out = [
        {
            "id": i.id,
            "location": i.location,
            "authority": i.authority,
            "address": i.address,
        }
        for i in items
    ]
    return jsonify(out)
