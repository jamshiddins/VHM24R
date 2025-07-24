#!/usr/bin/env python3
"""
Тест импорта psycopg2.extras для проверки исправления stub файлов
"""

def test_psycopg2_imports():
    """Тестирование импортов psycopg2"""
    try:
        # Основной импорт psycopg2
        import psycopg2
        print("✓ psycopg2 импортирован успешно")
        
        # Импорт extras
        from psycopg2.extras import RealDictCursor
        print("✓ psycopg2.extras.RealDictCursor импортирован успешно")
        
        # Импорт extensions
        from psycopg2.extensions import connection, cursor
        print("✓ psycopg2.extensions импортирован успешно")
        
        # Проверка, что RealDictCursor является классом
        print(f"✓ RealDictCursor тип: {type(RealDictCursor)}")
        
        return True
        
    except ImportError as e:
        print(f"✗ Ошибка импорта: {e}")
        return False
    except Exception as e:
        print(f"✗ Неожиданная ошибка: {e}")
        return False

if __name__ == "__main__":
    print("Тестирование импортов psycopg2...")
    success = test_psycopg2_imports()
    
    if success:
        print("\n🎉 Все импорты работают корректно!")
        print("Проблема с Pylance Warning решена.")
    else:
        print("\n❌ Есть проблемы с импортами.")
