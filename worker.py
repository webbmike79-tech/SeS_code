import sqlite3
import json
import time
import threading
import logging
import requests
from queue_manager import DB_FILE
from hybrid_router import hybrid_generate

logger = logging.getLogger(__name__)

MAX_ATTEMPTS = 3


def check_internet():
    """Checks for an active internet connection by pinging Google's DNS."""
    try:
        requests.get("https://8.8.8.8", timeout=2)
        return True
    except requests.ConnectionError:
        return False


def execute_task(task_type, payload):
    """Runs one task and returns its result string.

    cloud_llm_request tasks go through the hybrid router (cloud model with
    local fallback). Unknown task types are logged and skipped.
    """
    if task_type == "cloud_llm_request":
        prompt = payload.get("prompt", "")
        return hybrid_generate(prompt)
    if task_type == "email_alert":
        # TODO: hand off to your real mail sender here.
        to = payload.get("to", "(no recipient)")
        subject = payload.get("subject", "(no subject)")
        logger.info("Email alert queued for %s: %s", to, subject)
        return f"email_alert staged for {to}"
    logger.warning("Unknown task type '%s'; skipping.", task_type)
    return f"unknown task type: {task_type}"


def process_queue():
    """Processes all pending tasks in the queue if online.

    Failed tasks are retried on later passes (up to MAX_ATTEMPTS) with the
    attempt count stored in the database.
    """
    if not check_internet():
        logger.info("Offline. Queue processing paused.")
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

    logger.info("System is Online. Found %d pending task(s).", len(tasks))

    for task in tasks:
        task_id = task['id']
        payload = json.loads(task['payload'])
        attempts = (task['attempts'] or 0) + 1

        # 1. Lock task to prevent duplicate processing
        cursor.execute(
            "UPDATE task_queue SET status = 'processing', attempts = ? WHERE id = ?",
            (attempts, task_id),
        )
        conn.commit()

        logger.info("Processing task %d (Type: %s, attempt %d/%d)...",
                    task_id, task['task_type'], attempts, MAX_ATTEMPTS)

        try:
            # 2. Execute the real task logic
            result = execute_task(task['task_type'], payload)

            # 3. Mark Complete, storing a truncated result
            cursor.execute('''
                UPDATE task_queue
                SET status = 'completed', processed_at = ?, result = ?
                WHERE id = ?
            ''', (time.time(), str(result)[:2000], task_id))
            logger.info("Task %d completed successfully.", task_id)

        except Exception as e:
            # 4. Handle Failure: retry later, or give up after MAX_ATTEMPTS
            if attempts >= MAX_ATTEMPTS:
                cursor.execute(
                    "UPDATE task_queue SET status = 'failed', result = ? WHERE id = ?",
                    (f"failed after {attempts} attempts: {e}", task_id),
                )
                logger.error("Task %d failed permanently after %d attempts: %s",
                             task_id, attempts, e)
            else:
                cursor.execute(
                    "UPDATE task_queue SET status = 'pending', result = ? WHERE id = ?",
                    (f"attempt {attempts} failed, will retry: {e}", task_id),
                )
                logger.warning("Task %d failed (attempt %d/%d), will retry: %s",
                               task_id, attempts, MAX_ATTEMPTS, e)

        conn.commit()

    conn.close()


def queue_worker_loop(interval_seconds):
    """The infinite loop running in the daemon thread."""
    logger.info("Background worker started. Checking queue every %d seconds.", interval_seconds)
    while True:
        try:
            process_queue()
        except Exception as e:
            logger.exception("Error encountered in worker loop: %s", e)

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
