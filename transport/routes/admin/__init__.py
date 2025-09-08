from flask import Blueprint, render_template, jsonify
from sqlalchemy import func

# Models
from transport.models import (
    db,
    Company,
    Agreement,
    LorryDetails,
    LocationAuthority,
    Route,
    RouteStop,
)

# ---------------------------------
# Blueprint (prefix baked in)
# ---------------------------------
admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# ---------------------------------
# Helpers (kept minimal for Step 2)
# ---------------------------------
def _authorities_js_list(authorities):
    """Return a JSON-serializable list of authorities for front-end JS."""
    return [
        {
            "id": a.id,
            "location": a.location,
            "authority": a.authority,
            "address": a.address,
        }
        for a in authorities
    ]


def _routes_with_stops(routes):
    """Attach ordered .stops to each route (so templates can render them)."""
    for r in routes:
        r.stops = (
            RouteStop.query.filter_by(route_id=r.id)
            .order_by(RouteStop.order.asc())
            .all()
        )
    return routes


# ---------------------------------
# Dashboard view
# ---------------------------------
@admin_bp.route("/")
def view_dashboard():
    """
    Renders the modular admin dashboard.
    NOTE: Your template should already include the parts inside base_dashboard.html.
    """
    companies = Company.query.order_by(Company.id.desc()).all()
    agreements = Agreement.query.order_by(Agreement.id.desc()).all()
    lorries = LorryDetails.query.order_by(LorryDetails.id.desc()).all()
    authorities = LocationAuthority.query.order_by(LocationAuthority.id.desc()).all()
    routes = _routes_with_stops(Route.query.order_by(Route.id.desc()).all())

    # JSON-friendly list used by authority.js and dynamic selects
    authorities_js = _authorities_js_list(authorities)

    # IMPORTANT: we render the modular base that includes all parts
    # (templates/admin/base_dashboard.html)
    return render_template(
        "admin/base_dashboard.html",
        companies=companies,
        agreements=agreements,
        lorries=lorries,
        authorities=authorities,
        authorities_js=authorities_js,
        routes=routes,
    )


# ---------------------------------
# Minimal APIs used by your frontend JS
#  (We add the rest of CRUD routes in later steps.)
# ---------------------------------
@admin_bp.route("/api/authorities")
def api_authorities():
    """
    Return authorities for authority.js autofill and dynamic selects.
    """
    items = (
        LocationAuthority.query.order_by(LocationAuthority.id.desc())
        .with_entities(
            LocationAuthority.id,
            LocationAuthority.location,
            LocationAuthority.authority,
            LocationAuthority.address,
        )
        .all()
    )
    out = [
        dict(id=i.id, location=i.location, authority=i.authority, address=i.address)
        for i in items
    ]
    return jsonify(out)



