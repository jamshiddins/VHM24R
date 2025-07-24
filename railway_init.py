#!/usr/bin/env python3
"""
VHM24R - Railway Production Initialization Script
Автоматическая настройка базы данных и проверка системы
"""

import os
import sys
import time
from datetime import datetime

def log(message):
    """Логирование с временной меткой"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def check_environment():
    """Проверка переменных окружения"""
    log("🔍 Проверка переменных окружения...")
    
    required_vars = ['DATABASE_URL', 'SECRET_KEY']
    missing_vars = []
    
    for var in required_vars:
        if not os.environ.get(var):
            missing_vars.append(var)
    
    if missing_vars:
        log(f"❌ Отсутствуют обязательные переменные: {', '.join(missing_vars)}")
        return False
    
    log("✅ Все обязательные переменные присутствуют")
    return True

def init_database():
    """Инициализация базы данных"""
    log("🗄️ Инициализация базы данных...")
    
    try:
        from models import get_database
        
        # Подключение к базе данных
        db = get_database()
        log("✅ Подключение к базе данных установлено")
        
        # Проверка таблиц
        tables = db.execute_query("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        
        log(f"📊 Найдено таблиц в базе: {len(tables)}")
        
        if len(tables) == 0:
            log("🔧 База данных пуста, инициализация схемы...")
            # Схема инициализируется автоматически в models.py
        
        # Проверка работы базы данных
        stats = db.get_processing_stats()
        log(f"📈 Статистика базы данных: {stats}")
        
        return True
        
    except Exception as e:
        log(f"❌ Ошибка инициализации базы данных: {e}")
        return False

def check_components():
    """Проверка всех компонентов системы"""
    log("🔧 Проверка компонентов системы...")
    
    try:
        # Проверка процессоров
        from processors_updated import OrderProcessor, RecipeProcessor, FinanceProcessor
        from models import get_database
        
        db = get_database()
        
        order_processor = OrderProcessor(db)
        recipe_processor = RecipeProcessor(db)
        finance_processor = FinanceProcessor(db)
        
        log("✅ Процессоры инициализированы")
        
        # Проверка детектора файлов
        from file_detector_updated import AdvancedFileTypeDetector
        file_detector = AdvancedFileTypeDetector()
        log("✅ Детектор файлов инициализирован")
        
        # Проверка хранилища
        from storage import init_storage
        file_manager = init_storage(db, 'uploads')
        log("✅ Файловое хранилище инициализировано")
        
        # Проверка Telegram (опционально)
        from telegram_bot import init_telegram
        telegram_notifier, _ = init_telegram(db)
        if telegram_notifier:
            log("✅ Telegram интеграция активна")
        else:
            log("⚠️ Telegram интеграция отключена (нет токена)")
        
        # Проверка планировщика
        scheduler_enabled = os.environ.get('SCHEDULER_ENABLED', 'false').lower() == 'true'
        if scheduler_enabled:
            from scheduler import init_scheduler
            scheduler = init_scheduler(db, order_processor, telegram_notifier, file_manager)
            log("✅ Планировщик задач активен")
        else:
            log("⚠️ Планировщик задач отключен")
        
        return True
        
    except Exception as e:
        log(f"❌ Ошибка проверки компонентов: {e}")
        return False

def health_check():
    """Проверка здоровья системы"""
    log("🏥 Проверка здоровья системы...")
    
    try:
        from models import get_database
        
        db = get_database()
        
        # Проверка подключения к БД
        result = db.execute_query("SELECT 1 as test")
        if result and result[0]['test'] == 1:
            log("✅ База данных отвечает")
        else:
            log("❌ База данных не отвечает")
            return False
        
        # Проверка статистики
        stats = db.get_processing_stats()
        log(f"📊 Общая статистика: {stats.get('total', 0)} записей")
        
        return True
        
    except Exception as e:
        log(f"❌ Ошибка проверки здоровья: {e}")
        return False

def setup_production_optimizations():
    """Настройка оптимизаций для production"""
    log("⚡ Настройка production оптимизаций...")
    
    try:
        # Установка переменных окружения по умолчанию
        defaults = {
            'WEB_CONCURRENCY': '4',
            'WORKER_TIMEOUT': '300',
            'MAX_REQUESTS': '2000',
            'SCHEDULER_ENABLED': 'true',
            'BACKUP_ENABLED': 'true',
            'DEBUG': 'false'
        }
        
        for key, value in defaults.items():
            if not os.environ.get(key):
                os.environ[key] = value
                log(f"🔧 Установлена переменная {key}={value}")
        
        log("✅ Production оптимизации применены")
        return True
        
    except Exception as e:
        log(f"❌ Ошибка настройки оптимизаций: {e}")
        return False

def main():
    """Основная функция инициализации"""
    log("🚀 Запуск Railway Production Initialization для VHM24R")
    log("=" * 60)
    
    # Проверка переменных окружения
    if not check_environment():
        log("❌ Инициализация прервана из-за отсутствующих переменных")
        sys.exit(1)
    
    # Настройка оптимизаций
    if not setup_production_optimizations():
        log("⚠️ Не удалось применить все оптимизации")
    
    # Инициализация базы данных
    if not init_database():
        log("❌ Инициализация прервана из-за ошибки базы данных")
        sys.exit(1)
    
    # Проверка компонентов
    if not check_components():
        log("❌ Инициализация прервана из-за ошибки компонентов")
        sys.exit(1)
    
    # Финальная проверка здоровья
    if not health_check():
        log("❌ Система не прошла проверку здоровья")
        sys.exit(1)
    
    log("=" * 60)
    log("🎉 VHM24R успешно инициализирован для production!")
    log("🌐 Система готова к работе 24/7")
    log("📊 Доступные endpoints:")
    log("   - / (главная страница)")
    log("   - /upload (загрузка файлов)")
    log("   - /orders (управление заказами)")
    log("   - /health (проверка статуса)")
    log("=" * 60)

if __name__ == "__main__":
    main()
