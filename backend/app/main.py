from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import alerts, buses, chat, crowd, dashboard, departure, routes
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.services.transit import seed_database

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = PROJECT_ROOT / "frontend"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_database(db)
    finally:
        db.close()
    yield


app = FastAPI(
    title="PinkRoute AI API",
    version="1.0.0",
    description="XGBoost + PostgreSQL backend for the PinkRoute AI transit assistant.",
    lifespan=lifespan,
)

app.mount("/js", StaticFiles(directory=str(FRONTEND_DIR / "js")), name="js")
app.mount("/css", StaticFiles(directory=str(FRONTEND_DIR / "css")), name="css")
app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR / "assets")), name="assets")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:5500",
        "http://localhost:5500",
        "http://127.0.0.1:8000",
        "null",
    ],
    allow_origin_regex=r"https?://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dashboard.router)
app.include_router(buses.router)
app.include_router(routes.router)
app.include_router(crowd.router)
app.include_router(departure.router)
app.include_router(chat.router)
app.include_router(alerts.router)


@app.get("/")
def root():
    login_file = FRONTEND_DIR / "login.html"
    if login_file.exists():
        return FileResponse(login_file)
    return {"application": "PinkRoute AI", "status": "running"}


@app.get("/dashboard")
def dashboard_page():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"application": "PinkRoute AI", "status": "running"}


@app.get("/health")
def health():
    return {"status": "healthy"}
