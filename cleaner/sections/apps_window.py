#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTFD-Cleaner - Окно раздела "Приложения"
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import json
import threading
import sys
from pathlib import Path
from datetime import datetime


class AppsWindow:
    """Окно раздела приложений"""
    
    def __init__(self, parent, is_admin):
        self.window = tk.Toplevel(parent)
        self.window.title("TTFD-Cleaner - Приложения")
        self.window.geometry("900x700")
        self.window.configure(bg='#1a1d23')
        
        # Путь к CLI
        if getattr(sys, 'frozen', False):
            # Запущено из exe
            base_path = Path(sys._MEIPASS)
        else:
            # Запущено из Python
            base_path = Path(__file__).parent.parent
        self.cli_path = base_path / "TTFD.Cleaner.Cli.exe"
        self.is_admin = is_admin
        self.apps_list = []
        
        # Создать UI
        self.setup_ui()
    
    def setup_ui(self):
        """Создание UI"""
        # Верхняя панель
        top_frame = ttk.Frame(self.window, padding="10")
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Заголовок
        title_label = tk.Label(
            top_frame,
            text="Управление приложениями",
            font=("Segoe UI", 18, "bold"),
            fg='#e4e6eb',
            bg='#1a1d23'
        )
        title_label.pack(side=tk.LEFT)
        
        # Основной контейнер
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Таблица приложений
        columns = ("name", "publisher", "size")
        self.apps_tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=25)
        
        self.apps_tree.heading("name", text="Название")
        self.apps_tree.heading("publisher", text="Издатель")
        self.apps_tree.heading("size", text="Размер")
        
        self.apps_tree.column("name", width=400)
        self.apps_tree.column("publisher", width=300)
        self.apps_tree.column("size", width=100)
        
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.apps_tree.yview)
        self.apps_tree.configure(yscrollcommand=scrollbar.set)
        
        self.apps_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопки
        btn_frame = ttk.Frame(self.window, padding="10")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Обновить", command=self.load_apps).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить UWP", command=self.remove_uwp_app).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Открыть 'Приложения'", command=self.open_apps_settings).pack(side=tk.LEFT, padx=5)
        
        # Предупреждение
        if not self.is_admin:
            warning_label = tk.Label(
                btn_frame,
                text="⚠️ Требуются права администратора",
                font=("Segoe UI", 10),
                fg='#ff9800',
                bg='#1a1d23'
            )
            warning_label.pack(side=tk.LEFT, padx=10)
    
    def load_apps(self):
        """Загрузка списка приложений"""
        if not self.is_admin:
            messagebox.showwarning("Предупреждение", "Требуются права администратора!")
            return
        
        print("[INFO] Загрузка приложений...")
        messagebox.showinfo("Информация", "Функция в разработке")
    
    def remove_uwp_app(self):
        """Удаление UWP приложения"""
        if not self.is_admin:
            messagebox.showwarning("Предупреждение", "Требуются права администратора!")
            return
        
        messagebox.showinfo("Информация", "Функция в разработке")
    
    def open_apps_settings(self):
        """Открытие настроек приложений Windows"""
        try:
            subprocess.Popen(["ms-settings:appsfeatures"])
            print("[OK] Открыты настройки приложений")
        except Exception as e:
            print(f"[ERROR] Ошибка открытия настроек: {e}")
