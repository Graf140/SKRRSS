# backend/routes/schemes.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

# === Модели данных ===
class ClickableArea(BaseModel):
    id: str = Field(..., alias="device_id")
    x: int
    y: int
    width: int
    height: int
    label: str
    type: str

class DeviceIPs(BaseModel):
    ip_address: str
    subnet_mask: str
    gateway: str
    dns: str = "8.8.8.8"

class DeviceIPResponse(BaseModel):
    device_id: str
    scheme_id: str
    ips: DeviceIPs
    saved_at: str  # ISO 8601 строка

# === Импорты из БД ===
from backend.database.models import (
    get_all_schemes,
    get_devices_by_scheme,
    get_device_config,
    save_device_config
)

# === Роутер ===
router = APIRouter(prefix="/api/schemes", tags=["Schemes"])

# === Эндпоинты ===
@router.get("/list")
async def list_schemes():
    try:
        schemes = get_all_schemes()
        return {"schemes": schemes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{scheme_id}/areas", response_model=List[ClickableArea])
async def get_scheme_areas(scheme_id: str):
    try:
        devices = get_devices_by_scheme(scheme_id)
        if not devices:
            raise HTTPException(status_code=404, detail="Схема не найдена")
        # Pydantic автоматически преобразует dict → ClickableArea
        return devices
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{scheme_id}/device/{device_id}/ips", response_model=DeviceIPResponse)
async def get_device_ips(scheme_id: str, device_id: str):
    config = get_device_config(scheme_id, device_id)
    if not config:
        raise HTTPException(status_code=404, detail="Конфигурация не найдена")
    return DeviceIPResponse(
        device_id=device_id,
        scheme_id=scheme_id,
        ips=DeviceIPs(
            ip_address=config["ip_address"],
            subnet_mask=config["subnet_mask"],
            gateway=config["gateway"],
            dns=config["dns"] or "8.8.8.8"
        ),
        saved_at=config["updated_at"].isoformat()
    )

@router.post("/{scheme_id}/device/{device_id}/set_ips", response_model=DeviceIPResponse)
async def set_device_ips(scheme_id: str, device_id: str, ips: DeviceIPs):
    # Проверяем, существует ли устройство
    devices = get_devices_by_scheme(scheme_id)
    if not any(d["device_id"] == device_id for d in devices):
        raise HTTPException(status_code=404, detail="Устройство не найдено")

    config_row = save_device_config(scheme_id, device_id, ips.dict())
    return DeviceIPResponse(
        device_id=device_id,
        scheme_id=scheme_id,
        ips=ips,
        saved_at=config_row["updated_at"].isoformat()
    )