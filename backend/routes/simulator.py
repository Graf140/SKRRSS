# backend/routes/simulator.py
from typing import Dict
from fastapi import Request
from fastapi.responses import HTMLResponse
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.database.repositories import get_user_session
from backend.templating import templates
from backend.services.simulator_service import (
    start_session,
    select_mode,
    configure_console,
    configure_antenna,
    can_access_antenna_web
    # check_web_access
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

class AntennaConfigRequest(BaseModel):
    ip_address: str
    subnet_mask: str

@router.post("/start")
async def api_start_session(request: StartSessionRequest):
    return start_session(request.user_id)

@router.post("/{user_id}/select_mode")
async def api_select_mode(user_id: str, request: ModeSelectionRequest):
    return select_mode(user_id, request.band, request.topology)

@router.post("/{user_id}/console/{console_id}/configure")
async def api_configure_console(user_id: str, console_id: str, request: ConsoleConfigRequest):
    return configure_console(user_id, console_id, request.ip_address, request.subnet_mask)

# @router.post("/{user_id}/antenna/{antenna_id}/configure")
# async def api_configure_antenna(user_id: str, antenna_id: str, request: AntennaConfigRequest):
#     return configure_antenna(user_id, antenna_id, request.ip_address, request.subnet_mask)

# @router.get("/{user_id}/antenna/{antenna_id}/web_access")
# async def api_check_web_access(user_id: str, antenna_id: str):
#     return check_web_access(user_id, antenna_id)

# @router.get("/available_devices")
# async def get_available_devices():
#     from backend.config.system_config import ANTENNAS, CONSOLES
#     return {
#         "antennas": list(ANTENNAS.keys()),
#         "consoles": list(CONSOLES.keys())
#     }


@router.post("/{user_id}/antenna/{antenna_id}/configure")
async def api_configure_antenna(
        user_id: str,
        antenna_id: str,
        request: Dict[str, str]
):
    ip = request.get("ip_address")
    mask = request.get("subnet_mask")

    if not ip or not mask:
        return {"status": "error", "message": "Требуются ip_address и subnet_mask"}

    return configure_antenna(user_id, antenna_id, ip, mask)


@router.get("/web/antenna/{user_id}/{antenna_id}", response_class=HTMLResponse)
async def web_antenna_page(request: Request, user_id: str, antenna_id: str):
    check = can_access_antenna_web(user_id, antenna_id)
    if not check["allowed"]:
        return HTMLResponse(check["error"], status_code=403)

    return templates.TemplateResponse(
        "antenna_config.html",
        {"request": request, "antenna_id": antenna_id, "user_id": user_id}
    )

    return templates.TemplateResponse(
        "antenna_config.html",
        {"request": request, "antenna_id": antenna_id, "user_id": user_id}
    )


@router.get("/{user_id}/antenna/{antenna_id}/status")
async def antenna_status(user_id: str, antenna_id: str):
    session = get_user_session(user_id)
    if not session:
        return {"configured": False}
    antenna_cfg = (session.get("antenna_configs") or {}).get(antenna_id)
    return {"configured": antenna_cfg is not None}