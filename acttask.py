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

    title = data.get("title")
    description = data.get("description")
    status = data.get("status")

    newTask = Task(title=title, description=description, status=status)

    db.session.add(newTask)
    db.session.commit()

    return {"message":"New task added!"}, 201

# Get all tasks
@actTask.route("/tasks",methods=["GET"])
def listTask():
    tasks = db.session.scalars(select(Task)).all()
    taskList = []

    for task in tasks:
        taskList.append({
            "id" : task.id,
            "title" : task.title,
            "description" : task.description,
            "status" : task.status,
        })

    return jsonify(taskList)

# Get a specific task 
@actTask.route("/tasks/<int:id>",methods=["GET"])
def getTask(id):
    task = db.session.get(Task, id)

    if not task:
        return {"error":"No such task."}, 404
    
    return jsonify({
        "id" : task.id,
        "title" : task.title,
        "description" : task.description,
        "status" : task.status
    })

# Update a task
@actTask.route("/tasks/<int:id>",methods=["PUT"])
def updateTask(id):
    task = db.session.get(Task, id)

    if not task:
        return {"error":"No such task."}, 404
    
    data = request.get_json()

    task.title = data.get("title",task.title)
    task.description = data.get("description",task.description)
    task.status = data.get("status",task.status)

    db.session.commit()
    
    return jsonify({
        "id" : task.id,
        "title" : task.title,
        "description" : task.description,
        "status" : task.status
    })

# Delete a task
@actTask.route("/tasks/<int:id>",methods=["DELETE"])
def deleteTask(id):
    task = db.session.get(Task, id)

    if not task:
        return {"error":"No such task."}, 404
    
    db.session.delete(task)
    db.session.commit()

    return {"message":"Deleted successfully."}

if __name__ == "__main__":
    # Create database
    with actTask.app_context():
        print("Creating database tables...")
        db.create_all()

    # Developer mode
    actTask.run(debug=True)