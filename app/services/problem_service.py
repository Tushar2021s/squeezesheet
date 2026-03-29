# app/services/problem_service.py

import requests
from sqlalchemy.orm import Session
import models
import random
from datetime import datetime

CODEFORCES_API = "https://codeforces.com/api/problemset.problems"


# ----------------------------------------
# Fetch all problems
# ----------------------------------------
def fetch_all_problems():
    response = requests.get(CODEFORCES_API)
    data = response.json()

    if data["status"] != "OK":
        return []

    return data["result"]["problems"]


# ----------------------------------------
# Filter problems
# ----------------------------------------
def filter_problems(problems, min_rating, max_rating, tag=None):
    filtered = [
        p for p in problems
        if p.get("rating") and min_rating <= p["rating"] <= max_rating
    ]

    if tag:
        filtered = [p for p in filtered if tag in p.get("tags", [])]

    filtered.sort(key=lambda x: x["rating"])
    return filtered


# ----------------------------------------
# Get solved problems
# ----------------------------------------
def get_solved_set(db: Session, username: str):
    solved = db.query(models.ProblemStatus).filter(
        models.ProblemStatus.username == username,
        models.ProblemStatus.status == "solved"
    ).all()

    return set(p.problem_name for p in solved)


# ----------------------------------------
# Remove solved
# ----------------------------------------
def exclude_solved(problems, solved_set):
    return [p for p in problems if p["name"] not in solved_set]


# ----------------------------------------
# Smart sheet generator
# ----------------------------------------
def generate_sheet(problems, count):
    if not problems:
        return []

    easy = [p for p in problems if p["rating"] <= 1000]
    medium = [p for p in problems if 1000 < p["rating"] <= 1600]
    hard = [p for p in problems if p["rating"] > 1600]

    e_count = int(count * 0.3)
    m_count = int(count * 0.5)
    h_count = count - (e_count + m_count)

    return easy[:e_count] + medium[:m_count] + hard[:h_count]


# ----------------------------------------
# Tags
# ----------------------------------------
def get_all_tags(problems):
    tags = set()

    for p in problems:
        for t in p.get("tags", []):
            tags.add(t)

    return sorted(list(tags))