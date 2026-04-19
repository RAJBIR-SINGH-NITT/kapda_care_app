from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager
from flask_cors import CORS          # ← ADD THIS LINE

db     = SQLAlchemy()
bcrypt = Bcrypt()
jwt    = JWTManager()

def create_app():
    app = Flask(__name__)
    from .config import Config
    app.config.from_object(Config)
    
    CORS(app)                        # ← ADD THIS LINE
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    
    with app.app_context():
        from .routes.auth    import auth_bp
        from .routes.orders  import orders_bp
        from .routes.vendor  import vendor_bp
        from .routes.partner import partner_bp
        from .routes.admin   import admin_bp
        
        app.register_blueprint(auth_bp,    url_prefix='/auth')
        app.register_blueprint(orders_bp,  url_prefix='/orders')
        app.register_blueprint(vendor_bp,  url_prefix='/vendor')
        app.register_blueprint(partner_bp, url_prefix='/partner')
        app.register_blueprint(admin_bp,   url_prefix='/admin')
        
        db.create_all()
    return app