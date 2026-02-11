#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTFD-Cleaner - Окно раздела "Отчёты"
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import json
from pathlib import Path


class ReportsWindow:
    """Окно раздела отчётов"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("TTFD-Cleaner - Отчёты")
        self.window.geometry("900x700")
        self.window.configure(bg='#1a1d23')
        
        # Путь к конфигу
        self.config_dir = Path("Config")
        self.history_file = self.config_dir / "history.json"
        
        # Создать UI
        self.setup_ui()
        self.load_history()
    
    def setup_ui(self):
        """Создание UI"""
        # Верхняя панель
        top_frame = ttk.Frame(self.window, padding="10")
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Заголовок
        title_label = tk.Label(
            top_frame,
            text="Отчёты и история",
            font=("Segoe UI", 18, "bold"),
            fg='#e4e6eb',
            bg='#1a1d23'
        )
        title_label.pack(side=tk.LEFT)
        
        # Основной контейнер
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # История
        history_frame = ttk.LabelFrame(main_frame, text="История операций", padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.history_text = scrolledtext.ScrolledText(history_frame, height=30, wrap=tk.WORD)
        self.history_text.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Обновить", command=self.load_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Экспорт Baseline", command=self.export_baseline).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Восстановить Baseline", command=self.restore_baseline).pack(side=tk.LEFT, padx=5)
    
    def load_history(self):
        """Загрузка истории"""
        self.history_text.delete(1.0, tk.END)
        
        if not self.history_file.exists():
            self.history_text.insert(tk.END, "История пуста")
            return
        
        try:
            with open(self.history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
            
            for entry in history:
                timestamp = entry.get("timestamp", "Unknown")
                action = entry.get("action", "Unknown")
                details = entry.get("details", "")
                
                self.history_text.insert(tk.END, f"[{timestamp}] {action}\n")
                self.history_text.insert(tk.END, f"  {details}\n\n")
            
            print(f"[OK] Загружено {len(history)} записей истории")
        except Exception as e:
            self.history_text.insert(tk.END, f"Ошибка загрузки истории: {e}")
            print(f"[ERROR] Ошибка загрузки истории: {e}")
    
    def export_baseline(self):
        """Экспорт baseline"""
        print("[INFO] Экспорт baseline...")
        messagebox.showinfo("Информация", "Функция в разработке")
    
    def restore_baseline(self):
        """Восстановление baseline"""
        confirm = messagebox.askyesno(
            "Подтверждение",
            "Восстановить систему из baseline?\n\nЭто отменит изменения автозапуска."
        )
        
        if not confirm:
            return
        
        print("[INFO] Восстановление baseline...")
        messagebox.showinfo("Информация", "Функция в разработке")
