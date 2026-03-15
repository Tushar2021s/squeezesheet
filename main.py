from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from starlette.middleware.sessions import SessionMiddleware
from authlib.integrations.starlette_client import OAuth
import random
import requests
import models
from database import engine, SessionLocal

# -------------------------------
# Create database tables
# -------------------------------
models.Base.metadata.create_all(bind=engine)

# -------------------------------
# Create FastAPI app
# -------------------------------
app = FastAPI()

# -------------------------------
# Middleware
# -------------------------------
app.add_middleware(SessionMiddleware, secret_key="super-secret-key")

# -------------------------------
# Static files
# -------------------------------
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------------
# Templates
# -------------------------------
templates = Jinja2Templates(directory="app/templates")

# -------------------------------
# Password hashing
# -------------------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# -------------------------------
# Database dependency
# -------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -------------------------------
# OAuth Setup (Google)
# -------------------------------
oauth = OAuth()

oauth.register(
    name="google",
    client_id="YOUR_GOOGLE_CLIENT_ID",
    client_secret="YOUR_GOOGLE_CLIENT_SECRET",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile"
    }
)

# =====================================================
# -------------------- ROUTES -------------------------
# =====================================================

# -------------------------------
# Home
# -------------------------------
@app.get("/")
def home(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "user": user}
    )

# -------------------------------
# Register
# -------------------------------

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
    existing_user = db.query(models.User).filter(
        (models.User.username == username) |
        (models.User.email == email)
    ).first()

    if existing_user:
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Username or Email already exists"}
        )

    hashed_password = pwd_context.hash(password)

    new_user = models.User(
        username=username,
        email=email,
        password=hashed_password,
        provider="local"
    )

    db.add(new_user)
    db.commit()

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "message": "Registration Successful! Please Login."}
    )
@app.get("/register/google")
async def register_google(request: Request):
    redirect_uri = request.url_for("auth_register_google")
    return await oauth.google.authorize_redirect(request, redirect_uri)


@app.get("/auth/register/google")
async def auth_register_google(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token["userinfo"]

    google_id = user_info["sub"]
    email = user_info["email"]
    name = user_info["name"]

    # If already exists → show error
    existing_user = db.query(models.User).filter(
        models.User.google_id == google_id
    ).first()

    if existing_user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Already registered. Please login."}
        )

    # Create new user
    new_user = models.User(
        username=name,
        email=email,
        google_id=google_id,
        provider="google"
    )

    db.add(new_user)
    db.commit()

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "message": "Registered successfully. Please login."}
    )
# -------------------------------
# Login Page
# -------------------------------
@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# -------------------------------
# Login User
# -------------------------------
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

    request.session["user"] = user.username

    return RedirectResponse("/", status_code=303)

# -------------------------------
# Logout
# -------------------------------
@app.get("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)

# -------------------------------
# Google Login
# -------------------------------
@app.get("/login/google")
async def login_google(request: Request):
    redirect_uri = request.url_for("auth_google")
    return await oauth.google.authorize_redirect(request, redirect_uri)

@app.get("/auth/google")
async def auth_google(request: Request, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token["userinfo"]

    google_id = user_info["sub"]

    # Only allow if already registered
    user = db.query(models.User).filter(
        models.User.google_id == google_id
    ).first()

    if not user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Not registered. Please register first."}
        )

    request.session["user"] = user.username
    return RedirectResponse("/", status_code=303)
# @app.get("/auth/google")
# async def auth_google(request: Request, db: Session = Depends(get_db)):
#     token = await oauth.google.authorize_access_token(request)
#     user_info = token["userinfo"]

#     google_id = user_info["sub"]
#     email = user_info["email"]
#     name = user_info["name"]

#     user = db.query(models.User).filter(
#         models.User.google_id == google_id
#     ).first()

#     if not user:
#         user = models.User(
#             username=name,
#             email=email,
#             google_id=google_id,
#             provider="google"
#         )
#         db.add(user)
#         db.commit()

#     request.session["user"] = user.username
#     return RedirectResponse("/", status_code=303)

# -------------------------------
# Codeforces Login
# -------------------------------

@app.post("/register/codeforces")
def register_codeforces(
    request: Request,
    cf_handle: str = Form(...),
    db: Session = Depends(get_db)
):
    url = f"https://codeforces.com/api/user.info?handles={cf_handle}"
    response = requests.get(url)
    data = response.json()

    if data["status"] != "OK":
        return templates.TemplateResponse(
            "register.html",
            {"request": request, "error": "Invalid Codeforces Handle"}
        )

    existing_user = db.query(models.User).filter(
        models.User.cf_handle == cf_handle
    ).first()

    if existing_user:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Already registered. Please login."}
        )

    new_user = models.User(
        username=cf_handle,
        cf_handle=cf_handle,
        provider="codeforces"
    )

    db.add(new_user)
    db.commit()

    return templates.TemplateResponse(
        "login.html",
        {"request": request, "message": "Registered successfully. Please login."}
    )
@app.post("/login/codeforces")
def login_codeforces(
    request: Request,
    cf_handle: str = Form(...),
    db: Session = Depends(get_db)
):
    url = f"https://codeforces.com/api/user.info?handles={cf_handle}"
    response = requests.get(url)
    data = response.json()

    if data["status"] != "OK":
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid Codeforces Handle"}
        )

    user = db.query(models.User).filter(
        models.User.cf_handle == cf_handle
    ).first()

    if not user:
        user = models.User(
            username=cf_handle,
            cf_handle=cf_handle,
            provider="codeforces"
        )
        db.add(user)
        db.commit()

    request.session["user"] = user.username
    return RedirectResponse("/", status_code=303)

# -------------------------------
# Problems Generator
# -------------------------------
@app.get("/problems", response_class=HTMLResponse)
def get_problems(
    request: Request,
    min_rating: int = 800,
    max_rating: int = 1500,
    count: int = 20
):

    # 🔐 Require login
    if not request.session.get("user"):
        return RedirectResponse("/login", status_code=303)

    url = "https://codeforces.com/api/problemset.problems"
    response = requests.get(url)
    data = response.json()

    if data["status"] != "OK":
        return templates.TemplateResponse(
            "problems.html",
            {"request": request, "error": "Unable to fetch problems"}
        )

    problems = data["result"]["problems"]

    # Filter by rating
    filtered = [
        p for p in problems
        if p.get("rating") and min_rating <= p["rating"] <= max_rating
    ]

    #  Sort by rating (low → high)
    filtered.sort(key=lambda x: x["rating"])

    #  Take first N problems
    sheet = filtered[:count]

    return templates.TemplateResponse(
        "problems.html",
        {
            "request": request,
            "problems": sheet,
            "min_rating": min_rating,
            "max_rating": max_rating,
            "count": count
        }
    )

@app.get("/rating", response_class=HTMLResponse)
def rating_wise(
    request: Request,
    min_rating: int = 800,
    max_rating: int = 1200
):
    url = "https://codeforces.com/api/problemset.problems"
    response = requests.get(url)
    data = response.json()

    problems = data["result"]["problems"]

    filtered = [
        p for p in problems
        if p.get("rating") and min_rating <= p["rating"] <= max_rating
    ]

    filtered.sort(key=lambda x: x["rating"])

    # Generate rating options 800 to 2000 step 100
    rating_options = list(range(800, 2100, 100))

    return templates.TemplateResponse(
        "rating.html",
        {
            "request": request,
            "problems": filtered[:25],
            "rating_options": rating_options,
            "min_rating": min_rating,
            "max_rating": max_rating
        }
    )

@app.get("/topic", response_class=HTMLResponse)
def topic_wise(
    request: Request,
    tag: str = ""
):
    url = "https://codeforces.com/api/problemset.problems"
    response = requests.get(url)
    data = response.json()

    problems = data["result"]["problems"]

    # Collect all unique tags
    all_tags = set()
    for p in problems:
        for t in p.get("tags", []):
            all_tags.add(t)

    all_tags = sorted(list(all_tags))

    filtered = []
    if tag:
        filtered = [p for p in problems if tag in p.get("tags", [])]

    return templates.TemplateResponse(
        "topic.html",
        {
            "request": request,
            "problems": filtered[:25],
            "all_tags": all_tags,
            "selected_tag": tag
        }
    )
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

#         if min_rating <= rating <= max_rating:
#             if tag == "" or tag in tags:
#                 filtered.append(problem)

#     sheet = random.sample(filtered, min(count, len(filtered)))

#     return templates.TemplateResponse(
#         "problems.html",
#         {
#             "request": request,
#             "problems": sheet,
#             "min_rating": min_rating,
#             "max_rating": max_rating,
#             "tag": tag,
#             "count": count
#         }
#     )



# from fastapi import FastAPI, Request, Form, Depends
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates
# from fastapi.staticfiles import StaticFiles
# from sqlalchemy.orm import Session
# from passlib.context import CryptContext
# from starlette.middleware.sessions import SessionMiddleware
# from app.routes.home import router as home_router
# import random
# import requests

# import models
# from database import engine, SessionLocal
# from authlib.integrations.starlette_client import OAuth
# import os
# # Create tables
# models.Base.metadata.create_all(bind=engine)

# app = FastAPI()
# app.add_middleware(SessionMiddleware, secret_key="super-secret-key")
# # Mount static files
# app.mount("/static", StaticFiles(directory="static"), name="static")
# oauth = OAuth()

# oauth.register(
#     name="google",
#     client_id="YOUR_GOOGLE_CLIENT_ID",
#     client_secret="YOUR_GOOGLE_CLIENT_SECRET",
#     server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
#     client_kwargs={
#         "scope": "openid email profile"
#     }
# )
# from fastapi.responses import RedirectResponse

# @app.get("/login/google")
# async def login_google(request: Request):
#     redirect_uri = request.url_for("auth_google")
#     return await oauth.google.authorize_redirect(request, redirect_uri)

# @app.get("/auth/google")
# async def auth_google(request: Request, db: Session = Depends(get_db)):
#     token = await oauth.google.authorize_access_token(request)
#     user_info = token["userinfo"]

#     google_id = user_info["sub"]
#     email = user_info["email"]
#     name = user_info["name"]

#     user = db.query(models.User).filter(models.User.google_id == google_id).first()

#     if not user:
#         user = models.User(
#             username=name,
#             email=email,
#             google_id=google_id,
#             provider="google"
#         )
#         db.add(user)
#         db.commit()

#     request.session["user"] = user.username
#     return RedirectResponse("/", status_code=303)
# @app.post("/login/codeforces")
# def login_codeforces(
#     request: Request,
#     cf_handle: str = Form(...),
#     db: Session = Depends(get_db)
# ):
#     url = f"https://codeforces.com/api/user.info?handles={cf_handle}"
#     response = requests.get(url)

#     data = response.json()

#     if data["status"] != "OK":
#         return templates.TemplateResponse(
#             "login.html",
#             {"request": request, "error": "Invalid Codeforces Handle"}
#         )

#     user = db.query(models.User).filter(models.User.cf_handle == cf_handle).first()

#     if not user:
#         user = models.User(
#             username=cf_handle,
#             cf_handle=cf_handle,
#             provider="codeforces"
#         )
#         db.add(user)
#         db.commit()

#     request.session["user"] = user.username
#     return RedirectResponse("/", status_code=303)
# # Create tables
# models.Base.metadata.create_all(bind=engine)

# # app = FastAPI()
# # app.add_middleware(SessionMiddleware, secret_key="super-secret-key")
# # # Mount static files
# # app.mount("/static", StaticFiles(directory="static"), name="static")

# # Templates
# templates = Jinja2Templates(directory="app/templates")
# # Password hashing
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # Database dependency
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# @app.get("/")
# def home(request: Request):
#     user = request.session.get("user")
#     return templates.TemplateResponse(
#         "index.html",
#         {
#             "request": request,
#             "user": user
#         }
#     )
# # @app.get("/")
# # def home(request: Request):
# #     return templates.TemplateResponse("index.html", {"request": request})

# # @app.get("/register", response_class=HTMLResponse)
# # def register_page(request: Request):
# #     return templates.TemplateResponse("register.html", {"request": request})


# @app.post("/register", response_class=HTMLResponse)
# def register_user(
#     request: Request,
#     username: str = Form(...),
#     email: str = Form(...),
#     password: str = Form(...),
#     db: Session = Depends(get_db)
# ):
#     # Check if user already exists
#     existing_user = db.query(models.User).filter(
#         (models.User.username == username) | 
#         (models.User.email == email)
#     ).first()

#     if existing_user:
#         return templates.TemplateResponse(
#             "register.html",
#             {
#                 "request": request,
#                 "error": "Username or Email already exists"
#             }
#         )

#     # Hash password
#     hashed_password = pwd_context.hash(password)

#     # Create user
#     new_user = models.User(
#         username=username,
#         email=email,
#         password=hashed_password
#     )

#     db.add(new_user)
#     db.commit()

#     return templates.TemplateResponse(
#         "index.html",
#         {
#             "request": request,
#             "message": "Registration Successful! Please Login."
#         }
#     )

# @app.get("/login", response_class=HTMLResponse)
# def login_page(request: Request):
#     return templates.TemplateResponse("login.html", {"request": request})


# @app.post("/login", response_class=HTMLResponse)
# def login_user(
#     request: Request,
#     username: str = Form(...),
#     password: str = Form(...),
#     db: Session = Depends(get_db)
# ):
#     user = db.query(models.User).filter(
#         models.User.username == username
#     ).first()

#     if not user:
#         return templates.TemplateResponse(
#             "login.html",
#             {"request": request, "error": "Invalid Username"}
#         )

#     if not pwd_context.verify(password, user.password):
#         return templates.TemplateResponse(
#             "login.html",
#             {"request": request, "error": "Invalid Password"}
#         )

#     # Store user in session
#     request.session["user"] = user.username

#     return templates.TemplateResponse(
#         "index.html",
#         {"request": request, "message": "Login Successful!"}
#     )

# @app.get("/logout")
# def logout(request: Request):
#     request.session.clear()
#     return templates.TemplateResponse(
#         "index.html",
#         {"request": request, "message": "Logged out successfully"}
#     )

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

#         if min_rating <= rating <= max_rating:
#             if tag == "" or tag in tags:
#                 filtered.append(problem)

#     sheet = random.sample(filtered, min(count, len(filtered)))

#     return templates.TemplateResponse(
#         "problems.html",
#         {
#             "request": request,
#             "problems": sheet,
#             "min_rating": min_rating,
#             "max_rating": max_rating,
#             "tag": tag,
#             "count": count
#         }
#     )






# # from fastapi import FastAPI, Request, Depends
# # from fastapi.responses import HTMLResponse
# # from fastapi.templating import Jinja2Templates
# # from fastapi.staticfiles import StaticFiles
# # from sqlalchemy.orm import Session
# # from database import engine
# # from models import User
# # from database import SessionLocal
# # from passlib.context import CryptContext
# # from fastapi import Form, Depends

# # pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# # User.metadata.create_all(bind=engine)
# # import random
# # import requests

# # import models
# # from database import engine, SessionLocal

# # models.Base.metadata.create_all(bind=engine)

# # app = FastAPI()

# # app.mount("/static", StaticFiles(directory="static"), name="static")
# # templates = Jinja2Templates(directory="templates")

# # # Dependency
# # def get_db():
# #     db = SessionLocal()
# #     try:
# #         yield db
# #     finally:
# #         db.close()


# # @app.get("/")
# # def home(request: Request):
# #     return templates.TemplateResponse("index.html", {"request": request})

# # @app.get("/problems", response_class=HTMLResponse)
# # def get_problems(
# #     request: Request,
# #     min_rating: int = 800,
# #     max_rating: int = 1500,
# #     tag: str = "",
# #     count: int = 10
# # ):
# #     url = "https://codeforces.com/api/problemset.problems"
# #     response = requests.get(url)
# #     data = response.json()

# #     filtered = []

# #     for problem in data["result"]["problems"]:
# #         rating = problem.get("rating")
# #         tags = problem.get("tags", [])

# #         if rating is None:
# #             continue

# #         if rating >= min_rating and rating <= max_rating:
# #             if tag == "" or tag in tags:
# #                 filtered.append(problem)

# #     # Randomly pick problems
# #     sheet = random.sample(filtered, min(count, len(filtered)))

# #     return templates.TemplateResponse(
# #     "problems.html",
# #     {
# #         "request": request,
# #         "problems": sheet,
# #         "min_rating": min_rating,
# #         "max_rating": max_rating,
# #         "tag": tag,
# #         "count": count
# #     }
# # )


# # # @app.get("/problems", response_class=HTMLResponse)
# # # def get_problems(
# # #     request: Request,
# # #     min_rating: int = 800,
# # #     max_rating: int = 1500,
# # #     tag: str = None
# # # ):
# # #     url = "https://codeforces.com/api/problemset.problems"
# # #     response = requests.get(url)
# # #     data = response.json()

# # #     problems = []

# # #     for problem in data["result"]["problems"]:
# # #         if "rating" in problem:
# # #             if min_rating <= problem["rating"] <= max_rating:
# # #                 if tag:
# # #                     if tag not in problem["tags"]:
# # #                         continue

# # #                 problems.append(problem)

# # #     return templates.TemplateResponse(
# # #         "problems.html",
# # #         {
# # #             "request": request,
# # #             "problems": problems[:50],
# # #             "min_rating": min_rating,
# # #             "max_rating": max_rating,
# # #             "tag": tag
# # #         }
# # #     )