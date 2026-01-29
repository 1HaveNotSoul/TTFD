// Settings Page JavaScript
console.log('⚙️ Settings.js загружен');

// ==================== UPLOAD AREAS ====================

// Функция для настройки upload area
function setupUploadArea(areaId, fileInputId, onFileSelect) {
    const area = document.getElementById(areaId);
    const fileInput = document.getElementById(fileInputId);
    
    if (!area || !fileInput) return;
    
    // Клик по area открывает file input
    area.addEventListener('click', () => fileInput.click());
    
    // Drag & Drop
    area.addEventListener('dragover', (e) => {
        e.preventDefault();
        area.classList.add('drag-over');
    });
    
    area.addEventListener('dragleave', () => {
        area.classList.remove('drag-over');
    });
    
    area.addEventListener('drop', (e) => {
        e.preventDefault();
        area.classList.remove('drag-over');
        
        if (e.dataTransfer.files.length > 0) {
            fileInput.files = e.dataTransfer.files;
            if (onFileSelect) onFileSelect(e.dataTransfer.files[0]);
        }
    });
    
    // File select
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            if (onFileSelect) onFileSelect(e.target.files[0]);
        }
    });
}

// Настройка всех upload areas
setupUploadArea('avatarUploadArea', 'avatar_file', (file) => {
    console.log('📸 Выбран файл аватарки:', file.name);
    showPreview('avatarUploadArea', file, 'image');
});

setupUploadArea('musicUploadArea', 'music_file', (file) => {
    console.log('🎵 Выбран файл музыки:', file.name);
    showPreview('musicUploadArea', file, 'audio');
});

setupUploadArea('profileBgUploadArea', 'profile_bg_file', (file) => {
    console.log('🖼️ Выбран фон профиля:', file.name);
    showPreview('profileBgUploadArea', file, 'image');
});

setupUploadArea('backgroundUploadArea', 'background_file', (file) => {
    console.log('🖼️ Выбран фон сайта:', file.name);
    const type = file.type.startsWith('video/') ? 'video' : 'image';
    showPreview('backgroundUploadArea', file, type);
});

// Показать preview загруженного файла
function showPreview(areaId, file, type) {
    const area = document.getElementById(areaId);
    const placeholder = area.querySelector('.upload-placeholder');
    
    const reader = new FileReader();
    reader.onload = (e) => {
        if (type === 'image') {
            placeholder.innerHTML = `<img src="${e.target.result}" alt="Preview" class="preview-image fade-in">`;
        } else if (type === 'video') {
            placeholder.innerHTML = `<video src="${e.target.result}" class="preview-video fade-in" controls></video>`;
        } else if (type === 'audio') {
            placeholder.innerHTML = `<audio src="${e.target.result}" class="preview-audio fade-in" controls></audio>`;
        }
    };
    reader.readAsDataURL(file);
}

// Показать прогресс загрузки
function showProgress(progressId, percent) {
    const progress = document.getElementById(progressId);
    const bar = progress.querySelector('.progress-bar');
    
    progress.style.display = 'block';
    bar.style.width = percent + '%';
    
    if (percent >= 100) {
        setTimeout(() => {
            progress.style.display = 'none';
            bar.style.width = '0%';
        }, 1000);
    }
}

// ==================== FORMS ====================

// Profile Form
document.getElementById('profileForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const data = {
        display_name: document.getElementById('display_name').value,
        bio: document.getElementById('bio').value
    };
    await updateProfile(data);
});

// Avatar Form
document.getElementById('avatarForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('avatar_file');
    
    if (!fileInput.files || !fileInput.files[0]) {
        showMessage('Выбери файл для загрузки', 'error');
        return;
    }
    
    if (fileInput.files[0].size > 5 * 1024 * 1024) {
        showMessage('Файл слишком большой! Максимум 5MB', 'error');
        return;
    }
    
    await uploadFile('/api/upload_avatar', 'avatar', fileInput.files[0], 'avatarProgress');
});

// Music Form
document.getElementById('musicForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('music_file');
    
    if (!fileInput.files || !fileInput.files[0]) {
        showMessage('Выбери MP3 файл для загрузки', 'error');
        return;
    }
    
    if (fileInput.files[0].size > 10 * 1024 * 1024) {
        showMessage('Файл слишком большой! Максимум 10MB', 'error');
        return;
    }
    
    await uploadFile('/api/upload_music', 'music', fileInput.files[0], 'musicProgress');
});

// Profile Background Form
document.getElementById('profileBgForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('profile_bg_file');
    
    if (!fileInput.files || !fileInput.files[0]) {
        showMessage('Выбери файл для загрузки', 'error');
        return;
    }
    
    if (fileInput.files[0].size > 10 * 1024 * 1024) {
        showMessage('Файл слишком большой! Максимум 10MB', 'error');
        return;
    }
    
    await uploadFile('/api/upload_profile_bg', 'profile_bg', fileInput.files[0], 'profileBgProgress');
});

// Theme Form (color)
document.getElementById('themeForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const bgColor = document.getElementById('bg_color').value;
    const data = { bg_color: bgColor };
    const result = await updateProfile(data);
    if (result) {
        applyThemePreview(bgColor);
    }
});

// Background Form (image/video)
document.getElementById('backgroundForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById('background_file');
    
    if (!fileInput.files || !fileInput.files[0]) {
        showMessage('Выбери файл для загрузки', 'error');
        return;
    }
    
    if (fileInput.files[0].size > 50 * 1024 * 1024) {
        showMessage('Файл слишком большой! Максимум 50MB', 'error');
        return;
    }
    
    await uploadFile('/api/upload_background', 'background', fileInput.files[0], 'backgroundProgress');
});

// Discord Form
document.getElementById('discordForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const discord_id = document.getElementById('discord_id').value;
    
    if (!discord_id || discord_id.length < 17) {
        showMessage('Введи корректный Discord ID', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/link_discord', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({discord_id})
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage('✅ Discord успешно привязан!', 'success');
        } else {
            showMessage(data.error, 'error');
        }
    } catch (error) {
        showMessage('Ошибка привязки Discord', 'error');
    }
});

// Password Form
document.getElementById('passwordForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const old_password = document.getElementById('old_password').value;
    const new_password = document.getElementById('new_password').value;
    const new_password2 = document.getElementById('new_password2').value;
    
    if (new_password !== new_password2) {
        showMessage('Новые пароли не совпадают', 'error');
        return;
    }
    
    if (new_password.length < 6) {
        showMessage('Пароль должен быть минимум 6 символов', 'error');
        return;
    }
    
    try {
        const response = await fetch('/api/change_password', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({old_password, new_password})
        });
        const data = await response.json();
        
        if (data.success) {
            showMessage('✅ Пароль успешно изменён!', 'success');
            document.getElementById('passwordForm').reset();
        } else {
            showMessage(data.error, 'error');
        }
    } catch (error) {
        showMessage('Ошибка смены пароля', 'error');
    }
});

// ==================== COLOR PICKERS ====================

// Sync color pickers
document.getElementById('bg_color')?.addEventListener('input', function(e) {
    document.getElementById('bg_color_text').value = e.target.value;
    applyThemePreview(e.target.value);
});

document.getElementById('bg_color_text')?.addEventListener('input', function(e) {
    const color = e.target.value;
    if (/^#[0-9A-F]{6}$/i.test(color)) {
        document.getElementById('bg_color').value = color;
        applyThemePreview(color);
    }
});

document.getElementById('profile_bg_color')?.addEventListener('input', function(e) {
    document.getElementById('profile_bg_color_text').value = e.target.value;
});

document.getElementById('profile_bg_color_text')?.addEventListener('input', function(e) {
    const color = e.target.value;
    if (/^#[0-9A-F]{6}$/i.test(color)) {
        document.getElementById('profile_bg_color').value = color;
    }
});

function resetColor() {
    const defaultColor = '#667eea';
    document.getElementById('bg_color').value = defaultColor;
    document.getElementById('bg_color_text').value = defaultColor;
    applyThemePreview(defaultColor);
}

function resetProfileColor() {
    const defaultColor = '#667eea';
    document.getElementById('profile_bg_color').value = defaultColor;
    document.getElementById('profile_bg_color_text').value = defaultColor;
}

function applyThemePreview(color) {
    const lighterColor = adjustColor(color, 20);
    document.body.style.background = `linear-gradient(135deg, ${color} 0%, ${lighterColor} 100%)`;
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

// ==================== PROFILE BG SAVE ====================

async function saveProfileBg() {
    const color = document.getElementById('profile_bg_color').value;
    const data = { profile_bg_color: color };
    await updateProfile(data);
}

// ==================== API FUNCTIONS ====================

async function updateProfile(data) {
    try {
        const response = await fetch('/api/update_profile', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(data)
        });
        const result = await response.json();
        
        if (result.success) {
            showMessage('✅ Профиль обновлён!', 'success');
            return true;
        } else {
            showMessage(result.error, 'error');
            return false;
        }
    } catch (error) {
        showMessage('Ошибка обновления профиля', 'error');
        return false;
    }
}

async function uploadFile(endpoint, fieldName, file, progressId) {
    const formData = new FormData();
    formData.append(fieldName, file);
    
    try {
        showProgress(progressId, 0);
        
        const xhr = new XMLHttpRequest();
        
        xhr.upload.addEventListener('progress', (e) => {
            if (e.lengthComputable) {
                const percent = (e.loaded / e.total) * 100;
                showProgress(progressId, percent);
            }
        });
        
        xhr.addEventListener('load', () => {
            showProgress(progressId, 100);
            
            if (xhr.status === 200) {
                const data = JSON.parse(xhr.responseText);
                if (data.success) {
                    showMessage('✅ Файл загружен!', 'success');
                    setTimeout(() => location.reload(), 1500);
                } else {
                    showMessage(data.error, 'error');
                }
            } else {
                showMessage('Ошибка загрузки файла', 'error');
            }
        });
        
        xhr.addEventListener('error', () => {
            showMessage('Ошибка соединения', 'error');
        });
        
        xhr.open('POST', endpoint);
        xhr.send(formData);
        
    } catch (error) {
        showMessage('Ошибка загрузки файла', 'error');
    }
}

function showMessage(text, type) {
    const msg = document.getElementById('message');
    msg.className = 'message ' + type;
    msg.style.display = 'block';
    msg.textContent = text;
    window.scrollTo({top: 0, behavior: 'smooth'});
    setTimeout(() => {
        msg.style.display = 'none';
    }, 5000);
}
