# app/routes/daily.py

from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.services.daily_service import (
    get_daily_problem,
    get_problem_details
)

from database import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/daily", response_class=HTMLResponse)
def daily_problem(request: Request, db: Session = Depends(get_db)):

    if not request.session.get("user"):
        return RedirectResponse("/login", status_code=303)

    # 1️ Get daily problem ID
    problem_id = get_daily_problem(db)

    if not problem_id:
        return templates.TemplateResponse(
            "daily.html",
            {"request": request, "error": "No problem available"}
        )

    # 2️ Get full problem details
    problem = get_problem_details(problem_id)

    return templates.TemplateResponse(
        "daily.html",
        {
            "request": request,
            "problem": problem,
            "problem_id": problem_id
        }
    )