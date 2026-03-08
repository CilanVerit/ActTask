from flask import Flask, request, jsonify, abort
from flask_migrate import Migrate
from models import db, Task
from sqlalchemy import select, func
import math
from config import Config

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

# Homepage
@actTask.route("/")
def home():
    return "ActTask is now running!"

# Create a task 
@actTask.route("/tasks",methods=["POST"])
def createTask():
    data = request.get_json()

    # Information
    title = data.get("title")
    description = data.get("description")

    # Dates
    deadline = data.get("deadline")

    if not title or title.strip() == "":
        abort(400)

    newTask = Task(title=title, description=description, deadline=deadline)

    db.session.add(newTask)
    db.session.commit()

    return jsonify(newTask.serialize()), 201

# Get all tasks
@actTask.route("/tasks",methods=["GET"])
def listTask():
    # Status filter (Overdue, Pending, Completed)
    status_filter = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int) # Number of tasks in a page
    search = request.args.get("search")

    query = select(Task)

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

# Get statistic
@actTask.route("/tasks/stats", methods=["GET"])
def getStats():
    total = db.session.scalar(select(func.count()).select_from(Task))
    completed = db.session.scalar(select(func.count()).where(Task.status == "Completed"))
    pending = db.session.scalar(select(func.count()).where(Task.status == "Pending"))
    overdue = db.session.scalar(select(func.count()).where(Task.status == "Overdue"))

    return jsonify({
        "total" : total,
        "completed" : completed,
        "pending" : pending,
        "overdue" : overdue,
    })

# Get a specific task 
@actTask.route("/tasks/<int:id>",methods=["GET"])
def getTask(id):
    task = db.session.get(Task, id)

    if not task:
        abort(404)
    
    task.update_deadline()

    return jsonify(task.serialize())

# Update a task
@actTask.route("/tasks/<int:id>",methods=["PUT"])
def updateTask(id):
    task = db.session.get(Task, id)

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
def updateStatus(id):
    task = db.session.get(Task, id)

    data = request.get_json()
    task.status = data.get("status", task.status)

    if not task:
        abort(404)
    
    task.status = "Completed"
    db.session.commit()

    return jsonify(task.serialize())

# Delete a task
@actTask.route("/tasks/<int:id>",methods=["DELETE"])
def deleteTask(id):
    task = db.session.get(Task, id)

    if not task:
        abort(404)
    
    db.session.delete(task)
    db.session.commit()

    return jsonify({"message":"Deleted successfully."})

# Error Handlers
@actTask.errorhandler(400)
def requiredEmpty(error):
    return jsonify({"error" : "This field is required"}), 400

@actTask.errorhandler(404)
def notFound(error):
    return jsonify({"error" : "No tasks found."}), 404

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