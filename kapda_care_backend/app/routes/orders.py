# ============================================================
# ORDERS ROUTES — Place, Track, and Review
# The core engine of Kapda Care
# ============================================================
import json
from flask import Blueprint, request, jsonify
from .. import db
from ..models import User, Order, SubOrder, OrderTimeline, Partner, Review
from ..utils import calculate_total_price, split_items_by_service, add_timeline_entry, STATUS_MESSAGES
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime

orders_bp = Blueprint('orders', __name__)


# --- PLACE ORDER (THE BIG ONE) ---
# POST /orders/place
# Body: {
#   "items": [{"type": "shirt", "quantity": 2, "service": "wash"}],
#   "pickup_address": "...",
#   "is_express": false,
#   "special_notes": "..."
# }
@orders_bp.route('/place', methods=['POST'])
@jwt_required()
def place_order():
    customer_id = int(get_jwt_identity())
    data        = request.get_json()
    items       = data.get('items', [])
    
    if not items:
        return jsonify({"msg": "No items found in the order!"}), 400
    
    is_express = data.get('is_express', False)
    
    # ---- STEP 1: Calculate price ----
    total, discount, final = calculate_total_price(items, is_express)
    
    # ---- STEP 2: Save the main Order ----
    user = User.query.get(customer_id)
    pickup_addr = data.get('pickup_address') or user.address or "Address not provided"
    
    new_order = Order(
        customer_id    = customer_id,
        total_price    = total,
        discount       = discount,
        final_price    = final,
        pickup_address = pickup_addr,
        items          = json.dumps(items),
        is_express     = is_express,
        special_notes  = data.get('special_notes', ''),
        status         = 'pending'
    )
    db.session.add(new_order)
    db.session.flush()  # Flush before commit to get the ID
    
    # ---- STEP 3: SPLIT ROUTING — KAPDA CARE MAGIC ----
    # Split items into laundry and tailoring
    laundry_items, tailoring_items = split_items_by_service(items)
    
    if laundry_items:
        # Calculate price for laundry sub-order
        l_total, _, l_final = calculate_total_price(laundry_items, is_express)
        laundry_sub = SubOrder(
            parent_order_id = new_order.id,
            service_type    = 'laundry',
            items           = json.dumps(laundry_items),
            sub_total       = l_final,
            status          = 'pending'
        )
        db.session.add(laundry_sub)
    
    if tailoring_items:
        # Calculate price for tailoring sub-order
        t_total, _, t_final = calculate_total_price(tailoring_items, is_express)
        tailoring_sub = SubOrder(
            parent_order_id = new_order.id,
            service_type    = 'tailoring',
            items           = json.dumps(tailoring_items),
            sub_total       = t_final,
            status          = 'pending'
        )
        db.session.add(tailoring_sub)
    
    # ---- STEP 4: Add first entry to timeline ----
    add_timeline_entry(
        order_id   = new_order.id,
        status     = 'pending',
        message    = STATUS_MESSAGES['pending'],
        updated_by = customer_id
    )
    
    db.session.commit()
    
    return jsonify({
        "msg": "Order placed successfully!",
        "order_id":     new_order.id,
        "total_price":  total,
        "discount":     discount,
        "final_price":  final,
        "laundry_items_count":   len(laundry_items),
        "tailoring_items_count": len(tailoring_items),
        "is_express":   is_express,
        "pickup_address": pickup_addr
    }), 201


# --- MY ORDERS (Customer views their orders) ---
# GET /orders/my
@orders_bp.route('/my', methods=['GET'])
@jwt_required()
def my_orders():
    customer_id = int(get_jwt_identity())
    orders      = Order.query.filter_by(customer_id=customer_id)\
                             .order_by(Order.created_at.desc()).all()
    
    return jsonify([o.to_dict() for o in orders]), 200


# --- ORDER DETAIL + TIMELINE ---
# GET /orders/<id>
@orders_bp.route('/<int:order_id>', methods=['GET'])
@jwt_required()
def order_detail(order_id):
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)
    order   = Order.query.get(order_id)
    
    if not order:
        return jsonify({"msg": "Order not found!"}), 404
    
    # Only the customer, vendor, or admin can view this
    if order.customer_id != user_id and user.role not in ['vendor', 'admin']:
        return jsonify({"msg": "Access denied! This is not your order."}), 403
    
    # Fetch timeline
    timeline = OrderTimeline.query.filter_by(order_id=order_id)\
                                  .order_by(OrderTimeline.timestamp.asc()).all()
    timeline_data = [{
        'status':    t.status,
        'message':   t.message,
        'timestamp': t.timestamp.isoformat()
    } for t in timeline]
    
    # Fetch sub-orders
    sub_orders = SubOrder.query.filter_by(parent_order_id=order_id).all()
    
    result = order.to_dict()
    result['timeline']   = timeline_data
    result['sub_orders'] = [s.to_dict() for s in sub_orders]
    
    return jsonify(result), 200


# --- CANCEL ORDER ---
# PUT /orders/<id>/cancel
@orders_bp.route('/<int:order_id>/cancel', methods=['PUT'])
@jwt_required()
def cancel_order(order_id):
    user_id = int(get_jwt_identity())
    order   = Order.query.get(order_id)
    
    if not order:
        return jsonify({"msg": "Order not found!"}), 404
    
    if order.customer_id != user_id:
        return jsonify({"msg": "You can only cancel your own orders!"}), 403
    
    # Only pending orders can be cancelled
    if order.status != 'pending':
        return jsonify({"msg": f"Order cannot be cancelled while in '{order.status}' status!"}), 400
    
    order.status = 'cancelled'
    add_timeline_entry(order_id, 'cancelled', STATUS_MESSAGES['cancelled'], user_id)
    db.session.commit()
    
    return jsonify({"msg": "Order cancelled successfully!"}), 200


# --- SUBMIT REVIEW ---
# POST /orders/<id>/review
# Body: { "partner_id": 1, "rating": 5, "comment": "..." }
@orders_bp.route('/<int:order_id>/review', methods=['POST'])
@jwt_required()
def submit_review(order_id):
    user_id = int(get_jwt_identity())
    order   = Order.query.get(order_id)
    data    = request.get_json()
    
    if not order or order.customer_id != user_id:
        return jsonify({"msg": "Order not found or permission denied!"}), 403
    
    if order.status != 'delivered':
        return jsonify({"msg": "Reviews can only be submitted for delivered orders!"}), 400
    
    # Already reviewed?
    existing = Review.query.filter_by(order_id=order_id, customer_id=user_id).first()
    if existing:
        return jsonify({"msg": "You have already reviewed this order!"}), 409
    
    rating = data.get('rating')
    if not rating or not (1 <= int(rating) <= 5):
        return jsonify({"msg": "Rating must be between 1 and 5!"}), 400
    
    review = Review(
        order_id    = order_id,
        customer_id = user_id,
        partner_id  = data.get('partner_id'),
        rating      = int(rating),
        comment     = data.get('comment', '')
    )
    db.session.add(review)
    
    # Update partner's average rating
    partner = Partner.query.get(data.get('partner_id'))
    if partner:
        all_reviews = Review.query.filter_by(partner_id=partner.id).all()
        avg = (sum(r.rating for r in all_reviews) + int(rating)) / (len(all_reviews) + 1)
        partner.rating = round(avg, 1)
    
    db.session.commit()
    return jsonify({"msg": "Review submitted successfully! Thank you 🙏"}), 201


# POST /orders/create-payment  ← Creates Razorpay order
# POST /orders/verify-payment  ← Verifies payment