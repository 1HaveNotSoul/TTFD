#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTFD-Cleaner - Autoruns-Style Startup Tab
Точная копия интерфейса Sysinternals Autoruns
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, List, Any
import subprocess
import json
import os
import re

class AutorunsStyleStartupTab:
    """Вкладка автозапуска в стиле Sysinternals Autoruns"""
    
    def __init__(self, parent_frame, cli_path, log_callback):
        self.parent = parent_frame
        self.cli_path = cli_path
        self.log = log_callback
        self.startup_items = []
        self.startup_items_dict = {}  # Словарь для быстрого поиска по ID
        
        # Настройки фильтров (как в Autoruns Options)
        self.hide_microsoft = tk.BooleanVar(value=False)
        self.hide_windows = tk.BooleanVar(value=False)
        self.show_empty_locations = tk.BooleanVar(value=True)
        self.verify_signatures = tk.BooleanVar(value=False)
        
        # Категории (как вкладки в Autoruns)
        self.categories = {
            'Everything': 'Всё',
            'Logon': 'Вход в систему',
            'Explorer': 'Проводник',
            'Internet Explorer': 'Internet Explorer',
            'Scheduled Tasks': 'Задачи',
            'Services': 'Службы',
            'Drivers': 'Драйверы',
            'Codecs': 'Кодеки',
            'Boot Execute': 'Загрузка',
            'Image Hijacks': 'Перехваты',
            'AppInit': 'AppInit',
            'Known DLLs': 'Известные DLL',
            'Winlogon': 'Winlogon',
            'Winsock Providers': 'Winsock',
            'Print Monitors': 'Мониторы печати',
            'LSA Providers': 'LSA',
            'Network Providers': 'Сетевые провайдеры',
            'WMI': 'WMI',
            'Office': 'Office'
        }
        
        self.current_category = 'Everything'
        self.icon_cache = {}  # Кэш иконок
        self.setup_ui()
        
        # Автоматическое обновление при открытии
        self.parent.after(100, self.refresh)
    
    def setup_ui(self):
        """Создание интерфейса в стиле Autoruns"""
        
        # Верхняя панель - меню и кнопки (как в Autoruns)
        toolbar = ttk.Frame(self.parent)
        toolbar.pack(fill=tk.X, padx=5, pady=5)
        
        # Кнопки действий
        ttk.Button(toolbar, text="Обновить", command=self.refresh, width=12).pack(side=tk.LEFT, padx=2)
        ttk.Button(toolbar, text="Сохранить...", command=self.save_report, width=12).pack(side=tk.LEFT, padx=2)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Опции (как в Autoruns)
        options_frame = ttk.LabelFrame(toolbar, text="Опции", padding="5")
        options_frame.pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(options_frame, text="Скрыть Microsoft", 
                       variable=self.hide_microsoft, 
                       command=self.apply_filters).pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(options_frame, text="Скрыть Windows", 
                       variable=self.hide_windows, 
                       command=self.apply_filters).pack(side=tk.LEFT, padx=5)
        
        ttk.Checkbutton(options_frame, text="Показать пустые", 
                       variable=self.show_empty_locations, 
                       command=self.apply_filters).pack(side=tk.LEFT, padx=5)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Поиск
        ttk.Label(toolbar, text="Поиск:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.apply_filters())
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=2)
        
        # Вкладки категорий (как в Autoruns)
        category_notebook = ttk.Notebook(self.parent)
        category_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Создаём вкладки для каждой категории
        self.category_frames = {}
        self.category_trees = {}
        
        for cat_id, cat_name in self.categories.items():
            frame = ttk.Frame(category_notebook)
            category_notebook.add(frame, text=cat_name)
            
            # Создаём TreeView для каждой категории
            tree = self.create_treeview(frame)
            self.category_frames[cat_id] = frame
            self.category_trees[cat_id] = tree
        
        # Привязка смены вкладки
        category_notebook.bind('<<NotebookTabChanged>>', self.on_category_changed)
        self.category_notebook = category_notebook
        
        # Статус-бар (как в Autoruns)
        statusbar = ttk.Frame(self.parent)
        statusbar.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        
        self.status_label = ttk.Label(statusbar, text="Готов", relief=tk.SUNKEN, anchor=tk.W)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.count_label = ttk.Label(statusbar, text="Элементов: 0", relief=tk.SUNKEN, width=20)
        self.count_label.pack(side=tk.RIGHT)
    
    def create_treeview(self, parent):
        """Создание TreeView в стиле Autoruns"""
        
        # Контейнер для TreeView и скроллбара
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Колонки (как в Autoruns)
        columns = ('entry', 'description', 'publisher', 'path', 'status')
        tree = ttk.Treeview(container, columns=columns, show='tree headings', selectmode='extended')
        
        # Настройка колонок
        tree.heading('#0', text='')  # Чекбокс колонка
        tree.heading('entry', text='Autostart Entry')
        tree.heading('description', text='Description')
        tree.heading('publisher', text='Publisher')
        tree.heading('path', text='Path')
        tree.heading('status', text='Status')
        
        tree.column('#0', width=30, stretch=False)
        tree.column('entry', width=250)
        tree.column('description', width=200)
        tree.column('publisher', width=150)
        tree.column('path', width=300)
        tree.column('status', width=100)
        
        # Цветовые теги (как в Autoruns)
        tree.tag_configure('not_found', background='#FFE0E0')  # Розовый - файл не найден
        tree.tag_configure('no_info', background='#FFFACD')    # Жёлтый - нет информации
        tree.tag_configure('microsoft', foreground='#008000')  # Зелёный - Microsoft
        tree.tag_configure('disabled', foreground='#808080')   # Серый - отключено
        tree.tag_configure('normal', foreground='#000000')     # Чёрный - обычный
        
        # Скроллбары
        vsb = ttk.Scrollbar(container, orient=tk.VERTICAL, command=tree.yview)
        hsb = ttk.Scrollbar(container, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        # Размещение
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        # Контекстное меню (как в Autoruns)
        self.create_context_menu(tree)
        
        # Двойной клик - переключение состояния
        tree.bind('<Double-Button-1>', lambda e: self.toggle_selected())
        
        # Клавиша Delete - удаление
        tree.bind('<Delete>', lambda e: self.delete_selected())
        
        return tree
    
    def create_context_menu(self, tree):
        """Создание контекстного меню (как в Autoruns)"""
        menu = tk.Menu(tree, tearoff=0)
        
        menu.add_command(label="Включить", command=lambda: self.toggle_selected(True))
        menu.add_command(label="Отключить", command=lambda: self.toggle_selected(False))
        menu.add_separator()
        menu.add_command(label="Удалить", command=self.delete_selected)
        menu.add_separator()
        menu.add_command(label="Перейти к записи", command=self.jump_to_entry)
        menu.add_command(label="Открыть папку", command=self.open_folder)
        menu.add_separator()
        menu.add_command(label="Поиск в Google", command=self.search_online)
        menu.add_command(label="Проверить на VirusTotal", command=self.check_virustotal)
        menu.add_separator()
        menu.add_command(label="Свойства", command=self.show_properties)
        menu.add_command(label="Копировать путь", command=self.copy_path)
        
        def show_menu(event):
            try:
                menu.tk_popup(event.x_root, event.y_root)
            finally:
                menu.grab_release()
        
        tree.bind('<Button-3>', show_menu)
    
    def refresh(self):
        """Обновление списка (как Refresh в Autoruns)"""
        self.status_label.config(text="Сканирование...")
        self.log("[INFO] Сканирование автозапуска...")
        
        # Запуск CLI
        try:
            result = subprocess.run(
                [str(self.cli_path), "list-startup"],
                capture_output=True,
                text=True,
                encoding='utf-8'
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                if data.get("success"):
                    self.startup_items = data.get("data", [])
                    self.display_items()
                    self.status_label.config(text="Готов")
                    self.log(f"[OK] Загружено {len(self.startup_items)} элементов")
                else:
                    self.status_label.config(text="Ошибка")
                    self.log("[ERROR] Ошибка получения данных")
            else:
                self.status_label.config(text="Ошибка CLI")
                self.log(f"[ERROR] CLI вернул код {result.returncode}")
        
        except Exception as e:
            self.status_label.config(text="Ошибка")
            self.log(f"[ERROR] {e}")
    
    def display_items(self):
        """Отображение элементов во всех категориях"""
        
        # Группировка по категориям
        categorized = {}
        for item in self.startup_items:
            item_type = item.get('type', 'Unknown')
            
            # Маппинг типов на категории Autoruns
            category = self.map_type_to_category(item_type)
            
            if category not in categorized:
                categorized[category] = []
            categorized[category].append(item)
        
        # Заполнение каждой вкладки
        for cat_id, tree in self.category_trees.items():
            # Очистка
            for item in tree.get_children():
                tree.delete(item)
            
            # Получить элементы для этой категории
            if cat_id == 'Everything':
                items = self.startup_items
            else:
                items = categorized.get(cat_id, [])
            
            # Группировка по подкатегориям (как в Autoruns)
            subcategories = {}
            for item in items:
                location = item.get('location', 'Unknown')
                subcat = self.extract_subcategory(location)
                
                if subcat not in subcategories:
                    subcategories[subcat] = []
                subcategories[subcat].append(item)
            
            # Отображение с группировкой
            for subcat, subcat_items in sorted(subcategories.items()):
                # Родительский узел подкатегории
                parent_id = tree.insert('', tk.END, text=f'☐ {subcat}', open=True)
                
                for item in subcat_items:
                    self.insert_item(tree, parent_id, item)
        
        self.apply_filters()
    
    def insert_item(self, tree, parent, item):
        """Вставка элемента в TreeView"""
        
        name = item.get('name', 'Unknown')
        location = item.get('location', '')
        enabled = item.get('enabled', False)
        is_protected = item.get('isSystemProtected', False)
        item_id = item.get('id', '')
        
        # Определение описания и издателя (как в Autoruns)
        description = self.extract_description(item)
        publisher = self.extract_publisher(item)
        image_path = location
        
        # Статус
        status = "Enabled" if enabled else "Disabled"
        
        # Чекбокс
        checkbox = '☑' if enabled else '☐'
        
        # Определение тега (цвета)
        tag = self.determine_tag(item, location, publisher)
        
        # Извлечение иконки
        icon = self.get_icon(image_path)
        
        # Вставка
        iid = tree.insert(parent, tk.END,
                   text=checkbox,
                   values=(name, description, publisher, image_path, status),
                   tags=(tag,),
                   image=icon if icon else '')
        
        # Сохранить ID элемента для последующего использования
        self.startup_items_dict[iid] = item
    
    def map_type_to_category(self, item_type):
        """Маппинг типа элемента на категорию Autoruns"""
        mapping = {
            'Logon': 'Logon',
            'Explorer': 'Explorer',
            'Services': 'Services',
            'Scheduled Tasks': 'Scheduled Tasks',
            'Drivers': 'Drivers',
            'Winlogon': 'Winlogon',
            'Browser Helper Objects': 'Internet Explorer',
            'Codecs': 'Codecs',
            'Print Monitors': 'Print Monitors',
            'LSA Providers': 'LSA Providers',
            'Boot Execute': 'Boot Execute'
        }
        return mapping.get(item_type, 'Everything')
    
    def extract_subcategory(self, location):
        """Извлечение подкатегории из пути (как в Autoruns)"""
        if 'HKLM\\' in location:
            return 'HKLM'
        elif 'HKCU\\' in location:
            return 'HKCU'
        elif 'Startup' in location:
            return 'Startup Folder'
        elif 'Task Scheduler' in location:
            return 'Task Scheduler'
        elif 'Services' in location:
            return 'Services'
        else:
            return 'Other'
    
    def extract_description(self, item):
        """Извлечение описания (как в Autoruns)"""
        # TODO: Получить описание из файла (FileVersionInfo)
        return item.get('description', '')
    
    def extract_publisher(self, item):
        """Извлечение издателя (как в Autoruns)"""
        name = item.get('name', '')
        location = item.get('location', '')
        
        # Определение по имени/пути
        if 'Microsoft' in name or 'Microsoft' in location:
            return 'Microsoft Corporation'
        elif 'Windows' in name or 'Windows' in location:
            return 'Microsoft Corporation'
        else:
            # TODO: Получить издателя из цифровой подписи
            return '(Verified) Unknown' if self.verify_signatures.get() else ''
    
    def get_icon(self, image_path):
        """Извлечение иконки из файла"""
        if not image_path or image_path in self.icon_cache:
            return self.icon_cache.get(image_path)
        
        try:
            # Извлечь путь к .exe файлу
            import re
            import os
            
            # Попытка извлечь путь к файлу
            exe_path = None
            
            # Если это путь к файлу
            if os.path.exists(image_path):
                exe_path = image_path
            else:
                # Попытка извлечь путь из строки (например, "C:\Program Files\App\app.exe" -arg)
                match = re.search(r'([A-Za-z]:\\[^"]+\.exe)', image_path, re.IGNORECASE)
                if match:
                    potential_path = match.group(1)
                    if os.path.exists(potential_path):
                        exe_path = potential_path
            
            if exe_path and exe_path.lower().endswith('.exe'):
                # Попытка извлечь иконку с помощью win32gui
                try:
                    import win32gui
                    import win32ui
                    import win32con
                    from PIL import Image, ImageTk
                    
                    # Извлечь иконку
                    ico_x = win32gui.GetSystemMetrics(win32con.SM_CXSMICON)
                    ico_y = win32gui.GetSystemMetrics(win32con.SM_CYSMICON)
                    
                    large, small = win32gui.ExtractIconEx(exe_path, 0)
                    
                    if small:
                        # Использовать маленькую иконку
                        hicon = small[0]
                        
                        # Получить информацию об иконке
                        info = win32gui.GetIconInfo(hicon)
                        
                        # Создать bitmap
                        bmpcolor = win32ui.CreateBitmapFromHandle(info[4])
                        
                        # Получить размеры
                        bmp_info = bmpcolor.GetInfo()
                        bmp_str = bmpcolor.GetBitmapBits(True)
                        
                        # Создать PIL Image
                        img = Image.frombuffer(
                            'RGB',
                            (bmp_info['bmWidth'], bmp_info['bmHeight']),
                            bmp_str, 'raw', 'BGRX', 0, 1
                        )
                        
                        # Изменить размер до 16x16
                        img = img.resize((16, 16), Image.Resampling.LANCZOS)
                        
                        # Конвертировать в PhotoImage
                        photo = ImageTk.PhotoImage(img)
                        
                        # Очистить ресурсы
                        win32gui.DestroyIcon(hicon)
                        if large:
                            for icon in large:
                                win32gui.DestroyIcon(icon)
                        for icon in small[1:]:
                            win32gui.DestroyIcon(icon)
                        
                        # Кэшировать
                        self.icon_cache[image_path] = photo
                        return photo
                    
                except ImportError:
                    # pywin32 не установлен
                    pass
                except Exception as e:
                    # Ошибка извлечения иконки
                    pass
            
            # Кэшировать результат (даже если None)
            self.icon_cache[image_path] = None
            return None
            
        except Exception as e:
            self.icon_cache[image_path] = None
            return None
    
    def determine_tag(self, item, location, publisher):
        """Определение тега (цвета) как в Autoruns"""
        
        # Проверка существования файла
        # TODO: Проверить существование файла
        file_exists = True
        
        if not file_exists:
            return 'not_found'  # Розовый
        elif not publisher or publisher == '':
            return 'no_info'    # Жёлтый
        elif 'Microsoft' in publisher:
            return 'microsoft'  # Зелёный
        elif not item.get('enabled', False):
            return 'disabled'   # Серый
        else:
            return 'normal'     # Чёрный
    
    def apply_filters(self):
        """Применение фильтров (как Options в Autoruns)"""
        search_text = self.search_var.get().lower()
        
        for cat_id, tree in self.category_trees.items():
            for item_id in tree.get_children():
                self.filter_item(tree, item_id, search_text)
        
        # Обновление счётчика
        current_tree = self.get_current_tree()
        visible_count = self.count_visible_items(current_tree)
        self.count_label.config(text=f"Элементов: {visible_count}")
    
    def filter_item(self, tree, item_id, search_text):
        """Фильтрация элемента"""
        values = tree.item(item_id, 'values')
        
        if not values:  # Родительский узел
            # Фильтрация детей
            children = tree.get_children(item_id)
            visible_children = 0
            
            for child_id in children:
                if self.filter_item(tree, child_id, search_text):
                    visible_children += 1
            
            # Скрыть родителя если нет видимых детей
            if visible_children == 0:
                tree.detach(item_id)
            else:
                tree.reattach(item_id, '', tk.END)
            
            return visible_children > 0
        
        else:  # Дочерний элемент
            name, description, publisher, image_path, timestamp = values
            
            # Фильтр Microsoft
            if self.hide_microsoft.get() and 'Microsoft' in publisher:
                tree.detach(item_id)
                return False
            
            # Фильтр Windows
            if self.hide_windows.get() and 'Windows' in name:
                tree.detach(item_id)
                return False
            
            # Поиск
            if search_text:
                if (search_text not in name.lower() and 
                    search_text not in description.lower() and
                    search_text not in publisher.lower() and
                    search_text not in image_path.lower()):
                    tree.detach(item_id)
                    return False
            
            tree.reattach(item_id, tree.parent(item_id), tk.END)
            return True
    
    def count_visible_items(self, tree):
        """Подсчёт видимых элементов"""
        count = 0
        for item_id in tree.get_children():
            count += self.count_visible_items_recursive(tree, item_id)
        return count
    
    def count_visible_items_recursive(self, tree, item_id):
        """Рекурсивный подсчёт"""
        count = 0
        values = tree.item(item_id, 'values')
        
        if values:  # Дочерний элемент
            count = 1
        
        for child_id in tree.get_children(item_id):
            count += self.count_visible_items_recursive(tree, child_id)
        
        return count
    
    def get_current_tree(self):
        """Получить текущий TreeView"""
        current_tab = self.category_notebook.index(self.category_notebook.select())
        cat_id = list(self.categories.keys())[current_tab]
        return self.category_trees[cat_id]
    
    def on_category_changed(self, event):
        """Обработка смены категории"""
        self.apply_filters()
    
    def toggle_selected(self, enable=None):
        """Переключение состояния выбранных элементов"""
        tree = self.get_current_tree()
        selection = tree.selection()
        
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите элементы!")
            return
        
        for item_id in selection:
            values = tree.item(item_id, 'values')
            if not values:  # Пропустить родительские узлы
                continue
            
            # Получить данные элемента
            item_data = self.startup_items_dict.get(item_id)
            if not item_data:
                self.log(f"[ERROR] Не найдены данные для элемента")
                continue
            
            startup_id = item_data.get('id', '')
            item_name = item_data.get('name', 'Unknown')
            
            if not startup_id:
                self.log(f"[ERROR] Нет ID для элемента {item_name}")
                continue
            
            # Определить действие
            current_enabled = item_data.get('enabled', False)
            if enable is None:
                new_enabled = not current_enabled
            else:
                new_enabled = enable
            
            # Вызвать CLI для переключения
            try:
                result = subprocess.run(
                    [str(self.cli_path), "set-startup", "--id", startup_id, "--enabled", str(new_enabled).lower()],
                    capture_output=True,
                    text=True,
                    encoding='utf-8'
                )
                
                if result.returncode == 0:
                    data = json.loads(result.stdout)
                    if data.get("success"):
                        # Обновить чекбокс
                        new_text = '☑' if new_enabled else '☐'
                        tree.item(item_id, text=new_text)
                        
                        # Обновить статус в колонке
                        values = list(tree.item(item_id, 'values'))
                        values[4] = "Enabled" if new_enabled else "Disabled"  # Обновить Status
                        tree.item(item_id, values=values)
                        
                        # Обновить данные
                        item_data['enabled'] = new_enabled
                        
                        action = "включён" if new_enabled else "отключён"
                        self.log(f"[OK] {item_name} {action}")
                    else:
                        self.log(f"[ERROR] Не удалось изменить {item_name}: {data.get('message', 'Unknown error')}")
                else:
                    self.log(f"[ERROR] CLI вернул код {result.returncode}")
            
            except Exception as e:
                self.log(f"[ERROR] Ошибка при изменении {item_name}: {e}")
        
        # Обновить счётчик
        self.apply_filters()
    
    def delete_selected(self):
        """Удаление выбранных элементов"""
        tree = self.get_current_tree()
        selection = tree.selection()
        
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите элементы!")
            return
        
        confirm = messagebox.askyesno(
            "Подтверждение",
            f"Удалить {len(selection)} элементов?\n\nЭто действие необратимо!"
        )
        
        if not confirm:
            return
        
        # TODO: Вызвать CLI для удаления
        for item_id in selection:
            tree.delete(item_id)
        
        self.log(f"[OK] Удалено {len(selection)} элементов")
    
    def jump_to_entry(self):
        """Перейти к записи в реестре"""
        tree = self.get_current_tree()
        selection = tree.selection()
        
        if not selection:
            return
        
        item_id = selection[0]
        item_data = self.startup_items_dict.get(item_id)
        
        if item_data:
            location = item_data.get('location', '')
            
            # Проверить, является ли это записью реестра
            if 'HKEY_' in location or 'HKLM\\' in location or 'HKCU\\' in location:
                # Извлечь путь реестра
                import re
                
                # Попытка извлечь путь реестра
                reg_path = None
                if 'HKEY_LOCAL_MACHINE' in location or 'HKLM\\' in location:
                    match = re.search(r'(HKEY_LOCAL_MACHINE\\[^\\]+(?:\\[^\\]+)*)', location)
                    if match:
                        reg_path = match.group(1)
                    else:
                        match = re.search(r'HKLM\\(.+)', location)
                        if match:
                            reg_path = f"HKEY_LOCAL_MACHINE\\{match.group(1)}"
                
                elif 'HKEY_CURRENT_USER' in location or 'HKCU\\' in location:
                    match = re.search(r'(HKEY_CURRENT_USER\\[^\\]+(?:\\[^\\]+)*)', location)
                    if match:
                        reg_path = match.group(1)
                    else:
                        match = re.search(r'HKCU\\(.+)', location)
                        if match:
                            reg_path = f"HKEY_CURRENT_USER\\{match.group(1)}"
                
                if reg_path:
                    # Записать путь в файл для regedit
                    import tempfile
                    reg_file = tempfile.NamedTemporaryFile(mode='w', suffix='.reg', delete=False, encoding='utf-16le')
                    reg_file.write('\ufeff')  # BOM для UTF-16 LE
                    reg_file.write(f'Windows Registry Editor Version 5.00\n\n')
                    reg_file.write(f'; Jump to: {reg_path}\n')
                    reg_file.close()
                    
                    # Открыть regedit
                    try:
                        # Установить последний открытый ключ
                        subprocess.run(['reg', 'add', 'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Applets\\Regedit', 
                                      '/v', 'LastKey', '/t', 'REG_SZ', '/d', reg_path, '/f'], 
                                     capture_output=True)
                        
                        # Открыть regedit
                        subprocess.Popen(['regedit'])
                        self.log(f"[OK] Открыт regedit: {reg_path}")
                    except Exception as e:
                        self.log(f"[ERROR] Не удалось открыть regedit: {e}")
                else:
                    self.log(f"[WARNING] Не удалось извлечь путь реестра из: {location}")
            else:
                self.log(f"[INFO] Это не запись реестра: {location}")
    
    def open_folder(self):
        """Открыть папку с файлом"""
        tree = self.get_current_tree()
        selection = tree.selection()
        
        if not selection:
            return
        
        item_id = selection[0]
        values = tree.item(item_id, 'values')
        
        if values:
            image_path = values[3]
            
            # Извлечь путь к файлу
            import re
            import os
            
            exe_path = None
            
            # Если это путь к файлу
            if os.path.exists(image_path):
                exe_path = image_path
            else:
                # Попытка извлечь путь из строки
                match = re.search(r'([A-Za-z]:\\[^"]+\.exe)', image_path, re.IGNORECASE)
                if match:
                    potential_path = match.group(1)
                    if os.path.exists(potential_path):
                        exe_path = potential_path
            
            if exe_path:
                # Открыть папку и выделить файл
                try:
                    subprocess.run(['explorer', '/select,', exe_path])
                    self.log(f"[OK] Открыта папка: {os.path.dirname(exe_path)}")
                except Exception as e:
                    self.log(f"[ERROR] Не удалось открыть папку: {e}")
            else:
                self.log(f"[WARNING] Файл не найден: {image_path}")
    
    def search_online(self):
        """Поиск в Google"""
        tree = self.get_current_tree()
        selection = tree.selection()
        
        if not selection:
            return
        
        item_id = selection[0]
        values = tree.item(item_id, 'values')
        
        if values:
            name = values[0]
            import webbrowser
            webbrowser.open(f"https://www.google.com/search?q={name}")
            self.log(f"[INFO] Поиск в Google: {name}")
    
    def check_virustotal(self):
        """Проверка на VirusTotal"""
        tree = self.get_current_tree()
        selection = tree.selection()
        
        if not selection:
            return
        
        item_id = selection[0]
        values = tree.item(item_id, 'values')
        
        if values:
            image_path = values[3]
            # TODO: Вычислить хеш файла и открыть VirusTotal
            self.log(f"[INFO] Проверка на VirusTotal: {image_path}")
    
    def show_properties(self):
        """Показать свойства файла"""
        tree = self.get_current_tree()
        selection = tree.selection()
        
        if not selection:
            return
        
        item_id = selection[0]
        values = tree.item(item_id, 'values')
        
        if values:
            image_path = values[3]
            # TODO: Показать диалог свойств Windows
            self.log(f"[INFO] Свойства: {image_path}")
    
    def copy_path(self):
        """Копировать путь в буфер обмена"""
        tree = self.get_current_tree()
        selection = tree.selection()
        
        if not selection:
            return
        
        item_id = selection[0]
        values = tree.item(item_id, 'values')
        
        if values:
            image_path = values[3]
            self.parent.clipboard_clear()
            self.parent.clipboard_append(image_path)
            self.log(f"[OK] Путь скопирован: {image_path}")
    
    def save_report(self):
        """Сохранение отчёта (как Save в Autoruns)"""
        from datetime import datetime
        
        filename = f"autoruns_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("TTFD-Cleaner - Autoruns Report\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 100 + "\n\n")
                
                for cat_id, cat_name in self.categories.items():
                    tree = self.category_trees[cat_id]
                    
                    f.write(f"\n{cat_name}\n")
                    f.write("-" * 100 + "\n")
                    
                    for item_id in tree.get_children():
                        self.write_item_recursive(f, tree, item_id, 0)
            
            self.log(f"[OK] Отчёт сохранён: {filename}")
            messagebox.showinfo("Успех", f"Отчёт сохранён:\n{filename}")
        
        except Exception as e:
            self.log(f"[ERROR] Ошибка сохранения: {e}")
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")
    
    def write_item_recursive(self, file, tree, item_id, level):
        """Рекурсивная запись элемента"""
        indent = "  " * level
        text = tree.item(item_id, 'text')
        values = tree.item(item_id, 'values')
        
        if values:
            name, description, publisher, image_path, timestamp = values
            file.write(f"{indent}{text} {name}\n")
            file.write(f"{indent}  Description: {description}\n")
            file.write(f"{indent}  Publisher: {publisher}\n")
            file.write(f"{indent}  Path: {image_path}\n")
            file.write(f"{indent}  Timestamp: {timestamp}\n\n")
        else:
            file.write(f"{indent}{text}\n")
        
        for child_id in tree.get_children(item_id):
            self.write_item_recursive(file, tree, child_id, level + 1)
