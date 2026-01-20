# backend/database/models.py
import os
from dotenv import load_dotenv
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import List, Optional, Dict, Any
import json
load_dotenv()

def get_db_connection():
    return psycopg2.connect(
        os.getenv("DATABASE_URL"),
        cursor_factory=RealDictCursor
    )

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS schemes (
        name TEXT PRIMARY KEY,
        description TEXT
    );
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS scheme_objects (
        id SERIAL PRIMARY KEY,
        scheme_name TEXT NOT NULL REFERENCES schemes(name) ON DELETE CASCADE,
        object_id TEXT NOT NULL,
        type TEXT NOT NULL,
        x INT NOT NULL,
        y INT NOT NULL,
        width INT NOT NULL,
        height INT NOT NULL,
        clickable BOOLEAN NOT NULL DEFAULT false,
        label TEXT,
        status TEXT DEFAULT 'normal',
        data JSONB,
        UNIQUE(scheme_name, object_id)
    );
    """)

    conn.commit()
    cur.close()
    conn.close()

def seed_initial_objects():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("INSERT INTO schemes (name, description) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                ("scheme1", "Основная схема СКРРСС"))

    objects = [
        # Антенны
        ("ac1", "antenna", 200, 600, 80, 80, True, "AC 1 (P-448TH)", "normal", {}),
        ("ac2", "antenna", 900, 600, 80, 80, True, "AC 2 (P-448TH)", "normal", {}),

        # Консоли
        ("console_ac1", "console", 200, 700, 60, 40, True, "Консоль AC 1", "normal", {}),
        ("console_ac2", "console", 900, 700, 60, 40, True, "Консоль AC 2", "normal", {}),

        # ПК
        ("pc1", "pc", 300, 200, 50, 30, True, "ПК 1 (ВКС)", "normal", {}),
        ("pc2", "pc", 800, 200, 50, 30, True, "ПК 2 (ВКС)", "normal", {}),

        # Кнопки (не имеют IP)
        ("button_range", "button", 50, 100, 200, 40, True, "Выбор диапазона", "normal", {}),
        ("button_topology", "button", 50, 160, 200, 40, True, "Топология сети", "normal", {}),

        # Текст
        ("text_satellite", "text", 500, 50, 150, 30, False, "КА, 77° в.д.\nС-диапазон", "normal", {}),
    ]

    for obj in objects:
        obj_id, typ, x, y, w, h, clickable, label, status, data = obj
        data_json = json.dumps(data, ensure_ascii=False)
        cur.execute("""
            INSERT INTO scheme_objects (
                scheme_name, object_id, type, x, y, width, height,
                clickable, label, status, data
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (scheme_name, object_id) DO UPDATE SET
                type = EXCLUDED.type,
                x = EXCLUDED.x,
                y = EXCLUDED.y,
                width = EXCLUDED.width,
                height = EXCLUDED.height,
                clickable = EXCLUDED.clickable,
                label = EXCLUDED.label,
                status = EXCLUDED.status,
                data = EXCLUDED.data
        """, ("scheme1", obj_id, typ, x, y, w, h, clickable, label, status, data_json))

    conn.commit()
    cur.close()
    conn.close()

def get_all_schemes() -> List[str]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT name FROM schemes")
    rows = [row["name"] for row in cur.fetchall()]
    cur.close()
    conn.close()
    return rows

def get_scheme_objects(scheme_name: str) -> List[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM scheme_objects WHERE scheme_name = %s", (scheme_name,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

def get_object_config(scheme_name: str, object_id: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT * FROM scheme_objects
        WHERE scheme_name = %s AND object_id = %s
    """, (scheme_name, object_id))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row

def save_object_config(scheme_name: str, object_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    conn = get_db_connection()
    cur = conn.cursor()
    data_json = json.dumps(data, ensure_ascii=False)  # ← сериализуем
    cur.execute("""
        UPDATE scheme_objects
        SET data = %s
        WHERE scheme_name = %s AND object_id = %s
        RETURNING *
    """, (data_json, scheme_name, object_id))
    row = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()
    return row