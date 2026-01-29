// Theme Manager - Применение пользовательской темы
(function() {
    // Получаем данные из data-атрибутов body
    const userColor = document.body.getAttribute('data-user-color');
    const backgroundUrl = document.body.getAttribute('data-background-url');
    const backgroundType = document.body.getAttribute('data-background-type');
    
    // Применяем background (изображение/видео имеет приоритет над цветом)
    if (backgroundUrl && backgroundType) {
        applyBackgroundMedia(backgroundUrl, backgroundType);
    } else if (userColor && userColor !== '#667eea') {
        applyTheme(userColor);
    }
    
    function applyBackgroundMedia(url, type) {
        if (type === 'video') {
            // Создаём видео фон
            const video = document.createElement('video');
            video.src = url;
            video.autoplay = true;
            video.loop = true;
            video.muted = true;
            video.style.cssText = `
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                object-fit: cover;
                z-index: -1;
            `;
            document.body.insertBefore(video, document.body.firstChild);
            document.body.style.background = 'transparent';
        } else {
            // Применяем изображение как фон
            document.body.style.background = `url('${url}') center/cover fixed`;
        }
    }
    
    function applyTheme(color) {
        // Create gradient with user color
        const lighterColor = adjustColor(color, 20);
        document.body.style.background = `linear-gradient(135deg, ${color} 0%, ${lighterColor} 100%)`;
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
