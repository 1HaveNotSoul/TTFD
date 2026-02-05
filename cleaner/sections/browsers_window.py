#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTFD-Cleaner - Окно раздела "Браузеры"
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import json
import threading
import sys
from pathlib import Path
from datetime import datetime


class BrowsersWindow:
    """Окно раздела браузеров"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("TTFD-Cleaner - Браузеры")
        self.window.geometry("800x600")
        self.window.configure(bg='#1a1d23')
        
        # Путь к CLI
        if getattr(sys, 'frozen', False):
            # Запущено из exe
            base_path = Path(sys._MEIPASS)
        else:
            # Запущено из Python
            base_path = Path(__file__).parent.parent
        self.cli_path = base_path / "TTFD.Cleaner.Cli.exe"
        
        # Создать UI
        self.setup_ui()
        self.load_browsers()
    
    def setup_ui(self):
        """Создание UI"""
        # Верхняя панель
        top_frame = ttk.Frame(self.window, padding="10")
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Заголовок
        title_label = tk.Label(
            top_frame,
            text="Управление браузерами",
            font=("Segoe UI", 18, "bold"),
            fg='#e4e6eb',
            bg='#1a1d23'
        )
        title_label.pack(side=tk.LEFT)
        
        # Основной контейнер
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Обнаруженные браузеры
        browsers_frame = ttk.LabelFrame(main_frame, text="Обнаруженные браузеры", padding="10")
        browsers_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.browsers_label = ttk.Label(browsers_frame, text="Загрузка...")
        self.browsers_label.pack(anchor=tk.W)
        
        # Опции очистки
        options_frame = ttk.LabelFrame(main_frame, text="Что очистить", padding="10")
        options_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.browser_clean_vars = {}
        options = [
            ("cache", "Кэш"),
            ("cookies", "Cookies (разлогинит!)"),
            ("history", "История"),
        ]
        
        for opt_id, opt_name in options:
            var = tk.BooleanVar(value=True if opt_id == "cache" else False)
            self.browser_clean_vars[opt_id] = var
            ttk.Checkbutton(options_frame, text=opt_name, variable=var).pack(anchor=tk.W, pady=2)
        
        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(btn_frame, text="Очистить браузеры", command=self.clean_browsers).pack(side=tk.LEFT, padx=5)
        
        # Предупреждение
        warning_label = tk.Label(
            main_frame,
            text="⚠️ Очистка cookies разлогинит вас со всех сайтов!\n⚠️ Закройте браузеры перед очисткой.",
            font=("Segoe UI", 10),
            fg='#ff9800',
            bg='#1a1d23',
            justify=tk.LEFT
        )
        warning_label.pack(anchor=tk.W, pady=10)
        
        # Лог
        log_frame = ttk.LabelFrame(main_frame, text="Лог", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
    
    def load_browsers(self):
        """Загрузка списка браузеров"""
        def task():
            try:
                result = subprocess.run(
                    [str(self.cli_path), "status"],
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    if data.get("success"):
                        system_info = data.get("data", {})
                        browsers = system_info.get("browsers", [])
                        
                        if browsers:
                            self.window.after(0, lambda: self.browsers_label.config(
                                text=f"Найдено: {', '.join(browsers)}"
                            ))
                            self.window.after(0, lambda: self.log(f"[OK] Браузеры: {', '.join(browsers)}"))
                        else:
                            self.window.after(0, lambda: self.browsers_label.config(text="Браузеры не найдены"))
                            self.window.after(0, lambda: self.log("[WARNING] Браузеры не найдены"))
            except Exception as e:
                self.window.after(0, lambda: self.log(f"[ERROR] {e}"))
        
        threading.Thread(target=task, daemon=True).start()
    
    def clean_browsers(self):
        """Очистка браузеров"""
        options = [opt for opt, var in self.browser_clean_vars.items() if var.get()]
        
        if not options:
            messagebox.showwarning("Предупреждение", "Выберите хотя бы одну опцию!")
            return
        
        if "cookies" in options:
            confirm = messagebox.askyesno(
                "Подтверждение",
                "Очистка cookies разлогинит вас со всех сайтов!\n\nПродолжить?"
            )
            if not confirm:
                return
        
        self.log(f"[INFO] Очистка браузеров: {', '.join(options)}")
        messagebox.showinfo("Информация", "Функция в разработке")
    
    def log(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
