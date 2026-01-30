# Главный файл - запускает только веб-сервер
import os

def main():
    """Главная функция"""
    print("=" * 50)
    print("🌐 Запуск веб-сервера TTFD")
    print("=" * 50)
    
    # Запускаем веб-сервер
    from app import app
    port = int(os.environ.get('PORT', 10000))
    
    print(f"✅ Веб-сервер запущен на порту {port}")
    print("💡 Discord бот теперь в отдельном проекте: TTFD-Discord")
    
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()
