# app/services/daily_service.py

import random
from datetime import datetime
from sqlalchemy.orm import Session
import requests
import models

CODEFORCES_API = "https://codeforces.com/api/problemset.problems"


# ----------------------------------------
# Fetch all problems from Codeforces
# ----------------------------------------
def fetch_all_problems():
    try:
        response = requests.get(CODEFORCES_API, timeout=10)
        data = response.json()

        if data.get("status") != "OK":
            return []

        return data["result"]["problems"]

    except Exception:
        return []


# ----------------------------------------
# Get or create today's daily problem
# ----------------------------------------
def get_daily_problem(db: Session, min_rating=800, max_rating=1500):
    today = datetime.now().strftime("%Y-%m-%d")

    # 1️ Check if already exists in DB
    existing = db.query(models.DailyChallenge).filter(
        models.DailyChallenge.date == today
    ).first()

    if existing:
        return existing.problem_ids  # format: "contestId-index"

    # 2️ Fetch problems
    problems = fetch_all_problems()

    if not problems:
        return None

    # 3️ Filter by rating
    filtered = [
        p for p in problems
        if p.get("rating") and min_rating <= p["rating"] <= max_rating
    ]

    if not filtered:
        return None

    # 4️ Pick random problem
    problem = random.choice(filtered)

    problem_id = f"{problem['contestId']}-{problem['index']}"

    # 5️ Store in DB
    new_entry = models.DailyChallenge(
        date=today,
        problem_ids=problem_id
    )

    db.add(new_entry)
    db.commit()

    return problem_id


# ----------------------------------------
# Get full problem details from problem_id
# ----------------------------------------
def get_problem_details(problem_id: str):
    """
    Input: "1791-A"
    Output: full problem dict
    """

    if not problem_id:
        return None

    try:
        contest_id, index = problem_id.split("-")
    except ValueError:
        return None

    problems = fetch_all_problems()

    for p in problems:
        if str(p["contestId"]) == contest_id and p["index"] == index:
            return p

    return None


# ----------------------------------------
# Helper: Generate direct problem link
# ----------------------------------------
def get_problem_link(problem):
    if not problem:
        return None

    return f"https://codeforces.com/problemset/problem/{problem['contestId']}/{problem['index']}"