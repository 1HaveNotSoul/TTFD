from flask import Flask, render_template, jsonify, send_from_directory, request, session, redirect, url_for, flash
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Импорт базы данных
try:
    from database_postgres import db, RANKS
    print("✅ Используется PostgreSQL")
except Exception as e:
    from database import db, RANKS
    print(f"⚠️ Используется JSON файл: {e}")

# Импорт Discord OAuth
from discord_oauth import get_oauth_url, handle_oauth_callback

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Отключение кэша для разработки
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.config['TEMPLATES_AUTO_RELOAD'] = True

# Email конфигурация (нужно будет настроить)
EMAIL_CONFIG = {
    'smtp_server': 'smtp.gmail.com',  # Или другой SMTP сервер
    'smtp_port': 587,
    'sender_email': 'your-bot-email@gmail.com',  # Email бота
    'sender_password': 'your-app-password',  # Пароль приложения
    'sender_name': 'TTFD Bot'
}

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

def get_current_user():
    """Получить текущего пользователя из сессии"""
    if 'token' in session:
        return db.get_account_by_token(session['token'])
    return None

@app.route('/')
def index():
    """Главная страница"""
    current_user = get_current_user()
    
    # # Автологин для тестирования (ОТКЛЮЧЕНО - используйте Discord OAuth)
    # if not current_user:
    #     test_user = db.get_account_by_username('testuser')
    #     if not test_user:
    #         result = db.create_account('testuser@local.test', 'testuser', 'password123', 'Test User')
    #         if result['success']:
    #             test_user = db.get_account_by_username('testuser')
    #     
    #     if test_user:
    #         login_result = db.login('testuser', 'password123')
    #         if login_result['success']:
    #             session['token'] = login_result['token']
    #             current_user = db.get_account_by_token(session['token'])
    
    return render_template('index.html', user=current_user)

@app.route('/settings')
def settings():
    """Страница настроек"""
    current_user = get_current_user()
    if not current_user:
        flash('Войдите, чтобы получить доступ к настройкам', 'info')
        return redirect(url_for('login'))
    return render_template('settings.html', user=current_user)

@app.route('/profile')
def profile():
    """Страница профиля"""
    current_user = get_current_user()
    if not current_user:
        flash('Войдите, чтобы получить доступ к профилю', 'info')
        return redirect(url_for('login'))
    return render_template('profile.html', user=current_user)

@app.route('/customize')
def customize():
    """Страница кастомизации темы"""
    current_user = get_current_user()
    if not current_user:
        flash('Войдите, чтобы получить доступ к кастомизации', 'info')
        return redirect(url_for('login'))
    return render_template('customize.html', user=current_user)

@app.route('/music_player')
def music_player():
    """Скрытый плеер для непрерывного воспроизведения музыки"""
    return render_template('music_player.html')

@app.route('/shop')
def shop():
    """Интернет-магазин TTFD"""
    current_user = get_current_user()
    if not current_user:
        flash('Войдите, чтобы получить доступ к магазину', 'info')
        return redirect(url_for('login'))
    return render_template('shop.html', user=current_user)

@app.route('/download/bat_optimizer')
def download_bat_optimizer():
    """Скачивание BAT файлов для оптимизации Windows"""
    import os
    from flask import send_file
    
    # Путь к файлу
    file_path = os.path.join(os.path.dirname(__file__), 'templates', 'shop', 'батники', 'батники.rar')
    
    if os.path.exists(file_path):
        return send_file(
            file_path,
            as_attachment=True,
            download_name='TTFD_Windows_Optimizer.rar',
            mimetype='application/x-rar-compressed'
        )
    else:
        return jsonify({'error': 'Файл не найден'}), 404

@app.route('/static/фотографии/<path:filename>')
def serve_photos(filename):
    """Раздача фотографий"""
    return send_from_directory('фотографии', filename)

@app.route('/api/update_profile', methods=['POST'])
def api_update_profile():
    """API для обновления профиля"""
    current_user = get_current_user()
    if not current_user:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401
    
    data = request.get_json()
    result = db.update_profile(current_user['id'], **data)
    return jsonify(result)

@app.route('/api/send_notification', methods=['POST'])
def api_send_notification():
    """API для отправки email уведомлений"""
    try:
        data = request.get_json()
        recipient_email = data.get('email')
        subject = data.get('subject', 'Уведомление от TTFD')
        message = data.get('message', 'Это тестовое уведомление')
        
        if not recipient_email:
            return jsonify({'success': False, 'error': 'Email не указан'})
        
        # Отправка email
        result = send_email(recipient_email, subject, message)
        
        if result:
            return jsonify({'success': True, 'message': 'Уведомление отправлено!'})
        else:
            return jsonify({'success': False, 'error': 'Ошибка отправки'})
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/proxy_audio', methods=['GET'])
def api_proxy_audio():
    """API прокси для VK аудио (обход CORS)"""
    import requests
    from flask import Response, stream_with_context
    
    try:
        audio_url = request.args.get('url')
        
        if not audio_url:
            return jsonify({'error': 'URL не указан'}), 400
        
        # Проверяем что это VK ссылка
        if 'vk.com' not in audio_url and 'userapi.com' not in audio_url:
            return jsonify({'error': 'Поддерживаются только VK ссылки'}), 400
        
        # Делаем запрос к VK с правильными заголовками
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://vk.com/',
            'Origin': 'https://vk.com'
        }
        
        # Получаем аудио поток
        response = requests.get(audio_url, headers=headers, stream=True)
        
        if response.status_code != 200:
            return jsonify({'error': 'Не удалось загрузить аудио'}), response.status_code
        
        # Возвращаем аудио с правильными CORS заголовками
        def generate():
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    yield chunk
        
        return Response(
            stream_with_context(generate()),
            content_type=response.headers.get('content-type', 'audio/mpeg'),
            headers={
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET',
                'Cache-Control': 'no-cache'
            }
        )
        
    except Exception as e:
        print(f"Ошибка прокси: {e}")
        return jsonify({'error': str(e)}), 500

def send_email(to_email, subject, message):
    """Функция отправки email"""
    try:
        # Создаём сообщение
        msg = MIMEMultipart('alternative')
        msg['From'] = f"{EMAIL_CONFIG['sender_name']} <{EMAIL_CONFIG['sender_email']}>"
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # HTML версия письма
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background: #1a1a2e; color: #ffffff; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background: #16213e; border-radius: 12px; padding: 30px; border: 2px solid #667eea;">
                    <h2 style="color: #667eea; margin-top: 0;">🎮 TTFD Notification</h2>
                    <p style="font-size: 16px; line-height: 1.6;">{message}</p>
                    <hr style="border: none; border-top: 1px solid #667eea; margin: 20px 0;">
                    <p style="font-size: 14px; color: #888;">
                        Это автоматическое уведомление от TTFD Bot.<br>
                        Если вы не ожидали это письмо, просто проигнорируйте его.
                    </p>
                </div>
            </body>
        </html>
        """
        
        # Текстовая версия (fallback)
        text_body = f"{subject}\n\n{message}\n\n---\nЭто автоматическое уведомление от TTFD Bot."
        
        msg.attach(MIMEText(text_body, 'plain'))
        msg.attach(MIMEText(html_body, 'html'))
        
        # Подключение к SMTP серверу и отправка
        with smtplib.SMTP(EMAIL_CONFIG['smtp_server'], EMAIL_CONFIG['smtp_port']) as server:
            server.starttls()
            server.login(EMAIL_CONFIG['sender_email'], EMAIL_CONFIG['sender_password'])
            server.send_message(msg)
        
        return True
        
    except Exception as e:
        print(f"Ошибка отправки email: {e}")
        return False

if __name__ == '__main__':
    # Для онлайн версии используется production WSGI сервер (gunicorn)
    # Локальный запуск отключен
    print("⚠️ Локальный запуск отключен. Используйте production WSGI сервер (gunicorn)")
    print("💡 Для локальной разработки используйте TTFD-WebsiteOffline")
    # print("Регай: http://localhost:3000")
    # app.run(debug=True, host='0.0.0.0', port=3000)

# ==================== DISCORD OAUTH ====================

@app.route('/login')
def login():
    """Страница входа"""
    return render_template('login.html')

@app.route('/auth/discord')
def auth_discord():
    """Начать авторизацию через Discord"""
    try:
        oauth_url = get_oauth_url()
        if not oauth_url:
            flash('Discord OAuth не настроен. Обратитесь к администратору.', 'error')
            return redirect(url_for('login'))
        
        return redirect(oauth_url)
    except Exception as e:
        print(f"❌ Ошибка при создании OAuth URL: {e}")
        flash('Ошибка при подключении к Discord', 'error')
        return redirect(url_for('login'))

@app.route('/auth/discord/callback')
def auth_discord_callback():
    """Обработать callback от Discord"""
    print("=" * 50)
    print("🔵 Discord OAuth Callback")
    print("=" * 50)
    
    try:
        # Проверяем наличие ошибки от Discord
        error = request.args.get('error')
        if error:
            error_description = request.args.get('error_description', 'Unknown error')
            print(f"❌ Ошибка от Discord: {error} - {error_description}")
            flash(f'Ошибка Discord: {error_description}', 'error')
            return redirect(url_for('login'))
        
        print("🔄 Вызов handle_oauth_callback...")
        result = handle_oauth_callback(db)
        print(f"📊 Результат OAuth: {result}")
        
        if result['success']:
            print(f"✅ OAuth успешен! Токен: {result['token'][:10]}...")
            session['token'] = result['token']
            print(f"✅ Токен сохранен в сессию")
            
            if result['is_new']:
                flash(f'Добро пожаловать, {result["account"]["display_name"]}!', 'success')
            elif result.get('was_linked'):
                flash(f'Discord успешно привязан! С возвращением, {result["account"]["display_name"]}!', 'success')
            else:
                flash(f'С возвращением, {result["account"]["display_name"]}!', 'success')
            
            print("🔄 Редирект на главную страницу...")
            return redirect(url_for('index'))
        else:
            error_msg = result.get('error', 'Unknown error')
            print(f"❌ OAuth не удался: {error_msg}")
            flash(f'Ошибка авторизации: {error_msg}', 'error')
            return redirect(url_for('login'))
    except Exception as e:
        print(f"❌ Критическая ошибка в OAuth callback: {e}")
        import traceback
        traceback.print_exc()
        flash('Произошла ошибка при авторизации', 'error')
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    """Выход из аккаунта"""
    if 'token' in session:
        db.logout(session['token'])
        session.pop('token', None)
    flash('Вы вышли из аккаунта', 'info')
    return redirect(url_for('index'))
