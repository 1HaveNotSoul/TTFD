// JavaScript для страницы настроек
console.log('⚙️ Settings.js загружен');

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initSettings();
});

function initSettings() {
    // Настраиваем табы
    setupTabs();
    
    // Инициализируем toggle текст
    initializeToggles();
    
    console.log('✅ Settings инициализирован');
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

// Обновление текста toggle кнопок
function updateToggleText(checkbox) {
    const slider = checkbox.nextElementSibling;
    if (slider && slider.classList.contains('toggle-slider')) {
        const onText = slider.getAttribute('data-on');
        const offText = slider.getAttribute('data-off');
        if (onText && offText) {
            slider.textContent = checkbox.checked ? onText : offText;
        }
    }
}

// Инициализация всех toggle кнопок
function initializeToggles() {
    document.querySelectorAll('.toggle-label input[type="checkbox"]').forEach(checkbox => {
        // Загружаем сохранённое состояние
        const key = checkbox.id;
        const saved = localStorage.getItem(key);
        if (saved !== null) {
            checkbox.checked = saved === 'true';
        }
        
        // Устанавливаем начальный текст
        updateToggleText(checkbox);
        
        // Обработчик изменения
        checkbox.addEventListener('change', function() {
            updateToggleText(this);
            localStorage.setItem(key, this.checked);
        });
    });
}

// Обработка формы профиля
document.getElementById('profileForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const data = {
        display_name: document.getElementById('display_name').value,
        bio: document.getElementById('bio').value
    };
    
    try {
        const response = await fetch('/api/update_profile', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('✅ Профиль обновлён!', 'success');
        } else {
            showMessage('❌ Ошибка обновления', 'error');
        }
    } catch (error) {
        showMessage('❌ Ошибка соединения', 'error');
    }
});

// Выбор темы (удалено - используется кастомизация)

// Применение темы (удалено)

// Загрузка сохранённой темы (удалено)

// Загрузка аватарки
document.getElementById('avatar_file')?.addEventListener('change', async function(e) {
    const file = e.target.files[0];
    if (file) {
        // Проверка размера (макс 5MB)
        if (file.size > 5 * 1024 * 1024) {
            showMessage('❌ Файл слишком большой! Максимум 5MB', 'error');
            return;
        }
        
        // Показываем preview
        const reader = new FileReader();
        reader.onload = function(event) {
            document.getElementById('avatarPreview').src = event.target.result;
        };
        reader.readAsDataURL(file);
        
        // Загружаем на сервер
        const formData = new FormData();
        formData.append('avatar', file);
        
        try {
            showMessage('📤 Загрузка...', 'success');
            
            const response = await fetch('/api/upload_avatar', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            
            if (result.success) {
                showMessage('✅ Аватарка загружена!', 'success');
                // Обновляем аватарку в профиле
                setTimeout(() => location.reload(), 1000);
            } else {
                showMessage(`❌ Ошибка: ${result.error}`, 'error');
            }
        } catch (error) {
            showMessage('❌ Ошибка загрузки', 'error');
            console.error('Upload error:', error);
        }
    }
});

// Расширенные настройки (удалено - теперь это отдельная вкладка)

// Загрузка email
const savedEmail = localStorage.getItem('user_email');
if (savedEmail) {
    const emailInput = document.getElementById('user_email');
    if (emailInput) {
        emailInput.value = savedEmail;
    }
}

// Сохранение email при изменении
document.getElementById('user_email')?.addEventListener('change', function() {
    localStorage.setItem('user_email', this.value);
    showMessage('✅ Email сохранён', 'success');
});

// Отправка тестового уведомления
window.sendTestNotification = async function() {
    const email = document.getElementById('user_email').value;
    
    if (!email) {
        showMessage('❌ Введите email адрес!', 'error');
        return;
    }
    
    // Проверка валидности email
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        showMessage('❌ Неверный формат email!', 'error');
        return;
    }
    
    try {
        showMessage('📧 Отправка...', 'success');
        
        const response = await fetch('/api/send_notification', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                email: email,
                subject: 'Тестовое уведомление от TTFD',
                message: 'Привет! Это тестовое уведомление от TTFD Bot. Если ты получил это письмо, значит всё работает отлично! 🎮'
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            showMessage('✅ Уведомление отправлено! Проверь почту.', 'success');
        } else {
            showMessage(`❌ Ошибка: ${result.error}`, 'error');
        }
    } catch (error) {
        showMessage('❌ Ошибка соединения', 'error');
        console.error('Email error:', error);
    }
}

// Сохранение всех настроек
window.saveSettings = function() {
    // Сохраняем профиль
    const displayName = document.getElementById('display_name').value;
    const bio = document.getElementById('bio').value;
    
    localStorage.setItem('display_name', displayName);
    localStorage.setItem('bio', bio);
    
    // Все toggle настройки уже сохраняются автоматически
    
    showMessage('✅ Все настройки сохранены!', 'success');
}

// Сброс настроек
window.resetSettings = function() {
    if (confirm('Сбросить все настройки к значениям по умолчанию?')) {
        // Очищаем все настройки
        const keys = ['display_name', 'bio', 'profile_public', 'show_stats', 'sound_notifications', 'user_email'];
        keys.forEach(key => localStorage.removeItem(key));
        
        // Перезагружаем страницу
        location.reload();
    }
}

// Показ сообщений
function showMessage(text, type) {
    const message = document.getElementById('message');
    message.textContent = text;
    message.className = `message ${type}`;
    message.style.display = 'block';
    
    setTimeout(() => {
        message.style.display = 'none';
    }, 3000);
}

console.log('✅ Все функции настроек загружены');

// Выход из аккаунта
window.logoutAccount = function() {
    if (confirm('Вы уверены что хотите выйти из аккаунта?')) {
        showMessage('👋 Выход из аккаунта...', 'success');
        setTimeout(() => {
            window.location.href = '/logout';
        }, 1000);
    }
}
