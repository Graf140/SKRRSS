# backend/database/models.py
from . import get_db_connection
from typing import List, Optional, Dict, Any

def init_db():
    """Создаёт таблицы, если их нет"""
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS schemes (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        description TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS devices (
        id SERIAL PRIMARY KEY,
        scheme_name TEXT NOT NULL REFERENCES schemes(name) ON DELETE CASCADE,
        device_id TEXT NOT NULL,  -- ac1, pc1 и т.д.
        label TEXT NOT NULL,
        type TEXT NOT NULL,       -- antenna, console, pc
        x INT NOT NULL,
        y INT NOT NULL,
        width INT NOT NULL,
        height INT NOT NULL,
        UNIQUE(scheme_name, device_id)
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS device_configs (
        id SERIAL PRIMARY KEY,
        scheme_name TEXT NOT NULL,
        device_id TEXT NOT NULL,
        ip_address TEXT,
        subnet_mask TEXT,
        gateway TEXT,
        dns TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (scheme_name, device_id)
            REFERENCES devices(scheme_name, device_id)
            ON DELETE CASCADE
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

def seed_initial_data():
    """Заполняет БД начальными данными (6 устройств)"""
    conn = get_db_connection()
    cur = conn.cursor()

    # Вставляем схему
    cur.execute("INSERT INTO schemes (name, description) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                ("scheme1", "Раскидываем начало"))

    # Устройства
    devices = [
        ("ac1", "AC 1 (P-448TH)", "antenna", 200, 600, 150, 80),
        ("ac2", "AC 2 (P-448TH)", "antenna", 900, 600, 150, 80),
        ("console_ac1", "Консоль AC 1", "console", 200, 700, 120, 40),
        ("console_ac2", "Консоль AC 2", "console", 900, 700, 120, 40),
        ("pc1", "ПК 1 (потребитель)", "pc", 300, 200, 100, 60),
        ("pc2", "ПК 2 (потребитель)", "pc", 800, 200, 100, 60),
    ]

    for dev_id, label, dev_type, x, y, w, h in devices:
        cur.execute("""
            INSERT INTO devices (scheme_name, device_id, label, type, x, y, width, height)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (scheme_name, device_id) DO NOTHING
        """, ("scheme1", dev_id, label, dev_type, x, y, w, h))

    conn.commit()
    cur.close()
    conn.close()

def get_devices_by_scheme(scheme_name: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM devices WHERE scheme_name = %s", (scheme_name,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_device_config(scheme_name: str, device_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM device_configs
        WHERE scheme_name = %s AND device_id = %s
    """, (scheme_name, device_id))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def save_device_config(scheme_name: str, device_id: str, config: Dict[str, str]) -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor()

    # Удаляем старую запись (если есть)
    cur.execute("""
        DELETE FROM device_configs
        WHERE scheme_name = %s AND device_id = %s
    """, (scheme_name, device_id))

    # Вставляем новую
    cur.execute("""
        INSERT INTO device_configs (scheme_name, device_id, ip_address, subnet_mask, gateway, dns)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING *
    """, (scheme_name, device_id, config["ip_address"], config["subnet_mask"],
          config["gateway"], config["dns"]))

    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return row

def get_all_schemes() -> List[str]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM schemes")
    rows = [row["name"] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return rows