from flask import Blueprint, render_template, request, redirect, url_for
from transport.models import db, Company, Agreement, LorryDetails, Route, RouteStop, LetterRecord

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
def view_dashboard():
    companies = Company.query.all()
    agreements = Agreement.query.all()
    lorries = LorryDetails.query.all()
    routes = Route.query.all()
    for route in routes:
        route.stops = RouteStop.query.filter_by(route_id=route.id).order_by(RouteStop.sequence_no).all()
    return render_template('dashboard.html', companies=companies, agreements=agreements, lorries=lorries, routes=routes)

@admin_bp.route('/company/add', methods=['POST'])
def add_company():
    name = request.form['name']
    address = request.form['address']
    phone = request.form.get('phone') or ''
    email = request.form.get('email') or ''

    company = Company(name=name, address=address, phone=phone, email=email)
    db.session.add(company)
    db.session.commit()
    return redirect(url_for('admin.view_dashboard'))

@admin_bp.route('/company/edit/<int:company_id>', methods=['GET', 'POST'])
def edit_company(company_id):
    company = Company.query.get_or_404(company_id)

    if request.method == 'POST':
        company.name = request.form['name']
        company.address = request.form['address']
        company.phone = request.form.get('phone') or ''
        company.email = request.form.get('email') or ''
        db.session.commit()
        return redirect(url_for('admin.view_dashboard'))

    return render_template('edit_company.html', company=company)

@admin_bp.route('/agreement/add', methods=['POST'])
def add_agreement():
    company_id = request.form['company_id']
    loa_number = request.form['loa_number']
    rate = request.form['rate_per_mt_km']
    mtkm = request.form['total_mt_km']
    agreement = Agreement(
        company_id=company_id,
        loa_number=loa_number,
        rate_per_mt_km=rate,
        total_mt_km=mtkm
    )
    db.session.add(agreement)
    db.session.commit()
    return redirect(url_for('admin.view_dashboard'))


@admin_bp.route('/agreement/set_active/<int:agreement_id>')
def set_active_agreement(agreement_id):
    # First deactivate all
    Agreement.query.update({Agreement.is_active: False})
    
    # Then activate the selected agreement
    agreement = Agreement.query.get_or_404(agreement_id)
    agreement.is_active = True

    db.session.commit()
    return redirect(url_for('admin.view_dashboard'))

@admin_bp.route('/lorry/add', methods=['POST'])
def add_lorry():
    capacity = request.form['capacity']
    carrier_size = request.form['carrier_size']
    remarks = request.form.get('remarks', '')
    number_of_wheels = request.form.get('number_of_wheels', type=int)
    lorry = LorryDetails(
        capacity=capacity,
        carrier_size=carrier_size,
        remarks=remarks,
        number_of_wheels=number_of_wheels
    )
    db.session.add(lorry)
    db.session.commit()
    return redirect(url_for('admin.view_dashboard'))

@admin_bp.route('/lorry/edit/<int:id>', methods=['POST'])
def edit_lorry(id):
    lorry = LorryDetails.query.get_or_404(id)

    lorry.capacity = request.form['capacity']
    lorry.carrier_size = request.form['carrier_size']
    lorry.remarks = request.form.get('remarks', '')
    lorry.number_of_wheels = request.form.get('number_of_wheels', type=int)

    db.session.commit()
    return redirect(url_for('admin.view_dashboard'))

@admin_bp.route('/route/add', methods=['POST'])
def add_route():
    name = request.form['name']
    waypoints_raw = request.form['waypoints']
    waypoints = [w.strip() for w in waypoints_raw.split(',') if w.strip()]

    route = Route(name=name)
    db.session.add(route)
    db.session.flush()  # Get the ID before commit

    for index, wp in enumerate(waypoints):
        stop = RouteStop(route_id=route.id, sequence_no=index + 1, location=wp)
        db.session.add(stop)

    db.session.commit()
    return redirect(url_for('admin.view_dashboard'))

@admin_bp.route('/letter/add', methods=['POST'])
def add_letter():
    lorry_id = request.form['lorry_id']
    route_id = request.form['route_id']
    booking_unit = request.form['booking_unit']
    is_home_depot = bool(int(request.form['is_home_depot']))
    load_at_home = bool(int(request.form['load_at_home']))
    far_end_action = request.form['far_end_action']
    remarks = request.form['remarks']

    active_agreement = Agreement.query.filter_by(active=True).first()
    if not active_agreement:
        return "No active agreement", 400

    last_letter = LetterRecord.query.filter_by(agreement_id=active_agreement.id).order_by(LetterRecord.id.desc()).first()
    next_letter_id = 1 if not last_letter else last_letter.letter_id_within_agreement + 1

    letter = LetterRecord(
        lorry_id=lorry_id,
        route_id=route_id,
        agreement_id=active_agreement.id,
        letter_id_within_agreement=next_letter_id,
        booking_unit=booking_unit,
        is_home_depot=is_home_depot,
        load_at_home=load_at_home,
        far_end_action=far_end_action,
        remarks=remarks
    )
    db.session.add(letter)
    db.session.commit()
    return redirect(url_for('admin.view_dashboard'))
