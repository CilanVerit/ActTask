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

if __name__ == "__main__":
    # Create database
    with actTask.app_context():
        print("Creating database tables...")
        db.create_all()

    # Developer mode
    actTask.run(debug=True)