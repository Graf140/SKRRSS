# backend/config/system_config.py
from typing import Dict, List

ANTENNAS = {
    "ac1": {
        "serial_suffix": "15",
        "fixed_ip": "192.168.1.1",
    },
    "ac2": {
        "serial_suffix": "25",
        "fixed_ip": "192.168.2.1",
    }
}

CONSOLES = {f"console_{ant_id}": ant_id for ant_id in ANTENNAS}