from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import select, func
import math

from models import db, Task

task_bp = Blueprint("task", __name__)

# 1. Create a task 
@task_bp.route("/tasks",methods=["POST"])
@jwt_required()
def createTask():
    data = request.get_json()

    current_user = int(get_jwt_identity())

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


# 2. Get all tasks
@task_bp.route("/tasks",methods=["GET"])
@jwt_required()
def listTask():
    # Status filter (Overdue, Pending, Completed)
    status_filter = request.args.get("status")
    page = request.args.get("page", 1, type=int)
    limit = request.args.get("limit", 10, type=int) # Number of tasks in a page
    search = request.args.get("search")

    current_user = int(get_jwt_identity())
    query = select(Task).where(Task.owner == current_user)

    if search:
        query = query.where(
            Task.title.ilike(f"%{search}%") |
            Task.description.ilike(f"%{search}%")
        )

    if status_filter:
        query = query.where(Task.status == status_filter)

    # Get total tasks, pages, query amount
    total_tasks = db.session.scalar(select(func.count()).where(Task.owner == current_user))
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


# 3. Get statistics
@task_bp.route("/tasks/stats", methods=["GET"])
@jwt_required()
def getStats():

    current_user = int(get_jwt_identity())

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


# 4. Get a specific task 
@task_bp.route("/tasks/<int:id>",methods=["GET"])
@jwt_required()
def getTask(id):

    task = db.session.get(Task, id)

    if not task:
        abort(404)
    if task.owner != int(get_jwt_identity()):
        abort(403)
    
    task.update_deadline()

    return jsonify(task.serialize())

# 5. Update a task
@task_bp.route("/tasks/<int:id>",methods=["PUT"])
@jwt_required()
def updateTask(id):
    task = db.session.get(Task, id)

    if task.owner != int(get_jwt_identity()):
        abort(403)
    
    data = request.get_json()

    title = data.get("title")

    if not title or title.strip() == "":
        abort (400)

    task.title = data.get("title",task.title)
    task.description = data.get("description",task.description)

    db.session.commit()
    
    return jsonify(task.serialize())

# 6. Update status
@task_bp.route("/tasks/<int:id>/status", methods=["PATCH"])
@jwt_required()
def updateStatus(id):
    task = db.session.get(Task, id)

    if not task:
        abort(404)

    if task.owner != int(get_jwt_identity()):
        abort(403)

    data = request.get_json()
    task.status = data.get("status", task.status)

    db.session.commit()

    return jsonify(task.serialize())

# 7. Delete a task
@task_bp.route("/tasks/<int:id>",methods=["DELETE"])
@jwt_required()
def deleteTask(id):
    task = db.session.get(Task, id)

    if not task:
        abort(404)

    if task.owner != int(get_jwt_identity()):
        abort(403)
    
    db.session.delete(task)
    db.session.commit()

    return jsonify({"message":"Deleted successfully."})