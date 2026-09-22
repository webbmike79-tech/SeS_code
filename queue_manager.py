import sqlite3
import json
import time

DB_FILE = 'ai_task_queue.db'

def setup_database():
    """Initializes the SQLite queue table for the AI tasks."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Statuses will be: 'pending', 'processing', 'completed', 'failed'
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS task_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type TEXT NOT NULL,
            payload TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            created_at REAL NOT NULL,
            processed_at REAL
        )
    ''')
    conn.commit()
    conn.close()

def add_task(task_type, payload_dict):
    """Adds a new task to the local queue."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Convert the Python dictionary payload to a JSON string for SQLite storage
    payload_str = json.dumps(payload_dict)

    cursor.execute('''
        INSERT INTO task_queue (task_type, payload, created_at)
        VALUES (?, ?, ?)
    ''', (task_type, payload_str, time.time()))

    conn.commit()
    conn.close()
    print(f"[Queue] Task '{task_type}' safely stored locally.")
