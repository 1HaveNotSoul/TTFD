# Система автоматической выдачи ролей за ранги

import discord
import json
import os
from font_converter import convert_to_font

# Файл с ID ролей
RANK_ROLES_FILE = 'json/rank_roles.json'

def load_rank_roles():
    """Загрузить ID ролей из файла"""
    if os.path.exists(RANK_ROLES_FILE):
        try:
            with open(RANK_ROLES_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Возвращаем только роли, без info
                roles = {k: v for k, v in data.items() if k != 'info'}
                print(f"✅ Загружены роли из {RANK_ROLES_FILE}: {list(roles.keys())}")
                return roles
        except Exception as e:
            print(f"⚠️ Ошибка загрузки ролей из файла: {e}")
    else:
        print(f"⚠️ Файл {RANK_ROLES_FILE} не найден, используются значения по умолчанию")
    
    return {
        'F': {'role_id': None, 'required_xp': 100},
        'E': {'role_id': None, 'required_xp': 500},
        'D': {'role_id': None, 'required_xp': 1500},
        'C': {'role_id': None, 'required_xp': 2800},
        'B': {'role_id': None, 'required_xp': 5000},
        'A': {'role_id': None, 'required_xp': 15000},
        'S': {'role_id': None, 'required_xp': 50000},
    }

def save_rank_roles(roles):
    """Сохранить ID ролей в файл"""
    os.makedirs('json', exist_ok=True)
    data = roles.copy()
    data['info'] = {
        "description": "ID ролей Discord для каждого ранга с требованиями XP",
        "last_updated": "02.02.2026",
        "note": "Роли выдаются автоматически при достижении required_xp"
    }
    with open(RANK_ROLES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Загружаем роли при импорте
RANK_ROLES = load_rank_roles()

def get_role_for_xp(xp):
    """
    Определить какую роль должен иметь пользователь по XP
    
    Args:
        xp: Количество опыта пользователя
    
    Returns:
        str: Буква ранга (F, E, D, C, B, A, S) или None
    """
    # Сортируем роли по required_xp в обратном порядке (от большего к меньшему)
    sorted_roles = sorted(
        [(tier, data) for tier, data in RANK_ROLES.items()],
        key=lambda x: x[1].get('required_xp', 0),
        reverse=True
    )
    
    # Находим подходящую роль
    for tier, data in sorted_roles:
        if xp >= data.get('required_xp', 0):
            return tier
    
    return None  # Недостаточно XP для любой роли

async def update_user_rank_role(member, xp):
    """
    Обновить роль пользователя в соответствии с его XP
    
    Args:
        member: Discord Member объект
        xp: Количество опыта пользователя
    
    Returns:
        dict: Информация об обновлении роли
    """
    if not member or not member.guild:
        return {'success': False, 'error': 'Member or guild not found'}
    
    guild = member.guild
    
    # Определяем какую роль должен иметь пользователь
    target_tier = get_role_for_xp(xp)
    
    if not target_tier:
        # Недостаточно XP для любой роли
        return {'success': False, 'error': 'Not enough XP for any role'}
    
    # Получаем ID нужной роли
    role_data = RANK_ROLES.get(target_tier)
    if not role_data or not role_data.get('role_id'):
        print(f"⚠️ Роль для ранга {target_tier} не настроена в RANK_ROLES")
        return {'success': False, 'error': f'Role for rank {target_tier} not configured'}
    
    target_role_id = role_data['role_id']
    
    # Получаем объект роли
    target_role = guild.get_role(target_role_id)
    
    if not target_role:
        print(f"⚠️ Роль с ID {target_role_id} не найдена на сервере")
        return {'success': False, 'error': f'Role {target_role_id} not found'}
    
    # Проверяем, есть ли уже эта роль у пользователя
    if target_role in member.roles:
        return {'success': True, 'action': 'already_has', 'role': target_role, 'tier': target_tier}
    
    # Удаляем все старые роли рангов
    roles_to_remove = []
    for rank_tier, rank_data in RANK_ROLES.items():
        role_id = rank_data.get('role_id') if isinstance(rank_data, dict) else rank_data
        if role_id:
            role = guild.get_role(role_id)
            if role and role in member.roles:
                roles_to_remove.append(role)
    
    # Удаляем старые роли
    if roles_to_remove:
        try:
            await member.remove_roles(*roles_to_remove, reason="Обновление ранга")
            print(f"🗑️ Удалены старые роли рангов у {member.name}")
        except Exception as e:
            print(f"❌ Ошибка удаления старых ролей: {e}")
    
    # Добавляем новую роль
    try:
        await member.add_roles(target_role, reason=f"Достигнут ранг {target_tier} ({xp} XP)")
        print(f"✅ Выдана роль {target_role.name} пользователю {member.name}")
        return {
            'success': True,
            'action': 'added',
            'role': target_role,
            'tier': target_tier,
            'removed_roles': roles_to_remove
        }
    except Exception as e:
        print(f"❌ Ошибка выдачи роли: {e}")
        return {'success': False, 'error': str(e)}

async def sync_all_user_roles(bot, db):
    """
    Синхронизировать роли всех пользователей с их XP
    Полезно при первом запуске или после изменения настроек
    
    Args:
        bot: Discord Bot объект
        db: Database объект
    
    Returns:
        dict: Статистика синхронизации
    """
    stats = {
        'total': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0
    }
    
    all_users = db.get_all_users()
    
    for user_id, user_data in all_users.items():
        stats['total'] += 1
        
        try:
            xp = user_data.get('xp', 0)
            
            # Находим пользователя на всех серверах
            for guild in bot.guilds:
                member = guild.get_member(int(user_id))
                
                if member:
                    result = await update_user_rank_role(member, xp)
                    
                    if result['success']:
                        if result['action'] == 'added':
                            stats['updated'] += 1
                        else:
                            stats['skipped'] += 1
                    else:
                        stats['errors'] += 1
                    
                    break  # Нашли пользователя, выходим из цикла
        
        except Exception as e:
            print(f"❌ Ошибка синхронизации роли для {user_id}: {e}")
            stats['errors'] += 1
    
    return stats

def get_rank_roles_config():
    """Получить текущую конфигурацию ролей"""
    return RANK_ROLES.copy()

def set_rank_role(tier, role_id):
    """
    Установить ID роли для ранга
    
    Args:
        tier: Буква ранга (F, E, D, C, B, A, S)
        role_id: ID роли Discord
    """
    global RANK_ROLES
    if tier in RANK_ROLES:
        RANK_ROLES[tier] = role_id
        save_rank_roles(RANK_ROLES)
        print(f"✅ Роль для ранга {tier} установлена: {role_id}")
        return True
    return False

def is_configured():
    """Проверить, настроены ли все роли"""
    return all(role_id is not None for role_id in RANK_ROLES.values())

def get_missing_roles():
    """Получить список ненастроенных рангов"""
    return [tier for tier, role_id in RANK_ROLES.items() if role_id is None]

async def send_rank_up_notification(ctx, member, old_xp, new_xp, old_tier, new_tier, role):
    """
    Отправить уведомление о повышении ранга с информацией о роли
    
    Args:
        ctx: Discord Context
        member: Discord Member
        old_xp: Старое количество XP
        new_xp: Новое количество XP
        old_tier: Старая буква ранга (F, E, D, C, B, A, S)
        new_tier: Новая буква ранга (F, E, D, C, B, A, S)
        role: Discord Role объект (новая роль)
    """
    from theme import BotTheme
    
    embed = BotTheme.create_embed(
        title=convert_to_font("🎊 новая роль!"),
        description=convert_to_font(f"поздравляем {member.mention}!"),
        embed_type='success'
    )
    
    if old_tier:
        embed.add_field(
            name=convert_to_font("старая роль"),
            value=convert_to_font(f"{old_tier} - ранг"),
            inline=True
        )
    
    embed.add_field(
        name=convert_to_font("новая роль"),
        value=f"{role.mention}",
        inline=True
    )
    
    embed.add_field(
        name=convert_to_font("💎 твой xp"),
        value=convert_to_font(str(new_xp)),
        inline=False
    )
    
    # Показываем требования для следующей роли
    next_tier_info = get_next_role_info(new_tier)
    if next_tier_info:
        xp_needed = next_tier_info['required_xp'] - new_xp
        embed.add_field(
            name=convert_to_font(f"📈 до {next_tier_info['tier']} - ранг"),
            value=convert_to_font(f"ещё {xp_needed} xp"),
            inline=False
        )
    
    await ctx.send(embed=embed)

def get_next_role_info(current_tier):
    """Получить информацию о следующей роли"""
    tiers_order = ['F', 'E', 'D', 'C', 'B', 'A', 'S']
    
    try:
        current_index = tiers_order.index(current_tier)
        if current_index < len(tiers_order) - 1:
            next_tier = tiers_order[current_index + 1]
            return {
                'tier': next_tier,
                'required_xp': RANK_ROLES[next_tier]['required_xp']
            }
    except:
        pass
    
    return None

