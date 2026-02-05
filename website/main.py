# Главный файл - запускает только веб-сервер
import os
import sys

def main():
    """Главная функция"""
    # Запускаем веб-сервер
    from app import app
    port = int(os.environ.get('PORT', 10000))
    
    print("🌐 TTFD Website запущен на порту", port)
    
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()
