// Customize Page JavaScript
console.log('🎨 Customize.js загружен');

let currentTheme = null;
let isPremium = false;

// Инициализация
document.addEventListener('DOMContentLoaded', function() {
    initCustomize();
});

function initCustomize() {
    // Загружаем текущую тему
    currentTheme = window.themeEngine.currentTheme;
    isPremium = window.themeEngine.isPremium;
    
    // Убеждаемся что все поля темы инициализированы
    if (!currentTheme.background) {
        currentTheme.background = {
            type: 'none',
            url: null,
            fit: 'cover',
            scale: 100,
            overlay: { enabled: true, color: 'rgba(0,0,0,0.3)' },
            blur: 0
        };
    }
    
    // Обновляем UI
    // updatePremiumBadge(); // Закомментировано - элемент удалён
    loadPresets();
    loadThemeToUI();
    
    // Настраиваем табы
    setupTabs();
    
    // Настраиваем обработчики
    setupEventListeners();
    
    console.log('✅ Customize инициализирован');
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

// Обработчики событий
function setupEventListeners() {
    // Кнопки выбора типа фона
    document.querySelectorAll('.bg-type-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.bg-type-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            document.getElementById('bgType').value = this.dataset.type;
            
            const uploadGroup = document.getElementById('bgUploadGroup');
            uploadGroup.style.display = this.dataset.type !== 'none' ? 'block' : 'none';
            updatePreview();
        });
    });
    
    // Кнопки выбора шрифта
    document.querySelectorAll('.font-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            document.querySelectorAll('.font-btn').forEach(b => b.classList.remove('active'));
            this.classList.add('active');
            document.getElementById('fontBase').value = this.dataset.font;
            updatePreview();
        });
    });
    
    // Фон
    document.getElementById('bgFile')?.addEventListener('change', handleBgUpload);
    document.getElementById('bgOverlay')?.addEventListener('change', function() {
        updateToggleText(this);
        updatePreview();
    });
    document.getElementById('bgBlur')?.addEventListener('input', function() {
        document.getElementById('bgBlurValue').textContent = this.value;
        updatePreview();
    });
    
    // Кнопки
    document.getElementById('btnRadius')?.addEventListener('input', function() {
        document.getElementById('btnRadiusValue').textContent = this.value;
        updatePreview();
    });
    document.getElementById('btnGlow')?.addEventListener('change', function() {
        updateToggleText(this);
        updatePreview();
    });
    document.getElementById('btnLift')?.addEventListener('input', function() {
        document.getElementById('btnLiftValue').textContent = this.value;
        updatePreview();
    });
    
    // Шрифты
    document.getElementById('fontScale')?.addEventListener('input', function() {
        document.getElementById('fontScaleValue').textContent = this.value;
        updatePreview();
    });
}
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

// Загрузка пресетов
function loadPresets() {
    const presets = window.themeEngine.getPresets();
    const grid = document.getElementById('presetsGrid');
    
    grid.innerHTML = presets.map(preset => `
        <div class="preset-card ${preset.id === currentTheme.id ? 'active' : ''}" 
             onclick="applyPreset('${preset.id}')">
            <div class="preset-preview" style="background: ${preset.colors.bg}"></div>
            <div class="preset-name">${preset.name}</div>
        </div>
    `).join('');
}

// Применить пресет
window.applyPreset = function(presetId) {
    const presets = window.themeEngine.getPresets();
    const preset = presets.find(p => p.id === presetId);
    
    if (preset) {
        // Сохраняем текущие настройки фона
        const currentBackground = currentTheme.background;
        
        // Применяем пресет
        currentTheme = JSON.parse(JSON.stringify(preset));
        
        // Восстанавливаем настройки фона
        currentTheme.background = currentBackground;
        
        loadThemeToUI();
        updatePreview();
        
        // Обновляем активный пресет
        document.querySelectorAll('.preset-card').forEach(card => {
            card.classList.remove('active');
        });
        event.target.closest('.preset-card').classList.add('active');
    }
}

// Загрузка темы в UI
function loadThemeToUI() {
    if (!currentTheme) {
        console.error('currentTheme не определена');
        return;
    }
    
    // Фон
    const bg = currentTheme.background || { type: 'none', fit: 'cover', scale: 100, overlay: { enabled: true }, blur: 0 };
    
    // Устанавливаем активную кнопку типа фона
    document.querySelectorAll('.bg-type-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.type === bg.type);
    });
    document.getElementById('bgType').value = bg.type;
    
    const bgOverlayCheckbox = document.getElementById('bgOverlay');
    bgOverlayCheckbox.checked = bg.overlay?.enabled || false;
    updateToggleText(bgOverlayCheckbox);
    document.getElementById('bgBlur').value = bg.blur || 0;
    document.getElementById('bgBlurValue').textContent = bg.blur || 0;
    document.getElementById('bgUploadGroup').style.display = bg.type !== 'none' ? 'block' : 'none';
    
    // Кнопки
    const buttons = currentTheme.buttons || { radius: 8, borderWidth: 2, glow: false, hover: { lift: 2 } };
    document.getElementById('btnRadius').value = buttons.radius;
    document.getElementById('btnRadiusValue').textContent = buttons.radius;
    
    const btnGlowCheckbox = document.getElementById('btnGlow');
    btnGlowCheckbox.checked = buttons.glow || false;
    updateToggleText(btnGlowCheckbox);
    
    document.getElementById('btnLift').value = buttons.hover?.lift || 2;
    document.getElementById('btnLiftValue').textContent = buttons.hover?.lift || 2;
    
    // Шрифты
    const fonts = currentTheme.fonts || { base: 'Segoe UI', sizeScale: 1.0 };
    
    // Устанавливаем активную кнопку шрифта
    document.querySelectorAll('.font-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.font === fonts.base);
    });
    document.getElementById('fontBase').value = fonts.base;
}

// Обновление preview
function updatePreview() {
    // Собираем данные из UI
    const theme = {
        ...currentTheme,
        background: {
            type: document.getElementById('bgType').value,
            url: currentTheme.background?.url || null,
            fit: 'cover',
            scale: 100,
            overlay: {
                enabled: document.getElementById('bgOverlay').checked,
                color: 'rgba(0,0,0,0.3)'
            },
            blur: parseInt(document.getElementById('bgBlur').value)
        },
        buttons: {
            radius: parseInt(document.getElementById('btnRadius').value),
            hover: {
                lift: parseInt(document.getElementById('btnLift').value),
                scale: 1.02
            },
            borderWidth: 2,
            glow: document.getElementById('btnGlow').checked
        },
        fonts: {
            base: document.getElementById('fontBase').value,
            heading: document.getElementById('fontBase').value,
            sizeScale: 1.0
        }
    };
    
    currentTheme = theme;
    
    // Применяем тему локально (не сохраняя)
    window.themeEngine.applyTheme(theme);
}

// Загрузка фона
function handleBgUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = function(event) {
        // Убеждаемся что background инициализирован
        if (!currentTheme.background) {
            currentTheme.background = {
                type: 'image',
                url: null,
                fit: 'cover',
                scale: 100,
                overlay: { enabled: true, color: 'rgba(0,0,0,0.3)' },
                blur: 0
            };
        }
        
        currentTheme.background.url = event.target.result;
        
        const preview = document.getElementById('bgPreview');
        if (currentTheme.background.type === 'video') {
            preview.innerHTML = `<video src="${event.target.result}" style="max-width:100%; max-height:100px;" controls></video>`;
        } else {
            preview.innerHTML = `<img src="${event.target.result}" style="max-width:100%; max-height:100px; border-radius:8px;">`;
        }
        
        updatePreview();
    };
    reader.readAsDataURL(file);
}

// Сохранение темы
window.saveTheme = function() {
    window.themeEngine.saveTheme(currentTheme);
    alert('✅ Тема сохранена и применена!');
}

// Сброс темы
window.resetTheme = function() {
    if (confirm('Сбросить тему к настройкам по умолчанию?')) {
        currentTheme = window.themeEngine.getDefaultTheme();
        loadThemeToUI();
        updatePreview();
        loadPresets();
    }
}

// Toggle Premium
window.togglePremium = function() {
    isPremium = !isPremium;
    window.themeEngine.setPremium(isPremium);
    updatePremiumBadge();
    updatePreview();
}

function updatePremiumBadge() {
    const badge = document.getElementById('premiumStatus');
    badge.textContent = isPremium ? '👑 Premium' : 'Free';
    badge.style.color = isPremium ? '#ffd700' : 'inherit';
    
    // Обновляем premium features
    document.querySelectorAll('.premium-feature').forEach(el => {
        if (isPremium) {
            el.classList.add('unlocked');
        } else {
            el.classList.remove('unlocked');
        }
    });
}

console.log('✅ Customize.js готов');
