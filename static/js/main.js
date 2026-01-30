// Основной JavaScript
console.log('🚀 TTFD загружен');

let musicPlayerFrame = null;
let playerReady = false;
let currentMusicPosition = 0;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    const currentPath = window.location.pathname;
    const globalPlayer = document.getElementById('globalMusicPlayer');
    
    // Скрываем глобальный плеер на странице профиля
    if (currentPath === '/profile') {
        if (globalPlayer) {
            globalPlayer.style.display = 'none';
        }
    } else {
        if (globalPlayer) {
            globalPlayer.style.display = 'block';
        }
    }
    
    initGlobalMusicPlayer();
});

// Слушаем сообщения от iframe
window.addEventListener('message', function(event) {
    if (event.data.type === 'playerReady') {
        playerReady = true;
        console.log('🎵 Плеер готов');
        startMusic();
    } else if (event.data.type === 'musicState') {
        currentMusicPosition = event.data.position;
        updateCoverAnimation(event.data.isPlaying);
        
        // Сохраняем позицию
        localStorage.setItem('music_position', currentMusicPosition);
        localStorage.setItem('music_playing', event.data.isPlaying ? 'true' : 'false');
    }
});

function initGlobalMusicPlayer() {
    musicPlayerFrame = document.getElementById('musicPlayerFrame');
    const coverElement = document.getElementById('globalMusicCover');
    
    if (!coverElement) return;
    
    // Устанавливаем обложку
    const musicCover = localStorage.getItem('music_cover');
    if (musicCover) {
        coverElement.style.backgroundImage = `url(${musicCover})`;
        coverElement.textContent = '';
    } else {
        coverElement.textContent = '🎵';
    }
    
    // Клик по кружку - toggle
    coverElement.addEventListener('click', function() {
        if (playerReady && musicPlayerFrame) {
            musicPlayerFrame.contentWindow.postMessage({ action: 'toggle' }, '*');
        }
    });
}

function startMusic() {
    const musicType = localStorage.getItem('music_type');
    const savedMusic = localStorage.getItem('background_music');
    const musicUrl = localStorage.getItem('music_url');
    const savedPosition = parseFloat(localStorage.getItem('music_position')) || 0;
    
    if (!musicType) return;
    
    console.log('🎵 Запуск музыки:', { musicType, savedPosition });
    
    if (musicPlayerFrame && playerReady) {
        musicPlayerFrame.contentWindow.postMessage({
            action: 'init',
            musicType: musicType,
            musicUrl: musicUrl,
            savedMusic: savedMusic,
            savedPosition: savedPosition
        }, '*');
    }
}

function updateCoverAnimation(isPlaying) {
    const coverElement = document.getElementById('globalMusicCover');
    if (!coverElement) return;
    
    if (isPlaying) {
        coverElement.classList.add('playing');
    } else {
        coverElement.classList.remove('playing');
    }
}

// Плавная прокрутка
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({ behavior: 'smooth' });
        }
    });
});

// Показать сообщение
function showMessage(text, type = 'success') {
    const message = document.getElementById('message');
    if (message) {
        message.textContent = text;
        message.className = `message ${type}`;
        message.style.display = 'block';
        
        setTimeout(() => {
            message.style.display = 'none';
        }, 5000);
    }
}

// Экспорт для использования в других скриптах
window.showMessage = showMessage;
