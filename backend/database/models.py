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
    CREATE TABLE IF NOT EXISTS user_sessions (
        user_id TEXT PRIMARY KEY,
        selected_band TEXT,
        selected_topology TEXT,
        console_configs JSONB,
        antenna_configs JSONB,
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );
    """)

    conn.commit()
    cur.close()
    conn.close()
