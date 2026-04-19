from . import db
from datetime import datetime

# ============================================================
# USER TABLE
# This stores data for all roles: customers, vendors, and admins
# ============================================================
class User(db.Model):
    __tablename__ = 'user'
    
    id           = db.Column(db.Integer, primary_key=True)
    username     = db.Column(db.String(50), unique=True, nullable=False)
    email        = db.Column(db.String(120), unique=True, nullable=False)
    password     = db.Column(db.String(200), nullable=False)
    phone        = db.Column(db.String(15), nullable=True)
    address      = db.Column(db.Text, nullable=True)
    role         = db.Column(db.String(20), default='customer')
    is_active    = db.Column(db.Boolean, default=True)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    orders       = db.relationship('Order', foreign_keys='Order.customer_id', backref='customer', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'address': self.address,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }


class Partner(db.Model):
    __tablename__ = 'partner'
    
    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    business_name  = db.Column(db.String(100), nullable=False)
    service_type   = db.Column(db.String(20), nullable=False)
    area           = db.Column(db.String(100), nullable=True)
    is_available   = db.Column(db.Boolean, default=True)
    rating         = db.Column(db.Float, default=5.0)
    total_orders   = db.Column(db.Integer, default=0)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    user           = db.relationship('User', backref='partner_profile')
    
    def to_dict(self):
        return {
            'id': self.id,
            'business_name': self.business_name,
            'service_type': self.service_type,
            'area': self.area,
            'is_available': self.is_available,
            'rating': self.rating,
            'total_orders': self.total_orders
        }


class Order(db.Model):
    __tablename__ = 'order'
    
    id              = db.Column(db.Integer, primary_key=True)
    customer_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status          = db.Column(db.String(30), default='pending')
    total_price     = db.Column(db.Float, nullable=False)
    discount        = db.Column(db.Float, default=0.0)
    final_price     = db.Column(db.Float, nullable=False)
    pickup_address  = db.Column(db.Text, nullable=True)
    items           = db.Column(db.Text, nullable=False)
    is_express      = db.Column(db.Boolean, default=False)
    special_notes   = db.Column(db.Text, nullable=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    picked_up_at    = db.Column(db.DateTime, nullable=True)
    delivered_at    = db.Column(db.DateTime, nullable=True)
    sub_orders      = db.relationship('SubOrder', backref='parent_order', lazy=True)
    timeline        = db.relationship('OrderTimeline', backref='order', lazy=True)
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'customer_id': self.customer_id,
            'status': self.status,
            'total_price': self.total_price,
            'discount': self.discount,
            'final_price': self.final_price,
            'pickup_address': self.pickup_address,
            'items': json.loads(self.items),
            'is_express': self.is_express,
            'special_notes': self.special_notes,
            'created_at': self.created_at.isoformat()
        }


class SubOrder(db.Model):
    __tablename__ = 'sub_order'
    
    id              = db.Column(db.Integer, primary_key=True)
    parent_order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    partner_id      = db.Column(db.Integer, db.ForeignKey('partner.id'), nullable=True)
    service_type    = db.Column(db.String(20), nullable=False)
    status          = db.Column(db.String(30), default='pending')
    items           = db.Column(db.Text, nullable=False)
    sub_total       = db.Column(db.Float, default=0.0)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    partner         = db.relationship('Partner', backref='assigned_sub_orders')
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'parent_order_id': self.parent_order_id,
            'partner_id': self.partner_id,
            'service_type': self.service_type,
            'status': self.status,
            'items': json.loads(self.items),
            'sub_total': self.sub_total
        }


class OrderTimeline(db.Model):
    __tablename__ = 'order_timeline'
    
    id          = db.Column(db.Integer, primary_key=True)
    order_id    = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    status      = db.Column(db.String(30), nullable=False)
    message     = db.Column(db.String(200), nullable=True)
    updated_by  = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    timestamp   = db.Column(db.DateTime, default=datetime.utcnow)


class Review(db.Model):
    __tablename__ = 'review'
    
    id          = db.Column(db.Integer, primary_key=True)
    order_id    = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    partner_id  = db.Column(db.Integer, db.ForeignKey('partner.id'), nullable=False)
    rating      = db.Column(db.Integer, nullable=False)
    comment     = db.Column(db.Text, nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)