from flask import request, redirect, url_for, abort
from sqlalchemy import func

from transport.models import db, Company, Agreement, LetterRecord

# Import the shared admin blueprint created in admin/__init__.py
from . import admin_bp


def _redirect_to_tab(tab_hash: str):
    """Convenience redirect back to a specific dashboard tab, e.g. '#company'."""
    return redirect(url_for("admin.view_dashboard") + tab_hash)


# -------------------------
# Company — Create
# -------------------------
@admin_bp.route("/company/add", methods=["POST"])
def add_company():
    name = (request.form.get("name") or "").strip()
    address = (request.form.get("address") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    email = (request.form.get("email") or "").strip()

    if not name or not address:
        # minimal guard; UI already requires these
        return _redirect_to_tab("#company")

    c = Company(name=name, address=address, phone=phone, email=email)
    db.session.add(c)
    db.session.commit()
    return _redirect_to_tab("#company")


# -------------------------
# Company — Update
# -------------------------
@admin_bp.route("/company/edit/<int:company_id>", methods=["POST"])
def edit_company(company_id: int):
    c = Company.query.get_or_404(company_id)

    name = (request.form.get("name") or "").strip()
    address = (request.form.get("address") or "").strip()
    phone = (request.form.get("phone") or "").strip()
    email = (request.form.get("email") or "").strip()

    if name:
        c.name = name
    if address:
        c.address = address
    c.phone = phone
    c.email = email

    db.session.commit()
    return _redirect_to_tab("#company")


# -------------------------
# Company — Delete
# (Restricted: only allowed if no dependent agreements or letters)
# -------------------------
@admin_bp.route("/company/delete/<int:company_id>", methods=["POST"])
def delete_company(company_id: int):
    c = Company.query.get_or_404(company_id)

    # Block delete when there are dependent objects
    has_agreements = (
        db.session.query(func.count(Agreement.id))
        .filter(Agreement.company_id == company_id)
        .scalar()
        or 0
    )
    has_letters = (
        db.session.query(func.count(LetterRecord.id))
        .filter(LetterRecord.company_id == company_id)
        .scalar()
        or 0
    )

    if has_agreements or has_letters:
        # Simply bounce back to the tab; UI could show a toast later if needed.
        return _redirect_to_tab("#company")

    db.session.delete(c)
    db.session.commit()
    return _redirect_to_tab("#company")


# -------------------------
# (Optional) Companies API
# -------------------------
@admin_bp.route("/api/companies")
def api_companies():
    items = Company.query.order_by(Company.id.desc()).all()
    return {
        "companies": [
            {
                "id": i.id,
                "name": i.name,
                "address": i.address,
                "phone": i.phone,
                "email": i.email,
            }
            for i in items
        ]
    }
