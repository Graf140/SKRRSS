# backend/config/system_config.py
from typing import Dict, List

ANTENNAS = {
    "ac1": {
        "serial_suffix": "15",
        "fixed_ip": "192.168.1.1",
        "allowed_gateways": ["192.168.222.222", "10.0.0.115"]
    },
    "ac2": {
        "serial_suffix": "25",
        "fixed_ip": "192.168.2.1",
        "allowed_gateways": ["192.168.222.222", "10.0.0.125"]
    }
}

CONSOLES = {f"console_{ant_id}": ant_id for ant_id in ANTENNAS}