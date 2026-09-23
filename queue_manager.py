import sqlite3
import json
import time
import logging

logger = logging.getLogger(__name__)

DB_FILE = 'ai_task_queue.db'


def setup_database():
    """Initializes the SQLite queue table for the AI tasks.

    Also migrates older databases: adds the attempts/result columns if
    they don't exist yet.
    """
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
            processed_at REAL,
            attempts INTEGER DEFAULT 0,
            result TEXT
        )
    ''')

    # Migrate databases created before attempts/result existed
    existing = {row[1] for row in cursor.execute("PRAGMA table_info(task_queue)")}
    if "attempts" not in existing:
        cursor.execute("ALTER TABLE task_queue ADD COLUMN attempts INTEGER DEFAULT 0")
    if "result" not in existing:
        cursor.execute("ALTER TABLE task_queue ADD COLUMN result TEXT")

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
    logger.info("Task '%s' safely stored locally.", task_type)
