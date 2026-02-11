#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TTFD-Cleaner - UI Effects Module
Дымный эффект и анимированный фон
"""

import tkinter as tk
import random
import math
from typing import List, Tuple, Optional


class Particle:
    """Частица дыма"""
    
    def __init__(self, x: float, y: float):
        self.x = x + random.uniform(-10, 10)
        self.y = y
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(-2, -1)
        self.life = 50
        self.max_life = 50
        self.size = random.uniform(3, 8)
        self.id = None
    
    def update(self):
        """Обновить позицию и состояние"""
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        self.size += 0.1
        
        # Добавить небольшое колебание
        self.vx += random.uniform(-0.1, 0.1)
        self.vy += random.uniform(-0.05, 0.05)
    
    def is_dead(self) -> bool:
        """Проверить, мертва ли частица"""
        return self.life <= 0
    
    def get_alpha(self) -> int:
        """Получить прозрачность (0-255)"""
        return int(255 * (self.life / self.max_life))
    
    def get_color(self) -> str:
        """Получить цвет с учётом прозрачности"""
        alpha = self.get_alpha()
        # Серый цвет с прозрачностью
        return f'#{alpha:02x}{alpha:02x}{alpha:02x}'


class SmokeEffect:
    """Дымный эффект при наведении курсора"""
    
    def __init__(self, canvas: tk.Canvas):
        self.canvas = canvas
        self.particles: List[Particle] = []
        self.running = False
        self.animation_id = None
        self.spawn_rate = 5  # Количество частиц за раз
    
    def start(self, x: int, y: int):
        """Начать эффект в позиции (x, y)"""
        self.running = True
        
        # Создать несколько частиц
        for _ in range(self.spawn_rate):
            particle = Particle(x, y)
            
            # Создать овал на canvas
            particle.id = self.canvas.create_oval(
                particle.x - particle.size,
                particle.y - particle.size,
                particle.x + particle.size,
                particle.y + particle.size,
                fill=particle.get_color(),
                outline='',
                stipple='gray50'
            )
            
            self.particles.append(particle)
        
        # Запустить анимацию если ещё не запущена
        if self.animation_id is None:
            self.update()
    
    def stop(self):
        """Остановить создание новых частиц"""
        self.running = False
    
    def update(self):
        """Обновить все частицы"""
        # Обновить каждую частицу
        for particle in self.particles[:]:
            particle.update()
            
            # Обновить на canvas
            try:
                self.canvas.coords(
                    particle.id,
                    particle.x - particle.size,
                    particle.y - particle.size,
                    particle.x + particle.size,
                    particle.y + particle.size
                )
                
                # Обновить цвет (прозрачность)
                self.canvas.itemconfig(particle.id, fill=particle.get_color())
            except:
                pass
            
            # Удалить мёртвые частицы
            if particle.is_dead():
                try:
                    self.canvas.delete(particle.id)
                except:
                    pass
                self.particles.remove(particle)
        
        # Продолжить анимацию если есть частицы
        if self.particles or self.running:
            self.animation_id = self.canvas.after(30, self.update)
        else:
            self.animation_id = None
    
    def clear(self):
        """Очистить все частицы"""
        for particle in self.particles:
            try:
                self.canvas.delete(particle.id)
            except:
                pass
        self.particles.clear()
        self.running = False
        if self.animation_id:
            self.canvas.after_cancel(self.animation_id)
            self.animation_id = None


class AnimatedBackground:
    """Анимированный фон с градиентом"""
    
    def __init__(self, canvas: tk.Canvas, width: int, height: int):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.gradient_offset = 0
        self.animation_id = None
        
        # Цвета градиента (тёмная тема)
        self.color1 = (30, 30, 40)   # Тёмно-синий
        self.color2 = (50, 50, 60)   # Светло-серый
        
        self.create_gradient()
    
    def create_gradient(self):
        """Создать градиентный фон"""
        # Создать вертикальный градиент
        steps = 100
        for i in range(steps):
            y1 = (self.height * i) // steps
            y2 = (self.height * (i + 1)) // steps
            
            # Интерполяция цвета
            ratio = i / steps
            r = int(self.color1[0] + (self.color2[0] - self.color1[0]) * ratio)
            g = int(self.color1[1] + (self.color2[1] - self.color1[1]) * ratio)
            b = int(self.color1[2] + (self.color2[2] - self.color1[2]) * ratio)
            
            color = f'#{r:02x}{g:02x}{b:02x}'
            
            self.canvas.create_rectangle(
                0, y1, self.width, y2,
                fill=color,
                outline=''
            )
    
    def start_animation(self):
        """Запустить анимацию фона"""
        if self.animation_id is None:
            self.animate()
    
    def stop_animation(self):
        """Остановить анимацию фона"""
        if self.animation_id:
            self.canvas.after_cancel(self.animation_id)
            self.animation_id = None
    
    def animate(self):
        """Анимация градиента"""
        # Простая анимация - изменение оттенка
        self.gradient_offset += 1
        
        # Обновить цвета (плавное изменение)
        offset = math.sin(self.gradient_offset * 0.01) * 10
        
        # Пересоздать градиент с новыми цветами
        # (для производительности можно оптимизировать)
        
        # Продолжить анимацию
        self.animation_id = self.canvas.after(50, self.animate)


class UIEffectsManager:
    """Менеджер UI эффектов"""
    
    def __init__(self, root: tk.Tk):
        self.root = root
        self.canvas: Optional[tk.Canvas] = None
        self.smoke: Optional[SmokeEffect] = None
        self.background: Optional[AnimatedBackground] = None
        self.mouse_tracking = False
        self.last_mouse_pos = (0, 0)
    
    def setup(self, width: int = 1000, height: int = 650):
        """Настроить эффекты"""
        # Создать Canvas для эффектов (под всеми виджетами)
        self.canvas = tk.Canvas(
            self.root,
            width=width,
            height=height,
            bg='#1e1e28',
            highlightthickness=0
        )
        self.canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self.canvas.lower()  # Поместить под все виджеты
        
        # Создать эффекты
        self.smoke = SmokeEffect(self.canvas)
        self.background = AnimatedBackground(self.canvas, width, height)
        
        # Привязать события мыши
        self.root.bind('<Motion>', self.on_mouse_move)
        self.root.bind('<Leave>', self.on_mouse_leave)
    
    def on_mouse_move(self, event):
        """Обработка движения мыши"""
        if not self.smoke:
            return
        
        # Создать дым с вероятностью 10%
        if random.random() < 0.1:
            self.smoke.start(event.x, event.y)
        
        self.last_mouse_pos = (event.x, event.y)
    
    def on_mouse_leave(self, event):
        """Обработка выхода мыши за пределы окна"""
        if self.smoke:
            self.smoke.stop()
    
    def enable_smoke(self, enabled: bool = True):
        """Включить/выключить дымный эффект"""
        self.mouse_tracking = enabled
        if not enabled and self.smoke:
            self.smoke.clear()
    
    def enable_background_animation(self, enabled: bool = True):
        """Включить/выключить анимацию фона"""
        if not self.background:
            return
        
        if enabled:
            self.background.start_animation()
        else:
            self.background.stop_animation()
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self.smoke:
            self.smoke.clear()
        if self.background:
            self.background.stop_animation()
        if self.canvas:
            self.canvas.destroy()


# Пример использования:
# 
# from ui_effects import UIEffectsManager
# 
# # В __init__ главного окна:
# self.effects = UIEffectsManager(self.root)
# self.effects.setup(width=1000, height=650)
# self.effects.enable_smoke(True)
# self.effects.enable_background_animation(False)  # Опционально
# 
# # При закрытии окна:
# self.effects.cleanup()
