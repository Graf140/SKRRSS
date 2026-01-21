# backend/services/simulator_service.py
from typing import Optional, Dict, Any
from backend.database.repositories import (
    create_user_session,
    get_user_session,
    update_session_field,
    update_console_config,
    update_antenna_config
)
from ipaddress import IPv4Address, IPv4Network
from backend.config.system_config import ANTENNAS, CONSOLES

# ANTENNA_SERIALS = {"ac1": "101", "ac2": "102"}
# FIXED_ANTENNA_IPS = {"ac1": "192.168.222.217", "ac2": "192.168.222.217"}
# ALLOWED_GATEWAYS = {
#     "ac1": ["192.168.222.222", "10.0.0.101"],
#     "ac2": ["192.168.222.222", "10.0.0.102"]
# }


def start_session(user_id: str) -> dict:
    create_user_session(user_id)
    return {"status": "ok", "message": "Сессия создана"}


def select_mode(user_id: str, band: str, topology: str) -> dict:
    if band != "C":
        return {"status": "error", "message": "Доступен только С-диапазон"}
    if topology != "point-to-point":
        return {"status": "error", "message": "Доступна только топология точка-точка"}

    update_session_field(user_id, "selected_band", "C")
    update_session_field(user_id, "selected_topology", "point-to-point")
    return {"status": "ok", "message": "Режим выбран. Консоли активированы."}


def configure_console(user_id: str, console_id: str, ip: str, mask: str, gateway: str) -> dict:
    if console_id not in CONSOLES:
        return {"status": "error", "message": f"Неизвестная консоль: {console_id}"}

    config = {
        "ip": ip,
        "subnet_mask": mask,
        "gateway": gateway
    }
    update_console_config(user_id, console_id, config)
    return {"status": "ok", "message": f"Конфигурация консоли {console_id} сохранена"}


def validate_console_config(console_cfg: dict, antenna_id: str) -> dict:
    try:
        ip = IPv4Address(console_cfg["ip"])
        mask = IPv4Address(console_cfg["subnet_mask"])
        gw = IPv4Address(console_cfg["gateway"])
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

    allowed_gws = ANTENNAS[antenna_id]["allowed_gateways"]
    if str(gw) not in allowed_gws:
        return {
            "valid": False,
            "error": f"Неверный шлюз. Допустимые значения: {', '.join(allowed_gws)}"
        }

    return {"valid": True}


def check_web_access(user_id: str, antenna_id: str) -> dict:
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
        return {"status": "error", "message": "Эй, ты ещё не настроил консоль!"}

    validation = validate_console_config(console_cfg, antenna_id)
    if not validation["valid"]:
        return {"status": "error", "message": validation["error"]}

    return {"status": "ok", "message": "Доступ к веб-интерфейсу разрешён"}


def configure_antenna(user_id: str, antenna_id: str, ip: str, mask: str, gateway: str) -> dict:
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

    # Проверка шлюза антенны: должен совпадать с её IP
    if gateway not in ANTENNAS[antenna_id]["allowed_gateways"]:
        allowed = ', '.join(ANTENNAS[antenna_id]["allowed_gateways"])
        return {
            "status": "error",
            "message": f"Шлюз антенны должен быть одним из ({allowed}), указано: {gateway}"
        }

    config = {"ip": ip, "subnet_mask": mask, "gateway": gateway}
    update_antenna_config(user_id, antenna_id, config)
    return {"status": "ok", "message": "Антенна успешно настроена"}