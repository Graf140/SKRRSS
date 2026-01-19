# backend/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from backend.routes.schemes import router as schemes_router
from backend.database.models import init_db, seed_initial_data

app = FastAPI(title="СКРРСС API с БД")

BASE_DIR = Path(__file__).parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# Инициализация БД при старте
@app.on_event("startup")
def startup():
    init_db()
    seed_initial_data()

app.include_router(schemes_router)