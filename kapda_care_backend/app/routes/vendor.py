# ============================================================
# VENDOR ROUTES — Dashboard for Washer and Tailor Managers
# Vendors use these routes to view orders and update statuses
# ============================================================
import json
from flask import Blueprint, request, jsonify
from .. import db
from ..models import User, Order, SubOrder, OrderTimeline
from ..utils import add_timeline_entry, STATUS_MESSAGES
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

vendor_bp = Blueprint('vendor', __name__)

VALID_STATUSES = ['pending', 'assigned', 'picked_up', 'at_partner', 'qc_check', 'out_for_delivery', 'delivered', 'cancelled']


def require_vendor_or_admin(user_id):
    """Helper: Verify if the user has a vendor or admin role"""
    user = User.query.get(user_id)
    if not user or user.role not in ['vendor', 'admin']:
        return None, (jsonify({"msg": "Access denied! Only Vendors or Admins can access this area."}), 403)
    return user, None


# --- ALL ORDERS (Vendor View) ---
# GET /vendor/orders
# Optional query: ?status=pending, ?page=1
@vendor_bp.route('/orders', methods=['GET'])
@jwt_required()
def get_all_orders():
    user_id      = int(get_jwt_identity())
    user, err    = require_vendor_or_admin(user_id)
    if err: return err
    
    status_filter = request.args.get('status')
    page          = int(request.args.get('page', 1))
    per_page      = 20
    
    query = Order.query.order_by(Order.created_at.desc())
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    orders = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        "orders":      [o.to_dict() for o in orders.items],
        "total":       orders.total,
        "page":        page,
        "total_pages": orders.pages
    }), 200


# --- UPDATE ORDER STATUS ---
# PUT /vendor/orders/<id>/status
# Body: { "status": "picked_up", "message": "..." }
@vendor_bp.route('/orders/<int:order_id>/status', methods=['PUT'])
@jwt_required()
def update_order_status(order_id):
    user_id   = int(get_jwt_identity())
    user, err = require_vendor_or_admin(user_id)
    if err: return err
    
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"msg": "Order not found!"}), 404
    
    data       = request.get_json()
    new_status = data.get('status')
    
    if not new_status or new_status not in VALID_STATUSES:
        return jsonify({"msg": f"Invalid status. Valid statuses are: {VALID_STATUSES}"}), 400
    
    old_status   = order.status
    order.status = new_status
    
    # Special timestamps
    if new_status == 'picked_up':
        order.picked_up_at = datetime.utcnow()
    elif new_status == 'delivered':
        order.delivered_at = datetime.utcnow()
    
    # Timeline entry
    message = data.get('message') or STATUS_MESSAGES.get(new_status, f"Status updated to: {new_status}")
    add_timeline_entry(order_id, new_status, message, user_id)
    
    db.session.commit()
    
    return jsonify({
        "msg": f"Order status successfully updated from '{old_status}' to '{new_status}'!",
        "order_id": order_id
    }), 200


# --- ASSIGN SUB-ORDER TO PARTNER ---
# PUT /vendor/suborders/<id>/assign
# Body: { "partner_id": 3 }
@vendor_bp.route('/suborders/<int:sub_id>/assign', methods=['PUT'])
@jwt_required()
def assign_sub_order(sub_id):
    user_id   = int(get_jwt_identity())
    user, err = require_vendor_or_admin(user_id)
    if err: return err
    
    sub_order  = SubOrder.query.get(sub_id)
    data       = request.get_json()
    partner_id = data.get('partner_id')
    
    if not sub_order:
        return jsonify({"msg": "Sub-order not found!"}), 404
    
    sub_order.partner_id = partner_id
    sub_order.status     = 'assigned'
    
    db.session.commit()
    
    return jsonify({
        "msg": f"Sub-order #{sub_id} successfully assigned to partner #{partner_id}!",
        "sub_order": sub_order.to_dict()
    }), 200


# --- DASHBOARD STATS ---
# GET /vendor/dashboard
@vendor_bp.route('/dashboard', methods=['GET'])
@jwt_required()
def dashboard():
    user_id   = int(get_jwt_identity())
    user, err = require_vendor_or_admin(user_id)
    if err: return err
    
    total_orders     = Order.query.count()
    pending_orders   = Order.query.filter_by(status='pending').count()
    delivered_orders = Order.query.filter_by(status='delivered').count()
    today_orders     = Order.query.filter(
        Order.created_at >= datetime.utcnow().replace(hour=0, minute=0, second=0)
    ).count()
    
    # Total revenue
    all_delivered = Order.query.filter_by(status='delivered').all()
    total_revenue = sum(o.final_price for o in all_delivered)
    
    return jsonify({
        "total_orders":     total_orders,
        "pending_orders":   pending_orders,
        "delivered_orders": delivered_orders,
        "today_orders":     today_orders,
        "total_revenue":    round(total_revenue, 2)
    }), 200