# Веб-сайт для бота
from flask import Flask, render_template, jsonify, request, session, redirect, url_for, flash
from datetime import datetime
import config
import os
from database import db, RANKS
from functools import wraps

app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY

# Данные бота (будут обновляться из main.py)
bot_data = {
    'status': 'offline',
    'uptime': 0,
    'guilds': 0,
    'users': 0,
    'commands_used': 0,
    'messages_seen': 0,
    'latency': 0,
    'online_members': [],
}

@app.route('/')
def index():
    """Главная страница"""
    current_user = None
    if 'token' in session:
        current_user = db.get_account_by_token(session['token'])
    return render_template('index.html', bot_data=bot_data, current_user=current_user)

@app.route('/game')
def game():
    """Страница мини-игры"""
    current_user = None
    if 'token' in session:
        current_user = db.get_account_by_token(session['token'])
    return render_template('game.html', current_user=current_user)

@app.route('/leaderboard')
def leaderboard():
    """Таблица лидеров"""
    leaders = db.get_leaderboard(50)
    current_user = None
    if 'token' in session:
        current_user = db.get_account_by_token(session['token'])
    return render_template('leaderboard.html', leaders=leaders, ranks=RANKS, current_user=current_user)

@app.route('/ranks')
def ranks():
    """Список всех рангов"""
    current_user = None
    if 'token' in session:
        current_user = db.get_account_by_token(session['token'])
    return render_template('ranks.html', ranks=RANKS, current_user=current_user)

# ==================== АУТЕНТИФИКАЦИЯ ====================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация"""
    if request.method == 'POST':
        data = request.json
        result = db.create_account(
            email=data.get('email'),
            username=data.get('username'),
            password=data.get('password'),
            display_name=data.get('display_name')
        )
        return jsonify(result)
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Вход"""
    if request.method == 'POST':
        data = request.json
        result = db.login(data.get('username'), data.get('password'))
        
        if result['success']:
            session['token'] = result['token']
        
        return jsonify(result)
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Выход"""
    if 'token' in session:
        db.logout(session['token'])
        session.pop('token', None)
    return redirect(url_for('index'))

# ==================== ПРОФИЛИ ====================

@app.route('/profile/<username>')
def profile(username):
    """Публичный профиль пользователя"""
    account = db.get_account_by_username(username)
    if not account:
        return "Пользователь не найден", 404
    
    # Получаем игровые данные если привязан Discord
    game_data = None
    if account.get('discord_id'):
        game_data = db.get_user(account['discord_id'])
    
    current_user = None
    if 'token' in session:
        current_user = db.get_account_by_token(session['token'])
    
    return render_template('profile.html', account=account, game_data=game_data, current_user=current_user, ranks=RANKS)

@app.route('/settings')
def settings():
    """Настройки профиля"""
    if 'token' not in session:
        return redirect(url_for('login'))
    
    current_user = db.get_account_by_token(session['token'])
    if not current_user:
        return redirect(url_for('login'))
    
    return render_template('settings.html', current_user=current_user)

@app.route('/api/update_profile', methods=['POST'])
def api_update_profile():
    """API: обновить профиль"""
    if 'token' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    account = db.get_account_by_token(session['token'])
    if not account:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    data = request.json
    result = db.update_profile(account['id'], **data)
    return jsonify(result)

@app.route('/api/change_password', methods=['POST'])
def api_change_password():
    """API: сменить пароль"""
    if 'token' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    account = db.get_account_by_token(session['token'])
    if not account:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    data = request.json
    result = db.change_password(
        account['id'],
        data.get('old_password'),
        data.get('new_password')
    )
    return jsonify(result)

@app.route('/api/link_discord', methods=['POST'])
def api_link_discord():
    """API: привязать Discord ID"""
    if 'token' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    account = db.get_account_by_token(session['token'])
    if not account:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    data = request.json
    result = db.link_discord(account['id'], data.get('discord_id'))
    return jsonify(result)

# ==================== API ====================

@app.route('/api/stats')
def api_stats():
    """API: статистика бота"""
    return jsonify(bot_data)

@app.route('/api/status')
def api_status():
    """API: статус бота"""
    return jsonify({
        'status': bot_data['status'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/online')
def api_online():
    """API: онлайн пользователи"""
    return jsonify({
        'count': len(bot_data['online_members']),
        'members': bot_data['online_members']
    })

@app.route('/api/user/<user_id>')
def api_user(user_id):
    """API: данные пользователя"""
    user = db.get_user(user_id)
    rank = db.get_rank_info(user['rank_id'])
    
    # Следующий ранг
    next_rank = None
    if user['rank_id'] < len(RANKS):
        next_rank = RANKS[user['rank_id']]
    
    return jsonify({
        'user': user,
        'rank': rank,
        'next_rank': next_rank
    })

@app.route('/api/click', methods=['POST'])
def api_click():
    """API: обработка клика в игре"""
    data = request.json
    user_id = data.get('user_id')
    
    if not user_id:
        return jsonify({'error': 'user_id required'}), 400
    
    user = db.get_user(user_id)
    user['clicks'] += 1
    
    # Даём 1 XP за клик
    xp_result = db.add_xp(user_id, 1)
    
    # Обновляем прогресс заданий на основе общего количества кликов
    for task in user['daily_tasks']:
        if not task['completed'] and 'клик' in task['name'].lower():
            # Используем общее количество кликов как прогресс
            task['progress'] = min(user['clicks'], task['target'])
    
    db.save_data()
    db.data['global_stats']['total_clicks'] += 1
    
    return jsonify({
        'success': True,
        'clicks': user['clicks'],
        'xp': user['xp'],
        'coins': user['coins'],
        'rank_up': xp_result['rank_up'],
        'new_rank': db.get_rank_info(xp_result['new_rank']) if xp_result['rank_up'] else None
    })

@app.route('/api/tasks/<user_id>')
def api_tasks(user_id):
    """API: получить задания пользователя"""
    user = db.get_user(user_id)
    return jsonify({
        'tasks': user['daily_tasks']
    })

@app.route('/api/complete_task', methods=['POST'])
def api_complete_task():
    """API: завершить задание"""
    data = request.json
    user_id = data.get('user_id')
    task_id = data.get('task_id')
    
    if not user_id or not task_id:
        return jsonify({'error': 'user_id and task_id required'}), 400
    
    result = db.complete_task(user_id, task_id)
    return jsonify(result)

@app.route('/api/leaderboard')
def api_leaderboard():
    """API: таблица лидеров"""
    leaders = db.get_leaderboard(50)
    return jsonify({
        'leaders': leaders,
        'ranks': RANKS
    })

@app.route('/api/ranks')
def api_ranks():
    """API: все ранги"""
    return jsonify({
        'ranks': RANKS
    })

def update_bot_data(data):
    """Обновить данные бота"""
    global bot_data
    bot_data.update(data)

def run_web():
    """Запуск веб-сервера"""
    print(f"🌐 Веб-сервер запущен на http://localhost:{config.WEB_PORT}")
    app.run(host='0.0.0.0', port=config.WEB_PORT, debug=False)

if __name__ == "__main__":
    run_web()
