from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/generate")
def generate_sheet(request: Request):
    return templates.TemplateResponse("generate.html", {"request": request})