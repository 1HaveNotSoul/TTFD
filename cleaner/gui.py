#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTFD-Cleaner GUI
Безопасный очиститель и оптимизатор для Windows 7/10/11
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import threading
from datetime import datetime

# UI эффекты
try:
    from ui_effects import UIEffectsManager
    UI_EFFECTS_AVAILABLE = True
except ImportError:
    UI_EFFECTS_AVAILABLE = False

# Константы
def get_base_path():
    """Получить базовый путь (работает для .exe и .py)"""
    if getattr(sys, 'frozen', False):
        # Запущено как .exe (PyInstaller)
        return Path(sys._MEIPASS)
    else:
        # Запущено как .py
        return Path(__file__).parent

BASE_PATH = get_base_path()
CLI_EXE = "TTFD.Cleaner.Cli.exe"
CONFIG_DIR = Path("Config")
VERSION = "1.1.0"

class CleanerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title(f"TTFD-Cleaner v{VERSION}")
        self.root.geometry("1000x650")
        self.root.resizable(True, True)
        
        # UI эффекты (дымный эффект и живые обои)
        self.effects = None
        if UI_EFFECTS_AVAILABLE:
            try:
                self.effects = UIEffectsManager(self.root)
                self.effects.setup(width=1000, height=650)
                self.effects.enable_smoke(True)  # Включить дымный эффект
                # self.effects.enable_background_animation(True)  # Опционально - анимация фона
            except Exception as e:
                print(f"[WARNING] Не удалось инициализировать UI эффекты: {e}")
                self.effects = None
        
        # Стили
        style = ttk.Style()
        style.configure("Warning.TButton", foreground="orange")
        
        # Проверка CLI
        # Ищем CLI в нескольких местах
        possible_paths = [
            BASE_PATH / CLI_EXE,  # Рядом с .exe (PyInstaller)
            Path(CLI_EXE),  # Текущая директория
            Path(__file__).parent / CLI_EXE if not getattr(sys, 'frozen', False) else None  # Рядом с .py
        ]
        
        self.cli_path = None
        for path in possible_paths:
            if path and path.exists():
                self.cli_path = path
                break
        
        if not self.cli_path:
            self.cli_path = Path(CLI_EXE)  # Fallback
        
        self.is_admin = False
        self.system_info = {}
        
        # Данные
        self.scan_result = None
        self.startup_items = []
        self.apps_list = []
        
        # UI
        self.setup_ui()
        self.check_cli()
        self.load_system_info()
    
    def setup_ui(self):
        """Создание интерфейса"""
        # Верхняя панель
        top_frame = ttk.Frame(self.root, padding="10")
        top_frame.pack(side=tk.TOP, fill=tk.X)

        
        # Статус
        self.status_label = ttk.Label(top_frame, text="Загрузка...", font=("Arial", 10))
        self.status_label.pack(side=tk.LEFT)
        
        ttk.Separator(self.root, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10)
        
        # Основной контейнер
        main_container = ttk.Frame(self.root)
        main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Notebook (вкладки)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Вкладки
        self.tab_cleaning = ttk.Frame(self.notebook)
        self.tab_browsers = ttk.Frame(self.notebook)
        self.tab_startup = ttk.Frame(self.notebook)
        self.tab_apps = ttk.Frame(self.notebook)
        self.tab_exclusions = ttk.Frame(self.notebook)
        self.tab_reports = ttk.Frame(self.notebook)
        
        self.notebook.add(self.tab_cleaning, text="Очистка")
        self.notebook.add(self.tab_browsers, text="Браузеры")
        self.notebook.add(self.tab_startup, text="Автозапуск")
        self.notebook.add(self.tab_apps, text="Приложения")
        self.notebook.add(self.tab_exclusions, text="Исключения")
        self.notebook.add(self.tab_reports, text="Отчёты")
        
        # Правая панель - лог
        log_frame = ttk.LabelFrame(main_container, text="Лог событий", padding="5")
        log_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        
        self.log_text = scrolledtext.ScrolledText(log_frame, width=35, height=30, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Заполнение вкладок
        self.setup_cleaning_tab()
        self.setup_browsers_tab()
        self.setup_startup_tab()
        self.setup_apps_tab()
        self.setup_exclusions_tab()
        self.setup_reports_tab()

    
    def setup_cleaning_tab(self):
        """Вкладка очистки"""
        frame = ttk.Frame(self.tab_cleaning, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Категории очистки
        ttk.Label(frame, text="Выберите категории для очистки:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        self.clean_vars = {}
        
        # БЕЗОПАСНЫЕ категории (зелёные)
        safe_frame = ttk.LabelFrame(frame, text="✅ Безопасные (рекомендуется)", padding="5")
        safe_frame.pack(fill=tk.X, pady=(0, 5))
        
        safe_categories = [
            ("temp", "Временные файлы (%TEMP%)"),
            ("cache", "Кэш приложений"),
            ("thumbnails", "Кэш миниатюр (превью изображений)"),
            ("icon-cache", "Кэш иконок"),
            ("shader-cache", "Кэш шейдеров (DirectX)"),
            ("nvidia-cache", "Кэш драйверов NVIDIA"),
            ("amd-cache", "Кэш драйверов AMD"),
            ("intel-cache", "Кэш драйверов Intel"),
            ("store-cache", "Кэш Microsoft Store"),
            ("font-cache", "Кэш шрифтов"),
        ]
        
        for cat_id, cat_name in safe_categories:
            var = tk.BooleanVar(value=True)
            self.clean_vars[cat_id] = var
            ttk.Checkbutton(safe_frame, text=cat_name, variable=var).pack(anchor=tk.W, pady=1)
        
        # СРЕДНИЕ категории (жёлтые)
        medium_frame = ttk.LabelFrame(frame, text="⚠️ Средний риск (требуется осторожность)", padding="5")
        medium_frame.pack(fill=tk.X, pady=(0, 5))
        
        medium_categories = [
            ("recycle", "Корзина"),
            ("dumps", "Дампы и отчёты падений"),
            ("memory-dumps", "Дампы памяти (Minidump)"),
            ("error-reports", "Отчёты об ошибках Windows"),
            ("logs", "Логи приложений"),
            ("windows-search", "Индекс Windows Search (перестроится)"),
            ("delivery-optimization", "Delivery Optimization"),
        ]
        
        for cat_id, cat_name in medium_categories:
            var = tk.BooleanVar(value=False)
            self.clean_vars[cat_id] = var
            ttk.Checkbutton(medium_frame, text=cat_name, variable=var).pack(anchor=tk.W, pady=1)
        
        # ОПАСНЫЕ категории (красные)
        danger_frame = ttk.LabelFrame(frame, text="🔴 Требуется администратор / Высокий риск", padding="5")
        danger_frame.pack(fill=tk.X, pady=(0, 5))
        
        danger_categories = [
            ("windows-update", "Кэш обновлений Windows (откат станет невозможен!)"),
            ("event-logs", "Журналы событий Windows (потеря диагностики)"),
            ("downloads", "Папка Downloads (ОСТОРОЖНО!)"),
        ]
        
        for cat_id, cat_name in danger_categories:
            var = tk.BooleanVar(value=False)
            self.clean_vars[cat_id] = var
            cb = ttk.Checkbutton(danger_frame, text=cat_name, variable=var)
            cb.pack(anchor=tk.W, pady=1)
            if not self.is_admin and cat_id in ["windows-update", "event-logs"]:
                cb.config(state=tk.DISABLED)
        
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        
        # Результаты сканирования
        result_frame = ttk.LabelFrame(frame, text="Результаты сканирования", padding="10")
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.scan_text = scrolledtext.ScrolledText(result_frame, height=10, wrap=tk.WORD, state=tk.DISABLED)
        self.scan_text.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Сканировать", command=self.scan_cleaning).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Очистить", command=self.apply_cleaning).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Выбрать все безопасные", command=self.select_safe_categories).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Снять всё", command=self.deselect_all_categories).pack(side=tk.LEFT, padx=5)

    
    def setup_browsers_tab(self):
        """Вкладка браузеров"""
        frame = ttk.Frame(self.tab_browsers, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Управление браузерами", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Обнаруженные браузеры
        browsers_frame = ttk.LabelFrame(frame, text="Обнаруженные браузеры", padding="10")
        browsers_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.browsers_label = ttk.Label(browsers_frame, text="Загрузка...")
        self.browsers_label.pack(anchor=tk.W)
        
        # Опции очистки
        ttk.Label(frame, text="Что очистить:", font=("Arial", 9, "bold")).pack(anchor=tk.W, pady=(10, 5))
        
        self.browser_clean_vars = {}
        options = [
            ("cache", "Кэш"),
            ("cookies", "Cookies (разлогинит!)"),
            ("history", "История"),
        ]
        
        for opt_id, opt_name in options:
            var = tk.BooleanVar(value=True if opt_id == "cache" else False)
            self.browser_clean_vars[opt_id] = var
            ttk.Checkbutton(frame, text=opt_name, variable=var).pack(anchor=tk.W, pady=2)
        
        ttk.Separator(frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=15)
        
        # Кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Очистить браузеры", command=self.clean_browsers).pack(side=tk.LEFT, padx=5)
        
        # Информация
        info_text = "⚠️ Очистка cookies разлогинит вас со всех сайтов!\n⚠️ Закройте браузеры перед очисткой."
        ttk.Label(frame, text=info_text, foreground="orange").pack(anchor=tk.W, pady=10)

    
    def setup_startup_tab(self):
        """Вкладка автозапуска в стиле Sysinternals Autoruns"""
        # Импортируем новый класс
        from gui_autoruns_style import AutorunsStyleStartupTab
        
        # Создаём Autoruns-style интерфейс
        self.autoruns_tab = AutorunsStyleStartupTab(
            self.tab_startup,
            self.cli_path,
            self.log
        )

    
    def setup_apps_tab(self):
        """Вкладка приложений"""
        frame = ttk.Frame(self.tab_apps, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Управление приложениями", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Таблица приложений
        columns = ("name", "publisher", "size")
        self.apps_tree = ttk.Treeview(frame, columns=columns, show="headings", height=20)
        
        self.apps_tree.heading("name", text="Название")
        self.apps_tree.heading("publisher", text="Издатель")
        self.apps_tree.heading("size", text="Размер")
        
        self.apps_tree.column("name", width=300)
        self.apps_tree.column("publisher", width=250)
        self.apps_tree.column("size", width=100)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.apps_tree.yview)
        self.apps_tree.configure(yscrollcommand=scrollbar.set)
        
        self.apps_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопки
        btn_frame = ttk.Frame(self.tab_apps, padding="10")
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Обновить", command=self.load_apps).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Удалить UWP", command=self.remove_uwp_app).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Открыть 'Приложения'", command=self.open_apps_settings).pack(side=tk.LEFT, padx=5)
        
        # Информация
        if not self.is_admin:
            ttk.Label(btn_frame, text="⚠️ Требуются права администратора", foreground="orange").pack(side=tk.LEFT, padx=10)

    
    def setup_exclusions_tab(self):
        """Вкладка исключений"""
        frame = ttk.Frame(self.tab_exclusions, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Исключения (blacklist)", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # Список исключений
        list_frame = ttk.LabelFrame(frame, text="Исключённые пути", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.exclusions_listbox = tk.Listbox(list_frame, height=15)
        self.exclusions_listbox.pack(fill=tk.BOTH, expand=True)
        
        # Добавление
        add_frame = ttk.Frame(frame)
        add_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(add_frame, text="Путь:").pack(side=tk.LEFT, padx=5)
        self.exclusion_entry = ttk.Entry(add_frame, width=50)
        self.exclusion_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(add_frame, text="Добавить", command=self.add_exclusion).pack(side=tk.LEFT, padx=5)
        
        # Кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Удалить", command=self.remove_exclusion).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Сохранить", command=self.save_exclusions).pack(side=tk.LEFT, padx=5)
    
    def setup_reports_tab(self):
        """Вкладка отчётов"""
        frame = ttk.Frame(self.tab_reports, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="Отчёты и история", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(0, 10))
        
        # История
        history_frame = ttk.LabelFrame(frame, text="История операций", padding="10")
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.history_text = scrolledtext.ScrolledText(history_frame, height=20, wrap=tk.WORD, state=tk.DISABLED)
        self.history_text.pack(fill=tk.BOTH, expand=True)
        
        # Кнопки
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        ttk.Button(btn_frame, text="Обновить", command=self.load_history).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Экспорт Baseline", command=self.export_baseline).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Восстановить Baseline", command=self.restore_baseline).pack(side=tk.LEFT, padx=5)

    
    # === CLI взаимодействие ===
    
    def run_cli(self, args: List[str]) -> Optional[Dict[str, Any]]:
        """Запуск CLI команды"""
        if not self.cli_path.exists():
            self.log("[ERROR] CLI не найден!")
            messagebox.showerror("Ошибка", f"Файл {CLI_EXE} не найден!\n\nСоберите Backend проект.")
            return None
        
        try:
            cmd = [str(self.cli_path)] + args
            result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
            
            if result.returncode != 0:
                self.log(f"[ERROR] CLI вернул код {result.returncode}")
                self.log(result.stderr)
                return None
            
            # Парсинг JSON
            try:
                data = json.loads(result.stdout)
                return data
            except json.JSONDecodeError as e:
                self.log(f"[ERROR] Ошибка парсинга JSON: {e}")
                self.log(f"Вывод: {result.stdout}")
                return None
                
        except Exception as e:
            self.log(f"[ERROR] Ошибка запуска CLI: {e}")
            return None
    
    def check_cli(self):
        """Проверка наличия CLI"""
        if not self.cli_path.exists():
            self.log("[WARNING] CLI не найден! Соберите Backend проект.")
            self.status_label.config(text="⚠️ CLI не найден", foreground="orange")
        else:
            self.log("[OK] CLI найден")
    
    def load_system_info(self):
        """Загрузка информации о системе"""
        def task():
            result = self.run_cli(["status"])
            if result and result.get("success"):
                self.system_info = result.get("data", {})
                self.is_admin = self.system_info.get("isAdmin", False)
                
                # Обновление UI
                self.root.after(0, self.update_system_info_ui)
        
        threading.Thread(target=task, daemon=True).start()

    
    def update_system_info_ui(self):
        """Обновление UI с информацией о системе"""
        win_ver = self.system_info.get("windowsVersion", "Unknown")
        user = self.system_info.get("userName", "Unknown")
        admin_text = "Администратор" if self.is_admin else "Пользователь"
        
        status_text = f"{win_ver} | {user} | {admin_text}"
        self.status_label.config(text=status_text, foreground="green" if self.is_admin else "blue")
        
        # Браузеры
        browsers = self.system_info.get("browsers", [])
        if browsers:
            self.browsers_label.config(text=f"Найдено: {', '.join(browsers)}")
        else:
            self.browsers_label.config(text="Браузеры не найдены")
        
        self.log(f"[OK] Система: {status_text}")
        self.log(f"[OK] Браузеры: {', '.join(browsers) if browsers else 'нет'}")
    
    # === Очистка ===
    
    def scan_cleaning(self):
        """Сканирование для очистки"""
        categories = [cat for cat, var in self.clean_vars.items() if var.get()]
        
        if not categories:
            messagebox.showwarning("Предупреждение", "Выберите хотя бы одну категорию!")
            return
        
        self.log(f"[INFO] Сканирование: {', '.join(categories)}")
        
        def task():
            result = self.run_cli(["scan-cleaning", "--categories", ",".join(categories)])
            if result and result.get("success"):
                self.scan_result = result.get("data", {})
                self.root.after(0, self.display_scan_result)
        
        threading.Thread(target=task, daemon=True).start()
    
    def display_scan_result(self):
        """Отображение результатов сканирования"""
        if not self.scan_result:
            return
        
        self.scan_text.config(state=tk.NORMAL)
        self.scan_text.delete(1.0, tk.END)
        
        total_size = self.scan_result.get("totalSize", 0)
        total_files = self.scan_result.get("totalFiles", 0)
        
        self.scan_text.insert(tk.END, f"Всего файлов: {total_files}\n")
        self.scan_text.insert(tk.END, f"Общий размер: {self.format_size(total_size)}\n\n")
        
        categories = self.scan_result.get("categories", {})
        for cat_name, cat_data in categories.items():
            files = cat_data.get("files", 0)
            size = cat_data.get("size", 0)
            self.scan_text.insert(tk.END, f"{cat_name}:\n")
            self.scan_text.insert(tk.END, f"  Файлов: {files}\n")
            self.scan_text.insert(tk.END, f"  Размер: {self.format_size(size)}\n\n")
        
        self.scan_text.config(state=tk.DISABLED)
        self.log(f"[OK] Сканирование завершено: {total_files} файлов, {self.format_size(total_size)}")

    
    def apply_cleaning(self):
        """Применение очистки"""
        if not self.scan_result:
            messagebox.showwarning("Предупреждение", "Сначала выполните сканирование!")
            return
        
        total_size = self.scan_result.get("totalSize", 0)
        total_files = self.scan_result.get("totalFiles", 0)
        
        # Проверка опасных категорий
        dangerous_selected = []
        categories = [cat for cat, var in self.clean_vars.items() if var.get()]
        
        if "windows-update" in categories:
            dangerous_selected.append("Кэш обновлений Windows (откат обновлений станет невозможен!)")
        if "event-logs" in categories:
            dangerous_selected.append("Журналы событий (потеря диагностики)")
        if "downloads" in categories:
            dangerous_selected.append("Папка Downloads (могут быть важные файлы!)")
        
        warning_text = f"Удалить {total_files} файлов ({self.format_size(total_size)})?\n\n"
        
        if dangerous_selected:
            warning_text += "⚠️ ВНИМАНИЕ! Выбраны опасные категории:\n"
            for item in dangerous_selected:
                warning_text += f"  • {item}\n"
            warning_text += "\n"
        
        warning_text += "Это действие необратимо!"
        
        confirm = messagebox.askyesno("Подтверждение", warning_text)
        
        if not confirm:
            return
        
        self.log(f"[INFO] Очистка: {', '.join(categories)}")
        
        def task():
            result = self.run_cli(["apply-cleaning", "--categories", ",".join(categories), "--yes"])
            if result and result.get("success"):
                self.root.after(0, lambda: self.log("[OK] Очистка завершена!"))
                self.root.after(0, lambda: messagebox.showinfo("Успех", "Очистка завершена!"))
                self.scan_result = None
        
        threading.Thread(target=task, daemon=True).start()
    
    def select_safe_categories(self):
        """Выбрать все безопасные категории"""
        safe_cats = ["temp", "cache", "thumbnails", "icon-cache", "shader-cache", 
                     "nvidia-cache", "amd-cache", "intel-cache", "store-cache", "font-cache"]
        for cat in safe_cats:
            if cat in self.clean_vars:
                self.clean_vars[cat].set(True)
        self.log("[INFO] Выбраны все безопасные категории")
    
    def deselect_all_categories(self):
        """Снять все галочки"""
        for var in self.clean_vars.values():
            var.set(False)
        self.log("[INFO] Все категории сняты")
    
    # === Браузеры ===
    
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

    
    # === Автозапуск ===
    
    def load_startup_items(self):
        """Загрузка элементов автозапуска"""
        self.log("[INFO] Загрузка автозапуска...")
        
        def task():
            result = self.run_cli(["list-startup"])
            if result and result.get("success"):
                self.startup_items = result.get("data", [])
                self.root.after(0, self.display_startup_items)
        
        threading.Thread(target=task, daemon=True).start()
    
    def display_startup_items(self):
        """Отображение элементов автозапуска (группировка по категориям)"""
        # Очистка
        for item in self.startup_tree.get_children():
            self.startup_tree.delete(item)
        
        # Группировка по типам
        categories = {}
        for item in self.startup_items:
            item_type = item.get("type", "Unknown")
            if item_type not in categories:
                categories[item_type] = []
            categories[item_type].append(item)
        
        # Отображение по категориям
        for category, items in sorted(categories.items()):
            # Создать родительский узел категории
            category_id = self.startup_tree.insert("", tk.END, text=f"{category} ({len(items)})", open=True)
            
            for item in items:
                name = item.get("name", "Unknown")
                location = item.get("location", "")
                enabled = "Включен" if item.get("enabled", False) else "Отключен"
                item_type = item.get("type", "Unknown")
                is_protected = item.get("isSystemProtected", False)
                
                # Определить цвет
                tag = "normal"
                if is_protected:
                    tag = "protected"
                elif "Microsoft" in name or "Windows" in name:
                    tag = "microsoft"
                elif not item.get("enabled", True):
                    tag = "disabled"
                
                # Добавить элемент
                self.startup_tree.insert(category_id, tk.END, 
                                       values=(name, item_type, location, enabled),
                                       tags=(tag,))
        
        self.log(f"[OK] Загружено {len(self.startup_items)} элементов автозапуска")
    
    def filter_startup_items(self):
        """Фильтрация элементов автозапуска"""
        # Перезагрузить с фильтрами
        self.load_startup_items()
    
    def export_startup(self):
        """Экспорт списка автозапуска в TXT"""
        if not self.startup_items:
            messagebox.showwarning("Предупреждение", "Сначала загрузите список автозапуска!")
            return
        
        try:
            filename = f"startup_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, "w", encoding="utf-8") as f:
                f.write("TTFD-Cleaner - Экспорт автозапуска\n")
                f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                
                # Группировка по типам
                categories = {}
                for item in self.startup_items:
                    item_type = item.get("type", "Unknown")
                    if item_type not in categories:
                        categories[item_type] = []
                    categories[item_type].append(item)
                
                for category, items in sorted(categories.items()):
                    f.write(f"\n{category} ({len(items)} элементов)\n")
                    f.write("-" * 80 + "\n")
                    for item in items:
                        name = item.get("name", "Unknown")
                        location = item.get("location", "")
                        enabled = "Включен" if item.get("enabled", False) else "Отключен"
                        protected = " [ЗАЩИЩЕНО]" if item.get("isSystemProtected", False) else ""
                        f.write(f"  {name}{protected}\n")
                        f.write(f"    Статус: {enabled}\n")
                        f.write(f"    Путь: {location}\n\n")
            
            self.log(f"[OK] Экспорт сохранён: {filename}")
            messagebox.showinfo("Успех", f"Экспорт сохранён:\n{filename}")
        except Exception as e:
            self.log(f"[ERROR] Ошибка экспорта: {e}")
            messagebox.showerror("Ошибка", f"Не удалось экспортировать: {e}")
    
    def toggle_startup(self, enable: bool):
        """Включение/отключение автозапуска"""
        selection = self.startup_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите элемент!")
            return
        
        item_idx = self.startup_tree.index(selection[0])
        item = self.startup_items[item_idx]
        item_id = item.get("id", "")
        
        action = "включение" if enable else "отключение"
        self.log(f"[INFO] {action.capitalize()} автозапуска: {item.get('name')}")
        
        def task():
            result = self.run_cli(["set-startup", "--id", item_id, "--enabled", str(enable).lower()])
            if result and result.get("success"):
                self.root.after(0, lambda: self.log(f"[OK] {action.capitalize()} выполнено"))
                self.root.after(0, self.load_startup_items)
        
        threading.Thread(target=task, daemon=True).start()
    
    def disable_all_third_party(self):
        """Отключить все сторонние приложения (не Microsoft)"""
        if not self.startup_items:
            messagebox.showwarning("Предупреждение", "Сначала загрузите список автозапуска!")
            return
        
        # Найти все сторонние элементы (не Microsoft, не защищённые)
        third_party = []
        for item in self.startup_items:
            name = item.get("name", "")
            is_protected = item.get("isSystemProtected", False)
            is_enabled = item.get("enabled", False)
            
            # Пропустить защищённые и уже отключённые
            if is_protected or not is_enabled:
                continue
            
            # Пропустить Microsoft/Windows
            if "Microsoft" in name or "Windows" in name:
                continue
            
            third_party.append(item)
        
        if not third_party:
            messagebox.showinfo("Информация", "Нет сторонних приложений для отключения")
            return
        
        # Предупреждение
        warning_text = f"Отключить {len(third_party)} сторонних приложений?\n\n"
        warning_text += "Будут отключены:\n"
        for item in third_party[:5]:  # Показать первые 5
            warning_text += f"  - {item.get('name', 'Unknown')}\n"
        if len(third_party) > 5:
            warning_text += f"  ... и ещё {len(third_party) - 5}\n"
        warning_text += "\nЭто действие можно отменить вручную."
        
        confirm = messagebox.askyesno("Подтверждение", warning_text)
        if not confirm:
            return
        
        self.log(f"[INFO] Массовое отключение {len(third_party)} сторонних приложений...")
        
        def task():
            success_count = 0
            error_count = 0
            
            for item in third_party:
                item_id = item.get("id", "")
                item_name = item.get("name", "Unknown")
                
                result = self.run_cli(["set-startup", "--id", item_id, "--enabled", "false"])
                if result and result.get("success"):
                    success_count += 1
                    self.root.after(0, lambda n=item_name: self.log(f"[OK] Отключено: {n}"))
                else:
                    error_count += 1
                    self.root.after(0, lambda n=item_name: self.log(f"[ERROR] Ошибка: {n}"))
            
            # Финальное сообщение
            final_msg = f"Отключено: {success_count}, Ошибок: {error_count}"
            self.root.after(0, lambda: self.log(f"[OK] {final_msg}"))
            self.root.after(0, lambda: messagebox.showinfo("Готово", final_msg))
            self.root.after(0, self.load_startup_items)
        
        threading.Thread(target=task, daemon=True).start()
    
    def disable_selected_category(self):
        """Отключить все элементы в выбранной категории"""
        if not self.startup_items:
            messagebox.showwarning("Предупреждение", "Сначала загрузите список автозапуска!")
            return
        
        selection = self.startup_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите категорию или элемент!")
            return
        
        # Получить выбранный элемент
        selected_item = selection[0]
        parent = self.startup_tree.parent(selected_item)
        
        # Если выбран элемент (не категория), получить его родителя
        if parent:
            category_item = parent
        else:
            category_item = selected_item
        
        # Получить название категории
        category_text = self.startup_tree.item(category_item, "text")
        category_name = category_text.split(" (")[0]  # Убрать счётчик
        
        # Найти все элементы этой категории
        category_items = []
        for item in self.startup_items:
            item_type = item.get("type", "Unknown")
            is_protected = item.get("isSystemProtected", False)
            is_enabled = item.get("enabled", False)
            
            # Пропустить защищённые и уже отключённые
            if is_protected or not is_enabled:
                continue
            
            # Проверить соответствие категории
            if item_type == category_name:
                category_items.append(item)
        
        if not category_items:
            messagebox.showinfo("Информация", f"Нет элементов для отключения в категории '{category_name}'")
            return
        
        # Предупреждение
        warning_text = f"Отключить все элементы в категории '{category_name}'?\n\n"
        warning_text += f"Будет отключено: {len(category_items)} элементов\n\n"
        for item in category_items[:5]:  # Показать первые 5
            warning_text += f"  - {item.get('name', 'Unknown')}\n"
        if len(category_items) > 5:
            warning_text += f"  ... и ещё {len(category_items) - 5}\n"
        warning_text += "\nЭто действие можно отменить вручную."
        
        confirm = messagebox.askyesno("Подтверждение", warning_text)
        if not confirm:
            return
        
        self.log(f"[INFO] Массовое отключение категории '{category_name}' ({len(category_items)} элементов)...")
        
        def task():
            success_count = 0
            error_count = 0
            
            for item in category_items:
                item_id = item.get("id", "")
                item_name = item.get("name", "Unknown")
                
                result = self.run_cli(["set-startup", "--id", item_id, "--enabled", "false"])
                if result and result.get("success"):
                    success_count += 1
                    self.root.after(0, lambda n=item_name: self.log(f"[OK] Отключено: {n}"))
                else:
                    error_count += 1
                    self.root.after(0, lambda n=item_name: self.log(f"[ERROR] Ошибка: {n}"))
            
            # Финальное сообщение
            final_msg = f"Отключено: {success_count}, Ошибок: {error_count}"
            self.root.after(0, lambda: self.log(f"[OK] {final_msg}"))
            self.root.after(0, lambda: messagebox.showinfo("Готово", final_msg))
            self.root.after(0, self.load_startup_items)
        
        threading.Thread(target=task, daemon=True).start()

    
    # === Приложения ===
    
    def load_apps(self):
        """Загрузка списка приложений"""
        if not self.is_admin:
            messagebox.showwarning("Предупреждение", "Требуются права администратора!")
            return
        
        self.log("[INFO] Загрузка приложений...")
        
        def task():
            result = self.run_cli(["list-apps"])
            if result and result.get("success"):
                self.apps_list = result.get("data", [])
                self.root.after(0, self.display_apps)
        
        threading.Thread(target=task, daemon=True).start()
    
    def display_apps(self):
        """Отображение приложений"""
        # Очистка
        for item in self.apps_tree.get_children():
            self.apps_tree.delete(item)
        
        # Заполнение
        for app in self.apps_list:
            name = app.get("name", "Unknown")
            publisher = app.get("publisher", "Unknown")
            size = self.format_size(app.get("size", 0))
            
            self.apps_tree.insert("", tk.END, values=(name, publisher, size))
        
        self.log(f"[OK] Загружено {len(self.apps_list)} приложений")
    
    def remove_uwp_app(self):
        """Удаление UWP приложения"""
        if not self.is_admin:
            messagebox.showwarning("Предупреждение", "Требуются права администратора!")
            return
        
        selection = self.apps_tree.selection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите приложение!")
            return
        
        item_idx = self.apps_tree.index(selection[0])
        app = self.apps_list[item_idx]
        app_name = app.get("name", "Unknown")
        package = app.get("package", "")
        
        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Удалить приложение '{app_name}'?\n\nЭто действие необратимо!"
        )
        
        if not confirm:
            return
        
        self.log(f"[INFO] Удаление приложения: {app_name}")
        
        def task():
            result = self.run_cli(["remove-uwp", "--package", package, "--yes"])
            if result and result.get("success"):
                self.root.after(0, lambda: self.log(f"[OK] Приложение удалено"))
                self.root.after(0, self.load_apps)
        
        threading.Thread(target=task, daemon=True).start()
    
    def open_apps_settings(self):
        """Открытие настроек приложений Windows"""
        try:
            subprocess.Popen(["ms-settings:appsfeatures"])
            self.log("[OK] Открыты настройки приложений")
        except Exception as e:
            self.log(f"[ERROR] Ошибка открытия настроек: {e}")

    
    # === Исключения ===
    
    def add_exclusion(self):
        """Добавление исключения"""
        path = self.exclusion_entry.get().strip()
        if not path:
            messagebox.showwarning("Предупреждение", "Введите путь!")
            return
        
        self.exclusions_listbox.insert(tk.END, path)
        self.exclusion_entry.delete(0, tk.END)
        self.log(f"[OK] Добавлено исключение: {path}")
    
    def remove_exclusion(self):
        """Удаление исключения"""
        selection = self.exclusions_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите элемент!")
            return
        
        path = self.exclusions_listbox.get(selection[0])
        self.exclusions_listbox.delete(selection[0])
        self.log(f"[OK] Удалено исключение: {path}")
    
    def save_exclusions(self):
        """Сохранение исключений"""
        exclusions = list(self.exclusions_listbox.get(0, tk.END))
        
        # Сохранение в config.json
        CONFIG_DIR.mkdir(exist_ok=True)
        config_file = CONFIG_DIR / "config.json"
        
        config = {"exclusions": exclusions}
        
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.log(f"[OK] Сохранено {len(exclusions)} исключений")
            messagebox.showinfo("Успех", "Исключения сохранены!")
        except Exception as e:
            self.log(f"[ERROR] Ошибка сохранения: {e}")
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    
    # === Отчёты ===
    
    def load_history(self):
        """Загрузка истории"""
        history_file = CONFIG_DIR / "history.json"
        
        if not history_file.exists():
            self.history_text.config(state=tk.NORMAL)
            self.history_text.delete(1.0, tk.END)
            self.history_text.insert(tk.END, "История пуста")
            self.history_text.config(state=tk.DISABLED)
            return
        
        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history = json.load(f)
            
            self.history_text.config(state=tk.NORMAL)
            self.history_text.delete(1.0, tk.END)
            
            for entry in history:
                timestamp = entry.get("timestamp", "Unknown")
                action = entry.get("action", "Unknown")
                details = entry.get("details", "")
                
                self.history_text.insert(tk.END, f"[{timestamp}] {action}\n")
                self.history_text.insert(tk.END, f"  {details}\n\n")
            
            self.history_text.config(state=tk.DISABLED)
            self.log(f"[OK] Загружено {len(history)} записей истории")
        except Exception as e:
            self.log(f"[ERROR] Ошибка загрузки истории: {e}")
    
    def export_baseline(self):
        """Экспорт baseline"""
        self.log("[INFO] Экспорт baseline...")
        
        def task():
            result = self.run_cli(["export-baseline"])
            if result and result.get("success"):
                self.root.after(0, lambda: self.log("[OK] Baseline экспортирован"))
                self.root.after(0, lambda: messagebox.showinfo("Успех", "Baseline сохранён!"))
        
        threading.Thread(target=task, daemon=True).start()
    
    def restore_baseline(self):
        """Восстановление baseline"""
        confirm = messagebox.askyesno(
            "Подтверждение",
            "Восстановить систему из baseline?\n\nЭто отменит изменения автозапуска."
        )
        
        if not confirm:
            return
        
        self.log("[INFO] Восстановление baseline...")
        
        def task():
            result = self.run_cli(["restore-baseline"])
            if result and result.get("success"):
                self.root.after(0, lambda: self.log("[OK] Baseline восстановлен"))
                self.root.after(0, lambda: messagebox.showinfo("Успех", "Baseline восстановлен!"))
        
        threading.Thread(target=task, daemon=True).start()

    
    # === Утилиты ===
    
    def log(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def format_size(self, size_bytes: int) -> str:
        """Форматирование размера"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"


def main():
    root = tk.Tk()
    app = CleanerGUI(root)
    
    # Обработка закрытия окна
    def on_closing():
        if app.effects:
            app.effects.cleanup()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


if __name__ == "__main__":
    main()
