#!/usr/bin/env python3
"""
Тест для проверки импорта psycopg2.extras после исправления
"""

try:
    import psycopg2
    print("✓ psycopg2 импортирован успешно")
except ImportError as e:
    print(f"✗ Ошибка импорта psycopg2: {e}")

try:
    from psycopg2.extras import RealDictCursor
    print("✓ psycopg2.extras.RealDictCursor импортирован успешно")
except ImportError as e:
    print(f"✗ Ошибка импорта psycopg2.extras.RealDictCursor: {e}")

try:
    from psycopg2 import extras
    print("✓ psycopg2.extras модуль импортирован успешно")
except ImportError as e:
    print(f"✗ Ошибка импорта psycopg2.extras модуля: {e}")

# Проверяем доступность RealDictCursor
try:
    cursor_class = RealDictCursor
    print(f"✓ RealDictCursor доступен: {cursor_class}")
except NameError as e:
    print(f"✗ RealDictCursor недоступен: {e}")

print("\nТест завершен.")
