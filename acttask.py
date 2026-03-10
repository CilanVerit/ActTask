from flask import Flask, request, jsonify, abort
from flask_migrate import Migrate
from sqlalchemy import select, func
import math

from models import db, Task, User
from config import Config

from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from werkzeug.security import generate_password_hash, check_password_hash

# Start Flask app
actTask = Flask(__name__)

# Configuration
actTask.config.from_object(Config)

# JWT configuration
jwt = JWTManager(actTask)

# JSON key sorting
actTask.json.sort_keys = False

# Initialize database
db.init_app(actTask)

# Initialize migrations
migrate = Migrate(actTask, db)

# Homepage
@actTask.route("/")
def home():
    return "ActTask is now running!"

# Create a task 
@actTask.route("/tasks",methods=["POST"])
@jwt_required()
def createTask():
    data = request.get_json()

    current_user = get_jwt_identity()

    # Information
    title = data.get("title")
    description = data.get("description")

    # Dates
    deadline = data.get("deadline")

    # User
    owner = current_user

    if not title or title.strip() == "":
        abort(400)

    newTask = Task(title=title, description=description, deadline=deadline, owner=owner)

    db.session.add(newTask)
    db.session.commit()

    return jsonify(newTask.serialize()), 201

# Get all tasks
@actTask.route("/tasks",methods=["GET"])
@jwt_required()
def listTask():
    # Status filter (Overdue, Pending, Completed)
    status_filter = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int) # Number of tasks in a page
    search = request.args.get("search")

    current_user = get_jwt_identity()
    query = select(Task).where(Task.owner == current_user)

    if search:
        query = query.where(
            Task.title.ilike(f"%{search}%"),
            Task.description.ilike(f"%{search}%")
        )

    if status_filter:
        query = query.where(Task.status == status_filter)

    # Get total tasks, pages, query amount
    total_tasks = db.session.scalar(select(func.count()).select_from(Task))
    total_pages = math.ceil(total_tasks / limit) if limit else 1 # Prevent page 0 - invalid
    count_query = db.session.scalar(select(func.count()).select_from(query.subquery()))

    # Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)

    # Auto sort
    query = query.order_by(Task.created_at.desc())

    tasks = db.session.scalars(query).all()
    taskList = []

    for task in tasks:
        task.update_deadline()
        taskList.append(task.serialize())

    db.session.commit()

    return jsonify(({
        "page" : page,
        "limit" : limit,
        "total_tasks" : total_tasks,
        "total_pages" : total_pages,
        "count_query" : count_query,
        "task" : taskList,
        }))

@actTask.route("/tasks/stats", methods=["GET"])
@jwt_required()
def getStats():

    current_user = get_jwt_identity()

    total = db.session.scalar(
        select(func.count()).where(Task.owner == current_user)
    )

    completed = db.session.scalar(
        select(func.count()).where(
            Task.owner == current_user,
            Task.status == "Completed"
        )
    )

    pending = db.session.scalar(
        select(func.count()).where(
            Task.owner == current_user,
            Task.status == "Pending"
        )
    )

    overdue = db.session.scalar(
        select(func.count()).where(
            Task.owner == current_user,
            Task.status == "Overdue"
        )
    )

    return jsonify({
        "total": total,
        "completed": completed,
        "pending": pending,
        "overdue": overdue,
    })

# Get a specific task 
@actTask.route("/tasks/<int:id>",methods=["GET"])
@jwt_required()
def getTask(id):

    task = db.session.get(Task, id)

    if not task:
        abort(404)
    if task.owner != get_jwt_identity():
        abort(403)
    
    task.update_deadline()

    return jsonify(task.serialize())

# Update a task
@actTask.route("/tasks/<int:id>",methods=["PUT"])
@jwt_required()
def updateTask(id):
    task = db.session.get(Task, id)

    if task.owner != get_jwt_identity():
        abort(403)

    if not task:
        abort(404)
    
    data = request.get_json()

    title = data.get("title")

    if not title or title.strip() == "":
        abort (400)

    task.title = data.get("title",task.title)
    task.description = data.get("description",task.description)

    db.session.commit()
    
    return jsonify(task.serialize())

# Update status
@actTask.route("/tasks/<int:id>/status", methods=["PATCH"])
@jwt_required()
def updateStatus(id):
    task = db.session.get(Task, id)

    if not task:
        abort(404)

    if task.owner != get_jwt_identity():
        abort(403)

    data = request.get_json()
    task.status = data.get("status", task.status)

    db.session.commit()

    return jsonify(task.serialize())

# Delete a task
@actTask.route("/tasks/<int:id>",methods=["DELETE"])
@jwt_required()
def deleteTask(id):
    task = db.session.get(Task, id)

    if not task:
        abort(404)

    if task.owner != get_jwt_identity():
        abort(403)
    
    db.session.delete(task)
    db.session.commit()

    return jsonify({"message":"Deleted successfully."})

# Register account
@actTask.route("/auth/register",methods=["POST"])
def registerAccount():
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

# Login account
@actTask.route("/auth/login",methods=["POST"])
def login():
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

    access_token = create_access_token(identity = user.userid)

    return jsonify({"access_token": access_token})

# Error Handlers
@actTask.errorhandler(400)
def requiredEmpty(error):
    return jsonify({"error" : "This field is required."}), 400

@actTask.errorhandler(401)
def invalidUser(error):
    return jsonify({"error" : "Invalid user or password."}), 401

@actTask.errorhandler(403)
def unauthorized(error):
    return jsonify({"error": "Unauthorized"}), 403

@actTask.errorhandler(404)
def notFound(error):
    return jsonify({"error" : "No task found."}), 404

@actTask.errorhandler(409)
def existAcc(error):
    return jsonify({"error" : "Username existed."}), 409

@actTask.errorhandler(500)
def serverError(error):
    return jsonify({"error" : "Internal server error."}), 500

if __name__ == "__main__":
    """
    # Create database without migrations
        with actTask.app_context():
            db.create_all()
    """

    # Developer mode
    actTask.run(debug=True)