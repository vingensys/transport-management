from __future__ import annotations

from datetime import datetime
from typing import Optional

from flask import redirect, url_for
from sqlalchemy import func

from transport.models import db, Agreement, LetterRecord


# -------------------------------------------------------------------
# Simple redirect helper to land back on a specific dashboard tab
# -------------------------------------------------------------------
def redirect_to_tab(tab_hash: str):
    """
    Redirect back to the admin dashboard on a given tab (e.g., '#letter').
    """
    return redirect(url_for("admin.view_dashboard") + tab_hash)


# -------------------------------------------------------------------
# Active Agreement
# -------------------------------------------------------------------
def get_active_agreement() -> Optional[Agreement]:
    """
    Return the single active agreement, if any.
    """
    return Agreement.query.filter_by(is_active=True).first()


# -------------------------------------------------------------------
# Booking serial & letter number
# -------------------------------------------------------------------
def next_booking_serial(agreement_id: int) -> int:
    """
    Compute the next booking serial for a given agreement.
    """
    current_max = (
        db.session.query(func.max(LetterRecord.booking_serial))
        .filter(LetterRecord.agreement_id == agreement_id)
        .scalar()
    )
    return (current_max or 0) + 1


def make_letter_number(agreement: Agreement, serial: int) -> str:
    """
    Build a human-friendly letter/booking number.
    Falls back to 'AG<id>' if LOA number is empty.
    Example: 'LOA-1234-0007'
    """
    prefix = (agreement.loa_number or f"AG{agreement.id}").strip()
    return f"{prefix}-{serial:04d}"


# -------------------------------------------------------------------
# Dates
# -------------------------------------------------------------------
def parse_placement_date(s: Optional[str]):
    """
    Parse a yyyy-mm-dd string to a date object; returns None if invalid/empty.
    """
    if not s:
        return None
    try:
        # Accept both 'YYYY-MM-DD' and full ISO 'YYYY-MM-DDTHH:MM' (we keep date part)
        return datetime.fromisoformat(s).date()
    except Exception:
        try:
            return datetime.strptime(s, "%Y-%m-%d").date()
        except Exception:
            return None
