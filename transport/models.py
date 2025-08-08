from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Numeric, Enum

db = SQLAlchemy()

# ----------------------------
# Company Model
# ----------------------------
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(100))

# ----------------------------
# Agreement Model
# ----------------------------
class Agreement(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # Unique agreement identifier
    loa_number = db.Column(db.String(100), nullable=False)
    total_mt_km = db.Column(db.Float, nullable=False)
    rate_per_mt_km = db.Column(Numeric(10, 6), nullable=False)  # up to 9999.999999
    is_active = db.Column(db.Boolean, default=False)

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    company = db.relationship('Company')

# ----------------------------
# Lorry Details
# ----------------------------
class LorryDetails(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    capacity = db.Column(db.String(50), nullable=False)
    carrier_size = db.Column(db.String(50), nullable=False)
    remarks = db.Column(db.String(200))
    number_of_wheels = db.Column(db.Integer)  # renamed from no_of_wheels

# ----------------------------
# Location Authority
# ----------------------------
class LocationAuthority(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=False)
    authority = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), nullable=True)  # new field

# ----------------------------
# Route Model
# ----------------------------
class Route(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))  # Optional display label
    total_km = db.Column(db.Integer)

    stops = db.relationship('RouteStop', backref='route', lazy=True, cascade="all, delete-orphan")

# ----------------------------
# RouteStop Model
# ----------------------------
class RouteStop(db.Model):
    __tablename__ = 'route_stop'

    id = db.Column(db.Integer, primary_key=True)
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=False)
    location = db.Column(db.String(100), nullable=False)

    type = db.Column(Enum('from', 'intermediate', 'to', name='stop_type'), nullable=False)

    order = db.Column(db.Integer)  # display/order within the route
    authority_id = db.Column(db.Integer, db.ForeignKey('location_authority.id'))

    authority = db.relationship('LocationAuthority')

# ----------------------------
# Letter Record Model
# ----------------------------
class LetterRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    letter_number = db.Column(db.String(100), unique=True, nullable=False)
    date = db.Column(db.Date, default=datetime.utcnow)

    # Serial number per agreement (this replaces the need for "letter_id_within_agreement")
    booking_serial = db.Column(db.Integer, nullable=False)

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    lorry_id = db.Column(db.Integer, db.ForeignKey('lorry_details.id'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=False)
    agreement_id = db.Column(db.Integer, db.ForeignKey('agreement.id'))

    loa_number = db.Column(db.String(100))
    placement_date = db.Column(db.Date)
    authority_collection = db.Column(db.String(100))
    far_end_authority = db.Column(db.String(100))

    # Booking context
    is_for_home_depot = db.Column(db.Boolean, default=True)
    loading_at_home_depot = db.Column(db.Boolean, default=True)
    far_end_action = db.Column(db.String(20))  # 'load' or 'unload'

    # Advance Memo info
    am_amount = db.Column(db.Float)

    load_unload = db.Column(db.Boolean, default=True)

    company = db.relationship('Company')
    lorry = db.relationship('LorryDetails')
    route = db.relationship('Route')
    agreement = db.relationship('Agreement')
    materials = db.relationship('MaterialItem', backref='letter', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint('agreement_id', 'booking_serial', name='uq_agreement_booking_serial'),
    )

# ----------------------------
# Material Item Model
# ----------------------------
class MaterialItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    letter_id = db.Column(db.Integer, db.ForeignKey('letter_record.id'), nullable=False)
    description = db.Column(db.String(200))
    quantity = db.Column(db.Integer)
    value = db.Column(db.Float)
    amount = db.Column(db.Float)  # This can be auto-calculated later
