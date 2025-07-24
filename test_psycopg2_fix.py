#!/usr/bin/env python3
"""
Тест для проверки исправления импорта psycopg2.extras
"""

try:
    # Тестируем импорт psycopg2
    import psycopg2
    print("✓ psycopg2 импортирован успешно")
    
    # Тестируем импорт psycopg2.extras
    from psycopg2.extras import RealDictCursor
    print("✓ psycopg2.extras.RealDictCursor импортирован успешно")
    
    # Тестируем импорт других классов из extras
    from psycopg2.extras import DictCursor, NamedTupleCursor
    print("✓ Другие классы из psycopg2.extras импортированы успешно")
    
    # Тестируем импорт функций из extras
    from psycopg2.extras import register_uuid, register_inet
    print("✓ Функции из psycopg2.extras импортированы успешно")
    
    print("\n🎉 Все импорты psycopg2 работают корректно!")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
except Exception as e:
    print(f"❌ Неожиданная ошибка: {e}")
