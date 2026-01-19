# backend/main.py
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List
import json

# === Модель зоны ===
class ClickableArea(BaseModel):
    id: str
    x: int
    y: int
    width: int
    height: int
    label: str

# === Приложение ===
app = FastAPI(
    title="СКРРСС Multi-Scheme API",
    description="Поддержка нескольких интерактивных схем"
)

BASE_DIR = Path(__file__).parent
STATIC_SCHEMES_DIR = BASE_DIR / "static" / "schemes"
DATA_SCHEMES_DIR = BASE_DIR / "data" / "schemes"

for d in [STATIC_SCHEMES_DIR, DATA_SCHEMES_DIR]:
    if not d.exists():
        raise RuntimeError(f"Директория не найдена: {d}")

# === Монтируем статику: /static/schemes/... ===
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")

# === Эндпоинт: получение зон для конкретной схемы ===
@app.get("/api/schemes/{scheme_id}/areas", response_model=List[ClickableArea])
async def get_scheme_areas(scheme_id: str):
    """
    Возвращает список кликабельных областей для схемы с заданным ID.
    Ожидает, что существуют:
      - static/schemes/{scheme_id}.png
      - data/schemes/{scheme_id}.json
    """
    json_path = DATA_SCHEMES_DIR / f"{scheme_id}.json"

    if not json_path.exists():
        raise HTTPException(status_code=404, detail=f"Схема '{scheme_id}' не найдена")

    try:
        with open(json_path, encoding="utf-8") as f:
            data = json.load(f)
        return data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Некорректный формат JSON")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка загрузки данных: {str(e)}")


@app.get("/api/schemes/list")
async def list_schemes():
    """
    Возвращает список ID всех доступных схем.
    Определяется по наличию .json файлов в data/schemes/.
    """
    try:
        scheme_ids = [
            f.stem  # без расширения .json
            for f in DATA_SCHEMES_DIR.iterdir()
            if f.is_file() and f.suffix == ".json"
        ]
        return {"schemes": sorted(scheme_ids)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при чтении списка схем: {str(e)}")