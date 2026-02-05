#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTFD-Cleaner - Окно раздела "Автозапуск"
"""

import tkinter as tk
from tkinter import ttk
import sys
from pathlib import Path


class StartupWindow:
    """Окно раздела автозапуска"""
    
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("TTFD-Cleaner - Автозапуск")
        self.window.geometry("1200x800")
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
    
    def setup_ui(self):
        """Создание UI"""
        # Импортировать Autoruns-style интерфейс
        from gui_autoruns_style import AutorunsStyleStartupTab
        
        # Создать контейнер
        container = ttk.Frame(self.window)
        container.pack(fill=tk.BOTH, expand=True)
        
        # Создать Autoruns-style интерфейс
        self.autoruns_tab = AutorunsStyleStartupTab(
            container,
            self.cli_path,
            self.log
        )
    
    def log(self, message: str):
        """Логирование (для совместимости с AutorunsStyleStartupTab)"""
        print(message)
