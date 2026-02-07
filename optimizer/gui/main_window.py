# -*- coding: utf-8 -*-
"""
TTFD-Optimizer - GUI
Главное окно с кнопками для открытия системных файлов
"""
import os
import tkinter as tk
from tkinter import messagebox
import subprocess

class OptimizerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("TTFD-Optimizer")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        
        # Тёмная тема (как в TTFD-Cleaner)
        self.bg_color = "#2E1A47"  # Тёмно-фиолетовый
        self.fg_color = "white"    # Белый текст
        self.frame_bg = "#3D2557"  # Чуть светлее для фреймов
        
        self.root.configure(bg=self.bg_color)
        
        # Путь к папке assets
        self.assets_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
        
        self.create_widgets()
    
    def create_widgets(self):
        # Заголовок
        title = tk.Label(self.root, text="TTFD-Optimizer", 
                        font=("Arial", 24, "bold"), 
                        fg="#9C27B0", bg=self.bg_color)
        title.pack(pady=20)
        
        subtitle = tk.Label(self.root, text="Оптимизация Windows", 
                           font=("Arial", 12), 
                           fg=self.fg_color, bg=self.bg_color)
        subtitle.pack(pady=5)
        
        # Контейнер для кнопок
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(pady=40)
        
        # Получаем список файлов из assets
        files = self.get_asset_files()
        
        if not files:
            # Если файлов нет, показываем сообщение
            no_files_label = tk.Label(button_frame, 
                                     text="⚠️ Файлы не найдены в папке assets", 
                                     font=("Arial", 12), 
                                     fg="#FF9800", bg=self.bg_color)
            no_files_label.pack(pady=20)
        else:
            # Создаём кнопки для каждого файла
            for i, file in enumerate(files):
                self.create_file_button(button_frame, file, i)
        
        # Статус бар
        self.status_bar = tk.Label(self.root, text="Готов к работе", 
                                   bd=1, relief=tk.SUNKEN, anchor=tk.W,
                                   bg=self.frame_bg, fg=self.fg_color)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def get_asset_files(self):
        """Получить список файлов из папки assets"""
        if not os.path.exists(self.assets_path):
            return []
        
        files = []
        for file in os.listdir(self.assets_path):
            file_path = os.path.join(self.assets_path, file)
            if os.path.isfile(file_path):
                files.append(file)
        
        return sorted(files)
    
    def create_file_button(self, parent, filename, index):
        """Создать кнопку для файла"""
        # Определяем иконку и цвет в зависимости от расширения
        ext = os.path.splitext(filename)[1].lower()
        
        if ext in ['.reg']:
            icon = "📝"
            color = "#4CAF50"  # Зелёный
            description = "Файл реестра"
        elif ext in ['.bat', '.cmd']:
            icon = "⚙️"
            color = "#2196F3"  # Синий
            description = "Пакетный файл"
        elif ext in ['.ps1']:
            icon = "💻"
            color = "#9C27B0"  # Фиолетовый
            description = "PowerShell скрипт"
        else:
            icon = "📄"
            color = "#FF9800"  # Оранжевый
            description = "Системный файл"
        
        # Кнопка
        btn = tk.Button(parent, 
                       text=f"{icon} {filename}",
                       command=lambda: self.open_file(filename),
                       bg=color, fg="white",
                       font=("Arial", 12, "bold"),
                       width=40, height=2,
                       cursor="hand2")
        btn.pack(pady=10)
        
        # Описание
        desc_label = tk.Label(parent, text=description,
                             font=("Arial", 9), 
                             fg="#BDBDBD", bg=self.bg_color)
        desc_label.pack()
    
    def open_file(self, filename):
        """Открыть файл"""
        file_path = os.path.join(self.assets_path, filename)
        
        if not os.path.exists(file_path):
            messagebox.showerror("Ошибка", f"Файл не найден:\n{file_path}")
            self.status_bar.config(text=f"Ошибка: файл не найден")
            return
        
        try:
            self.status_bar.config(text=f"Открытие: {filename}...")
            
            # Открываем файл через проводник (откроется в программе по умолчанию)
            os.startfile(file_path)
            
            self.status_bar.config(text=f"Открыт: {filename}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось открыть файл:\n{e}")
            self.status_bar.config(text=f"Ошибка открытия файла")
