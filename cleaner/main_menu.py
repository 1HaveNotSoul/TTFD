#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTFD-Cleaner - Главное меню с навигацией
Использует изображения из assets/
"""

import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import sys
import ctypes
from pathlib import Path


def is_admin():
    """Проверка прав администратора"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def run_as_admin():
    """Запуск с правами администратора"""
    try:
        if sys.argv[0].endswith('.py'):
            # Запуск Python скрипта
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{sys.argv[0]}"', None, 1
            )
        else:
            # Запуск .exe
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.argv[0], "", None, 1
            )
        sys.exit(0)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось запустить с правами администратора: {e}")
        sys.exit(1)


class MainMenu(tk.Tk):
    """Главное меню приложения"""
    
    def __init__(self):
        super().__init__()
        
        # Проверка прав администратора
        self.is_admin = is_admin()
        
        if not self.is_admin:
            response = messagebox.askyesno(
                "Требуются права администратора",
                "Для полного функционала требуются права администратора.\n\n"
                "Запустить с правами администратора?"
            )
            if response:
                run_as_admin()
            else:
                messagebox.showwarning(
                    "Предупреждение",
                    "Некоторые функции будут недоступны без прав администратора."
                )
        
        self.title("TTFD-Cleaner")
        self.geometry("1200x800")
        
        # Пути к ресурсам
        if getattr(sys, 'frozen', False):
            # Запущено из exe
            self.base_path = Path(sys._MEIPASS)
        else:
            # Запущено из Python
            self.base_path = Path(__file__).parent
        self.assets_path = self.base_path / 'assets'
        
        # Загрузить фон
        self.setup_background()
        
        # Создать UI
        self.setup_ui()
    
    def setup_background(self):
        """Установка фонового изображения"""
        bg_path = self.assets_path / 'Rectangle 6.png'
        if bg_path.exists():
            try:
                # Загрузить фон
                bg_image = Image.open(bg_path)
                # Изменить размер под окно
                bg_image = bg_image.resize((1200, 800), Image.Resampling.LANCZOS)
                self.bg_photo = ImageTk.PhotoImage(bg_image)
                
                # Создать Canvas для фона
                self.canvas = tk.Canvas(self, width=1200, height=800, highlightthickness=0)
                self.canvas.pack(fill=tk.BOTH, expand=True)
                self.canvas.create_image(0, 0, image=self.bg_photo, anchor=tk.NW)
            except Exception as e:
                print(f"Ошибка загрузки фона: {e}")
                # Fallback на тёмный фон
                self.configure(bg='#1a1d23')
                self.canvas = tk.Canvas(self, width=1200, height=800, bg='#1a1d23', highlightthickness=0)
                self.canvas.pack(fill=tk.BOTH, expand=True)
        else:
            # Fallback на тёмный фон
            self.configure(bg='#1a1d23')
            self.canvas = tk.Canvas(self, width=1200, height=800, bg='#1a1d23', highlightthickness=0)
            self.canvas.pack(fill=tk.BOTH, expand=True)
    
    def setup_ui(self):
        """Создание UI главного меню"""
        # Логотип (Group 7.png) вместо текста
        logo_path = self.assets_path / 'Group 7.png'
        if logo_path.exists():
            try:
                logo_image = Image.open(logo_path)
                # Масштабировать логотип
                logo_image.thumbnail((400, 100), Image.Resampling.LANCZOS)
                self.logo_photo = ImageTk.PhotoImage(logo_image)
                
                # Разместить логотип на Canvas
                self.canvas.create_image(600, 80, image=self.logo_photo, anchor=tk.CENTER)
            except Exception as e:
                print(f"Ошибка загрузки логотипа: {e}")
                # Fallback на текст
                self.canvas.create_text(
                    600, 80,
                    text="TTFD-Cleaner",
                    font=("Segoe UI", 32, "bold"),
                    fill='#e4e6eb',
                    anchor=tk.CENTER
                )
        else:
            # Fallback на текст
            self.canvas.create_text(
                600, 80,
                text="TTFD-Cleaner",
                font=("Segoe UI", 32, "bold"),
                fill='#e4e6eb',
                anchor=tk.CENTER
            )
        
        # Кнопки разделов (целые изображения кликабельны)
        # Маппинг: файл → функция
        buttons = [
            ('Group 2.png', self.open_cleaning),      # Очистка
            ('Group 1.png', self.open_reports),       # Отчёты
            ('Group 3.png', self.open_startup),       # Автозапуск
            ('Group 4.png', self.open_browsers),      # Браузеры
            ('Group 5.png', self.open_apps),          # Приложения
            ('Group 6.png', self.open_exclusions),    # Исключения
        ]
        
        # Позиции кнопок (3 колонки, 2 ряда)
        positions = [
            (250, 300),   # Очистка (верх-лево)
            (600, 300),   # Отчёты (верх-центр)
            (950, 300),   # Автозапуск (верх-право)
            (250, 550),   # Браузеры (низ-лево)
            (600, 550),   # Приложения (низ-центр)
            (950, 550),   # Исключения (низ-право)
        ]
        
        for (image_file, command), (x, y) in zip(buttons, positions):
            self.create_button(image_file, x, y, command)
    
    def create_button(self, image_file, x, y, command):
        """Создание кнопки из изображения"""
        image_path = self.assets_path / image_file
        
        if image_path.exists():
            try:
                # Загрузить изображение
                img = Image.open(image_path)
                # Масштабировать (примерный размер кнопки)
                img.thumbnail((280, 180), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                
                # Создать кнопку на Canvas
                button_id = self.canvas.create_image(x, y, image=photo, anchor=tk.CENTER)
                
                # Сохранить ссылку на изображение
                if not hasattr(self, 'button_images'):
                    self.button_images = []
                self.button_images.append(photo)
                
                # Привязать клик
                self.canvas.tag_bind(button_id, '<Button-1>', lambda e: command())
                
                # Hover эффект (изменение курсора)
                self.canvas.tag_bind(button_id, '<Enter>', lambda e: self.canvas.config(cursor='hand2'))
                self.canvas.tag_bind(button_id, '<Leave>', lambda e: self.canvas.config(cursor=''))
                
            except Exception as e:
                print(f"Ошибка загрузки кнопки {image_file}: {e}")
        else:
            print(f"Файл не найден: {image_path}")
    
    def open_cleaning(self):
        """Открыть раздел очистки"""
        print("[INFO] Открытие раздела: Очистка")
        self.withdraw()  # Скрыть главное меню
        
        # Импортировать окно очистки
        from sections.cleaning_window import CleaningWindow
        
        # Создать окно очистки
        cleaning = CleaningWindow(self)
        
        # При закрытии окна вернуться в меню
        def on_close():
            cleaning.window.destroy()
            self.deiconify()  # Показать главное меню
        
        cleaning.window.protocol("WM_DELETE_WINDOW", on_close)
    
    def open_browsers(self):
        """Открыть раздел браузеров"""
        print("[INFO] Открытие раздела: Браузеры")
        self.withdraw()  # Скрыть главное меню
        
        # Импортировать окно браузеров
        from sections.browsers_window import BrowsersWindow
        
        # Создать окно браузеров
        browsers = BrowsersWindow(self)
        
        # При закрытии окна вернуться в меню
        def on_close():
            browsers.window.destroy()
            self.deiconify()  # Показать главное меню
        
        browsers.window.protocol("WM_DELETE_WINDOW", on_close)
    
    def open_startup(self):
        """Открыть раздел автозапуска"""
        print("[INFO] Открытие раздела: Автозапуск")
        self.withdraw()  # Скрыть главное меню
        
        # Импортировать окно автозапуска
        from sections.startup_window import StartupWindow
        
        # Создать окно автозапуска
        startup = StartupWindow(self)
        
        # При закрытии окна вернуться в меню
        def on_close():
            startup.window.destroy()
            self.deiconify()  # Показать главное меню
        
        startup.window.protocol("WM_DELETE_WINDOW", on_close)
    
    def open_apps(self):
        """Открыть раздел приложений"""
        print("[INFO] Открытие раздела: Приложения")
        self.withdraw()  # Скрыть главное меню
        
        # Импортировать окно приложений
        from sections.apps_window import AppsWindow
        
        # Создать окно приложений
        apps = AppsWindow(self, self.is_admin)
        
        # При закрытии окна вернуться в меню
        def on_close():
            apps.window.destroy()
            self.deiconify()  # Показать главное меню
        
        apps.window.protocol("WM_DELETE_WINDOW", on_close)
    
    def open_exclusions(self):
        """Открыть раздел исключений"""
        print("[INFO] Открытие раздела: Исключения")
        self.withdraw()  # Скрыть главное меню
        
        # Импортировать окно исключений
        from sections.exclusions_window import ExclusionsWindow
        
        # Создать окно исключений
        exclusions = ExclusionsWindow(self)
        
        # При закрытии окна вернуться в меню
        def on_close():
            exclusions.window.destroy()
            self.deiconify()  # Показать главное меню
        
        exclusions.window.protocol("WM_DELETE_WINDOW", on_close)
    
    def open_reports(self):
        """Открыть раздел отчётов"""
        print("[INFO] Открытие раздела: Отчёты")
        self.withdraw()  # Скрыть главное меню
        
        # Импортировать окно отчётов
        from sections.reports_window import ReportsWindow
        
        # Создать окно отчётов
        reports = ReportsWindow(self)
        
        # При закрытии окна вернуться в меню
        def on_close():
            reports.window.destroy()
            self.deiconify()  # Показать главное меню
        
        reports.window.protocol("WM_DELETE_WINDOW", on_close)
    
    def show_message(self, title, message):
        """Показать сообщение (не используется, оставлено для совместимости)"""
        from tkinter import messagebox
        messagebox.showinfo(title, message)


def main():
    """Главная функция"""
    app = MainMenu()
    app.mainloop()


if __name__ == '__main__':
    main()
