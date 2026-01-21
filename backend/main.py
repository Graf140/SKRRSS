from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from backend.database.models import init_db
from backend.routes.simulator import router as simulator_router  # ← только это

app = FastAPI(title="СКРРСС Симулятор")


@app.on_event("startup")
def startup():
    init_db()

app.include_router(simulator_router)