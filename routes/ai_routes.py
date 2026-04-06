import os

from flask import Blueprint, request, jsonify, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
import time

from models import db, Task, AILog
from sqlalchemy import select

from openai import OpenAI
import re

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

    if not tasks:
        abort(400)

    # Prepare task list
    task_list = [
        f"- {task.title} (status: {task.status})"
        for task in tasks
    ]

    prompt = f"""
    You are a productivity assistant.

    Tasks:
    {chr(10).join(task_list)}

    Instructions:
    - Prioritize overdue tasks first
    - Then handle pending tasks
    - Add estimated time for each task (examples, 30 min, 1 hour, etc)
    - Do not overload any time block
    - Create a realistic day plan (morning, then afternoon, then evening)
    - Keep it concise and actionable (bullet points)

    Output format:
    Morning:
    - ...

    Afternoon:
    - ...

    Evening:
    - ...
    """

    try:
        # Check latency
        start = time.time()

        # Planner
        # Initial plan
        planner_response = client.chat.completions.create(
            model="deepseek/deepseek-chat",
            messages=[
                {"role": "system", "content": "You are a helpful productivity assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
        )

        ai_plan = planner_response.choices[0].message.content or "No plan generated."

        # Improvement loop
        MAX_ITERATIONS = 2

        current_plan = ai_plan
        final_critique = None
        final_score = 0

        for _ in range(MAX_ITERATIONS):
            critique = critique_plan(current_plan, task_list)
            parsed_score = extract_score(critique)

            if parsed_score:
                final_score = parsed_score

            # Stop early if good enough
            if parsed_score and parsed_score >= 8:
                final_critique = critique
                break

            # Otherwise improve
            current_plan = improve_plan(current_plan, critique)
            final_critique = critique

        improved_plan = current_plan

        # Latency end
        latency = time.time() - start

        # Evaluate response
        score = final_score if final_score else evaluate_response(improved_plan)

        # Store log
        log = AILog(
            prompt=prompt,
            original_plan=ai_plan,
            critique=final_critique,
            final_plan=improved_plan,
            latency=latency,
            score=score
        )

        db.session.add(log)
        db.session.commit()

        return jsonify({
            "original_plan": ai_plan,
            "critique": critique,
            "final_plan": improved_plan,
            "latency": round(latency, 3),
            "score": score
        })

    except Exception as e:
        print("AI ERROR:", e)
        abort(500)

def critique_plan(plan_text, task_list):
    critique_prompt = f"""
    You are a strict productivity coach.

    Tasks:
    {chr(10).join(task_list)}

    Proposed Plan:
    {plan_text}

    Evaluate the plan based on:
    1. Task prioritization (overdue first?)
    2. Realism (not overloaded?)
    3. Clarity (easy to follow?)
    4. Coverage (important tasks included?)

    Output format:
    Score: X/10
    Feedback:
    - ...
    - ...
    - ...
    """

    response = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a strict and honest productivity critic."},
            {"role": "user", "content": critique_prompt}
        ],
        max_tokens=200,
    )

    return response.choices[0].message.content

def improve_plan(original_plan, critique):
    improve_prompt = f"""
    You are a productivity assistant improving your plan.

    Original Plan:
    {original_plan}

    Critique:
    {critique}

    Improve the plan based on the critique.

    Keep same format:
    Morning / Afternoon / Evening
    """

    response = client.chat.completions.create(
        model="deepseek/deepseek-chat",
        messages=[
            {"role": "system", "content": "You improve plans based on feedback."},
            {"role": "user", "content": improve_prompt}
        ],
        max_tokens=200,
    )

    return response.choices[0].message.content

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

def extract_score(critique_text):
    match = re.search(r"(\d+)/10", critique_text)
    if match:
        return int(match.group(1))
    return None