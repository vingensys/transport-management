from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort
from sqlalchemy import func
from datetime import datetime
from transport.models import (
    db, Company, Agreement, LorryDetails, Route, RouteStop,
    LocationAuthority, LetterRecord, MaterialGroup, MaterialItem
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ----------------------------
# Helpers
# ----------------------------
def redirect_to_tab(tab_hash: str):
    return redirect(url_for('admin.view_dashboard') + tab_hash)

def get_active_agreement():
    return Agreement.query.filter_by(is_active=True).first()

def next_booking_serial(agreement_id: int) -> int:
    max_serial = db.session.query(func.max(LetterRecord.booking_serial))\
        .filter(LetterRecord.agreement_id == agreement_id)\
        .scalar()
    return (max_serial or 0) + 1

def make_letter_number(agreement: Agreement, serial: int) -> str:
    base = agreement.loa_number or f"AG{agreement.id}"
    return f"{base}-{serial:04d}"


# ----------------------------
# Dashboard (HTML)
# ----------------------------
@admin_bp.route('/')
def view_dashboard():
    companies = Company.query.order_by(Company.id.desc()).all()
    agreements = Agreement.query.order_by(Agreement.id.desc()).all()
    lorries = LorryDetails.query.order_by(LorryDetails.id.desc()).all()
    authorities = LocationAuthority.query.order_by(LocationAuthority.id.desc()).all()

     # NEW: build a plain dict list for JS (JSON-serializable)
    authorities_js = [
        {
            "id": a.id,
            "authority": a.authority,
            "location": a.location,
            "address": a.address,
        }
        for a in authorities
    ]

    routes = Route.query.order_by(Route.id.desc()).all()
    for r in routes:
        r.stops = RouteStop.query.filter_by(route_id=r.id).order_by(RouteStop.order.asc()).all()

    return render_template(
        'dashboard.html',
        companies=companies,
        agreements=agreements,
        lorries=lorries,
        routes=routes,
        authorities=authorities,       # keep for Jinja loops in <select>
        authorities_js=authorities_js  # use this for JS tojson
    )


# ----------------------------
# Companies (Add/Edit/Delete)
# ----------------------------
@admin_bp.route('/company/add', methods=['POST'])
def add_company():
    name = request.form['name'].strip()
    address = request.form['address'].strip()
    phone = request.form.get('phone', '').strip()
    email = request.form.get('email', '').strip()
    db.session.add(Company(name=name, address=address, phone=phone, email=email))
    db.session.commit()
    return redirect_to_tab('#company')

@admin_bp.route('/company/edit/<int:company_id>', methods=['POST'])
def edit_company(company_id):
    c = Company.query.get_or_404(company_id)
    c.name = request.form['name'].strip()
    c.address = request.form['address'].strip()
    c.phone = request.form.get('phone', '').strip()
    c.email = request.form.get('email', '').strip()
    db.session.commit()
    return redirect_to_tab('#company')

@admin_bp.route('/company/delete/<int:company_id>', methods=['POST'])
def delete_company(company_id):
    c = Company.query.get_or_404(company_id)
    has_agreements = Agreement.query.filter_by(company_id=c.id).first()
    has_letters = LetterRecord.query.filter_by(company_id=c.id).first()
    if has_agreements or has_letters:
        return jsonify({
            "ok": False,
            "error": "Cannot delete company with dependent Agreements or Letters."
        }), 409
    db.session.delete(c)
    db.session.commit()
    return redirect_to_tab('#company')


# ----------------------------
# Agreements (Add/Edit/Activate + API)
# ----------------------------
@admin_bp.route('/agreement/add', methods=['POST'])
def add_agreement():
    ag = Agreement(
        company_id=int(request.form['company_id']),
        loa_number=request.form['loa_number'].strip(),
        total_mt_km=float(request.form['total_mt_km']),
        rate_per_mt_km=float(request.form['rate_per_mt_km']),
    )
    db.session.add(ag)
    db.session.commit()
    return redirect_to_tab('#agreement')

@admin_bp.route('/agreement/edit/<int:agreement_id>', methods=['POST'])
def edit_agreement(agreement_id):
    ag = Agreement.query.get_or_404(agreement_id)
    company_id = request.form.get('company_id', type=int)
    if company_id:
        ag.company_id = company_id
    loa = request.form.get('loa_number')
    if loa is not None:
        ag.loa_number = loa.strip()
    tkm = request.form.get('total_mt_km')
    if tkm not in (None, ''):
        ag.total_mt_km = float(tkm)
    rpmk = request.form.get('rate_per_mt_km')
    if rpmk not in (None, ''):
        ag.rate_per_mt_km = float(rpmk)
    db.session.commit()
    return redirect_to_tab('#agreement')

@admin_bp.route('/agreement/set_active/<int:agreement_id>', methods=['POST'])
def set_active_agreement(agreement_id):
    Agreement.query.update({Agreement.is_active: False})
    ag = Agreement.query.get_or_404(agreement_id)
    ag.is_active = True
    db.session.commit()
    return redirect_to_tab('#agreement')

@admin_bp.route('/api/agreements', methods=['GET'])
def api_agreements():
    data = [
        dict(
            id=x.id, loa_number=x.loa_number, total_mt_km=x.total_mt_km,
            rate_per_mt_km=str(x.rate_per_mt_km), is_active=x.is_active,
            company_id=x.company_id, company_name=x.company.name if x.company else None
        )
        for x in Agreement.query.order_by(Agreement.id.desc()).all()
    ]
    return jsonify(data)


# ----------------------------
# Lorries (Add/Edit + API)
# ----------------------------
@admin_bp.route('/lorry/add', methods=['POST'])
def add_lorry():
    l = LorryDetails(
        capacity=request.form['capacity'].strip(),
        carrier_size=request.form['carrier_size'].strip(),
        number_of_wheels=request.form.get('number_of_wheels', type=int),
        remarks=request.form.get('remarks', '').strip()
    )
    db.session.add(l)
    db.session.commit()
    return redirect_to_tab('#lorry')

@admin_bp.route('/lorry/edit/<int:lorry_id>', methods=['POST'])
def edit_lorry(lorry_id):
    l = LorryDetails.query.get_or_404(lorry_id)
    l.capacity = request.form['capacity'].strip()
    l.carrier_size = request.form['carrier_size'].strip()
    l.number_of_wheels = request.form.get('number_of_wheels', type=int)
    l.remarks = request.form.get('remarks', '').strip()
    db.session.commit()
    return redirect_to_tab('#lorry')

@admin_bp.route('/api/lorries', methods=['GET'])
def api_lorries():
    data = [
        dict(
            id=x.id, capacity=x.capacity, carrier_size=x.carrier_size,
            number_of_wheels=x.number_of_wheels, remarks=x.remarks
        )
        for x in LorryDetails.query.order_by(LorryDetails.id.desc()).all()
    ]
    return jsonify(data)


# ----------------------------
# Location Authorities (Add/Edit + API)
# ----------------------------
@admin_bp.route('/authority/add', methods=['POST'])
def add_authority():
    a = LocationAuthority(
        location=request.form['location'].strip(),
        authority=request.form['authority'].strip(),
        address=(request.form.get('address') or '').strip() or None
    )
    db.session.add(a)
    db.session.commit()
    # if it's from modal or tab, return back to authority tab
    if request.headers.get('Accept', '').startswith('text/html'):
        return redirect_to_tab('#authority')
    return jsonify({"ok": True, "id": a.id})

@admin_bp.route('/authority/edit/<int:authority_id>', methods=['POST'])
def edit_authority(authority_id):
    a = LocationAuthority.query.get_or_404(authority_id)
    loc = request.form.get('location')
    if loc is not None:
        a.location = loc.strip()
    auth = request.form.get('authority')
    if auth is not None:
        a.authority = auth.strip()
    addr = request.form.get('address')
    if addr is not None:
        a.address = addr.strip() or None
    db.session.commit()
    return redirect_to_tab('#authority')

@admin_bp.route('/api/authorities', methods=['GET'])
def api_authorities():
    data = [
        dict(id=x.id, location=x.location, authority=x.authority, address=x.address)
        for x in LocationAuthority.query.order_by(LocationAuthority.id.desc()).all()
    ]
    return jsonify(data)


# ----------------------------
# Routes & Stops (Add/Edit + API)
# ----------------------------
@admin_bp.route('/route/add', methods=['POST'])
def add_route():
    """
    Accepts:
      - name (required)
      - total_km (optional)
    Stops are added via /route/<id>/stop/add after creation (from the UI script).
    """
    name = request.form['name'].strip()
    total_km = request.form.get('total_km', type=int)
    r = Route(name=name, total_km=total_km)
    db.session.add(r)
    db.session.commit()
    return redirect_to_tab('#route')

@admin_bp.route('/route/edit/<int:route_id>', methods=['POST'])
def edit_route(route_id):
    r = Route.query.get_or_404(route_id)
    name = request.form.get('name')
    if name is not None:
        r.name = name.strip()
    tk = request.form.get('total_km')
    if tk not in (None, ''):
        r.total_km = int(tk)
    db.session.commit()
    return redirect_to_tab('#route')

@admin_bp.route('/route/<int:route_id>/stop/add', methods=['POST'])
def add_route_stop(route_id):
    Route.query.get_or_404(route_id)  # ensure exists
    s = RouteStop(
        route_id=route_id,
        location=request.form['location'].strip(),
        type=request.form['type'],  # 'from' | 'intermediate' | 'to'
        order=request.form.get('order', type=int) or 1,
        authority_id=request.form.get('authority_id', type=int)
    )
    db.session.add(s)
    db.session.commit()
    return jsonify({"ok": True, "route_id": route_id, "stop_id": s.id})

@admin_bp.route('/route/stop/edit/<int:stop_id>', methods=['POST'])
def edit_route_stop(stop_id):
    s = RouteStop.query.get_or_404(stop_id)
    loc = request.form.get('location')
    if loc is not None:
        s.location = loc.strip()
    stype = request.form.get('type')  # 'from'|'intermediate'|'to'
    if stype in ('from', 'intermediate', 'to'):
        s.type = stype
    order_val = request.form.get('order', type=int)
    if order_val is not None:
        s.order = order_val
    auth_id = request.form.get('authority_id', type=int)
    if auth_id is not None:
        s.authority_id = auth_id
    db.session.commit()
    return redirect_to_tab('#route')

@admin_bp.route('/api/routes', methods=['GET'])
def api_routes():
    routes = Route.query.order_by(Route.id.desc()).all()
    data = []
    for r in routes:
        stops = RouteStop.query.filter_by(route_id=r.id).order_by(RouteStop.order.asc()).all()
        data.append(dict(
            id=r.id, name=r.name, total_km=r.total_km,
            stops=[dict(id=s.id, location=s.location, type=s.type, order=s.order, authority_id=s.authority_id) for s in stops]
        ))
    return jsonify(data)


# ----------------------------
# Letters (Add + API)
# ----------------------------
@admin_bp.route('/letter/add', methods=['POST'])
def add_letter():
    active_ag = get_active_agreement()
    if not active_ag:
        abort(400, description="No active agreement. Set one active first.")

    serial = next_booking_serial(active_ag.id)
    letter_no = make_letter_number(active_ag, serial)

    letter = LetterRecord(
        letter_number=letter_no,
        booking_serial=serial,
        company_id=active_ag.company_id,
        lorry_id=request.form.get('lorry_id', type=int),
        route_id=request.form.get('route_id', type=int),
        agreement_id=active_ag.id,
        is_for_home_depot=bool(int(request.form.get('is_home_depot', 1))),
        loading_at_home_depot=bool(int(request.form.get('load_at_home', 1))),
        far_end_action=(request.form.get('far_end_action') or '').strip(),
    )
    db.session.add(letter)
    db.session.commit()
    return redirect_to_tab('#letter')

@admin_bp.route('/letter/edit/<int:letter_id>', methods=['POST'])
def edit_letter(letter_id):
    x = LetterRecord.query.get_or_404(letter_id)
    state = request.form.get('state')
    if state in ('DRAFT', 'PROPOSAL', 'APPROVED', 'CANCELLED'):
        x.state = state
    lorry_id = request.form.get('lorry_id', type=int)
    route_id = request.form.get('route_id', type=int)
    if lorry_id is not None:
        x.lorry_id = lorry_id
    if route_id is not None:
        x.route_id = route_id
    loa_number = request.form.get('loa_number')
    if loa_number is not None:
        x.loa_number = loa_number.strip()
    placement_date = request.form.get('placement_date')
    if placement_date:
        try:
            x.placement_date = datetime.fromisoformat(placement_date).date()
        except Exception:
            pass
    authority_collection = request.form.get('authority_collection')
    if authority_collection is not None:
        x.authority_collection = authority_collection.strip()
    far_end_authority = request.form.get('far_end_authority')
    if far_end_authority is not None:
        x.far_end_authority = far_end_authority.strip()
    is_for_home_depot = request.form.get('is_for_home_depot')
    if is_for_home_depot is not None:
        x.is_for_home_depot = bool(int(is_for_home_depot))
    loading_at_home_depot = request.form.get('loading_at_home_depot')
    if loading_at_home_depot is not None:
        x.loading_at_home_depot = bool(int(loading_at_home_depot))
    far_end_action = request.form.get('far_end_action')
    if far_end_action is not None:
        x.far_end_action = far_end_action.strip()
    db.session.commit()
    return redirect_to_tab('#letter')

@admin_bp.route('/api/letters', methods=['GET'])
def api_letters():
    letters = LetterRecord.query.order_by(LetterRecord.id.desc()).all()
    return jsonify([
        dict(
            id=x.id, letter_number=x.letter_number, date=str(x.date),
            state=x.state, booking_serial=x.booking_serial,
            agreement_id=x.agreement_id, lorry_id=x.lorry_id, route_id=x.route_id
        ) for x in letters
    ])


# ----------------------------
# Materials: Groups & Items (JSON endpoints)
# ----------------------------
@admin_bp.route('/material-group/add', methods=['POST'])
def add_material_group():
    letter_id = request.form.get('letter_id', type=int)
    total_amount = request.form.get('total_amount', type=float)
    if not letter_id or total_amount is None:
        abort(400, description="letter_id and total_amount are required")
    g = MaterialGroup(
        letter_id=letter_id,
        total_amount=total_amount,
        quantity=request.form.get('quantity', type=float),
        unit=request.form.get('unit', type=str)
    )
    db.session.add(g)
    db.session.commit()
    return jsonify({"ok": True, "group_id": g.id})

@admin_bp.route('/material-group/edit/<int:group_id>', methods=['POST'])
def edit_material_group(group_id):
    g = MaterialGroup.query.get_or_404(group_id)
    ta = request.form.get('total_amount', type=float)
    if ta is not None:
        g.total_amount = ta
    q = request.form.get('quantity', type=float)
    if q is not None:
        g.quantity = q
    u = request.form.get('unit')
    if u is not None:
        g.unit = (u or '').strip() or None
    db.session.commit()
    return jsonify({"ok": True})

@admin_bp.route('/material-item/add', methods=['POST'])
def add_material_item():
    letter_id = request.form.get('letter_id', type=int)
    if not letter_id:
        abort(400, description="letter_id is required")

    group_id = request.form.get('group_id', type=int)
    sl_no = request.form.get('sl_no', type=int)
    description = (request.form.get('description') or '').strip()
    if not description:
        abort(400, description="description is required")

    if group_id:
        item = MaterialItem(
            letter_id=letter_id, group_id=group_id, sl_no=sl_no,
            description=description, pricing_type='GROUPED_DETAIL',
            quantity=request.form.get('quantity', type=float),
            unit=request.form.get('unit')
        )
    else:
        qty = request.form.get('quantity', type=float)
        rate = request.form.get('rate', type=float)
        amount = request.form.get('amount', type=float)
        if amount is None and (qty is not None and rate is not None):
            amount = qty * rate
        item = MaterialItem(
            letter_id=letter_id, group_id=None, sl_no=sl_no,
            description=description, pricing_type='UNIT',
            quantity=qty, unit=request.form.get('unit'),
            rate=rate, amount=amount
        )
    db.session.add(item)
    db.session.commit()
    return jsonify({"ok": True, "item_id": item.id})

@admin_bp.route('/material-item/edit/<int:item_id>', methods=['POST'])
def edit_material_item(item_id):
    i = MaterialItem.query.get_or_404(item_id)
    desc = request.form.get('description')
    if desc is not None:
        i.description = desc.strip()
    ptype = request.form.get('pricing_type')
    if ptype in ('UNIT', 'GROUPED_DETAIL'):
        i.pricing_type = ptype
        if ptype == 'GROUPED_DETAIL':
            i.rate = None
            i.amount = None
    gid = request.form.get('group_id', type=int)
    if gid is not None:
        i.group_id = gid
    q = request.form.get('quantity', type=float)
    if q is not None:
        i.quantity = q
    u = request.form.get('unit')
    if u is not None:
        i.unit = (u or '').strip() or None
    if i.pricing_type == 'UNIT' and i.group_id is None:
        r = request.form.get('rate', type=float)
        a = request.form.get('amount', type=float)
        if r is not None:
            i.rate = r
        if a is not None:
            i.amount = a
        elif (i.quantity is not None and i.rate is not None):
            i.amount = i.quantity * i.rate
    db.session.commit()
    return jsonify({"ok": True})

@admin_bp.route('/api/letter/<int:letter_id>/materials', methods=['GET'])
def api_letter_materials(letter_id):
    letter = LetterRecord.query.get_or_404(letter_id)
    groups = MaterialGroup.query.filter_by(letter_id=letter.id).all()
    items = MaterialItem.query.filter_by(letter_id=letter.id).all()
    return jsonify({
        "letter_id": letter.id,
        "groups": [
            dict(id=g.id, total_amount=g.total_amount, quantity=g.quantity, unit=g.unit)
            for g in groups
        ],
        "items": [
            dict(
                id=i.id, group_id=i.group_id, sl_no=i.sl_no, description=i.description,
                pricing_type=i.pricing_type, quantity=i.quantity, unit=i.unit,
                rate=i.rate, amount=i.amount
            ) for i in items
        ]
    })
