# backend/database/repositories.py
import json
from .models import get_db_connection

def create_user_session(user_id: str):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO user_sessions (user_id)
        VALUES (%s)
        ON CONFLICT (user_id) DO NOTHING
    """, (user_id,))
    conn.commit()
    cur.close()
    conn.close()

def get_user_session(user_id: str) -> dict:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_sessions WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None

def update_session_field(user_id: str, field: str, value: any):
    conn = get_db_connection()
    cur = conn.cursor()
    serialized = json.dumps(value) if isinstance(value, dict) else value
    cur.execute(f"""
        UPDATE user_sessions
        SET {field} = %s, updated_at = NOW()
        WHERE user_id = %s
    """, (serialized, user_id))
    conn.commit()
    cur.close()
    conn.close()

def get_user_session(user_id: str) -> dict:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_sessions WHERE user_id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None

def update_console_config(user_id: str, console_id: str, config: dict):
    session = get_user_session(user_id)
    consoles = session.get("console_configs") or {}
    consoles[console_id] = config
    _update_json_field(user_id, "console_configs", consoles)

def update_antenna_config(user_id: str, antenna_id: str, config: dict):
    session = get_user_session(user_id)
    antennas = session.get("antenna_configs") or {}
    antennas[antenna_id] = config
    _update_json_field(user_id, "antenna_configs", antennas)

def _update_json_field(user_id: str, field: str, value: dict):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(f"UPDATE user_sessions SET {field} = %s, updated_at = NOW() WHERE user_id = %s",
                (json.dumps(value), user_id))
    conn.commit()
    cur.close()
    conn.close()