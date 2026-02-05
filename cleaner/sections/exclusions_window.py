#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTFD-Cleaner - Окно раздела "Исключения"
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json
from pathlib import Path


class ExclusionsWindow:
    """Окно раздела исключений"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("TTFD-Cleaner - Исключения")
        self.window.geometry("800x600")
        self.window.configure(bg='#1a1d23')
        
        # Путь к конфигу
        self.config_dir = Path("Config")
        self.config_file = self.config_dir / "config.json"
        
        # Создать UI
        self.setup_ui()
        self.load_exclusions()
    
    def setup_ui(self):
        """Создание UI"""
        # Верхняя панель
        top_frame = ttk.Frame(self.window, padding="10")
        top_frame.pack(side=tk.TOP, fill=tk.X)
        
        # Заголовок
        title_label = tk.Label(
            top_frame,
            text="Исключения (blacklist)",
            font=("Segoe UI", 18, "bold"),
            fg='#e4e6eb',
            bg='#1a1d23'
        )
        title_label.pack(side=tk.LEFT)
        
        # Основной контейнер
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Список исключений
        list_frame = ttk.LabelFrame(main_frame, text="Исключённые пути", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.exclusions_listbox = tk.Listbox(list_frame, height=20)
        self.exclusions_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Добавление
        add_frame = ttk.Frame(main_frame)
        add_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(add_frame, text="Путь:").pack(side=tk.LEFT, padx=5)
        self.exclusion_entry = ttk.Entry(add_frame, width=60)
        self.exclusion_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(add_frame, text="Добавить", command=self.add_exclusion).pack(side=tk.LEFT, padx=5)
        
        # Кнопки
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Удалить", command=self.remove_exclusion).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Сохранить", command=self.save_exclusions).pack(side=tk.LEFT, padx=5)
    
    def load_exclusions(self):
        """Загрузка исключений"""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                    exclusions = config.get("exclusions", [])
                    
                    for path in exclusions:
                        self.exclusions_listbox.insert(tk.END, path)
            except Exception as e:
                print(f"[ERROR] Ошибка загрузки исключений: {e}")
    
    def add_exclusion(self):
        """Добавление исключения"""
        path = self.exclusion_entry.get().strip()
        if not path:
            messagebox.showwarning("Предупреждение", "Введите путь!")
            return
        
        self.exclusions_listbox.insert(tk.END, path)
        self.exclusion_entry.delete(0, tk.END)
        print(f"[OK] Добавлено исключение: {path}")
    
    def remove_exclusion(self):
        """Удаление исключения"""
        selection = self.exclusions_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите элемент!")
            return
        
        path = self.exclusions_listbox.get(selection[0])
        self.exclusions_listbox.delete(selection[0])
        print(f"[OK] Удалено исключение: {path}")
    
    def save_exclusions(self):
        """Сохранение исключений"""
        exclusions = list(self.exclusions_listbox.get(0, tk.END))
        
        # Создать папку Config если не существует
        self.config_dir.mkdir(exist_ok=True)
        
        config = {"exclusions": exclusions}
        
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"[OK] Сохранено {len(exclusions)} исключений")
            messagebox.showinfo("Успех", "Исключения сохранены!")
        except Exception as e:
            print(f"[ERROR] Ошибка сохранения: {e}")
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")
