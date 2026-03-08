from flask import Flask, request, jsonify
from models import db, Task
from sqlalchemy import select

# Start Flask app
actTask = Flask(__name__)

# Configuration
actTask.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///acttask.db"
actTask.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# JSON key sorting
actTask.json.sort_keys = False

# Initialize database
db.init_app(actTask)

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
    status = data.get("status")

    # Dates
    deadline = data.get("deadline")

    if title is not None and title.strip() == "":
        return jsonify({"error": "Title cannot be empty."}), 400

    newTask = Task(title=title, description=description, status=status, deadline=deadline)

    db.session.add(newTask)
    db.session.commit()

    return jsonify({"message":"New task added!"}), 201

# Get all tasks
@actTask.route("/tasks",methods=["GET"])
def listTask():
    # Status filter (Missed, Pending, Completed)
    status_filter = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int) # Number of tasks in a page

    query = select(Task)

    if status_filter:
        query = query.where(Task.status == status_filter)

    # Pagination
    offset = (page - 1) * limit
    query = query.offset(offset).limit(limit)
    tasks = db.session.scalars(query).all()
    
    taskList = []

    for task in tasks:
        taskList.append({
            # Information
            "id" : task.id,
            "title" : task.title,
            "description" : task.description,
            "status" : task.status,

            # Dates
            "created_at" : task.created_at,
            "updated_at" : task.updated_at,
            "deadline" : task.deadline,
        })

    return jsonify(taskList)

# Get a specific task 
@actTask.route("/tasks/<int:id>",methods=["GET"])
def getTask(id):
    task = db.session.get(Task, id)

    if not task:
        return jsonify({"error":"No such task."}), 404
    
    return jsonify({
            # Information
            "id" : task.id,
            "title" : task.title,
            "description" : task.description,
            "status" : task.status,

            # Dates
            "created_at" : task.created_at,
            "updated_at" : task.updated_at,
            "deadline" : task.deadline,
    })

# Update a task
@actTask.route("/tasks/<int:id>",methods=["PUT"])
def updateTask(id):
    task = db.session.get(Task, id)

    if not task:
        return jsonify({"error":"No such task."}), 404
    
    data = request.get_json()

    title = data.get("title")

    if title is not None and title.strip() == "":
        return jsonify({"error": "Title cannot be empty."}), 400

    task.title = data.get("title",task.title)
    task.description = data.get("description",task.description)
    task.status = data.get("status",task.status)

    db.session.commit()
    
    return jsonify({
            # Information
            "id" : task.id,
            "title" : task.title,
            "description" : task.description,
            "status" : task.status,

            # Dates
            "created_at" : task.created_at,
            "updated_at" : task.updated_at,
            "deadline" : task.deadline,
    })

# Delete a task
@actTask.route("/tasks/<int:id>",methods=["DELETE"])
def deleteTask(id):
    task = db.session.get(Task, id)

    if not task:
        return jsonify({"error":"No such task."}), 404
    
    db.session.delete(task)
    db.session.commit()

    return jsonify({"message":"Deleted successfully."})

if __name__ == "__main__":
    # Create database
    with actTask.app_context():
        db.drop_all()
        db.create_all()

    # Developer mode
    actTask.run(debug=True)