# backend/services/simulator_service.py
from typing import Optional, Dict, Any
import re
from backend.database.repositories import (
    create_user_session,
    get_user_session,
    update_session_field,
    update_console_config,
    update_antenna_config
)
from ipaddress import IPv4Address, IPv4Network
from backend.config.system_config import ANTENNAS, CONSOLES


def start_session(user_id: str) -> dict:
    create_user_session(user_id)
    return {"status": "ok", "message": "Сессия создана"}


def select_mode(user_id: str, band: str, topology: str) -> dict:
    session = get_user_session(user_id)
    if not session:
        return {"status": "error", "message": "Сессия не найдена"}
    if band != "C":
        return {"status": "error", "message": "Доступен только С-диапазон"}
    if topology != "point-to-point":
        return {"status": "error", "message": "Доступна только топология точка-точка"}

    update_session_field(user_id, "selected_band", "C")
    update_session_field(user_id, "selected_topology", "point-to-point")
    return {"status": "ok", "message": "Режим выбран. Консоли активированы."}


def configure_console(user_id: str, console_id: str, ip: str, mask: str) -> dict:
    session = get_user_session(user_id)
    if not session:
        return {"status": "error", "message": "Сессия не найдена"}
    if console_id not in CONSOLES:
        return {"status": "error", "message": f"Неизвестная консоль: {console_id}"}

    config = {
        "ip": ip,
        "subnet_mask": mask,
    }
    update_console_config(user_id, console_id, config)
    return {"status": "ok", "message": f"Конфигурация консоли {console_id} сохранена"}


def validate_console_config(console_cfg: dict, antenna_id: str) -> dict:
    try:
        ip = IPv4Address(console_cfg["ip"])
        mask = IPv4Address(console_cfg["subnet_mask"])
    except Exception:
        return {"valid": False, "error": "Консоль настроена некорректно: неверный формат IP-адреса или маски"}

    try:
        network = IPv4Network(f"192.168.222.0/{mask}", strict=False)
        if ip not in network:
            return {"valid": False, "error": f"IP консоли ({ip}) не принадлежит подсети 192.168.222.0/{mask}"}
    except Exception:
        return {"valid": False, "error": "Некорректная маска подсети у консоли"}

    forbidden_ips = {
        IPv4Address("192.168.222.0"),
        IPv4Address("192.168.222.1"),
        IPv4Address("192.168.222.222"),
        IPv4Address("192.168.222.255")
    }

    if ip in forbidden_ips:
        return {"valid": False, "error": "IP консоли не может быть сетевым, широковещательным, адресом управления или зарезервированным"}


    return {"valid": True}





def configure_antenna(user_id: str, antenna_id: str, ip: str, mask: str) -> dict:
    if antenna_id not in ANTENNAS:
        return {"status": "error", "message": f"Неизвестная антенна: {antenna_id}"}

    session = get_user_session(user_id)
    if not session:
        return {"status": "error", "message": "Сессия не найдена"}

    related_console = None
    for cons_id, ant_id in CONSOLES.items():
        if ant_id == antenna_id:
            related_console = cons_id
            break

    if not related_console:
        return {"status": "error", "message": "Нет консоли для этой антенны"}

    console_cfg = (session.get("console_configs") or {}).get(related_console)
    if not console_cfg:
        return {"status": "error", "message": "Сначала настройте консоль!"}

    validation = validate_console_config(console_cfg, antenna_id)
    if not validation["valid"]:
        return {"status": "error", "message": validation["error"]}

    expected_ip = ANTENNAS[antenna_id]["fixed_ip"]
    if ip != expected_ip:
        return {
            "status": "error",
            "message": f"IP антенны должен быть {expected_ip}, введено: {ip}"
        }

    try:
        IPv4Address(mask)
    except Exception:
        return {
            "status": "error",
            "message": "Маска подсети должна быть корректным IP-адресом (например, 255.255.255.0)"
        }

    config = {"ip": ip, "subnet_mask": mask}
    update_antenna_config(user_id, antenna_id, config)
    return {"status": "ok", "message": "Антенна успешно настроена"}


def can_access_antenna_web(user_id: str, antenna_id: str) -> dict:
    if not user_id or not re.match(r"^[a-zA-Z0-9_-]{5,64}$", user_id):
        return {"allowed": False, "error": "Некорректный идентификатор"}
    session = get_user_session(user_id)
    if not session:
        return {"allowed": False, "error": "Сессия не найдена"}


    related_console = None
    for cons_id, ant_id in CONSOLES.items():
        if ant_id == antenna_id:
            related_console = cons_id
            break

    if not related_console:
        return {"allowed": False, "error": "Нет консоли для этой антенны"}

    console_cfg = (session.get("console_configs") or {}).get(related_console)
    if not console_cfg:
        return {"allowed": False, "error": "Консоль не настроена. Настройте консоль перед доступом к антенне."}

    validation = validate_console_config(console_cfg, antenna_id)
    if not validation["valid"]:
        return {"allowed": False, "error": f"Консоль настроена некорректно: {validation['error']}"}

    return {"allowed": True}