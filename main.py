from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from starlette.middleware.sessions import SessionMiddleware
import random
import requests

import models
from database import engine, SessionLocal

# Create tables
models.Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")
# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user
        }
    )
# @app.get("/")
# def home(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})

@app.get("/register", response_class=HTMLResponse)
def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register", response_class=HTMLResponse)
def register_user(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing_user = db.query(models.User).filter(
        (models.User.username == username) | 
        (models.User.email == email)
    ).first()

    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {
                "request": request,
                "error": "Username or Email already exists"
            }
        )

    # Hash password
    hashed_password = pwd_context.hash(password)

    # Create user
    new_user = models.User(
        username=username,
        email=email,
        password=hashed_password
    )

    db.add(new_user)
    db.commit()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "message": "Registration Successful! Please Login."
        }
    )

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/login", response_class=HTMLResponse)
def login_user(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(
        models.User.username == username
    ).first()

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid Username"}
        )

    if not pwd_context.verify(password, user.password):
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid Password"}
        )

    # Store user in session
    request.session["user"] = user.username

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "message": "Login Successful!"}
    )

@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "message": "Logged out successfully"}
    )

@app.get("/problems", response_class=HTMLResponse)
def get_problems(
    request: Request,
    min_rating: int = 800,
    max_rating: int = 1500,
    tag: str = "",
    count: int = 10
):
    url = "https://codeforces.com/api/problemset.problems"
    response = requests.get(url)
    data = response.json()

    filtered = []

    for problem in data["result"]["problems"]:
        rating = problem.get("rating")
        tags = problem.get("tags", [])

        if rating is None:
            continue

        if min_rating <= rating <= max_rating:
            if tag == "" or tag in tags:
                filtered.append(problem)

    sheet = random.sample(filtered, min(count, len(filtered)))

    return templates.TemplateResponse(
        "problems.html",
        {
            "request": request,
            "problems": sheet,
            "min_rating": min_rating,
            "max_rating": max_rating,
            "tag": tag,
            "count": count
        }
    )






# from fastapi import FastAPI, Request, Depends
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# from fastapi.staticfiles import StaticFiles
# from sqlalchemy.orm import Session
# from database import engine
# from models import User
# from database import SessionLocal
# from passlib.context import CryptContext
# from fastapi import Form, Depends

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# User.metadata.create_all(bind=engine)
# import random
# import requests

# import models
# from database import engine, SessionLocal

# models.Base.metadata.create_all(bind=engine)

# app = FastAPI()

# app.mount("/static", StaticFiles(directory="static"), name="static")
# templates = Jinja2Templates(directory="templates")

# # Dependency
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# @app.get("/")
# def home(request: Request):
#     return templates.TemplateResponse("index.html", {"request": request})

# @app.get("/problems", response_class=HTMLResponse)
# def get_problems(
#     request: Request,
#     min_rating: int = 800,
#     max_rating: int = 1500,
#     tag: str = "",
#     count: int = 10
# ):
#     url = "https://codeforces.com/api/problemset.problems"
#     response = requests.get(url)
#     data = response.json()

#     filtered = []

#     for problem in data["result"]["problems"]:
#         rating = problem.get("rating")
#         tags = problem.get("tags", [])

#         if rating is None:
#             continue

#         if rating >= min_rating and rating <= max_rating:
#             if tag == "" or tag in tags:
#                 filtered.append(problem)

#     # Randomly pick problems
#     sheet = random.sample(filtered, min(count, len(filtered)))

#     return templates.TemplateResponse(
#     "problems.html",
#     {
#         "request": request,
#         "problems": sheet,
#         "min_rating": min_rating,
#         "max_rating": max_rating,
#         "tag": tag,
#         "count": count
#     }
# )


# # @app.get("/problems", response_class=HTMLResponse)
# # def get_problems(
# #     request: Request,
# #     min_rating: int = 800,
# #     max_rating: int = 1500,
# #     tag: str = None
# # ):
# #     url = "https://codeforces.com/api/problemset.problems"
# #     response = requests.get(url)
# #     data = response.json()

# #     problems = []

# #     for problem in data["result"]["problems"]:
# #         if "rating" in problem:
# #             if min_rating <= problem["rating"] <= max_rating:
# #                 if tag:
# #                     if tag not in problem["tags"]:
# #                         continue

# #                 problems.append(problem)

# #     return templates.TemplateResponse(
# #         "problems.html",
# #         {
# #             "request": request,
# #             "problems": problems[:50],
# #             "min_rating": min_rating,
# #             "max_rating": max_rating,
# #             "tag": tag
# #         }
# #     )