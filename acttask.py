from flask import Flask, request, jsonify, abort, render_template
from flask_migrate import Migrate
from sqlalchemy import select, func
import math
import time
from routes.task_routes import task_bp
from routes.auth_routes import auth_bp
from routes.ai_routes import ai_bp

from models import db, Task, User
from config import Config

from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from werkzeug.security import generate_password_hash, check_password_hash

#start = time.time()

# Start Flask app
actTask = Flask(__name__)

# Configuration
actTask.config.from_object(Config)

# JSON key sorting
actTask.json.sort_keys = False

# Initialize database
db.init_app(actTask)

# Initialize migrations
migrate = Migrate(actTask, db)

# JWT configuration
jwt = JWTManager(actTask)

# Register blueprints from routes
actTask.register_blueprint(task_bp)
actTask.register_blueprint(auth_bp)
actTask.register_blueprint(ai_bp)

# Homepage
@actTask.route("/")
def home():
    return render_template("index.html")

# Error Handlers
@actTask.errorhandler(400)
def required_field(error):
    return jsonify({"error" : "This field is required."}), 400

@actTask.errorhandler(401)
def invalid_user(error):
    return jsonify({"error" : "Invalid user or password."}), 401

@actTask.errorhandler(403)
def unauthorized(error):
    return jsonify({"error": "Unauthorized"}), 403

@actTask.errorhandler(404)
def not_found(error):
    return jsonify({"error" : "No task found."}), 404

@actTask.errorhandler(409)
def existed_username(error):
    return jsonify({"error" : "Username existed."}), 409

@actTask.errorhandler(500)
def server_error(error):
    return jsonify({"error" : "Internal server error."}), 500

#end = time.time()

if __name__ == "__main__":
    '''
    # Create database without migrations
    with actTask.app_context():
        db.create_all()
    #'''
    #print((end - start) * 1000) #ms latency

    # Developer mode
    actTask.run(debug=True)