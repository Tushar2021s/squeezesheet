from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
# templates = Jinja2Templates(directory="templates")

@app.get("/")
def home(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")

    stats = None

    if user:
        solved_count = db.query(models.ProblemStatus).filter(
            models.ProblemStatus.username == user,
            models.ProblemStatus.status == "solved"
        ).count()

        attempted_count = db.query(models.ProblemStatus).filter(
            models.ProblemStatus.username == user
        ).count()

        stats = {
            "solved": solved_count,
            "attempted": attempted_count
        }

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user,
            "stats": stats
        }
    )