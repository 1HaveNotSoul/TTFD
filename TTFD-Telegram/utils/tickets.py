"""
Утилиты для работы с тикетами
Версия 2.0 - с file locking и расширенными полями
"""

import json
import os
import sys
from datetime import datetime
from config import TICKETS_FILE

# File locking для Windows и Linux
if sys.platform == 'win32':
    import msvcrt
    def lock_file(f):
        msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)
    def unlock_file(f):
        msvcrt.locking(f.fileno(), msvcrt.LK_UNLCK, 1)
else:
    import fcntl
    def lock_file(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    def unlock_file(f):
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)

def load_tickets():
    """Загрузить тикеты с file locking"""
    os.makedirs('data', exist_ok=True)
    
    if not os.path.exists(TICKETS_FILE):
        return {'tickets': {}, 'next_id': 1}
    
    try:
        with open(TICKETS_FILE, 'r', encoding='utf-8') as f:
            lock_file(f)
            try:
                data = json.load(f)
            finally:
                unlock_file(f)
            return data
    except Exception as e:
        print(f"❌ Ошибка загрузки тикетов: {e}")
        return {'tickets': {}, 'next_id': 1}

def save_tickets(tickets_data):
    """Сохранить тикеты с file locking (атомарная запись)"""
    try:
        # Сначала пишем во временный файл
        temp_file = TICKETS_FILE + '.tmp'
        with open(temp_file, 'w', encoding='utf-8') as f:
            lock_file(f)
            try:
                json.dump(tickets_data, f, indent=2, ensure_ascii=False)
                f.flush()
                os.fsync(f.fileno())
            finally:
                unlock_file(f)
        
        # Атомарная замена
        if os.path.exists(TICKETS_FILE):
            os.replace(temp_file, TICKETS_FILE)
        else:
            os.rename(temp_file, TICKETS_FILE)
    except Exception as e:
        print(f"❌ Ошибка сохранения тикетов: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)

def create_ticket(telegram_id, user_name, username, message, category='Общий', priority='medium'):
    """
    Создать новый тикет
    
    Args:
        telegram_id: ID пользователя в Telegram
        user_name: Имя пользователя
        username: Username пользователя
        message: Текст тикета
        category: Категория (Общий, Техническая проблема, Предложение, Жалоба)
        priority: Приоритет (low, medium, high)
    
    Returns:
        ticket_id: ID созданного тикета
    """
    tickets_data = load_tickets()
    
    ticket_id = tickets_data['next_id']
    tickets_data['next_id'] += 1
    
    tickets_data['tickets'][str(ticket_id)] = {
        'id': ticket_id,
        'telegram_id': str(telegram_id),
        'user_name': user_name,
        'username': username,
        'message': message,
        'category': category,
        'priority': priority,
        'status': 'open',
        'assigned_to': None,
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat(),
        'responses': []
    }
    
    save_tickets(tickets_data)
    return ticket_id

def get_ticket(ticket_id):
    """Получить тикет по ID"""
    tickets_data = load_tickets()
    return tickets_data['tickets'].get(str(ticket_id))

def get_user_tickets(telegram_id, status_filter=None):
    """
    Получить тикеты пользователя
    
    Args:
        telegram_id: ID пользователя
        status_filter: Фильтр по статусу (open, in_progress, closed) или None для всех
    """
    tickets_data = load_tickets()
    user_tickets = []
    
    for ticket in tickets_data['tickets'].values():
        if ticket['telegram_id'] == str(telegram_id):
            if status_filter is None or ticket['status'] == status_filter:
                user_tickets.append(ticket)
    
    # Сортируем по дате создания (новые первые)
    user_tickets.sort(key=lambda x: x['created_at'], reverse=True)
    return user_tickets

def get_all_tickets(status_filter=None, priority_filter=None):
    """
    Получить все тикеты с фильтрами
    
    Args:
        status_filter: Фильтр по статусу (open, in_progress, closed) или None
        priority_filter: Фильтр по приоритету (low, medium, high) или None
    """
    tickets_data = load_tickets()
    all_tickets = list(tickets_data['tickets'].values())
    
    # Применяем фильтры
    if status_filter:
        all_tickets = [t for t in all_tickets if t['status'] == status_filter]
    
    if priority_filter:
        all_tickets = [t for t in all_tickets if t['priority'] == priority_filter]
    
    # Сортируем: сначала по приоритету (high > medium > low), потом по дате
    priority_order = {'high': 0, 'medium': 1, 'low': 2}
    all_tickets.sort(key=lambda x: (priority_order.get(x['priority'], 1), x['created_at']), reverse=True)
    
    return all_tickets

def update_ticket_status(ticket_id, status):
    """
    Обновить статус тикета
    
    Args:
        ticket_id: ID тикета
        status: Новый статус (open, in_progress, closed)
    """
    tickets_data = load_tickets()
    
    if str(ticket_id) in tickets_data['tickets']:
        tickets_data['tickets'][str(ticket_id)]['status'] = status
        tickets_data['tickets'][str(ticket_id)]['updated_at'] = datetime.now().isoformat()
        save_tickets(tickets_data)
        return True
    return False

def assign_ticket(ticket_id, admin_id, admin_name):
    """
    Назначить тикет админу
    
    Args:
        ticket_id: ID тикета
        admin_id: ID админа
        admin_name: Имя админа
    """
    tickets_data = load_tickets()
    
    if str(ticket_id) in tickets_data['tickets']:
        tickets_data['tickets'][str(ticket_id)]['assigned_to'] = {
            'admin_id': str(admin_id),
            'admin_name': admin_name,
            'assigned_at': datetime.now().isoformat()
        }
        tickets_data['tickets'][str(ticket_id)]['status'] = 'in_progress'
        tickets_data['tickets'][str(ticket_id)]['updated_at'] = datetime.now().isoformat()
        save_tickets(tickets_data)
        return True
    return False

def add_ticket_response(ticket_id, responder_id, responder_name, message, is_admin=False):
    """
    Добавить ответ к тикету
    
    Args:
        ticket_id: ID тикета
        responder_id: ID отвечающего
        responder_name: Имя отвечающего
        message: Текст ответа
        is_admin: Ответ от админа или пользователя
    """
    tickets_data = load_tickets()
    
    if str(ticket_id) in tickets_data['tickets']:
        tickets_data['tickets'][str(ticket_id)]['responses'].append({
            'responder_id': str(responder_id),
            'responder_name': responder_name,
            'message': message,
            'is_admin': is_admin,
            'created_at': datetime.now().isoformat()
        })
        tickets_data['tickets'][str(ticket_id)]['updated_at'] = datetime.now().isoformat()
        save_tickets(tickets_data)
        return True
    return False

def get_ticket_stats():
    """Получить статистику по тикетам"""
    tickets_data = load_tickets()
    all_tickets = list(tickets_data['tickets'].values())
    
    return {
        'total': len(all_tickets),
        'open': len([t for t in all_tickets if t['status'] == 'open']),
        'in_progress': len([t for t in all_tickets if t['status'] == 'in_progress']),
        'closed': len([t for t in all_tickets if t['status'] == 'closed']),
        'high_priority': len([t for t in all_tickets if t['priority'] == 'high']),
        'medium_priority': len([t for t in all_tickets if t['priority'] == 'medium']),
        'low_priority': len([t for t in all_tickets if t['priority'] == 'low'])
    }
