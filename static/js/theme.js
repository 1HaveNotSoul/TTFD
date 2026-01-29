// Theme Manager - Применение пользовательской темы
(function() {
    // Получаем цвет из data-атрибута body
    const userColor = document.body.getAttribute('data-user-color');
    
    if (userColor && userColor !== '#667eea') {
        applyTheme(userColor);
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
