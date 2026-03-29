from sqlalchemy import Column, Integer, String
from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=True)

    password = Column(String, nullable=True)

    google_id = Column(String, unique=True, nullable=True)
    cf_handle = Column(String, unique=True, nullable=True)

    provider = Column(String, default="local")


class ProblemStatus(Base):
    __tablename__ = "problem_status"

    id = Column(Integer, primary_key=True, index=True)

    username = Column(String, index=True)

    problem_id = Column(String, index=True)
    problem_name = Column(String)

    rating = Column(Integer)
    tag = Column(String)

    status = Column(String)  # solved / attempted

    timestamp = Column(String)


class DailyChallenge(Base):
    __tablename__ = "daily_challenge"

    id = Column(Integer, primary_key=True)

    date = Column(String, unique=True)

    problem_ids = Column(String)


class UserStats(Base):
    __tablename__ = "user_stats"

    id = Column(Integer, primary_key=True)

    username = Column(String, unique=True)

    problems_solved = Column(Integer, default=0)
    problems_attempted = Column(Integer, default=0)

    current_streak = Column(Integer, default=0)
    max_streak = Column(Integer, default=0)

    last_solved_date = Column(String, nullable=True)