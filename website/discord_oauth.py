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
    print("🔍 OAuth callback начат")
    
    # Проверяем state для защиты от CSRF
    state = request.args.get('state')
    session_state = session.get('oauth_state')
    print(f"🔍 State проверка: получен={state[:10]}..., ожидается={session_state[:10] if session_state else None}...")
    
    if state != session_state:
        print("❌ State не совпадает!")
        return {'success': False, 'error': 'Invalid state'}
    
    # Получаем код авторизации
    code = request.args.get('code')
    print(f"🔍 Код авторизации: {code[:10] if code else None}...")
    
    if not code:
        print("❌ Код не предоставлен!")
        return {'success': False, 'error': 'No code provided'}
    
    # Обмениваем код на токен
    print("🔄 Обмен кода на токен...")
    token_data = exchange_code(code)
    if not token_data:
        print("❌ Не удалось обменять код!")
        return {'success': False, 'error': 'Failed to exchange code'}
    
    access_token = token_data.get('access_token')
    print(f"✅ Access token получен: {access_token[:10] if access_token else None}...")
    
    if not access_token:
        print("❌ Access token отсутствует!")
        return {'success': False, 'error': 'No access token'}
    
    # Получаем информацию о пользователе
    print("👤 Получение информации о пользователе...")
    user_info = get_user_info(access_token)
    if not user_info:
        print("❌ Не удалось получить информацию о пользователе!")
        return {'success': False, 'error': 'Failed to get user info'}
    
    discord_id = user_info.get('id')
    discord_username = user_info.get('username')
    discord_email = user_info.get('email')
    discord_avatar = user_info.get('avatar')
    
    print(f"✅ Пользователь Discord: {discord_username} (ID: {discord_id})")
    print(f"📧 Email: {discord_email}")
    
    # Формируем URL аватара
    avatar_url = None
    if discord_avatar:
        avatar_url = f"https://cdn.discordapp.com/avatars/{discord_id}/{discord_avatar}.png"
    
    # Проверяем существует ли аккаунт с таким Discord ID или email
    print("🔍 Поиск существующего аккаунта...")
    existing_account = None
    try:
        # Для PostgreSQL
        if hasattr(db, 'get_connection'):
            print("🔍 Используется PostgreSQL")
            conn = db.get_connection()
            cur = conn.cursor()
            # Ищем по discord_id ИЛИ по email
            cur.execute(
                "SELECT * FROM accounts WHERE discord_id = %s OR email = %s", 
                (discord_id, discord_email or f"{discord_id}@discord.user")
            )
            result = cur.fetchone()
            if result:
                existing_account = dict(result)
            cur.close()
            conn.close()
        # Для JSON
        else:
            print("🔍 Используется JSON база")
            for acc in db.accounts['accounts'].values():
                if acc.get('discord_id') == discord_id or acc.get('email') == (discord_email or f"{discord_id}@discord.user"):
                    existing_account = acc
                    print(f"✅ Найден существующий аккаунт: {acc['username']}")
                    break
    except Exception as e:
        print(f"❌ Ошибка поиска аккаунта: {e}")
        import traceback
        traceback.print_exc()
    
    if existing_account:
        print(f"✅ Аккаунт найден: {existing_account['username']}")
        
        # Аккаунт уже существует - обновляем Discord ID если его не было
        if not existing_account.get('discord_id'):
            print(f"🔗 Привязываем Discord ID к существующему аккаунту: {existing_account['username']}")
            db.link_discord(existing_account['id'], discord_id)
        else:
            print(f"✅ Discord ID уже привязан")
            
            # Обновляем аватарку если есть
            if avatar_url:
                db.update_profile(existing_account['id'], avatar_url=avatar_url)
        
        # Логиним пользователя
        print("🔐 Создание сессии...")
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
                # Убедимся что sessions существует
                if 'sessions' not in db.accounts:
                    db.accounts['sessions'] = {}
                    
                db.accounts['sessions'][token] = {
                    'account_id': str(existing_account['id']),
                    'created_at': datetime.now().isoformat()
                }
                db.save_accounts()
                print(f"✅ Сессия сохранена в JSON: account_id={existing_account['id']}, token={token[:10]}...")
            
            print(f"✅ Сессия создана: {token[:10]}...")
        except Exception as e:
            print(f"❌ Ошибка создания сессии: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': f'Failed to create session: {str(e)}'}
        
        print(f"✅ OAuth успешно завершен для существующего пользователя: {existing_account['username']}")
        return {
            'success': True,
            'token': token,
            'account': existing_account,
            'is_new': False,
            'was_linked': not existing_account.get('discord_id')
        }
    else:
        # Создаём новый аккаунт
        print("➕ Создание нового аккаунта...")
        username = f"discord_{discord_username}"
        display_name = discord_username
        email = discord_email or f"{discord_id}@discord.user"
        
        print(f"📝 Username: {username}, Email: {email}")
        
        # Генерируем случайный пароль (пользователь не будет его знать)
        random_password = secrets.token_urlsafe(32)
        
        # Создаём аккаунт
        print("🔄 Вызов db.create_account...")
        result = db.create_account(
            email=email,
            username=username,
            password=random_password,
            display_name=display_name
        )
        
        print(f"📊 Результат создания: {result}")
        
        if not result['success']:
            # Если username занят, добавляем цифры
            print(f"⚠️ Username занят, пробуем с ID...")
            username = f"discord_{discord_username}_{discord_id[:6]}"
            result = db.create_account(
                email=email,
                username=username,
                password=random_password,
                display_name=display_name
            )
            print(f"📊 Результат повторной попытки: {result}")
        
        if result['success']:
            account_id = result['account_id']
            print(f"✅ Аккаунт создан с ID: {account_id}")
            
            # Привязываем Discord ID
            print(f"🔗 Привязка Discord ID...")
            db.link_discord(account_id, discord_id)
            
            # Обновляем аватарку если есть
            if avatar_url:
                print(f"🖼️ Обновление аватара...")
                db.update_profile(account_id, avatar_url=avatar_url)
            
            # Создаём сессию
            print("🔐 Создание сессии для нового пользователя...")
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
                    # Убедимся что sessions существует
                    if 'sessions' not in db.accounts:
                        db.accounts['sessions'] = {}
                    
                    db.accounts['sessions'][token] = {
                        'account_id': str(account_id),
                        'created_at': datetime.now().isoformat()
                    }
                    db.save_accounts()
                    print(f"✅ Сессия сохранена в JSON: account_id={account_id}, token={token[:10]}...")
                
                print(f"✅ Сессия создана: {token[:10]}...")
            except Exception as e:
                print(f"❌ Ошибка создания сессии: {e}")
                import traceback
                traceback.print_exc()
                return {'success': False, 'error': f'Failed to create session: {str(e)}'}
            
            # Получаем созданный аккаунт
            print("📥 Получение созданного аккаунта...")
            account = db.get_account_by_token(token)
            
            if not account:
                print("❌ Не удалось получить аккаунт по токену!")
                return {'success': False, 'error': 'Failed to retrieve account'}
            
            print(f"✅ OAuth успешно завершен для нового пользователя: {account['username']}")
            return {
                'success': True,
                'token': token,
                'account': account,
                'is_new': True
            }
        else:
            print(f"❌ Не удалось создать аккаунт: {result.get('error')}")
            return {'success': False, 'error': result.get('error', 'Failed to create account')}
