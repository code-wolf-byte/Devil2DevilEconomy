import os

from main import app, run_startup_tasks, start_bot_thread

run_startup_tasks()

if os.getenv("RUN_DISCORD_BOT", "1") == "1":
    start_bot_thread()
