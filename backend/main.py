from fastapi import FastAPI
from backend.database.models import init_db
from backend.routes.simulator import router as simulator_router

app = FastAPI(title="СКРРСС Симулятор")


@app.get("/")
def heal_check():
    return {"status": "я родился"}

@app.on_event("startup")
def startup():
    init_db()

app.include_router(simulator_router)

#uvicorn backend.main:app --reload - для газа