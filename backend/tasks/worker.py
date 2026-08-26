"""
Huey Background Task Consumer CLI
Run with: python -m backend.tasks.worker
"""
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.append(str(ROOT_DIR))

from backend.tasks.huey_app import huey
import backend.tasks.worker_tasks  # Import tasks to register them with Huey

if __name__ == "__main__":
    if huey is not None:
        print("⚡ Starting Geo-CashWatch Huey Asynchronous Worker Process...")
        consumer = huey.create_consumer(workers=4, periodic=True)
        consumer.run()
    else:
        print("❌ Huey instance is not available. Exiting.")
        sys.exit(1)
