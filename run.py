import subprocess
import time
import sys
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os

BOT_FILE = "bot.py"

# Полный путь к Python из виртуального окружения
PYTHON_PATH = os.path.join("venv", "Scripts", "python.exe")

class BotReloader(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_bot()

    def start_bot(self):
        print("🔵 Запуск бота...")
        self.process = subprocess.Popen([PYTHON_PATH, BOT_FILE])

    def restart_bot(self):
        print("🟡 Обнаружены изменения — перезапуск бота...")
        if self.process:
            self.process.kill()
            self.process.wait()
        self.start_bot()

    def on_modified(self, event):
        if event.src_path.endswith(BOT_FILE):
            self.restart_bot()


if __name__ == "__main__":
    print("👀 Следим за изменениями в bot.py...")

    event_handler = BotReloader()
    observer = Observer()
    observer.schedule(event_handler, ".", recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.kill()

    observer.join()
