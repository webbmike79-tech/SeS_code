# SeS AI — Hybrid Offline/Online Assistant

A Python assistant that keeps working with or without an internet connection.
Tasks queue locally in SQLite, a background daemon thread processes them once
you're back online, cloud LLMs are reached through a LiteLLM gateway router
with a local Ollama fallback, and long-term memory persists in a local
ChromaDB vector store.

## Features

- **Offline-first task queue** (SQLite) with a background daemon worker thread
- **Gateway router pattern** — cloud LLM primary, local Ollama fallback when offline
- **Persistent RAG memory** with ChromaDB + Sentence-Transformers (works offline after first run)
- Runs anywhere Python runs; built and tested for PyCharm on Windows

## Project structure

```
├── main.py            # Demo entry point: sets up the DB, starts the daemon, queues sample tasks
├── queue_manager.py   # SQLite queue: setup_database(), add_task()
├── worker.py          # Background daemon: internet check, process_queue(), thread loop
├── memory_bank.py     # Persistent vector memory: learn_information(), recall_relevant_context()
├── hybrid_router.py   # LiteLLM cloud/local router example: hybrid_generate()
├── requirements.txt   # Python dependencies
└── .gitignore         # Python / venv / database / secrets ignores
```

## Quick start

```bash
# 1. Clone the repo
git clone <your-repo-url>
cd <repo>

# 2. Create and activate a virtual environment
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
# source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your cloud API key (used when online)
# Windows (PowerShell):
$env:OPENAI_API_KEY="sk-your-key"
# macOS/Linux:
# export OPENAI_API_KEY="sk-your-key"

# 5. Run the demo
python main.py
```

The demo queues two sample tasks, then lets the background worker process them.
`main.py` uses a 5-second worker interval for testing — in production, set
`start_background_processor(interval_seconds=300)` (5 minutes).

## Configuration

- `OPENAI_API_KEY` — environment variable for cloud LLM calls (used by `hybrid_router.py`).
- `worker.py` → `check_internet()` pings `https://8.8.8.8` to decide whether the queue can be processed.
- `memory_bank.py` stores its vector database in `./ai_memory_db/` (ignored by git).
- `queue_manager.py` stores the task queue in `ai_task_queue.db` (ignored by git).
- For the offline fallback in `hybrid_router.py`, install [Ollama](https://ollama.com) and pull `llama3`.

## Modules

- **queue_manager.py** — `setup_database()` creates the `task_queue` table
  (statuses: `pending`, `processing`, `completed`, `failed`); `add_task()` stores a
  task with a JSON payload.
- **worker.py** — `start_background_processor()` spawns a daemon thread running
  `queue_worker_loop()`; `process_queue()` locks each pending task, executes it
  via `execute_task()`, and marks it `completed` (with the result stored) or
  re-queues it for retry. Tasks get 3 attempts before being marked `failed`.
  `cloud_llm_request` tasks are executed for real through `hybrid_generate()`.
  All output goes through the `logging` module.
- **memory_bank.py** — `learn_information()` saves facts/articles to the persistent
  collection; `recall_relevant_context()` retrieves the most relevant memories to
  inject into an LLM prompt.
- **hybrid_router.py** — `hybrid_generate()` tries the cloud model first and falls
  back to local `ollama/llama3` on timeout or failure.

## License

No license file is included yet — add one (e.g. MIT) before publishing if you want
others to reuse this code.
