# backend/routes/schemes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict
from datetime import datetime
from ipaddress import IPv4Address, IPv4Network

# === Модели ===
class SchemeObject(BaseModel):
    id: str = Field(..., alias="object_id")
    type: str
    x: int
    y: int
    width: int
    height: int
    clickable: bool = False
    label: str = ""
    status: str = "normal"
    data: Dict[str, Any] = {}


class ObjectClickRequest(BaseModel):
    action: str = "click"


class ObjectClickResponse(BaseModel):
    message: str
    handled: bool
    object_id: str
    timestamp: str


# === Импорты из БД ===
from backend.database.models import (
    get_all_schemes,
    get_scheme_objects,
    get_object_config,
    save_object_config,
    seed_initial_objects
)

router = APIRouter(prefix="/api/schemes", tags=["Schemes"])


@router.get("/list")
async def list_schemes():
    try:
        schemes = get_all_schemes()
        return {"schemes": schemes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{scheme_id}/objects", response_model=List[SchemeObject])
async def get_scheme_objects_endpoint(scheme_id: str):
    try:
        objects = get_scheme_objects(scheme_id)
        if not objects:
            raise HTTPException(status_code=404, detail="Схема не найдена")
        return objects
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{scheme_id}/object/{object_id}", response_model=SchemeObject)
async def get_single_object(scheme_id: str, object_id: str):
    obj = get_object_config(scheme_id, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")
    return obj


@router.post("/{scheme_id}/object/{object_id}/click", response_model=ObjectClickResponse)
async def handle_object_click(scheme_id: str, object_id: str, request: ObjectClickRequest):
    # Проверяем, существует ли объект
    obj = get_object_config(scheme_id, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")

    if not obj["clickable"]:
        raise HTTPException(status_code=400, detail="Объект не кликабельный")

    message = f"Обработка действия '{request.action}' для объекта '{object_id}'"
    return ObjectClickResponse(
        message=message,
        handled=True,
        object_id=object_id,
        timestamp=datetime.now().isoformat()
    )


@router.put("/{scheme_id}/object/{object_id}/validate_and_save", response_model=dict)
async def validate_and_save_ip_config(
    scheme_id: str,
    object_id: str,
    update_data: Dict[str, str]
):
    """
    Принимает IP-конфигурацию, валидирует и сохраняет.
    Ожидает поля: ip_address, subnet_mask, gateway
    """
    # Получаем объект
    obj = get_object_config(scheme_id, object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Объект не найден")

    # Разрешены только для консолей
    if obj["type"] != "console":
        return {"status": "skipped", "message": "Валидация применима только к консолям"}

    # Извлекаем данные
    ip_str = update_data.get("ip_address")
    mask_str = update_data.get("subnet_mask")
    gw_str = update_data.get("gateway")

    if not all([ip_str, mask_str, gw_str]):
        raise HTTPException(status_code=400, detail="Требуются ip_address, subnet_mask, gateway")

    try:
        ip = IPv4Address(ip_str)
        mask = IPv4Address(mask_str)
        gateway = IPv4Address(gw_str)
    except Exception as e:
        return {"status": "error", "message": f"Некорректный IP или маска: {str(e)}"}

    # Определяем, к какой антенне привязана консоль
    if object_id == "console_ac1":
        antenna_id = "ac1"
    elif object_id == "console_ac2":
        antenna_id = "ac2"
    else:
        return {"status": "error", "message": "Неизвестная консоль"}

    # Получаем данные антенны
    antenna = get_object_config(scheme_id, antenna_id)
    if not antenna or not antenna["data"]:
        return {"status": "error", "message": f"Антенна {antenna_id} не настроена"}

    antenna_ip_str = antenna["data"].get("ip")
    if not antenna_ip_str:
        return {"status": "error", "message": f"IP антенны {antenna_id} не задан"}

    try:
        antenna_ip = IPv4Address(antenna_ip_str)
    except Exception:
        return {"status": "error", "message": "Некорректный IP антенны"}

    # Проверка 1: IP антенны должен быть вида 192.168.X.1
    if not (
        str(antenna_ip).startswith("192.168.") and
        int(str(antenna_ip).split(".")[-1]) == 1
    ):
        return {"status": "error", "message": "IP антенны должен быть вида 192.168.X.1"}

    # Формируем подсеть антенны
    try:
        antenna_network = IPv4Network(f"{antenna_ip}/{mask}", strict=False)
    except Exception as e:
        return {"status": "error", "message": f"Ошибка при создании подсети антенны: {str(e)}"}

    # Проверка 2: IP консоли должен быть в той же подсети
    if ip not in antenna_network:
        return {
            "status": "error",
            "message": f"IP консоли {ip} не входит в подсеть антенны {antenna_network}"
        }

    # Проверка 3: IP консоли не должен быть равен IP антенны
    if ip == antenna_ip:
        return {"status": "error", "message": "IP консоли не может совпадать с IP антенны"}

    # Проверка 4: Шлюз должен быть IP антенны
    if gateway != antenna_ip:
        return {
            "status": "error",
            "message": f"Шлюз должен быть {antenna_ip}, а не {gateway}"
        }

    # ✅ Всё прошло — сохраняем
    new_data = {
        "ip": str(ip),
        "subnet_mask": str(mask),
        "gateway": str(gateway),
        "dns": update_data.get("dns", "8.8.8.8")
    }
    save_object_config(scheme_id, object_id, new_data)

    return {
        "status": "ok",
        "message": "Конфигурация успешно сохранена",
        "validated_against": str(antenna_ip)
    }

@router.put("/{scheme_id}/object/{object_id}/set_antenna_ip", response_model=dict)
async def set_antenna_ip(
    scheme_id: str,
    object_id: str,
    update_data: Dict[str, str]
):
    if object_id not in ["ac1", "ac2"]:
        raise HTTPException(status_code=400, detail="Только для антенн")

    ip_str = update_data.get("ip")
    if not ip_str:
        raise HTTPException(status_code=400, detail="Требуется IP")

    # Проверка формата
    try:
        ip = IPv4Address(ip_str)
        parts = str(ip).split(".")
        if not (parts[0] == "192" and parts[1] == "168" and parts[3] == "1"):
            raise ValueError("IP должен быть вида 192.168.X.1")
    except Exception as e:
        return {"status": "error", "message": str(e)}

    save_object_config(scheme_id, object_id, {"ip": str(ip)})
    return {"status": "ok", "message": "IP антенны установлен"}