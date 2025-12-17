from database import get_connection
from datetime import datetime

def insert_history(timestamp, voie_id, train_number, action, confidence):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO historique_mouvements
    VALUES (?, ?, ?, ?, ?)
    """, (timestamp, voie_id, train_number, action, confidence))

    conn.commit()
    conn.close()


def update_occupation(voie_id, action, train_number):
    conn = get_connection()
    cursor = conn.cursor()

    if action == "arrival":
        status = "occupée"
    elif action == "departure":
        status = "libre"
        train_number = None
    else:
        status = "anomalie"

    cursor.execute("""
    INSERT OR REPLACE INTO occupation_voies
    VALUES (?, ?, ?, ?)
    """, (voie_id, status, train_number, datetime.now().isoformat()))

    conn.commit()
    conn.close()


def get_all_voies():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM occupation_voies")
    rows = cursor.fetchall()

    conn.close()
    return rows


def get_history():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM historique_mouvements")
    rows = cursor.fetchall()

    conn.close()
    return rows

