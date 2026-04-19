from flask import Blueprint, request, jsonify
from .. import db, bcrypt
from ..models import User
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

auth_bp = Blueprint('auth', __name__)

# --- HOME ---
@auth_bp.route('/')
def home():
    return jsonify({"message": "Welcome to Kapda Care Backend! 🧺"})

# --- SIGNUP ---
@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    
    required = ['username', 'email', 'password']
    for field in required:
        if not data.get(field):
            return jsonify({"msg": f"The '{field}' field is required!"}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({"msg": "This email is already registered!"}), 409
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({"msg": "This username is already taken!"}), 409
    
    hashed_pw = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    
    new_user = User(
        username = data['username'],
        email    = data['email'],
        password = hashed_pw,
        phone    = data.get('phone'),
        address  = data.get('address'),
        role     = data.get('role', 'customer') 
    )
    
    db.session.add(new_user)
    db.session.commit()
    
    return jsonify({"msg": "Account created successfully! Please log in.", "user_id": new_user.id}), 201

# --- LOGIN ---
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data.get('email') or not data.get('password'):
        return jsonify({"msg": "Both email and password are required!"}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if user and bcrypt.check_password_hash(user.password, data['password']):
        if not user.is_active:
            return jsonify({"msg": "Your account has been suspended. Please contact support."}), 403
        
        access_token = create_access_token(identity=str(user.id))
        
        return jsonify({
            "access_token": access_token,
            "user": user.to_dict()
        }), 200
    
    return jsonify({"msg": "Invalid email or password!"}), 401

# --- GET PROFILE ---
@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)
    
    if not user:
        return jsonify({"msg": "User not found!"}), 404
    
    return jsonify(user.to_dict()), 200

# --- UPDATE PROFILE ---
@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    user_id = int(get_jwt_identity())
    user    = User.query.get(user_id)
    data    = request.get_json()
    
    if data.get('phone'):   user.phone   = data['phone']
    if data.get('address'): user.address = data['address']
    if data.get('username'):
        existing = User.query.filter_by(username=data['username']).first()
        if existing and existing.id != user_id:
            return jsonify({"msg": "This username is already taken!"}), 409
        user.username = data['username']
    
    db.session.commit()
    return jsonify({"msg": "Profile updated successfully!", "user": user.to_dict()}), 200