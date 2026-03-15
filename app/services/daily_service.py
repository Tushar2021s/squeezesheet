import random

def get_daily_problem(user_rating, problems):
    suitable = [p for p in problems if abs(p.rating - user_rating) <= 100]
    return random.choice(suitable) if suitable else None