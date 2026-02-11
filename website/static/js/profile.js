// JavaScript для страницы профиля
console.log('👤 Profile.js загружен');

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initProfile();
});

function initProfile() {
    // Настраиваем табы
    setupTabs();
    
    // Загружаем данные из Discord если привязан
    loadDiscordData();
    
    console.log('✅ Profile инициализирован');
}

// Табы
function setupTabs() {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            
            // Убираем active со всех
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            
            // Добавляем active
            this.classList.add('active');
            document.getElementById(tabName).classList.add('active');
        });
    });
}

// Загрузка данных из Discord
async function loadDiscordData() {
    const statsContainer = document.getElementById('discord-stats');
    const achievementsContainer = document.getElementById('discord-achievements');
    
    if (!statsContainer && !achievementsContainer) {
        console.log('ℹ️ Discord не привязан');
        return;
    }
    
    try {
        // Получаем Discord ID из profile-panel data-attribute
        const profilePanel = document.querySelector('.profile-panel');
        const discordId = profilePanel ? profilePanel.dataset.discordId : null;
        
        if (!discordId) {
            console.log('⚠️ Discord ID не найден');
            return;
        }
        
        console.log(`🔄 Загрузка данных для Discord ID: ${discordId}`);
        
        // Загружаем данные пользователя из API
        const response = await fetch(`/api/user/${discordId}`);
        const data = await response.json();
        
        if (data.user) {
            // Отображаем статистику
            if (statsContainer) {
                displayStats(data.user, data.rank, data.next_rank);
            }
            
            // Отображаем достижения
            if (achievementsContainer) {
                displayAchievements(data.user, data.rank);
            }
        } else {
            throw new Error('Данные пользователя не найдены');
        }
        
    } catch (error) {
        console.error('❌ Ошибка загрузки данных Discord:', error);
        
        if (statsContainer) {
            statsContainer.innerHTML = '<div class="error">Ошибка загрузки статистики</div>';
        }
        if (achievementsContainer) {
            achievementsContainer.innerHTML = '<div class="error">Ошибка загрузки достижений</div>';
        }
    }
}

// Отображение статистики
function displayStats(user, rank, nextRank) {
    const container = document.getElementById('discord-stats');
    
    const html = `
        <div class="stat-row">
            <span class="stat-name">⭐ Опыт</span>
            <span class="stat-value">${user.xp.toLocaleString()}</span>
        </div>
        <div class="stat-row">
            <span class="stat-name">💰 Монеты</span>
            <span class="stat-value">${user.coins.toLocaleString()}</span>
        </div>
        <div class="stat-row">
            <span class="stat-name">🖱️ Кликов</span>
            <span class="stat-value">${user.clicks.toLocaleString()}</span>
        </div>
        <div class="stat-row">
            <span class="stat-name">✅ Заданий выполнено</span>
            <span class="stat-value">${user.tasks_completed}</span>
        </div>
        <div class="stat-row">
            <span class="stat-name">🏆 Текущий ранг</span>
            <span class="stat-value">${rank.name}</span>
        </div>
        ${nextRank ? `
        <div class="stat-row">
            <span class="stat-name">📈 До следующего ранга</span>
            <span class="stat-value">${(nextRank.xp_required - user.xp).toLocaleString()} XP</span>
        </div>
        ` : ''}
    `;
    
    container.innerHTML = html;
}

// Отображение достижений
function displayAchievements(user, rank) {
    const container = document.getElementById('discord-achievements');
    
    const html = `
        <div class="achievements-grid">
            <div class="achievement-card">
                <div class="achievement-icon">🎖️</div>
                <div class="achievement-name">Ранг</div>
                <div class="achievement-desc">${rank.name}</div>
            </div>
            <div class="achievement-card">
                <div class="achievement-icon">⭐</div>
                <div class="achievement-name">Опыт</div>
                <div class="achievement-desc">${user.xp.toLocaleString()} XP</div>
            </div>
            <div class="achievement-card">
                <div class="achievement-icon">💰</div>
                <div class="achievement-name">Монеты</div>
                <div class="achievement-desc">${user.coins.toLocaleString()}</div>
            </div>
            <div class="achievement-card">
                <div class="achievement-icon">🖱️</div>
                <div class="achievement-name">Кликов</div>
                <div class="achievement-desc">${user.clicks.toLocaleString()}</div>
            </div>
            <div class="achievement-card">
                <div class="achievement-icon">✅</div>
                <div class="achievement-name">Заданий</div>
                <div class="achievement-desc">${user.tasks_completed}</div>
            </div>
        </div>
    `;
    
    container.innerHTML = html;
}

console.log('✅ Profile.js готов');
