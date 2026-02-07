# -*- coding: utf-8 -*-
"""
TTFD-Optimizer - Оптимизация Windows
Главный файл запуска
"""
import tkinter as tk
from gui.main_window import OptimizerGUI

def main():
    root = tk.Tk()
    app = OptimizerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
