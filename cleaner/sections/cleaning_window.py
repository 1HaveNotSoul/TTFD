#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTFD-Cleaner - Окно раздела "Очистка"
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import json
import threading
import sys
from pathlib import Path
from datetime import datetime


class CleaningWindow:
    """Окно раздела очистки"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("TTFD-Cleaner - Очистка")
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
        
        # Данные
        self.scan_result = None
        
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
            text="Очистка системы",
            font=("Segoe UI", 18, "bold"),
            fg='#e4e6eb',
            bg='#1a1d23'
        )
        title_label.pack(side=tk.LEFT)
        
        # Основной контейнер
        main_container = ttk.Frame(self.window)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Левая панель - категории
        left_frame = ttk.LabelFrame(main_container, text="Категории очистки", padding="10")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 5))
        
        self.clean_vars = {}
        
        # БЕЗОПАСНЫЕ категории
        safe_frame = ttk.LabelFrame(left_frame, text="✅ Безопасные (рекомендуется)", padding="5")
        safe_frame.pack(fill=tk.X, pady=(0, 5))
        
        safe_categories = [
            ("temp", "Временные файлы (%TEMP%)"),
            ("cache", "Кэш приложений"),
            ("thumbnails", "Кэш миниатюр"),
            ("icon-cache", "Кэш иконок"),
            ("shader-cache", "Кэш шейдеров (DirectX)"),
            ("nvidia-cache", "Кэш драйверов NVIDIA"),
            ("amd-cache", "Кэш драйверов AMD"),
            ("intel-cache", "Кэш драйверов Intel"),
        ]
        
        for cat_id, cat_name in safe_categories:
            var = tk.BooleanVar(value=True)
            self.clean_vars[cat_id] = var
            ttk.Checkbutton(safe_frame, text=cat_name, variable=var).pack(anchor=tk.W, pady=1)
        
        # СРЕДНИЕ категории
        medium_frame = ttk.LabelFrame(left_frame, text="⚠️ Средний риск", padding="5")
        medium_frame.pack(fill=tk.X, pady=(0, 5))
        
        medium_categories = [
            ("recycle", "Корзина"),
            ("dumps", "Дампы и отчёты падений"),
            ("logs", "Логи приложений"),
        ]
        
        for cat_id, cat_name in medium_categories:
            var = tk.BooleanVar(value=False)
            self.clean_vars[cat_id] = var
            ttk.Checkbutton(medium_frame, text=cat_name, variable=var).pack(anchor=tk.W, pady=1)
        
        # Кнопки действий
        btn_frame = ttk.Frame(left_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Сканировать", command=self.scan_cleaning).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Очистить", command=self.apply_cleaning).pack(side=tk.LEFT, padx=5)
        
        # Правая панель - результаты
        right_frame = ttk.LabelFrame(main_container, text="Результаты", padding="10")
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 0))
        
        self.result_text = scrolledtext.ScrolledText(right_frame, height=30, wrap=tk.WORD)
        self.result_text.pack(fill=tk.BOTH, expand=True)
    
    def scan_cleaning(self):
        """Сканирование для очистки"""
        categories = [cat for cat, var in self.clean_vars.items() if var.get()]
        
        if not categories:
            messagebox.showwarning("Предупреждение", "Выберите хотя бы одну категорию!")
            return
        
        self.log(f"[INFO] Сканирование: {', '.join(categories)}")
        
        def task():
            try:
                result = subprocess.run(
                    [str(self.cli_path), "scan-cleaning", "--categories", ",".join(categories)],
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    if data.get("success"):
                        self.scan_result = data.get("data", {})
                        self.window.after(0, self.display_scan_result)
                else:
                    self.window.after(0, lambda: self.log(f"[ERROR] CLI вернул код {result.returncode}"))
            except Exception as e:
                self.window.after(0, lambda: self.log(f"[ERROR] {e}"))
        
        threading.Thread(target=task, daemon=True).start()
    
    def display_scan_result(self):
        """Отображение результатов сканирования"""
        if not self.scan_result:
            return
        
        total_size = self.scan_result.get("totalSize", 0)
        total_files = self.scan_result.get("totalFiles", 0)
        
        self.log(f"\n[OK] Найдено файлов: {total_files}")
        self.log(f"[OK] Общий размер: {self.format_size(total_size)}\n")
        
        categories = self.scan_result.get("categories", {})
        for cat_name, cat_data in categories.items():
            files = cat_data.get("files", 0)
            size = cat_data.get("size", 0)
            self.log(f"{cat_name}: {files} файлов, {self.format_size(size)}")
    
    def apply_cleaning(self):
        """Применение очистки"""
        if not self.scan_result:
            messagebox.showwarning("Предупреждение", "Сначала выполните сканирование!")
            return
        
        categories = [cat for cat, var in self.clean_vars.items() if var.get()]
        total_size = self.scan_result.get("totalSize", 0)
        total_files = self.scan_result.get("totalFiles", 0)
        
        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Удалить {total_files} файлов ({self.format_size(total_size)})?\n\nЭто действие необратимо!"
        )
        
        if not confirm:
            return
        
        self.log(f"\n[INFO] Очистка: {', '.join(categories)}")
        
        def task():
            try:
                result = subprocess.run(
                    [str(self.cli_path), "apply-cleaning", "--categories", ",".join(categories), "--yes"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                
                if result.returncode == 0:
                    self.window.after(0, lambda: self.log("[OK] Очистка завершена!"))
                    self.window.after(0, lambda: messagebox.showinfo("Успех", "Очистка завершена!"))
                    self.scan_result = None
                else:
                    self.window.after(0, lambda: self.log(f"[ERROR] CLI вернул код {result.returncode}"))
            except Exception as e:
                self.window.after(0, lambda: self.log(f"[ERROR] {e}"))
        
        threading.Thread(target=task, daemon=True).start()
    
    def log(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.result_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.result_text.see(tk.END)
    
    def format_size(self, size_bytes: int) -> str:
        """Форматирование размера"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
