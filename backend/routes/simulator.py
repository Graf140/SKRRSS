# backend/routes/simulator.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services.simulator_service import (
    start_session,
    select_mode,
    configure_console,
    configure_antenna,
    check_web_access
)

router = APIRouter(prefix="/api/session", tags=["Simulator"])

class StartSessionRequest(BaseModel):
    user_id: str

class ModeSelectionRequest(BaseModel):
    band: str
    topology: str

class ConsoleConfigRequest(BaseModel):
    ip_address: str
    subnet_mask: str
    gateway: str

class AntennaConfigRequest(BaseModel):
    ip_address: str
    subnet_mask: str
    gateway: str

@router.post("/start")
async def api_start_session(request: StartSessionRequest):
    return start_session(request.user_id)

@router.post("/{user_id}/select_mode")
async def api_select_mode(user_id: str, request: ModeSelectionRequest):
    return select_mode(user_id, request.band, request.topology)

@router.post("/{user_id}/console/{console_id}/configure")
async def api_configure_console(user_id: str, console_id: str, request: ConsoleConfigRequest):
    return configure_console(user_id, console_id, request.ip_address, request.subnet_mask, request.gateway)

@router.post("/{user_id}/antenna/{antenna_id}/configure")
async def api_configure_antenna(user_id: str, antenna_id: str, request: AntennaConfigRequest):
    return configure_antenna(user_id, antenna_id, request.ip_address, request.subnet_mask, request.gateway)

@router.get("/{user_id}/antenna/{antenna_id}/web_access")
async def api_check_web_access(user_id: str, antenna_id: str):
    return check_web_access(user_id, antenna_id)

@router.get("/available_devices")
async def get_available_devices():
    from backend.config.system_config import ANTENNAS, CONSOLES
    return {
        "antennas": list(ANTENNAS.keys()),
        "consoles": list(CONSOLES.keys())
    }