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

async def on_voice_state_update(member, before, after):
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
