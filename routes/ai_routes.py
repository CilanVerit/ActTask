from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
import time

from models import db, Task, AILog
from sqlalchemy import select

from openai import OpenAI
import os

# LLM Client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    base_url="https://openrouter.ai/api/v1",
)

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")

@ai_bp.route("/plan", methods=["POST"])
@jwt_required()
def plan_day():
    current_user = int(get_jwt_identity())

    # Get user tasks
    tasks = db.session.scalars(
        select(Task)
        .where(
            Task.owner == current_user,
            Task.status != "Completed"
        )
        .order_by(Task.created_at.desc())
    ).all()
    tasks = sorted(tasks, key=lambda t: t.status == "Overdue", reverse=True)

    tasks_text = "\n".join(
        [f"- {t.title} ({t.status})" for t in tasks]
    )

    if not tasks:
        abort(400)

    # Prepare task list
    task_list = [
        f"- {task.title} (status: {task.status})"
        for task in tasks
    ]

    prompt = f"""
    You are a productivity assistant.

    Given the following tasks:
    {chr(10).join(task_list)}

    Create a simple, realistic plan for the day.
    Prioritize important and pending tasks.
    Keep it short and clear.
    """

    try:
        # Check latency
        start = time.time()

        response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful productivity assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
        )

        # Latency end
        latency = time.time() - start

        ai_response = response.choices[0].message.content

        # Score
        score = evaluate_response(ai_response)

        # Store log
        log = AILog(
            prompt=prompt,
            response=ai_response,
            latency=latency,
            score=score
        )

        db.session.add(log)
        db.session.commit()

        return jsonify({
            "plan": ai_response,
            "latency": round(latency, 3),
            "score": score
        })

    except Exception as e:
        print("AI ERROR:", e)
        abort(500)

# Evaluate response
def evaluate_response(response_text):
    if not response_text:
        return 0

    length_score = min(len(response_text) / 200, 1)

    keyword_bonus = 0
    if "priority" in response_text.lower():
        keyword_bonus += 0.2
    if "morning" in response_text.lower():
        keyword_bonus += 0.2

    return round(min(length_score + keyword_bonus, 1), 2)