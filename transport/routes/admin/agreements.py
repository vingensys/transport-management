from flask import request, redirect, url_for
from sqlalchemy import func

from transport.models import db, Agreement, Company

# Use the shared admin blueprint defined in admin/__init__.py
from . import admin_bp


def _redirect_to_tab(tab_hash: str):
    """Redirect back to a specific dashboard tab (e.g., '#agreement')."""
    return redirect(url_for("admin.view_dashboard") + tab_hash)


# -------------------------
# Agreement — Create
# -------------------------
@admin_bp.route("/agreement/add", methods=["POST"])
def add_agreement():
    company_id = request.form.get("company_id", type=int)
    loa_number = (request.form.get("loa_number") or "").strip()
    total_mt_km = request.form.get("total_mt_km", type=float)
    rate_per_mt_km = request.form.get("rate_per_mt_km", type=float)

    if not company_id or not loa_number or total_mt_km is None or rate_per_mt_km is None:
        return _redirect_to_tab("#agreement")

    # Ensure company exists
    company = Company.query.get(company_id)
    if not company:
        return _redirect_to_tab("#agreement")

    ag = Agreement(
        company_id=company_id,
        loa_number=loa_number,
        total_mt_km=total_mt_km,
        rate_per_mt_km=rate_per_mt_km,
        is_active=False,  # new agreements are inactive by default
    )
    db.session.add(ag)
    db.session.commit()
    return _redirect_to_tab("#agreement")


# -------------------------
# Agreement — Update
# -------------------------
@admin_bp.route("/agreement/edit/<int:agreement_id>", methods=["POST"])
def edit_agreement(agreement_id: int):
    ag = Agreement.query.get_or_404(agreement_id)

    company_id = request.form.get("company_id", type=int)
    loa_number = (request.form.get("loa_number") or "").strip()
    total_mt_km = request.form.get("total_mt_km", type=float)
    rate_per_mt_km = request.form.get("rate_per_mt_km", type=float)

    # Only assign if present (allows partial edits)
    if company_id:
        # Validate company
        company = Company.query.get(company_id)
        if company:
            ag.company_id = company_id

    if loa_number:
        ag.loa_number = loa_number

    if total_mt_km is not None:
        ag.total_mt_km = total_mt_km

    if rate_per_mt_km is not None:
        ag.rate_per_mt_km = rate_per_mt_km

    db.session.commit()
    return _redirect_to_tab("#agreement")


# -------------------------
# Agreement — Make Active
# (Sets this agreement active and all others inactive for the same company)
# -------------------------
@admin_bp.route("/agreement/set_active/<int:agreement_id>", methods=["POST"])
def set_active_agreement(agreement_id: int):
    ag = Agreement.query.get_or_404(agreement_id)

    # Deactivate all agreements for the same company
    db.session.query(Agreement).filter(
        Agreement.company_id == ag.company_id
    ).update({Agreement.is_active: False})

    # Activate this one
    ag.is_active = True
    db.session.commit()
    return _redirect_to_tab("#agreement")


# -------------------------
# (Optional) Agreements API
# -------------------------
@admin_bp.route("/api/agreements")
def api_agreements():
    items = (
        Agreement.query
        .order_by(Agreement.id.desc())
        .all()
    )
    return {
        "agreements": [
            {
                "id": i.id,
                "company_id": i.company_id,
                "company_name": i.company.name if i.company else None,
                "loa_number": i.loa_number,
                "total_mt_km": i.total_mt_km,
                "rate_per_mt_km": float(i.rate_per_mt_km) if i.rate_per_mt_km is not None else None,
                "is_active": bool(i.is_active),
            }
            for i in items
        ]
    }
