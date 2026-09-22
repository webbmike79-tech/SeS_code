import time
from queue_manager import setup_database, add_task
from worker import start_background_processor

if __name__ == "__main__":
    print("=== Starting Hybrid AI Offline/Online System ===\n")

    # 1. Initialize the SQLite Database
    setup_database()

    # 2. Start the background thread
    # (Set to 5 seconds here for testing. In production, 300 seconds / 5 mins is ideal)
    start_background_processor(interval_seconds=5)

    # 3. Simulate application usage
    print("\n[Main App] Simulating user adding tasks while 'offline'...")
    add_task("cloud_llm_request", {"prompt": "Analyze the latest tech market trends", "model": "gpt-4o"})
    time.sleep(1)
    add_task("email_alert", {"to": "mike.webb@example.com", "subject": "Daily Status Update"})

    print("\n[Main App] The main application thread is now free to handle other UI/Logic.")
    print("[Main App] Waiting to let the background worker process the database queue...\n")

    try:
        # Keep the main application alive so the background thread can run.
        # It will run for 15 seconds, allowing the queue worker to fire a few times.
        for i in range(15):
            time.sleep(1)

        print("\n[Main App] Demo complete. Shutting down gracefully.")

    except KeyboardInterrupt:
        print("\n[Main App] Force shut down via keyboard interrupt.")
