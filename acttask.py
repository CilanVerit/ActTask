from flask import Flask, request, jsonify
from models import db, Task
from sqlalchemy import select

actTask = Flask(__name__)

# Fetch Database
actTask.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///acttask.db"
actTask.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Start
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

if __name__ == "__main__":
    # Create database
    with actTask.app_context():
        print("Creating database tables...")
        db.create_all()

    # Developer mode
    actTask.run(debug=True)