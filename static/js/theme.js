// Theme Manager - Применение пользовательской темы
(function() {
    console.log('🎨 Theme.js загружен');
    
    // Получаем данные из data-атрибутов body
    const userColor = document.body.getAttribute('data-user-color');
    const backgroundUrl = document.body.getAttribute('data-background-url');
    const backgroundType = document.body.getAttribute('data-background-type');
    
    console.log('📦 Данные темы:', { userColor, backgroundUrl, backgroundType });
    
    // Применяем background (изображение/видео имеет приоритет над цветом)
    if (backgroundUrl && backgroundUrl !== '' && backgroundType) {
        console.log('✅ Применяем background media:', backgroundUrl);
        applyBackgroundMedia(backgroundUrl, backgroundType);
    } else if (userColor && userColor !== '#667eea' && userColor !== '') {
        console.log('✅ Применяем цвет:', userColor);
        applyTheme(userColor);
    } else {
        console.log('ℹ️ Используется стандартный градиент');
    }
    
    function applyBackgroundMedia(url, type) {
        // Убираем стандартный градиент
        document.body.style.background = 'none';
        
        if (type === 'video') {
            console.log('🎬 Создаём видео фон');
            // Создаём видео фон
            const video = document.createElement('video');
            video.src = url;
            video.autoplay = true;
            video.loop = true;
            video.muted = true;
            video.playsInline = true;
            video.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                object-fit: cover;
                z-index: -1;
                pointer-events: none;
            `;
            document.body.insertBefore(video, document.body.firstChild);
            
            // Добавляем полупрозрачный оверлей для читаемости
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.3);
                z-index: -1;
                pointer-events: none;
            `;
            document.body.insertBefore(overlay, document.body.children[1]);
        } else {
            console.log('🖼️ Применяем изображение фон');
            // Применяем изображение как фон
            document.body.style.backgroundImage = `url('${url}')`;
            document.body.style.backgroundSize = 'cover';
            document.body.style.backgroundPosition = 'center';
            document.body.style.backgroundAttachment = 'fixed';
            document.body.style.backgroundRepeat = 'no-repeat';
            
            // Добавляем полупрозрачный оверлей для читаемости
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.2);
                z-index: -1;
                pointer-events: none;
            `;
            document.body.insertBefore(overlay, document.body.firstChild);
        }
    }
    
    function applyTheme(color) {
        // Create gradient with user color
        const lighterColor = adjustColor(color, 20);
        document.body.style.background = `linear-gradient(135deg, ${color} 0%, ${lighterColor} 100%)`;
        document.body.style.backgroundAttachment = 'fixed';
        document.body.style.minHeight = '100vh';
    }
    
    function adjustColor(color, percent) {
        const num = parseInt(color.replace("#",""), 16);
        const amt = Math.round(2.55 * percent);
        const R = (num >> 16) + amt;
        const G = (num >> 8 & 0x00FF) + amt;
        const B = (num & 0x0000FF) + amt;
        return "#" + (0x1000000 + (R<255?R<1?0:R:255)*0x10000 +
            (G<255?G<1?0:G:255)*0x100 + (B<255?B<1?0:B:255))
            .toString(16).slice(1);
    }
})();
