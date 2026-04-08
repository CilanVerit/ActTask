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
    You are a strict productivity assistant.

    Tasks:
    {chr(10).join(task_list)}

    Instructions:
    - Prioritize overdue tasks first
    - Then handle pending tasks
    - Use ONLY plain text (NO markdown symbols like ** or ###)
    - Format clean bullet points using "-"
    - Always include time estimates (e.g., 30 min, 1 hour)
    - Keep each section short and readable
    - Do not overload any time block
    - Create a realistic day plan (morning, then afternoon, then evening)
    - Keep it concise and actionable (bullet points)

    IMPORTANT:
    - Use ONLY tasks from the provided list
    - Do NOT invent new tasks

    If rules are broken, fix them aggressively.

    Output format:
    Morning:
    - Task (time)

    Afternoon:
    - Task (time)

    Evening:
    - Task (time)
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
            max_tokens=min(500, 100 + len(task_list) * 20),
        )

        ai_plan = planner_response.choices[0].message.content or "No plan generated."

        # Improvement loop
        max_iterations = 2

        current_plan = ai_plan
        final_critique = None
        final_score = 0

        for _ in range(max_iterations):
            critique = critique_plan(current_plan, task_list)
            parsed_score = extract_score(critique)

            if parsed_score:
                final_score = parsed_score
            
            if extract_overload_flag(critique):
                final_score = min(final_score, 5)

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

        # Realism constraint
        total_minutes = estimate_total_time(improved_plan)

        if total_minutes > 480:  # 8 hours
            score = min(score, 5)

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
    1. Prioritization:
    - Are overdue tasks scheduled first?

    2. Realism:
    - Total planned work time must NOT exceed 8 hours, unless user wants to
    - Each task must have a clear time estimate (examples, 30 min, 1 hour, etc.)
    - Avoid scheduling more than 3–5 tasks per time block
    - No time overlaps or impossible scheduling
    - Breaks or gaps should exist between tasks
    - Flag any overload clearly

    3. Clarity:
    - Is the plan easy to follow?

    4. Coverage:
    - Are important tasks included?

    Be precise and constructive.
    Only flag major issues.
    Do NOT invent new tasks.
    Do NOT change task list.
    State what were the broken rule(s).

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

    Improve the plan STRICTLY based on the critique.
    Fix the issues with a strong focus on:
    - Fix ordering, time estimates, workload balance
    - Keeping total time under 8 hours, unless user wants to do more
    - Adding realistic time estimates
    - Spreading tasks properly across the day
    - DO NOT add new tasks
    - DO NOT use markdown
    - Format clean bullet points using "-"

    Focus on where the broken rule(s) were and adjust correspondingly.

    Keep same format:
    Output format:
    Morning: 
    - Task (time)

    Afternoon: 
    - Task (time)

    Evening: 
    - Task (time)
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

    score = 0

    # Check required sections
    if "morning" in response_text.lower():
        score += 0.25
    if "afternoon" in response_text.lower():
        score += 0.25
    if "evening" in response_text.lower():
        score += 0.25

    # Check bullet points
    if "-" in response_text:
        score += 0.15

    # Check time estimates (very important)
    if re.search(r"\b(min|hour)", response_text.lower()):
        score += 0.1

    return round(score, 2)

def extract_score(critique_text):
    match = re.search(r"(\d+)/10", critique_text)
    if match:
        return int(match.group(1))
    return None

def estimate_total_time(plan_text):
    times = re.findall(r"(\d+(?:\.\d+)?)\s*(min|mins|hour|hours|hr|hrs)", plan_text.lower())
    total = 0

    for value, unit in times:
        value = float(value)
        if unit == "hour":
            total += value * 60
        else:
            total += value

    return total  # in minutes

def extract_overload_flag(text):
    if "rule!" in text.lower():
        return True
    return False