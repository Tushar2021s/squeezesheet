from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
from app.services.problem_service import (
    fetch_all_problems,
    filter_problems,
    get_solved_set,
    exclude_solved,
    generate_sheet
)
from database import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/problems", response_class=HTMLResponse)
def get_problems(
    request: Request,
    min_rating: int = 800,
    max_rating: int = 1500,
    tag: str = "",
    count: int = 20,
    db: Session = Depends(get_db)
):
    if not request.session.get("user"):
        return RedirectResponse("/login", status_code=303)

    user = request.session.get("user")

    problems = fetch_all_problems()

    filtered = filter_problems(problems, min_rating, max_rating, tag)

    solved_set = get_solved_set(db, user)
    filtered = exclude_solved(filtered, solved_set)

    sheet = generate_sheet(filtered, count)

    return templates.TemplateResponse(
        "problems.html",
        {
            "request": request,
            "problems": sheet,
            "solved_problems": solved_set,
            "min_rating": min_rating,
            "max_rating": max_rating,
            "count": count,
            "tag": tag
        }
    )