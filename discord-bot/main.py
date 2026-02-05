#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Главный файл запуска Discord бота
Запускает бота из папки py/
"""

import sys
import os

# Добавляем папку py в путь для импорта модулей
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'py'))

# Импортируем и запускаем бота
if __name__ == "__main__":
    from py import bot
    # Бот запускается через bot.py
