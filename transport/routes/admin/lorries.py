from flask import request, redirect, url_for
from sqlalchemy import func

from transport.models import db, LorryDetails
from . import admin_bp


def _redirect_to_tab(tab_hash: str):
    """Send the user back to a specific dashboard tab (e.g., '#lorry')."""
    return redirect(url_for("admin.view_dashboard") + tab_hash)


# -------------------------
# Lorry — Create
# -------------------------
@admin_bp.route("/lorry/add", methods=["POST"])
def add_lorry():
    lorry_number = (request.form.get("lorry_number") or "").strip()
    capacity = request.form.get("capacity", type=float)
    carrier_size = (request.form.get("carrier_size") or "").strip()
    remarks = (request.form.get("remarks") or "").strip()

    if not lorry_number:
        # UI requires this; bail back to tab quietly
        return _redirect_to_tab("#lorry")

    l = LorryDetails(
        lorry_number=lorry_number,
        capacity=capacity,
        carrier_size=carrier_size,
        remarks=remarks,
    )
    db.session.add(l)
    db.session.commit()
    return _redirect_to_tab("#lorry")


# -------------------------
# Lorry — Update
# -------------------------
@admin_bp.route("/lorry/edit/<int:lorry_id>", methods=["POST"])
def edit_lorry(lorry_id: int):
    l = LorryDetails.query.get_or_404(lorry_id)

    lorry_number = (request.form.get("lorry_number") or "").strip()
    capacity = request.form.get("capacity", type=float)
    carrier_size = (request.form.get("carrier_size") or "").strip()
    remarks = (request.form.get("remarks") or "").strip()

    if lorry_number:
        l.lorry_number = lorry_number
    # capacity may be None if field left blank; assign only when provided (including 0)
    if capacity is not None:
        l.capacity = capacity
    l.carrier_size = carrier_size
    l.remarks = remarks

    db.session.commit()
    return _redirect_to_tab("#lorry")


# -------------------------
# (Optional) Lorries API
# -------------------------
@admin_bp.route("/api/lorries")
def api_lorries():
    items = LorryDetails.query.order_by(LorryDetails.id.desc()).all()
    return {
        "lorries": [
            {
                "id": i.id,
                "lorry_number": i.lorry_number,
                "capacity": i.capacity,
                "carrier_size": i.carrier_size,
                "remarks": i.remarks,
            }
            for i in items
        ]
    }
