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
document.getElementById('avatar_file')?.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(event) {
            document.querySelector('.avatar-preview').src = event.target.result;
            localStorage.setItem('avatar', event.target.result);
            showMessage('✅ Аватарка загружена!', 'success');
        };
        reader.readAsDataURL(file);
    }
});

// Загрузка музыки
document.getElementById('music_file')?.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        // Проверка формата
        if (!file.type.includes('audio/mpeg') && !file.name.endsWith('.mp3')) {
            showMessage('❌ Только MP3 файлы!', 'error');
            return;
        }
        
        // Создаём временный audio элемент для проверки длительности
        const audio = new Audio();
        const reader = new FileReader();
        
        reader.onload = function(event) {
            audio.src = event.target.result;
            
            audio.addEventListener('loadedmetadata', function() {
                const duration = audio.duration;
                const maxDuration = 15 * 60; // 15 минут в секундах
                
                if (duration > maxDuration) {
                    showMessage('❌ Музыка не должна быть длиннее 15 минут!', 'error');
                    return;
                }
                
                // Сохраняем музыку
                localStorage.setItem('background_music', event.target.result);
                localStorage.setItem('music_type', 'file');
                localStorage.removeItem('music_url');
                
                // Обновляем preview
                const preview = document.getElementById('musicPreview');
                const minutes = Math.floor(duration / 60);
                const seconds = Math.floor(duration % 60);
                preview.innerHTML = `
                    <audio controls style="width: 100%; max-width: 200px;">
                        <source src="${event.target.result}" type="audio/mpeg">
                    </audio>
                    <small style="color: var(--text-light); font-size: 0.75rem;">${minutes}:${seconds.toString().padStart(2, '0')}</small>
                `;
                
                showMessage('✅ Музыка загружена!', 'success');
            });
        };
        
        reader.readAsDataURL(file);
    }
});

// Загрузка музыки по ссылке
window.loadMusicFromUrl = function() {
    const url = document.getElementById('music_url').value.trim();
    
    if (!url) {
        showMessage('❌ Введи ссылку на музыку!', 'error');
        return;
    }
    
    // Определяем тип ссылки
    let musicType = 'direct';
    let processedUrl = url;
    let coverUrl = null;
    
    // YouTube
    if (url.includes('youtube.com') || url.includes('youtu.be')) {
        musicType = 'youtube';
        // Извлекаем ID видео
        let videoId = '';
        if (url.includes('youtu.be/')) {
            videoId = url.split('youtu.be/')[1].split('?')[0];
        } else if (url.includes('watch?v=')) {
            videoId = url.split('watch?v=')[1].split('&')[0];
        }
        processedUrl = `https://www.youtube.com/embed/${videoId}?autoplay=1&loop=1`;
        
        // Автоматически получаем обложку YouTube
        coverUrl = `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`;
        localStorage.setItem('music_cover', coverUrl);
        showMessage('✅ Обложка YouTube загружена автоматически!', 'success');
    }
    // SoundCloud
    else if (url.includes('soundcloud.com')) {
        musicType = 'soundcloud';
        // Используем SoundCloud виджет
        processedUrl = `https://w.soundcloud.com/player/?url=${encodeURIComponent(url)}&auto_play=true&hide_related=true&show_comments=false&show_user=true&show_reposts=false&visual=true`;
        
        // Пытаемся получить обложку через oEmbed API
        fetch(`https://soundcloud.com/oembed?format=json&url=${encodeURIComponent(url)}`)
            .then(response => response.json())
            .then(data => {
                if (data.thumbnail_url) {
                    // Получаем большую версию обложки
                    coverUrl = data.thumbnail_url.replace('-large', '-t500x500');
                    localStorage.setItem('music_cover', coverUrl);
                    console.log('✅ Обложка SoundCloud загружена:', coverUrl);
                    
                    // Обновляем preview с обложкой
                    const preview = document.getElementById('musicPreview');
                    preview.innerHTML = `
                        <div style="width: 80px; height: 80px; border-radius: 8px; background-image: url(${coverUrl}); background-size: cover; background-position: center; border: 2px solid var(--primary);"></div>
                    `;
                }
            })
            .catch(e => console.log('Не удалось загрузить обложку SoundCloud'));
        
        showMessage('✅ SoundCloud будет загружен через виджет', 'success');
    }
    // VK Audio - используем прокси
    else if (url.includes('vk.com') || url.includes('vk.me') || url.includes('userapi.com')) {
        musicType = 'vk_proxy';
        // Используем наш прокси endpoint
        processedUrl = `/api/proxy_audio?url=${encodeURIComponent(url)}`;
        showMessage('✅ VK ссылка будет загружена через прокси', 'success');
    }
    // Проверка прямой ссылки на аудио
    else if (!url.match(/\.(mp3|wav|ogg|m4a)(\?.*)?$/i) && !url.includes('vk.com')) {
        showMessage('⚠️ Ссылка должна вести на аудио файл (.mp3, .wav, .ogg), YouTube или SoundCloud', 'error');
        return;
    }
    
    // Сохраняем
    localStorage.setItem('music_url', processedUrl);
    localStorage.setItem('music_type', musicType === 'vk_proxy' ? 'direct' : musicType);
    localStorage.removeItem('background_music');
    
    // Обновляем preview
    const preview = document.getElementById('musicPreview');
    
    // Для всех типов показываем только обложку в квадрате
    if (coverUrl) {
        preview.innerHTML = `
            <div style="width: 80px; height: 80px; border-radius: 8px; background-image: url(${coverUrl}); background-size: cover; background-position: center; border: 2px solid var(--primary);"></div>
        `;
    } else {
        preview.innerHTML = `
            <div style="width: 80px; height: 80px; border-radius: 8px; background: var(--bg); border: 2px solid var(--border); display: flex; align-items: center; justify-content: center; font-size: 2rem;">🎵</div>
        `;
    }
    
    showMessage('✅ Музыка загружена по ссылке!', 'success');
    document.getElementById('music_url').value = '';
}

// Загрузка обложки альбома
document.getElementById('music_cover_file')?.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        if (!file.type.startsWith('image/')) {
            showMessage('❌ Только изображения!', 'error');
            return;
        }
        
        const reader = new FileReader();
        reader.onload = function(event) {
            localStorage.setItem('music_cover', event.target.result);
            
            // Показываем preview
            const preview = document.getElementById('coverPreview');
            preview.innerHTML = `
                <img src="${event.target.result}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid var(--primary);">
            `;
            
            showMessage('✅ Обложка загружена!', 'success');
        };
        reader.readAsDataURL(file);
    }
});

// Загрузка сохранённой обложки при открытии страницы
const savedCover = localStorage.getItem('music_cover');
if (savedCover) {
    const preview = document.getElementById('coverPreview');
    if (preview) {
        preview.innerHTML = `
            <img src="${savedCover}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; border: 2px solid var(--primary);">
        `;
    }
}

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
        // Очищаем все настройки (кроме темы - она в кастомизации)
        const keys = ['display_name', 'bio', 'profile_public', 'show_stats', 'sound_notifications', 'user_email', 'avatar', 'background_music'];
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
