from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import Numeric
from sqlalchemy import Enum as SAEnum  # use SAEnum for all SQLAlchemy enums

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

    type = db.Column(SAEnum('from', 'intermediate', 'to', name='stop_type'), nullable=False)

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

    state = db.Column(  # New field for status tracking
        SAEnum('DRAFT', 'PROPOSAL', 'APPROVED', 'CANCELLED', name='letter_state'),
        nullable=False,
        default='DRAFT'
    )

    booking_serial = db.Column(db.Integer, nullable=False)

    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    lorry_id = db.Column(db.Integer, db.ForeignKey('lorry_details.id'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('route.id'), nullable=False)
    agreement_id = db.Column(db.Integer, db.ForeignKey('agreement.id'))

    loa_number = db.Column(db.String(100))
    placement_date = db.Column(db.Date)
    authority_collection = db.Column(db.String(100))
    far_end_authority = db.Column(db.String(100))

    is_for_home_depot = db.Column(db.Boolean, default=True)
    loading_at_home_depot = db.Column(db.Boolean, default=True)
    far_end_action = db.Column(db.String(20))
    am_amount = db.Column(db.Float)
    load_unload = db.Column(db.Boolean, default=True)

    company = db.relationship('Company')
    lorry = db.relationship('LorryDetails')
    route = db.relationship('Route')
    agreement = db.relationship('Agreement')

    materials = db.relationship('MaterialItem', backref='letter', lazy=True, cascade="all, delete-orphan")
    material_groups = db.relationship('MaterialGroup', backref='letter', lazy=True, cascade="all, delete-orphan")

    __table_args__ = (
        db.UniqueConstraint('agreement_id', 'booking_serial', name='uq_agreement_booking_serial'),
    )

# ----------------------------
# Material Group (for lump-sum lists with a single total)
# ----------------------------
class MaterialGroup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    letter_id = db.Column(db.Integer, db.ForeignKey('letter_record.id'), nullable=False)

    # Optional bundle-level quantity (e.g., "2 lots")
    quantity = db.Column(db.Float)                 # nullable
    unit = db.Column(db.String(20))                # nullable

    # One total amount for the whole list
    total_amount = db.Column(db.Float, nullable=False)

    # Child rows that belong to this lump-sum list
    items = db.relationship('MaterialItem', backref='group', lazy=True, cascade="all, delete-orphan")

# ----------------------------
# Material Item Model
# ----------------------------
class MaterialItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    letter_id = db.Column(db.Integer, db.ForeignKey('letter_record.id'), nullable=False)

    # If this row is part of a lump-sum list, link to the group
    group_id = db.Column(db.Integer, db.ForeignKey('material_group.id'))  # nullable

    sl_no = db.Column(db.Integer)
    description = db.Column(db.String(200), nullable=False)

    # Per-unit fields (used only when pricing_type='UNIT' and group_id IS NULL)
    quantity = db.Column(db.Float)                 # nullable to allow grouped detail rows without qty
    unit = db.Column(db.String(20))                # nullable
    rate = db.Column(db.Float)                     # nullable
    amount = db.Column(db.Float)                   # nullable

    pricing_type = db.Column(
        SAEnum('UNIT', 'GROUPED_DETAIL', name='pricing_type'),
        nullable=False,
        default='UNIT'
    )

    remarks = db.Column(db.String(200))
