#!/usr/bin/env python3
"""
VHM24R - Тестирование системы
Проверка всех компонентов согласно новым требованиям
"""

import os
import sys
import sqlite3
from datetime import datetime

def test_database_connection():
    """Тест подключения к базе данных"""
    print("🔍 Тестирование подключения к базе данных...")
    
    try:
        from models import get_database
        db = get_database()
        
        # Проверяем выполнение простого запроса
        result = db.execute_query("SELECT 1 as test")
        if result and result[0]['test'] == 1:
            print("✅ База данных подключена успешно")
            return True
        else:
            print("❌ Ошибка выполнения тестового запроса")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False

def test_file_detector():
    """Тест детектора файлов"""
    print("\n🔍 Тестирование детектора файлов...")
    
    try:
        from file_detector_updated import AdvancedFileTypeDetector
        detector = AdvancedFileTypeDetector()
        
        # Проверяем поддерживаемые типы
        supported_types = detector.get_supported_types()
        expected_types = ['happy_workers', 'vendhub', 'fiscal_bills', 'payme', 'click', 'uzum']
        
        for expected_type in expected_types:
            if expected_type in supported_types:
                print(f"✅ Тип файла {expected_type} поддерживается")
            else:
                print(f"❌ Тип файла {expected_type} НЕ поддерживается")
                return False
        
        print("✅ Детектор файлов работает корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка детектора файлов: {e}")
        return False

def test_processors():
    """Тест процессоров"""
    print("\n🔍 Тестирование процессоров...")
    
    try:
        from models import get_database
        from processors_updated import OrderProcessor, RecipeProcessor, FinanceProcessor
        
        db = get_database()
        
        # Тест OrderProcessor
        order_processor = OrderProcessor(db)
        if hasattr(order_processor, 'ORDER_STATUSES'):
            print("✅ OrderProcessor инициализирован")
        else:
            print("❌ OrderProcessor не содержит ORDER_STATUSES")
            return False
        
        # Тест RecipeProcessor
        recipe_processor = RecipeProcessor(db)
        stats = recipe_processor.get_recipe_stats()
        if isinstance(stats, dict):
            print("✅ RecipeProcessor работает")
        else:
            print("❌ RecipeProcessor не работает")
            return False
        
        # Тест FinanceProcessor
        finance_processor = FinanceProcessor(db)
        finance_stats = finance_processor.get_finance_stats()
        if isinstance(finance_stats, dict):
            print("✅ FinanceProcessor работает")
        else:
            print("❌ FinanceProcessor не работает")
            return False
        
        print("✅ Все процессоры работают корректно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка процессоров: {e}")
        return False

def test_app_initialization():
    """Тест инициализации приложения"""
    print("\n🔍 Тестирование инициализации приложения...")
    
    try:
        # Проверяем импорт основных модулей
        from models import get_database
        from processors_updated import OrderProcessor
        from file_detector_updated import AdvancedFileTypeDetector
        
        print("✅ Все модули импортируются успешно")
        
        # Проверяем Flask приложение
        import app
        if hasattr(app, 'app') and app.app is not None:
            print("✅ Flask приложение инициализировано")
        else:
            print("❌ Flask приложение не инициализировано")
            return False
        
        print("✅ Приложение инициализировано успешно")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации приложения: {e}")
        return False

def test_database_schema():
    """Тест схемы базы данных"""
    print("\n🔍 Тестирование схемы базы данных...")
    
    try:
        from models import get_database
        db = get_database()
        
        # Проверяем основные таблицы
        required_tables = [
            'orders', 'order_changes', 'unmatched_records', 
            'conflicts', 'file_metadata', 'system_config', 'processing_logs'
        ]
        
        for table in required_tables:
            try:
                result = db.execute_query(f"SELECT COUNT(*) as count FROM {table}")
                print(f"✅ Таблица {table} существует ({result[0]['count']} записей)")
            except Exception as e:
                print(f"❌ Таблица {table} не существует или недоступна: {e}")
                return False
        
        # Проверяем ключевые поля в таблице orders
        try:
            # Используем прямое подключение к SQLite для проверки
            import sqlite3
            conn = sqlite3.connect('orders.db')
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(orders)")
            columns = [row[1] for row in cursor.fetchall()]
            conn.close()
            print(f"🔍 Найдено колонок в таблице orders: {len(columns)}")
            
            required_columns = [
                'order_number', 'machine_code', 'order_price', 
                'creation_time', 'paying_time', 'match_status',
                'gateway_amount', 'fiscal_amount'  # Новые поля согласно ТЗ
            ]
            
            for column in required_columns:
                if column in columns:
                    print(f"✅ Колонка {column} существует")
                else:
                    print(f"❌ Колонка {column} отсутствует")
                    return False
            
        except Exception as e:
            print(f"❌ Ошибка проверки структуры таблицы orders: {e}")
            return False
        
        print("✅ Схема базы данных корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки схемы базы данных: {e}")
        return False

def test_configuration():
    """Тест конфигурации системы"""
    print("\n🔍 Тестирование конфигурации системы...")
    
    try:
        from models import get_database
        db = get_database()
        
        # Проверяем системную конфигурацию
        config = db.execute_query("SELECT * FROM system_config")
        
        required_configs = [
            'time_tolerance_seconds', 'amount_tolerance', 
            'commission_calculation'  # Новый параметр согласно ТЗ
        ]
        
        config_keys = [c['config_key'] for c in config]
        
        for req_config in required_configs:
            if req_config in config_keys:
                value = next(c['config_value'] for c in config if c['config_key'] == req_config)
                print(f"✅ Конфигурация {req_config} = {value}")
            else:
                print(f"❌ Конфигурация {req_config} отсутствует")
                return False
        
        # Проверяем критически важную настройку
        commission_calc = next(
            (c['config_value'] for c in config if c['config_key'] == 'commission_calculation'), 
            None
        )
        
        if commission_calc == 'direct_comparison':
            print("✅ Настройка комиссии корректна (прямое сравнение сумм)")
        else:
            print(f"❌ Неверная настройка комиссии: {commission_calc}")
            return False
        
        print("✅ Конфигурация системы корректна")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка проверки конфигурации: {e}")
        return False

def run_all_tests():
    """Запуск всех тестов"""
    print("🚀 Запуск полного тестирования системы VHM24R")
    print("=" * 60)
    
    tests = [
        ("База данных", test_database_connection),
        ("Детектор файлов", test_file_detector),
        ("Процессоры", test_processors),
        ("Инициализация приложения", test_app_initialization),
        ("Схема базы данных", test_database_schema),
        ("Конфигурация системы", test_configuration)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ Тест '{test_name}' провален")
        except Exception as e:
            print(f"❌ Критическая ошибка в тесте '{test_name}': {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ:")
    print(f"✅ Пройдено: {passed}/{total}")
    print(f"❌ Провалено: {total - passed}/{total}")
    
    if passed == total:
        print("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к работе.")
        return True
    else:
        print("⚠️  ЕСТЬ ПРОБЛЕМЫ! Необходимо исправить ошибки.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
