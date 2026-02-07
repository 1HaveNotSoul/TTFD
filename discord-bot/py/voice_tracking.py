# Система отслеживания времени в голосовых каналах

import discord
from discord.ext import commands
from datetime import datetime, timedelta
import json
import os

# Файл для хранения данных о войс активности
VOICE_DATA_FILE = 'json/voice_data.json'

# Активные сессии {user_id: {'channel_id': int, 'join_time': str, 'session_start': str}}
active_sessions = {}

def load_voice_data():
    """Загрузить данные о войс активности"""
    if os.path.exists(VOICE_DATA_FILE):
        try:
            with open(VOICE_DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {
        'users': {},  # {user_id: {'total_time': seconds, 'sessions': []}}
        'channels': {}  # {channel_id: {'total_time': seconds, 'sessions': []}}
    }

def save_voice_data(data):
    """Сохранить данные о войс активности"""
    os.makedirs('json', exist_ok=True)
    with open(VOICE_DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

async def on_voice_state_update(member, before, after, db=None):
    """Обработка изменения голосового состояния"""
    user_id = str(member.id)
    now = datetime.now()
    
    voice_data = load_voice_data()
    
    # Инициализация данных пользователя
    if user_id not in voice_data['users']:
        voice_data['users'][user_id] = {
            'total_time': 0,
            'sessions': [],
            'username': member.name
        }
    
    # Пользователь зашёл в войс канал
    if before.channel is None and after.channel is not None:
        channel_id = str(after.channel.id)
        
        # Инициализация данных канала
        if channel_id not in voice_data['channels']:
            voice_data['channels'][channel_id] = {
                'total_time': 0,
                'sessions': [],
                'channel_name': after.channel.name
            }
        
        # Сохраняем активную сессию
        active_sessions[user_id] = {
            'channel_id': channel_id,
            'join_time': now.isoformat(),
            'session_start': now.isoformat()
        }
        
        print(f"🎤 {member.name} зашёл в {after.channel.name}")
    
    # Пользователь вышел из войс канала
    elif before.channel is not None and after.channel is None:
        if user_id in active_sessions:
            session = active_sessions[user_id]
            channel_id = session['channel_id']
            join_time = datetime.fromisoformat(session['join_time'])
            
            # Вычисляем время сессии
            session_duration = (now - join_time).total_seconds()
            
            # Обновляем данные пользователя
            voice_data['users'][user_id]['total_time'] += session_duration
            voice_data['users'][user_id]['sessions'].append({
                'channel_id': channel_id,
                'start': session['join_time'],
                'end': now.isoformat(),
                'duration': session_duration
            })
            
            # Обновляем данные канала
            if channel_id in voice_data['channels']:
                voice_data['channels'][channel_id]['total_time'] += session_duration
                voice_data['channels'][channel_id]['sessions'].append({
                    'user_id': user_id,
                    'start': session['join_time'],
                    'end': now.isoformat(),
                    'duration': session_duration
                })
            
            # Начисляем XP за время в войсе
            if db and session_duration >= 60:  # Минимум 1 минута
                xp_reward = calculate_voice_xp(session_duration)
                if xp_reward > 0:
                    user = db.get_user(user_id)
                    old_xp = user.get('xp', 0)
                    user['xp'] = old_xp + xp_reward
                    db.check_rank_up(user)
                    db.save_user(user_id, user)
                    print(f"💎 {member.name} получил {xp_reward} XP за {format_time(session_duration)} в войсе")
            
            # Удаляем активную сессию
            del active_sessions[user_id]
            
            print(f"🎤 {member.name} вышел из войса (время: {format_time(session_duration)})")
            
            save_voice_data(voice_data)
    
    # Пользователь переключился между каналами
    elif before.channel is not None and after.channel is not None and before.channel != after.channel:
        # Завершаем старую сессию
        if user_id in active_sessions:
            session = active_sessions[user_id]
            old_channel_id = session['channel_id']
            join_time = datetime.fromisoformat(session['join_time'])
            
            session_duration = (now - join_time).total_seconds()
            
            # Обновляем данные для старого канала
            voice_data['users'][user_id]['total_time'] += session_duration
            voice_data['users'][user_id]['sessions'].append({
                'channel_id': old_channel_id,
                'start': session['join_time'],
                'end': now.isoformat(),
                'duration': session_duration
            })
            
            if old_channel_id in voice_data['channels']:
                voice_data['channels'][old_channel_id]['total_time'] += session_duration
                voice_data['channels'][old_channel_id]['sessions'].append({
                    'user_id': user_id,
                    'start': session['join_time'],
                    'end': now.isoformat(),
                    'duration': session_duration
                })
            
            # Начисляем XP за время в старом канале
            if db and session_duration >= 60:  # Минимум 1 минута
                xp_reward = calculate_voice_xp(session_duration)
                if xp_reward > 0:
                    user = db.get_user(user_id)
                    old_xp = user.get('xp', 0)
                    user['xp'] = old_xp + xp_reward
                    db.check_rank_up(user)
                    db.save_user(user_id, user)
                    print(f"💎 {member.name} получил {xp_reward} XP за {format_time(session_duration)} в войсе")
        
        # Начинаем новую сессию
        new_channel_id = str(after.channel.id)
        
        if new_channel_id not in voice_data['channels']:
            voice_data['channels'][new_channel_id] = {
                'total_time': 0,
                'sessions': [],
                'channel_name': after.channel.name
            }
        
        active_sessions[user_id] = {
            'channel_id': new_channel_id,
            'join_time': now.isoformat(),
            'session_start': now.isoformat()
        }
        
        print(f"🎤 {member.name} переключился в {after.channel.name}")
        
        save_voice_data(voice_data)

def format_time(seconds):
    """Форматировать время в читаемый вид"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}ч {minutes}м {secs}с"
    elif minutes > 0:
        return f"{minutes}м {secs}с"
    else:
        return f"{secs}с"

def get_top_users(limit=10):
    """Получить топ пользователей по времени в войсе"""
    voice_data = load_voice_data()
    
    users = []
    for user_id, data in voice_data['users'].items():
        users.append({
            'user_id': user_id,
            'username': data.get('username', 'Unknown'),
            'total_time': data['total_time'],
            'sessions_count': len(data['sessions'])
        })
    
    users.sort(key=lambda x: x['total_time'], reverse=True)
    return users[:limit]

def get_top_channels(limit=5):
    """Получить топ каналов по активности"""
    voice_data = load_voice_data()
    
    channels = []
    for channel_id, data in voice_data['channels'].items():
        channels.append({
            'channel_id': channel_id,
            'channel_name': data.get('channel_name', 'Unknown'),
            'total_time': data['total_time'],
            'sessions_count': len(data['sessions'])
        })
    
    channels.sort(key=lambda x: x['total_time'], reverse=True)
    return channels[:limit]

def get_longest_session():
    """Получить самую длительную сессию"""
    voice_data = load_voice_data()
    
    longest = None
    longest_duration = 0
    
    for user_id, data in voice_data['users'].items():
        for session in data['sessions']:
            if session['duration'] > longest_duration:
                longest_duration = session['duration']
                longest = {
                    'user_id': user_id,
                    'username': data.get('username', 'Unknown'),
                    'channel_id': session['channel_id'],
                    'duration': session['duration'],
                    'start': session['start'],
                    'end': session['end']
                }
    
    return longest

def get_user_voice_stats(user_id):
    """Получить статистику пользователя"""
    voice_data = load_voice_data()
    user_id = str(user_id)
    
    if user_id not in voice_data['users']:
        return None
    
    data = voice_data['users'][user_id]
    
    # Находим самую длительную сессию пользователя
    longest_session = 0
    for session in data['sessions']:
        if session['duration'] > longest_session:
            longest_session = session['duration']
    
    return {
        'total_time': data['total_time'],
        'sessions_count': len(data['sessions']),
        'longest_session': longest_session,
        'average_session': data['total_time'] / len(data['sessions']) if data['sessions'] else 0
    }


def calculate_voice_xp(duration_seconds):
    """
    Рассчитать XP за время в войсе
    
    Формула: 1 XP за каждые 5 минут (300 секунд)
    Максимум: 50 XP за сессию (250 минут)
    """
    # 1 XP за 5 минут
    xp = int(duration_seconds / 300)
    
    # Максимум 50 XP за сессию
    return min(xp, 50)

def calculate_message_xp(message_length):
    """
    Рассчитать XP за сообщение
    
    Формула:
    - Короткие сообщения (< 10 символов): 0 XP (спам)
    - Нормальные сообщения (10-100 символов): 1-3 XP
    - Длинные сообщения (> 100 символов): 3-5 XP
    """
    if message_length < 10:
        return 0  # Спам
    elif message_length < 50:
        return 1
    elif message_length < 100:
        return 2
    elif message_length < 200:
        return 3
    elif message_length < 500:
        return 4
    else:
        return 5  # Максимум за очень длинное сообщение

# Кулдаун для сообщений (чтобы избежать спама)
# {user_id: last_message_time}
message_cooldowns = {}

def can_earn_message_xp(user_id):
    """
    Проверить можно ли получить XP за сообщение
    Кулдаун: 30 секунд между сообщениями
    """
    now = datetime.now()
    user_id = str(user_id)
    
    if user_id not in message_cooldowns:
        message_cooldowns[user_id] = now
        return True
    
    last_message = message_cooldowns[user_id]
    time_diff = (now - last_message).total_seconds()
    
    if time_diff >= 30:  # 30 секунд кулдаун
        message_cooldowns[user_id] = now
        return True
    
    return False
