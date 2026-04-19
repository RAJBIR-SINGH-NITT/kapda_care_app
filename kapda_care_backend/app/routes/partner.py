# ============================================================
# PARTNER ROUTES — Washer and Tailor onboarding
# Local partners register with Kapda Care through these routes
# ============================================================
from flask import Blueprint, request, jsonify
from .. import db
from ..models import User, Partner, SubOrder
from flask_jwt_extended import jwt_required, get_jwt_identity

partner_bp = Blueprint('partner', __name__)


# --- REGISTER AS PARTNER ---
# POST /partner/register
# Body: { "business_name": "Sharma Dhobi", "service_type": "laundry", "area": "Lajpat Nagar" }
@partner_bp.route('/register', methods=['POST'])
@jwt_required()
def register_partner():
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)
    data    = request.get_json()
    
    if not data.get('business_name') or not data.get('service_type'):
        return jsonify({"msg": "Both 'business_name' and 'service_type' are required!"}), 400
    
    service = data['service_type']
    if service not in ['laundry', 'tailoring', 'both']:
        return jsonify({"msg": "'service_type' must be: laundry, tailoring, or both."}), 400
    
    # Check if the partner is already registered
    existing = Partner.query.filter_by(user_id=user_id).first()
    if existing:
        return jsonify({"msg": "You are already registered as a partner!"}), 409
    
    partner = Partner(
        user_id       = user_id,
        business_name = data['business_name'],
        service_type  = service,
        area          = data.get('area', '')
    )
    
    # Update the user's role to 'vendor'
    user.role = 'vendor'
    
    db.session.add(partner)
    db.session.commit()
    
    return jsonify({
        "msg": "Successfully registered as a Kapda Care partner! Welcome aboard 🎉",
        "partner": partner.to_dict()
    }), 201


# --- MY ASSIGNED JOBS ---
# GET /partner/my-jobs
# Partners can only view their assigned sub-orders
@partner_bp.route('/my-jobs', methods=['GET'])
@jwt_required()
def my_jobs():
    user_id = int(get_jwt_identity())
    partner = Partner.query.filter_by(user_id=user_id).first()
    
    if not partner:
        return jsonify({"msg": "Please register as a partner first!"}), 403
    
    sub_orders = SubOrder.query.filter_by(partner_id=partner.id)\
                               .order_by(SubOrder.created_at.desc()).all()
    
    return jsonify({
        "partner":    partner.to_dict(),
        "jobs":       [s.to_dict() for s in sub_orders],
        "total_jobs": len(sub_orders)
    }), 200


# --- UPDATE JOB STATUS ---
# PUT /partner/jobs/<sub_id>/status
# Body: { "status": "at_partner" }
@partner_bp.route('/jobs/<int:sub_id>/status', methods=['PUT'])
@jwt_required()
def update_job_status(sub_id):
    user_id   = int(get_jwt_identity())
    partner   = Partner.query.filter_by(user_id=user_id).first()
    
    if not partner:
        return jsonify({"msg": "Access denied! Only registered partners can access this route."}), 403
    
    sub_order = SubOrder.query.get(sub_id)
    
    if not sub_order or sub_order.partner_id != partner.id:
        return jsonify({"msg": "Access denied! This job is not assigned to you."}), 403
    
    data       = request.get_json()
    new_status = data.get('status')
    
    sub_order.status = new_status
    db.session.commit()
    
    return jsonify({"msg": f"Job status successfully updated to '{new_status}'!"}), 200


# --- ALL PARTNERS (Public list) ---
# GET /partner/all?service_type=laundry&area=Delhi
@partner_bp.route('/all', methods=['GET'])
def all_partners():
    service_filter = request.args.get('service_type')
    area_filter    = request.args.get('area')
    
    query = Partner.query.filter_by(is_available=True)
    
    if service_filter:
        query = query.filter(
            (Partner.service_type == service_filter) | (Partner.service_type == 'both')
        )
    if area_filter:
        query = query.filter(Partner.area.ilike(f'%{area_filter}%'))
    
    partners = query.order_by(Partner.rating.desc()).all()
    
    return jsonify([p.to_dict() for p in partners]), 200