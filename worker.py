import sqlite3
import json
import time
import threading
import requests
from queue_manager import DB_FILE

def check_internet():
    """Checks for an active internet connection by pinging Google's DNS."""
    try:
        requests.get("https://8.8.8.8", timeout=2)
        return True
    except requests.ConnectionError:
        return False

def process_queue():
    """Processes all pending tasks in the queue if online."""
    if not check_internet():
        print("[Worker] Offline. Queue processing paused.")
        return

    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Retrieve all pending tasks
    cursor.execute("SELECT * FROM task_queue WHERE status = 'pending'")
    tasks = cursor.fetchall()

    if not tasks:
        # No pending tasks, exit silently
        conn.close()
        return

    print(f"\n[Worker] System is Online. Found {len(tasks)} pending task(s).")

    for task in tasks:
        task_id = task['id']
        payload = json.loads(task['payload'])

        # 1. Lock task to prevent duplicate processing
        cursor.execute("UPDATE task_queue SET status = 'processing' WHERE id = ?", (task_id,))
        conn.commit()

        print(f"  -> [Worker] Processing task {task_id} (Type: {task['task_type']})...")

        try:
            # 2. EXECUTE YOUR CLOUD LLM / API LOGIC HERE
            # Simulating API latency (e.g., reaching out to OpenAI)
            time.sleep(2)

            # 3. Mark Complete
            cursor.execute('''
                UPDATE task_queue
                SET status = 'completed', processed_at = ?
                WHERE id = ?
            ''', (time.time(), task_id))
            print(f"  -> [Worker] Task {task_id} completed successfully.")

        except Exception as e:
            # 4. Handle Failure
            print(f"  -> [Worker] Task {task_id} failed: {e}")
            cursor.execute("UPDATE task_queue SET status = 'failed' WHERE id = ?", (task_id,))

        conn.commit()

    conn.close()

def queue_worker_loop(interval_seconds):
    """The infinite loop running in the daemon thread."""
    print(f"[Daemon] Background worker started. Checking queue every {interval_seconds} seconds.")
    while True:
        try:
            process_queue()
        except Exception as e:
            print(f"[Daemon] Error encountered in worker loop: {e}")

        # Sleep until the next check
        time.sleep(interval_seconds)

def start_background_processor(interval_seconds=300):
    """
    Spawns the background thread.
    daemon=True ensures this thread dies automatically when main.py stops.
    """
    worker_thread = threading.Thread(
        target=queue_worker_loop,
        kwargs={'interval_seconds': interval_seconds},
        daemon=True
    )
    worker_thread.start()
    return worker_thread
