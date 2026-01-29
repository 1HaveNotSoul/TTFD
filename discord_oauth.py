# Discord OAuth авторизация
import requests
from flask import redirect, request, session, url_for
from datetime import datetime
import config
import secrets

# Discord OAuth URLs
DISCORD_API_BASE = "https://discord.com/api/v10"
DISCORD_OAUTH_URL = "https://discord.com/api/oauth2/authorize"
DISCORD_TOKEN_URL = "https://discord.com/api/oauth2/token"
DISCORD_USER_URL = f"{DISCORD_API_BASE}/users/@me"

def get_oauth_url():
    """Получить URL для авторизации через Discord"""
    if not config.DISCORD_CLIENT_ID:
        return None
    
    # Генерируем state для защиты от CSRF
    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    
    params = {
        'client_id': config.DISCORD_CLIENT_ID,
        'redirect_uri': config.DISCORD_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'identify email',
        'state': state
    }
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    return f"{DISCORD_OAUTH_URL}?{query_string}"

def exchange_code(code):
    """Обменять код на access token"""
    data = {
        'client_id': config.DISCORD_CLIENT_ID,
        'client_secret': config.DISCORD_CLIENT_SECRET,
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': config.DISCORD_REDIRECT_URI
    }
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    
    try:
        response = requests.post(DISCORD_TOKEN_URL, data=data, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Ошибка обмена кода: {e}")
        return None

def get_user_info(access_token):
    """Получить информацию о пользователе"""
    headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    try:
        response = requests.get(DISCORD_USER_URL, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"❌ Ошибка получения данных пользователя: {e}")
        return None

def handle_oauth_callback(db):
    """Обработать callback от Discord"""
    # Проверяем state для защиты от CSRF
    state = request.args.get('state')
    if state != session.get('oauth_state'):
        return {'success': False, 'error': 'Invalid state'}
    
    # Получаем код авторизации
    code = request.args.get('code')
    if not code:
        return {'success': False, 'error': 'No code provided'}
    
    # Обмениваем код на токен
    token_data = exchange_code(code)
    if not token_data:
        return {'success': False, 'error': 'Failed to exchange code'}
    
    access_token = token_data.get('access_token')
    if not access_token:
        return {'success': False, 'error': 'No access token'}
    
    # Получаем информацию о пользователе
    user_info = get_user_info(access_token)
    if not user_info:
        return {'success': False, 'error': 'Failed to get user info'}
    
    discord_id = user_info.get('id')
    discord_username = user_info.get('username')
    discord_email = user_info.get('email')
    discord_avatar = user_info.get('avatar')
    
    # Формируем URL аватара
    avatar_url = None
    if discord_avatar:
        avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar}.png"
    
    # Проверяем существует ли аккаунт с таким Discord ID
    # Ищем по discord_id в базе
    existing_account = None
    try:
        # Для PostgreSQL
        if hasattr(db, 'get_connection'):
            conn = db.get_connection()
            cur = conn.cursor()
            cur.execute("SELECT * FROM accounts WHERE discord_id = %s", (discord_id,))
            result = cur.fetchone()
            if result:
                existing_account = dict(result)
            cur.close()
            conn.close()
        # Для JSON
        else:
            for acc in db.accounts['accounts'].values():
                if acc.get('discord_id') == discord_id:
                    existing_account = acc
                    break
    except Exception as e:
        print(f"❌ Ошибка поиска аккаунта: {e}")
    
    if existing_account:
        # Аккаунт уже существует - логиним
        token = secrets.token_urlsafe(32)
        
        try:
            if hasattr(db, 'get_connection'):
                conn = db.get_connection()
                cur = conn.cursor()
                cur.execute("INSERT INTO sessions (token, account_id) VALUES (%s, %s)", 
                           (token, existing_account['id']))
                conn.commit()
                cur.close()
                conn.close()
            else:
                db.accounts['sessions'][token] = {
                    'account_id': existing_account['id'],
                    'created_at': datetime.now().isoformat()
                }
                db.save_accounts()
        except Exception as e:
            print(f"❌ Ошибка создания сессии: {e}")
            return {'success': False, 'error': 'Failed to create session'}
        
        return {
            'success': True,
            'token': token,
            'account': existing_account,
            'is_new': False
        }
    else:
        # Создаём новый аккаунт
        username = f"discord_{discord_username}"
        display_name = discord_username
        email = discord_email or f"{discord_id}@discord.user"
        
        # Генерируем случайный пароль (пользователь не будет его знать)
        random_password = secrets.token_urlsafe(32)
        
        # Создаём аккаунт
        result = db.create_account(
            email=email,
            username=username,
            password=random_password,
            display_name=display_name
        )
        
        if not result['success']:
            # Если username занят, добавляем цифры
            username = f"discord_{discord_username}_{discord_id[:6]}"
            result = db.create_account(
                email=email,
                username=username,
                password=random_password,
                display_name=display_name
            )
        
        if result['success']:
            account_id = result['account_id']
            
            # Привязываем Discord ID
            db.link_discord(account_id, discord_id)
            
            # Обновляем аватарку если есть
            if avatar_url:
                db.update_profile(account_id, avatar_url=avatar_url)
            
            # Создаём сессию
            token = secrets.token_urlsafe(32)
            
            try:
                if hasattr(db, 'get_connection'):
                    conn = db.get_connection()
                    cur = conn.cursor()
                    cur.execute("INSERT INTO sessions (token, account_id) VALUES (%s, %s)", 
                               (token, account_id))
                    conn.commit()
                    cur.close()
                    conn.close()
                else:
                    from datetime import datetime
                    db.accounts['sessions'][token] = {
                        'account_id': str(account_id),
                        'created_at': datetime.now().isoformat()
                    }
                    db.save_accounts()
            except Exception as e:
                print(f"❌ Ошибка создания сессии: {e}")
                return {'success': False, 'error': 'Failed to create session'}
            
            # Получаем созданный аккаунт
            account = db.get_account_by_token(token)
            
            return {
                'success': True,
                'token': token,
                'account': account,
                'is_new': True
            }
        else:
            return {'success': False, 'error': result.get('error', 'Failed to create account')}
