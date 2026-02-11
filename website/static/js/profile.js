// JavaScript для страницы профиля
console.log('👤 Profile.js загружен');

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initProfile();
});

function initProfile() {
    // Настраиваем табы
    setupTabs();
    
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

console.log('✅ Profile.js готов');
