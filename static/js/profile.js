// JavaScript для страницы профиля
console.log('👤 Profile.js загружен');

let audioPlayer = null;
let isPlaying = false;

// Инициализация при загрузке страницы
document.addEventListener('DOMContentLoaded', function() {
    initProfile();
});

function initProfile() {
    // Настраиваем табы
    setupTabs();
    
    // Инициализируем музыкальный плеер
    initMusicPlayer();
    
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

// Музыкальный плеер
let soundcloudWidget = null;
let youtubePlayer = null;

function initMusicPlayer() {
    const musicType = localStorage.getItem('music_type');
    const savedMusic = localStorage.getItem('background_music');
    const musicUrl = localStorage.getItem('music_url');
    const musicCover = localStorage.getItem('music_cover'); // Обложка альбома
    
    console.log('🎵 Инициализация плеера:', { musicType, musicUrl: musicUrl ? 'есть' : 'нет' });
    
    // Устанавливаем обложку если есть
    const coverElement = document.getElementById('musicCover');
    if (musicCover) {
        coverElement.style.backgroundImage = `url(${musicCover})`;
        coverElement.textContent = ''; // Убираем текст/эмодзи
    } else {
        coverElement.textContent = '🎵'; // Показываем эмодзи если обложки нет
    }
    
    if (musicType === 'file' && savedMusic) {
        // Загруженный файл
        audioPlayer = new Audio(savedMusic);
        audioPlayer.loop = true;
        audioPlayer.volume = 0.7;
        audioPlayer.crossOrigin = "anonymous";
        
        audioPlayer.addEventListener('error', function(e) {
            console.error('❌ Ошибка загрузки файла:', e);
            document.getElementById('musicInfo').textContent = 'Ошибка загрузки файла';
        });
        
        audioPlayer.play().catch(e => {
            console.log('Автоплей заблокирован браузером, кликни по обложке');
            isPlaying = false;
        });
        isPlaying = true;
        
        updateMusicInfo();
        setupMusicControls();
    } else if (musicType === 'direct' && musicUrl) {
        // Прямая ссылка на аудио
        console.log('🎵 Загрузка прямой ссылки:', musicUrl);
        audioPlayer = new Audio();
        audioPlayer.crossOrigin = "anonymous";
        audioPlayer.src = musicUrl;
        audioPlayer.loop = true;
        audioPlayer.volume = 0.7;
        
        audioPlayer.addEventListener('error', function(e) {
            console.error('❌ Ошибка загрузки аудио:', e);
            console.error('Код ошибки:', audioPlayer.error ? audioPlayer.error.code : 'неизвестно');
            document.getElementById('musicInfo').textContent = 'Ошибка: ссылка недоступна (CORS)';
        });
        
        audioPlayer.addEventListener('canplay', function() {
            console.log('✅ Аудио готово к воспроизведению');
        });
        
        audioPlayer.play().catch(e => {
            console.log('Автоплей заблокирован браузером, кликни по обложке');
            isPlaying = false;
        });
        isPlaying = true;
        
        updateMusicInfo();
        setupMusicControls();
    } else if (musicType === 'youtube' && musicUrl) {
        // YouTube - создаем скрытый iframe для воспроизведения
        console.log('🎵 YouTube музыка');
        
        // Создаем скрытый контейнер для iframe
        let hiddenContainer = document.getElementById('hiddenMusicPlayer');
        if (!hiddenContainer) {
            hiddenContainer = document.createElement('div');
            hiddenContainer.id = 'hiddenMusicPlayer';
            hiddenContainer.style.position = 'fixed';
            hiddenContainer.style.bottom = '-200px';
            hiddenContainer.style.left = '-200px';
            hiddenContainer.style.width = '1px';
            hiddenContainer.style.height = '1px';
            hiddenContainer.style.overflow = 'hidden';
            document.body.appendChild(hiddenContainer);
        }
        
        hiddenContainer.innerHTML = `
            <iframe id="youtubeIframe" width="200" height="200" src="${musicUrl}" frameborder="0" allow="autoplay; encrypted-media"></iframe>
        `;
        
        document.getElementById('musicInfo').textContent = 'YouTube трек';
        isPlaying = true;
        
        // Для YouTube настраиваем контролы
        const coverElement = document.getElementById('musicCover');
        coverElement.classList.add('playing');
        setupYouTubeControls();
    } else if (musicType === 'soundcloud' && musicUrl) {
        // SoundCloud - создаем скрытый iframe для воспроизведения
        console.log('🎵 SoundCloud музыка');
        
        // Загружаем SoundCloud Widget API
        if (!window.SC) {
            const script = document.createElement('script');
            script.src = 'https://w.soundcloud.com/player/api.js';
            script.onload = () => initSoundCloudWidget(musicUrl);
            document.head.appendChild(script);
        } else {
            initSoundCloudWidget(musicUrl);
        }
    } else {
        // Музыка не загружена
        document.getElementById('musicInfo').textContent = 'Музыка не загружена';
    }
}

function initSoundCloudWidget(musicUrl) {
    // Создаем скрытый контейнер для iframe
    let hiddenContainer = document.getElementById('hiddenMusicPlayer');
    if (!hiddenContainer) {
        hiddenContainer = document.createElement('div');
        hiddenContainer.id = 'hiddenMusicPlayer';
        hiddenContainer.style.position = 'fixed';
        hiddenContainer.style.bottom = '-200px';
        hiddenContainer.style.left = '-200px';
        hiddenContainer.style.width = '1px';
        hiddenContainer.style.height = '1px';
        hiddenContainer.style.overflow = 'hidden';
        document.body.appendChild(hiddenContainer);
    }
    
    hiddenContainer.innerHTML = `
        <iframe id="soundcloudIframe" width="100%" height="166" scrolling="no" frameborder="no" allow="autoplay" src="${musicUrl}"></iframe>
    `;
    
    // Инициализируем Widget API
    const iframe = document.getElementById('soundcloudIframe');
    soundcloudWidget = SC.Widget(iframe);
    
    soundcloudWidget.bind(SC.Widget.Events.READY, function() {
        console.log('✅ SoundCloud готов');
        soundcloudWidget.setVolume(70);
        isPlaying = true;
        
        const coverElement = document.getElementById('musicCover');
        coverElement.classList.add('playing');
        
        setupSoundCloudControls();
    });
    
    document.getElementById('musicInfo').textContent = 'SoundCloud трек';
}

function setupYouTubeControls() {
    // Клик по обложке - play/pause для YouTube
    document.getElementById('musicCover').addEventListener('click', function() {
        const iframe = document.getElementById('youtubeIframe');
        if (isPlaying) {
            iframe.contentWindow.postMessage('{"event":"command","func":"pauseVideo","args":""}', '*');
            this.classList.remove('playing');
        } else {
            iframe.contentWindow.postMessage('{"event":"command","func":"playVideo","args":""}', '*');
            this.classList.add('playing');
        }
        isPlaying = !isPlaying;
    });
    
    // Громкость для YouTube (ограничена)
    setupCustomVolumeSlider();
}

function setupSoundCloudControls() {
    // Клик по обложке - play/pause
    document.getElementById('musicCover').addEventListener('click', function() {
        if (isPlaying) {
            soundcloudWidget.pause();
            this.classList.remove('playing');
        } else {
            soundcloudWidget.play();
            this.classList.add('playing');
        }
        isPlaying = !isPlaying;
    });
    
    // Прогресс бар
    const progressBar = document.querySelector('.music-progress-horizontal');
    const progressThumb = document.getElementById('musicProgressThumb');
    
    if (progressBar && progressThumb) {
        let isDragging = false;
        let wasPlaying = false;
        
        // Клик по треку
        progressBar.addEventListener('click', function(e) {
            const rect = this.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            
            soundcloudWidget.getDuration(function(duration) {
                soundcloudWidget.seekTo(duration * percent);
            });
        });
        
        // Начало перетаскивания
        progressThumb.addEventListener('mousedown', function(e) {
            isDragging = true;
            wasPlaying = isPlaying;
            if (wasPlaying) {
                soundcloudWidget.pause();
            }
            e.preventDefault();
            e.stopPropagation();
        });
        
        // Перетаскивание
        document.addEventListener('mousemove', function(e) {
            if (!isDragging) return;
            
            const rect = progressBar.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const percent = Math.max(0, Math.min(1, x / rect.width));
            
            soundcloudWidget.getDuration(function(duration) {
                soundcloudWidget.seekTo(duration * percent);
            });
        });
        
        // Конец перетаскивания
        document.addEventListener('mouseup', function() {
            if (isDragging && wasPlaying) {
                soundcloudWidget.play();
            }
            isDragging = false;
        });
    }
    
    // Обновление прогресса с requestAnimationFrame для плавности
    function updateSoundCloudProgress() {
        soundcloudWidget.getPosition(function(position) {
            soundcloudWidget.getDuration(function(duration) {
                const percent = (position / duration) * 100;
                const progressBar = document.getElementById('musicProgressBar');
                const progressThumb = document.getElementById('musicProgressThumb');
                
                if (progressBar && progressThumb) {
                    progressBar.style.width = percent + '%';
                    progressThumb.style.left = percent + '%';
                }
                
                const current = formatTime(position / 1000);
                const total = formatTime(duration / 1000);
                document.getElementById('musicInfo').textContent = `${current} / ${total}`;
            });
        });
        requestAnimationFrame(updateSoundCloudProgress);
    }
    updateSoundCloudProgress();
    
    // Громкость
    setupCustomVolumeSlider();
    
    // Клик по иконке громкости - mute/unmute
    document.getElementById('volumeIcon').addEventListener('click', function() {
        soundcloudWidget.getVolume(function(volume) {
            if (volume > 0) {
                soundcloudWidget.setVolume(0);
                updateVolumeUI(0);
                updateVolumeIcon(0);
            } else {
                soundcloudWidget.setVolume(70);
                updateVolumeUI(70);
                updateVolumeIcon(70);
            }
        });
    });
}

function setupMusicControls() {
    // Клик по обложке - play/pause
    document.getElementById('musicCover').addEventListener('click', togglePlayPause);
    
    // Прогресс бар
    const progressBar = document.querySelector('.music-progress-horizontal');
    const progressThumb = document.getElementById('musicProgressThumb');
    
    if (progressBar && progressThumb) {
        let isDragging = false;
        let wasPlaying = false;
        
        // Клик по треку
        progressBar.addEventListener('click', function(e) {
            if (!audioPlayer) return;
            const rect = this.getBoundingClientRect();
            const percent = (e.clientX - rect.left) / rect.width;
            audioPlayer.currentTime = audioPlayer.duration * percent;
        });
        
        // Начало перетаскивания
        progressThumb.addEventListener('mousedown', function(e) {
            isDragging = true;
            wasPlaying = !audioPlayer.paused;
            if (wasPlaying) {
                audioPlayer.pause();
            }
            e.preventDefault();
            e.stopPropagation();
        });
        
        // Перетаскивание
        document.addEventListener('mousemove', function(e) {
            if (!isDragging || !audioPlayer) return;
            
            const rect = progressBar.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const percent = Math.max(0, Math.min(1, x / rect.width));
            audioPlayer.currentTime = audioPlayer.duration * percent;
        });
        
        // Конец перетаскивания
        document.addEventListener('mouseup', function() {
            if (isDragging && wasPlaying && audioPlayer) {
                audioPlayer.play();
            }
            isDragging = false;
        });
    }
    
    // Обновление прогресса
    if (audioPlayer) {
        audioPlayer.addEventListener('timeupdate', updateProgress);
    }
    
    // Новый кастомный ползунок громкости
    setupCustomVolumeSlider();
    
    // Клик по иконке громкости - mute/unmute
    document.getElementById('volumeIcon').addEventListener('click', toggleMute);
}

function setupCustomVolumeSlider() {
    const volumeTrack = document.querySelector('.volume-track-horizontal');
    const volumeFill = document.getElementById('volumeFill');
    const volumeThumb = document.getElementById('volumeThumb');
    
    if (!volumeTrack || !volumeFill || !volumeThumb) return;
    
    let isDragging = false;
    
    // Установить начальную громкость (70%)
    updateVolumeUI(70);
    
    // Клик по треку
    volumeTrack.addEventListener('click', function(e) {
        const rect = this.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const percent = (x / rect.width) * 100;
        const volume = Math.max(0, Math.min(100, percent));
        
        // Устанавливаем громкость в зависимости от типа плеера
        if (audioPlayer) {
            audioPlayer.volume = volume / 100;
        } else if (soundcloudWidget) {
            soundcloudWidget.setVolume(volume);
        }
        
        updateVolumeUI(volume);
        updateVolumeIcon(volume);
    });
    
    // Начало перетаскивания
    volumeThumb.addEventListener('mousedown', function(e) {
        isDragging = true;
        e.preventDefault();
    });
    
    // Перетаскивание
    document.addEventListener('mousemove', function(e) {
        if (!isDragging) return;
        
        const rect = volumeTrack.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const percent = (x / rect.width) * 100;
        const volume = Math.max(0, Math.min(100, percent));
        
        // Устанавливаем громкость в зависимости от типа плеера
        if (audioPlayer) {
            audioPlayer.volume = volume / 100;
        } else if (soundcloudWidget) {
            soundcloudWidget.setVolume(volume);
        }
        
        updateVolumeUI(volume);
        updateVolumeIcon(volume);
    });
    
    // Конец перетаскивания
    document.addEventListener('mouseup', function() {
        isDragging = false;
    });
}

function updateVolumeUI(percent) {
    const volumeFill = document.getElementById('volumeFill');
    const volumeThumb = document.getElementById('volumeThumb');
    
    if (volumeFill && volumeThumb) {
        volumeFill.style.width = percent + '%';
        volumeThumb.style.left = percent + '%';
    }
}

function togglePlayPause() {
    if (!audioPlayer) return;
    
    const cover = document.getElementById('musicCover');
    
    if (isPlaying) {
        audioPlayer.pause();
        cover.classList.remove('playing');
    } else {
        audioPlayer.play();
        cover.classList.add('playing');
    }
    isPlaying = !isPlaying;
}

function updateProgress() {
    if (!audioPlayer) return;
    const percent = (audioPlayer.currentTime / audioPlayer.duration) * 100;
    const progressBar = document.getElementById('musicProgressBar');
    const progressThumb = document.getElementById('musicProgressThumb');
    
    if (progressBar && progressThumb) {
        progressBar.style.width = percent + '%';
        progressThumb.style.left = percent + '%';
    }
    
    // Обновляем время
    const current = formatTime(audioPlayer.currentTime);
    const total = formatTime(audioPlayer.duration);
    document.getElementById('musicInfo').textContent = `${current} / ${total}`;
}

function formatTime(seconds) {
    if (isNaN(seconds)) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
}

function updateVolumeIcon(volume) {
    const icon = document.getElementById('volumeIcon');
    if (volume == 0) {
        icon.textContent = '🔇';
    } else if (volume < 50) {
        icon.textContent = '🔉';
    } else {
        icon.textContent = '🔊';
    }
}

function toggleMute() {
    if (!audioPlayer) return;
    
    if (audioPlayer.volume > 0) {
        audioPlayer.dataset.prevVolume = audioPlayer.volume;
        audioPlayer.volume = 0;
        updateVolumeUI(0);
        updateVolumeIcon(0);
    } else {
        const prevVolume = parseFloat(audioPlayer.dataset.prevVolume) || 0.7;
        audioPlayer.volume = prevVolume;
        updateVolumeUI(prevVolume * 100);
        updateVolumeIcon(prevVolume * 100);
    }
}

function updateMusicInfo() {
    document.getElementById('musicInfo').textContent = 'Загружается...';
    const cover = document.getElementById('musicCover');
    cover.textContent = '';
    cover.classList.add('playing');
}

console.log('✅ Profile.js готов');
