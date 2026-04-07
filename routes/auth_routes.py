from flask import Blueprint, request, jsonify, abort
from sqlalchemy import select

from models import db, User
from flask_jwt_extended import create_access_token
from werkzeug.security import generate_password_hash, check_password_hash

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


# 8. Register account
@auth_bp.route("/register",methods=["POST"])
def register_account():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or username.strip() == "":
        abort(400)

    if not password or password.strip() == "":
        abort(400)

    # Check existed username
    existed = db.session.execute(select(User).where(User.username == username)).scalar()

    if existed:
        abort(409)

    hashed_password = generate_password_hash(password)

    new_user = User(username = username, password = hashed_password)

    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message" : "Account registered successfully."}), 201

# 9. Login account
@auth_bp.route("/login",methods=["POST"])
def login_account():
    data = request.get_json()

    username = data.get("username")
    password = data.get("password")

    if not username or username.strip() == "":
        abort(400)

    if not password or password.strip() == "":
        abort(400)

    # Check existed username
    user = db.session.execute(select(User).where(User.username == username)).scalar()

    if not user or not check_password_hash(user.password, password):
        abort(401)
    print("USER ID:", user.userid)
    access_token = create_access_token(identity = str(user.userid))

    return jsonify({"access_token": access_token})