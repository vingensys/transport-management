from flask import request, jsonify
from sqlalchemy import func

from transport.models import (
    db,
    LetterRecord,
    Route,
    LorryDetails,
    Agreement,
)
from . import admin_bp
from .utils import (
    redirect_to_tab,
    get_active_agreement,
    next_booking_serial,
    make_letter_number,
    parse_placement_date,
)


# ------------------------------------------------
# Create Letter (Lorry Booking)
# POST /admin/letter/add
# Expects (from booking.js):
#   - lorry_id (int, required)
#   - route_id (int, required)  -> route is created beforehand by UI flow
#   - is_home_depot ('1'|'0')
#   - load_at_home ('1'|'0')
#   - far_end_action ('load'|'unload')  -> UI computes from load_at_home, but we accept any
#   - placement_date (YYYY-MM-DD)       -> optional
#   - remarks (str)                      -> optional
# ------------------------------------------------
@admin_bp.route("/letter/add", methods=["POST"])
def add_letter():
    # Validate basics
    lorry_id = request.form.get("lorry_id", type=int)
    route_id = request.form.get("route_id", type=int)

    if not lorry_id or not route_id:
        return redirect_to_tab("#letter")

    lorry = LorryDetails.query.get(lorry_id)
    route = Route.query.get(route_id)
    if not lorry or not route:
        return redirect_to_tab("#letter")

    # Active agreement is mandatory for booking serial/letter number
    ag = get_active_agreement()
    if not ag:
        return redirect_to_tab("#letter")

    # Flags & fields
    is_home = request.form.get("is_home_depot", default="1").strip()
    load_at_home = request.form.get("load_at_home", default="1").strip()
    far_end_action = (request.form.get("far_end_action") or "").strip().lower()  # 'load'|'unload'
    remarks = (request.form.get("remarks") or "").strip()

    placement_date = parse_placement_date(request.form.get("placement_date"))

    # Serial and number
    serial = next_booking_serial(ag.id)
    letter_no = make_letter_number(ag, serial)

    # Create record
    letter = LetterRecord(
        letter_number=letter_no,
        booking_serial=serial,
        company_id=ag.company_id,
        lorry_id=lorry.id,
        route_id=route.id,
        agreement_id=ag.id,
        is_for_home_depot=(is_home == "1"),
        loading_at_home_depot=(load_at_home == "1"),
        far_end_action=far_end_action if far_end_action in {"load", "unload"} else None,
        placement_date=placement_date,
        remarks=remarks or None,
        # state: defaults as per your model default (e.g., 'DRAFT')
    )

    db.session.add(letter)
    db.session.commit()
    return redirect_to_tab("#letter")


# ------------------------------------------------
# Edit Letter
# POST /admin/letter/edit/<id>
# Allows updating lorry, route, flags, far_end_action, placement_date, remarks, and state
# (Does NOT change booking_serial or letter_number)
# ------------------------------------------------
@admin_bp.route("/letter/edit/<int:letter_id>", methods=["POST"])
def edit_letter(letter_id: int):
    letter = LetterRecord.query.get_or_404(letter_id)

    # Optional updates
    lorry_id = request.form.get("lorry_id", type=int)
    route_id = request.form.get("route_id", type=int)

    if lorry_id:
        l = LorryDetails.query.get(lorry_id)
        if l:
            letter.lorry_id = l.id

    if route_id:
        r = Route.query.get(route_id)
        if r:
            letter.route_id = r.id

    # Flags and fields
    if "is_home_depot" in request.form:
        letter.is_for_home_depot = (request.form.get("is_home_depot") == "1")

    if "load_at_home" in request.form:
        letter.loading_at_home_depot = (request.form.get("load_at_home") == "1")

    if "far_end_action" in request.form:
        fea = (request.form.get("far_end_action") or "").strip().lower()
        letter.far_end_action = fea if fea in {"load", "unload"} else None

    if "placement_date" in request.form:
        letter.placement_date = parse_placement_date(request.form.get("placement_date"))

    if "remarks" in request.form:
        letter.remarks = (request.form.get("remarks") or "").strip() or None

    # Optional: state updates if you exposed it in the UI
    if "state" in request.form:
        st = (request.form.get("state") or "").strip().upper()
        # Accept known values only if you constrained model; else store as-is
        letter.state = st

    db.session.commit()
    return redirect_to_tab("#letter")


# ------------------------------------------------
# (Optional) Letters API
# GET /admin/api/letters
# Handy for diagnostics / future list views
# ------------------------------------------------
@admin_bp.route("/api/letters")
def api_letters():
    items = (
        LetterRecord.query
        .order_by(LetterRecord.id.desc())
        .all()
    )
    out = []
    for i in items:
        out.append({
            "id": i.id,
            "letter_number": i.letter_number,
            "booking_serial": i.booking_serial,
            "company_id": i.company_id,
            "agreement_id": i.agreement_id,
            "lorry_id": i.lorry_id,
            "route_id": i.route_id,
            "is_for_home_depot": bool(i.is_for_home_depot),
            "loading_at_home_depot": bool(i.loading_at_home_depot),
            "far_end_action": i.far_end_action,
            "placement_date": i.placement_date.isoformat() if i.placement_date else None,
            "remarks": i.remarks,
            "state": getattr(i, "state", None),
        })
    return jsonify(out)
