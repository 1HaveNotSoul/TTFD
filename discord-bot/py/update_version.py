# Система управления версиями обновлений бота
import json
import os
from dataclasses import dataclass

VERSION_FILE = "data/update_version.json"

@dataclass
class Version:
    major: int
    minor: int
    
    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"

def _ensure_dir() -> None:
    """Создать папку data если её нет"""
    os.makedirs(os.path.dirname(VERSION_FILE), exist_ok=True)

def load_version() -> Version:
    """Загрузить текущую версию из файла"""
    _ensure_dir()
    if not os.path.exists(VERSION_FILE):
        v = Version(1, 1)
        save_version(v)
        return v
    
    with open(VERSION_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return Version(
        int(data.get("major", 1)),
        int(data.get("minor", 1))
    )

def bump_version() -> Version:
    """Увеличить версию на 1 (minor) и сохранить"""
    v = load_version()
    v.minor += 1
    save_version(v)
    return v

def save_version(v: Version) -> None:
    """Сохранить версию в файл"""
    _ensure_dir()
    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"major": v.major, "minor": v.minor},
            f,
            ensure_ascii=False,
            indent=2
        )

def get_current_version() -> Version:
    """Получить текущую версию без изменений"""
    return load_version()
