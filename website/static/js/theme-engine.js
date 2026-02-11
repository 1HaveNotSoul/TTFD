// Theme Engine - Управление темами
console.log('🎨 Theme Engine загружен');

class ThemeEngine {
    constructor() {
        this.defaultTheme = this.getDefaultTheme();
        this.currentTheme = null;
        this.isPremium = false; // Мок premium статуса
        this.init();
    }

    getDefaultTheme() {
        return {
            id: 'default',
            name: 'Default',
            colors: {
                bg: '#1a1a2e',
                cardBg: '#16213e',
                text: '#e5e7eb',
                textLight: '#9ca3af',
                accent: '#667eea',
                accentDark: '#764ba2',
                buttonBg: '#667eea',
                buttonText: '#ffffff',
                border: '#e2e8f0'
            },
            background: {
                type: 'none', // none, image, video, gif
                url: null,
                fit: 'cover', // cover, contain
                overlay: { enabled: true, color: 'rgba(0,0,0,0.1)' },
                blur: 0
            },
            buttons: {
                radius: 8,
                hover: { lift: 2, scale: 1.02 },
                borderWidth: 2,
                glow: false
            },
            fonts: {
                base: 'Segoe UI',
                heading: 'Segoe UI',
                sizeScale: 1.0
            },
            music: {
                enabled: false,
                url: null,
                volume: 0.35,
                autoplay: true
            },
            customCSS: ''
        };
    }

    init() {
        // Загружаем тему из localStorage
        const saved = localStorage.getItem('userTheme');
        const premium = localStorage.getItem('isPremium');
        
        this.isPremium = premium === 'true';
        
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                
                // Удаляем старые RGB настройки если они есть
                if (parsed.rgb_glow) {
                    delete parsed.rgb_glow;
                }
                if (parsed.gradients) {
                    delete parsed.gradients;
                }
                
                // Убеждаемся что все поля есть
                this.currentTheme = { ...this.defaultTheme, ...parsed };
            } catch (e) {
                console.error('Ошибка загрузки темы:', e);
                this.currentTheme = this.defaultTheme;
            }
        } else {
            this.currentTheme = this.defaultTheme;
        }
        
        // Применяем тему
        this.applyTheme(this.currentTheme);
        
        console.log('✅ Тема загружена:', this.currentTheme.name);
    }

    applyTheme(theme) {
        // Применяем premium гейты
        const effectiveTheme = this.applyPremiumGates(theme);
        
        // Применяем CSS variables
        this.applyCSSVariables(effectiveTheme.colors);
        
        // Применяем фон
        this.applyBackground(effectiveTheme.background);
        
        // Применяем стили кнопок
        this.applyButtonStyles(effectiveTheme.buttons);
        
        // Применяем шрифты
        this.applyFonts(effectiveTheme.fonts);
        
        // Применяем custom CSS
        this.applyCustomCSS(effectiveTheme.customCSS);
        
        // Применяем музыку (если premium)
        if (this.isPremium && effectiveTheme.music.enabled) {
            this.applyMusic(effectiveTheme.music);
        }
        
        this.currentTheme = effectiveTheme;
    }

    applyPremiumGates(theme) {
        const gated = JSON.parse(JSON.stringify(theme));
        
        if (!this.isPremium) {
            // Отключаем premium фичи
            gated.music.enabled = false;
        }
        
        return gated;
    }

    applyCSSVariables(colors) {
        const root = document.documentElement;
        
        root.style.setProperty('--bg', colors.bg);
        root.style.setProperty('--card-bg', colors.cardBg);
        root.style.setProperty('--text', colors.text);
        root.style.setProperty('--text-light', colors.textLight);
        root.style.setProperty('--primary', colors.accent);
        root.style.setProperty('--primary-dark', colors.accentDark);
        root.style.setProperty('--border', colors.border);
        
        // Сбрасываем градиент фона если он был (будет применён позже если нужно)
        document.body.style.background = colors.bg;
    }

    applyBackground(bg) {
        // Удаляем старый фон
        let bgLayer = document.getElementById('theme-bg-layer');
        if (bgLayer) bgLayer.remove();
        
        if (bg.type === 'none') return;
        
        // Создаём слой фона
        bgLayer = document.createElement('div');
        bgLayer.id = 'theme-bg-layer';
        bgLayer.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            pointer-events: none;
        `;
        
        if (bg.type === 'image' || bg.type === 'gif') {
            bgLayer.style.backgroundImage = `url(${bg.url})`;
            bgLayer.style.backgroundSize = bg.fit;
            bgLayer.style.backgroundPosition = 'center';
            bgLayer.style.backgroundRepeat = 'no-repeat';
            bgLayer.style.imageRendering = 'high-quality';
            bgLayer.style.imageRendering = '-webkit-optimize-contrast';
            
            // Применяем масштаб
            if (bg.scale && bg.scale !== 100) {
                bgLayer.style.transform = `scale(${bg.scale / 100})`;
            }
        } else if (bg.type === 'video') {
            const video = document.createElement('video');
            video.src = bg.url;
            video.autoplay = true;
            video.loop = true;
            video.muted = true;
            video.playsInline = true;
            video.style.cssText = `
                width: 100%;
                height: 100%;
                object-fit: ${bg.fit};
            `;
            
            // Применяем масштаб к видео
            if (bg.scale && bg.scale !== 100) {
                video.style.transform = `scale(${bg.scale / 100})`;
            }
            
            bgLayer.appendChild(video);
        }
        
        // Overlay
        if (bg.overlay.enabled) {
            const overlay = document.createElement('div');
            overlay.style.cssText = `
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: ${bg.overlay.color};
            `;
            bgLayer.appendChild(overlay);
        }
        
        // Blur
        if (bg.blur > 0) {
            bgLayer.style.filter = `blur(${bg.blur}px)`;
        }
        
        document.body.prepend(bgLayer);
    }

    applyButtonStyles(buttons) {
        const root = document.documentElement;
        
        root.style.setProperty('--btn-radius', buttons.radius + 'px');
        root.style.setProperty('--btn-border-width', buttons.borderWidth + 'px');
        root.style.setProperty('--btn-hover-lift', buttons.hover.lift + 'px');
        root.style.setProperty('--btn-hover-scale', buttons.hover.scale);
        
        // Применяем glow эффект
        if (buttons.glow) {
            const primaryColor = getComputedStyle(root).getPropertyValue('--primary').trim();
            root.style.setProperty('--btn-glow', `0 0 10px ${primaryColor}`);
        } else {
            root.style.setProperty('--btn-glow', 'none');
        }
    }

    applyFonts(fonts) {
        const root = document.documentElement;
        
        root.style.setProperty('--font-base', fonts.base);
        root.style.setProperty('--font-heading', fonts.heading);
        root.style.setProperty('--font-scale', fonts.sizeScale);
        
        document.body.style.fontFamily = fonts.base;
    }



    applyCustomCSS(css) {
        // Удаляем старый custom CSS
        let styleEl = document.getElementById('theme-custom-css');
        if (styleEl) styleEl.remove();
        
        if (!css) return;
        
        // Sanitize и применяем
        const sanitized = this.sanitizeCSS(css);
        
        styleEl = document.createElement('style');
        styleEl.id = 'theme-custom-css';
        styleEl.textContent = `.user-scope { ${sanitized} }`;
        document.head.appendChild(styleEl);
    }

    sanitizeCSS(css) {
        // Базовая санитизация
        let clean = css;
        
        // Удаляем опасные конструкции
        clean = clean.replace(/@import/gi, '');
        clean = clean.replace(/url\(/gi, '');
        clean = clean.replace(/expression\(/gi, '');
        clean = clean.replace(/behavior:/gi, '');
        clean = clean.replace(/-moz-binding/gi, '');
        
        // Ограничиваем position: fixed
        clean = clean.replace(/position:\s*fixed/gi, 'position: relative');
        
        return clean;
    }

    applyMusic(music) {
        // Удаляем старый плеер
        let audio = document.getElementById('theme-music');
        if (audio) audio.remove();
        
        if (!music.url) return;
        
        audio = document.createElement('audio');
        audio.id = 'theme-music';
        audio.src = music.url;
        audio.volume = music.volume;
        audio.loop = true;
        
        if (music.autoplay) {
            audio.play().catch(e => console.log('Autoplay blocked:', e));
        }
        
        document.body.appendChild(audio);
    }

    saveTheme(theme) {
        localStorage.setItem('userTheme', JSON.stringify(theme));
        this.applyTheme(theme);
        console.log('✅ Тема сохранена');
    }

    setPremium(status) {
        this.isPremium = status;
        localStorage.setItem('isPremium', status);
        this.applyTheme(this.currentTheme);
        console.log('✅ Premium статус:', status);
    }

    getPresets() {
        return [
            this.getDefaultTheme(),
            {
                ...this.getDefaultTheme(),
                id: 'dark',
                name: 'Dark',
                colors: {
                    bg: '#0b0f19',
                    cardBg: '#1a1f2e',
                    text: '#e5e7eb',
                    textLight: '#9ca3af',
                    accent: '#000000',
                    accentDark: '#1a1a1a',
                    buttonBg: '#000000',
                    buttonText: '#ffffff',
                    border: 'rgba(255,255,255,0.12)'
                }
            },
            {
                ...this.getDefaultTheme(),
                id: 'ocean',
                name: 'Ocean',
                colors: {
                    bg: '#0f172a',
                    cardBg: '#1e293b',
                    text: '#f1f5f9',
                    textLight: '#94a3b8',
                    accent: '#0ea5e9',
                    accentDark: '#0284c7',
                    buttonBg: '#0ea5e9',
                    buttonText: '#ffffff',
                    border: 'rgba(255,255,255,0.1)'
                }
            },
            {
                ...this.getDefaultTheme(),
                id: 'sunset',
                name: 'Sunset',
                colors: {
                    bg: '#1a0e0e',
                    cardBg: '#2d1b1b',
                    text: '#fef3c7',
                    textLight: '#fbbf24',
                    accent: '#f97316',
                    accentDark: '#ea580c',
                    buttonBg: '#f97316',
                    buttonText: '#ffffff',
                    border: 'rgba(249,115,22,0.2)'
                }
            },
            {
                ...this.getDefaultTheme(),
                id: 'forest',
                name: 'Forest',
                colors: {
                    bg: '#0a1f0a',
                    cardBg: '#1a2e1a',
                    text: '#d1fae5',
                    textLight: '#6ee7b7',
                    accent: '#10b981',
                    accentDark: '#059669',
                    buttonBg: '#10b981',
                    buttonText: '#ffffff',
                    border: 'rgba(16,185,129,0.2)'
                }
            },
            {
                ...this.getDefaultTheme(),
                id: 'neon',
                name: 'Neon',
                colors: {
                    bg: '#0a0a0a',
                    cardBg: '#1a1a1a',
                    text: '#ffffff',
                    textLight: '#a3a3a3',
                    accent: '#ec4899',
                    accentDark: '#db2777',
                    buttonBg: '#ec4899',
                    buttonText: '#ffffff',
                    border: 'rgba(236,72,153,0.3)'
                }
            },
            {
                ...this.getDefaultTheme(),
                id: 'cyberpunk',
                name: 'Cyberpunk',
                colors: {
                    bg: '#0d0221',
                    cardBg: '#1a0b3d',
                    text: '#00ffff',
                    textLight: '#ff00ff',
                    accent: '#ffff00',
                    accentDark: '#ff00ff',
                    buttonBg: '#ffff00',
                    buttonText: '#0d0221',
                    border: 'rgba(255,255,0,0.3)'
                }
            },
            {
                ...this.getDefaultTheme(),
                id: 'midnight',
                name: 'Midnight',
                colors: {
                    bg: '#020617',
                    cardBg: '#0f172a',
                    text: '#e2e8f0',
                    textLight: '#94a3b8',
                    accent: '#6366f1',
                    accentDark: '#4f46e5',
                    buttonBg: '#6366f1',
                    buttonText: '#ffffff',
                    border: 'rgba(99,102,241,0.2)'
                }
            },
            {
                ...this.getDefaultTheme(),
                id: 'rose',
                name: 'Rose',
                colors: {
                    bg: '#1f1018',
                    cardBg: '#2d1b28',
                    text: '#fce7f3',
                    textLight: '#f9a8d4',
                    accent: '#f43f5e',
                    accentDark: '#e11d48',
                    buttonBg: '#f43f5e',
                    buttonText: '#ffffff',
                    border: 'rgba(244,63,94,0.2)'
                }
            }
        ];
    }
}

// Глобальный экземпляр
window.themeEngine = new ThemeEngine();
