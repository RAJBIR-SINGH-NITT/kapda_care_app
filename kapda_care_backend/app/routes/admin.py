# ============================================================
# ADMIN ROUTES — Full Control Panel
# Only accessible by users with the 'admin' role
# ============================================================
from flask import Blueprint, request, jsonify
from .. import db
from ..models import User, Order, Partner, Review
from flask_jwt_extended import jwt_required, get_jwt_identity

admin_bp = Blueprint('admin', __name__)


def require_admin(user_id):
    """Helper function to check if the user is an admin."""
    user = User.query.get(user_id)
    if not user or user.role != 'admin':
        return None, (jsonify({"msg": "Access Denied: Admin privileges required!"}), 403)
    return user, None


# --- ALL USERS ---
# GET /admin/users
@admin_bp.route('/users', methods=['GET'])
@jwt_required()
def all_users():
    user_id = int(get_jwt_identity())
    _, err  = require_admin(user_id)
    if err: return err
    
    users = User.query.order_by(User.created_at.desc()).all()
    return jsonify([u.to_dict() for u in users]), 200


# --- BAN / UNBAN USER ---
# PUT /admin/users/<id>/toggle
@admin_bp.route('/users/<int:target_id>/toggle', methods=['PUT'])
@jwt_required()
def toggle_user(target_id):
    user_id = int(get_jwt_identity())
    _, err  = require_admin(user_id)
    if err: return err
    
    target = User.query.get(target_id)
    if not target:
        return jsonify({"msg": "User not found!"}), 404
    
    target.is_active = not target.is_active
    db.session.commit()
    
    status = "active" if target.is_active else "banned"
    return jsonify({"msg": f"User {target.username} is now {status}!"}), 200


# --- CHANGE USER ROLE ---
# PUT /admin/users/<id>/role
# Body: { "role": "vendor" }
@admin_bp.route('/users/<int:target_id>/role', methods=['PUT'])
@jwt_required()
def change_role(target_id):
    user_id = int(get_jwt_identity())
    _, err  = require_admin(user_id)
    if err: return err
    
    target = User.query.get(target_id)
    data   = request.get_json()
    
    if not target:
        return jsonify({"msg": "User not found!"}), 404
    
    new_role = data.get('role')
    if new_role not in ['customer', 'vendor', 'admin']:
        return jsonify({"msg": "Invalid role. Allowed roles: customer, vendor, admin"}), 400
    
    target.role = new_role
    db.session.commit()
    
    return jsonify({"msg": f"Role for user {target.username} successfully changed to '{new_role}'!"}), 200


# --- FULL ANALYTICS ---
# GET /admin/analytics
@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
def analytics():
    user_id = int(get_jwt_identity())
    _, err  = require_admin(user_id)
    if err: return err
    
    total_users      = User.query.count()
    total_customers  = User.query.filter_by(role='customer').count()
    total_vendors    = User.query.filter_by(role='vendor').count()
    total_orders     = Order.query.count()
    delivered        = Order.query.filter_by(status='delivered').all()
    total_revenue    = sum(o.final_price for o in delivered)
    total_partners   = Partner.query.count()
    avg_rating       = db.session.query(db.func.avg(Partner.rating)).scalar() or 0
    
    return jsonify({
        "users": {
            "total":     total_users,
            "customers": total_customers,
            "vendors":   total_vendors
        },
        "orders": {
            "total":     total_orders,
            "delivered": len(delivered),
            "pending":   Order.query.filter_by(status='pending').count()
        },
        "revenue": {
            "total": round(total_revenue, 2)
        },
        "partners": {
            "total":      total_partners,
            "avg_rating": round(avg_rating, 1)
        }
    }), 200