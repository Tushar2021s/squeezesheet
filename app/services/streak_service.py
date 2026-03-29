# streak.py

from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import models


def update_streak(db: Session, username: str):
    today = datetime.now().date()

    stats = db.query(models.UserStats).filter(
        models.UserStats.username == username
    ).first()

    # 1️ Create stats if not exist
    if not stats:
        stats = models.UserStats(
            username=username,
            current_streak=1,
            max_streak=1,
            last_solved_date=str(today),
            problems_solved=1
        )
        db.add(stats)
        db.commit()
        return stats

    # 2️ Convert last solved date
    if stats.last_solved_date:
        last_date = datetime.strptime(stats.last_solved_date, "%Y-%m-%d").date()
    else:
        last_date = None

    # 3️ Update logic
    if last_date == today:
        # Already solved today → no change
        return stats

    elif last_date == today - timedelta(days=1):
        # Continue streak
        stats.current_streak += 1

    else:
        # Streak broken
        stats.current_streak = 1

    # 4️ Update max streak
    stats.max_streak = max(stats.max_streak, stats.current_streak)

    # 5️ Update metadata
    stats.last_solved_date = str(today)
    stats.problems_solved += 1

    db.commit()

    return stats