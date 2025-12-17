import sqlite3

DB_NAME = "smart_yard.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS occupation_voies (
        voie_id INTEGER PRIMARY KEY,
        status TEXT,
        train_number TEXT,
        last_update TEXT
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS historique_mouvements (
        timestamp TEXT,
        voie_id INTEGER,
        train_number TEXT,
        action TEXT,
        confidence REAL
    )
    """)

    conn.commit()
    conn.close()

