#!/usr/bin/env python3
"""
VHM24R - Обновление базы данных
Применение новой схемы согласно требованиям
"""

import os
import sqlite3
from datetime import datetime

def backup_database():
    """Создание резервной копии базы данных"""
    if os.path.exists('orders.db'):
        backup_name = f"orders_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
        os.system(f'copy orders.db {backup_name}')
        print(f"✅ Создана резервная копия: {backup_name}")
        return backup_name
    return None

def apply_new_schema():
    """Применение новой схемы базы данных"""
    print("🔄 Применение новой схемы базы данных...")
    
    try:
        # Читаем новую схему
        with open('schema_final.sql', 'r', encoding='utf-8') as f:
            schema_sql = f.read()
        
        # Подключаемся к базе данных
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        
        # Удаляем старые таблицы если они существуют
        old_tables = [
            'orders', 'order_changes', 'unmatched_records', 
            'conflicts', 'file_metadata', 'system_config', 'processing_logs'
        ]
        
        for table in old_tables:
            try:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
                print(f"🗑️  Удалена старая таблица: {table}")
            except Exception as e:
                print(f"⚠️  Не удалось удалить таблицу {table}: {e}")
        
        # Применяем новую схему
        cursor.executescript(schema_sql)
        conn.commit()
        
        print("✅ Новая схема применена успешно")
        
        # Проверяем созданные таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        print("📋 Созданные таблицы:")
        for table in tables:
            cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = cursor.fetchone()[0]
            print(f"  - {table}: {count} записей")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка применения схемы: {e}")
        return False

def verify_schema():
    """Проверка корректности новой схемы"""
    print("\n🔍 Проверка новой схемы...")
    
    try:
        conn = sqlite3.connect('orders.db')
        cursor = conn.cursor()
        
        # Проверяем структуру таблицы orders
        cursor.execute("PRAGMA table_info(orders)")
        columns = [row[1] for row in cursor.fetchall()]
        
        required_columns = [
            'order_number', 'machine_code', 'order_price', 
            'creation_time', 'paying_time', 'match_status',
            'gateway_amount', 'fiscal_amount'
        ]
        
        missing_columns = []
        for col in required_columns:
            if col in columns:
                print(f"✅ Колонка {col} существует")
            else:
                missing_columns.append(col)
                print(f"❌ Колонка {col} отсутствует")
        
        # Проверяем конфигурацию
        cursor.execute("SELECT config_key, config_value FROM system_config WHERE config_key = 'commission_calculation'")
        result = cursor.fetchone()
        
        if result and result[1] == 'direct_comparison':
            print("✅ Конфигурация commission_calculation установлена корректно")
        else:
            print("❌ Конфигурация commission_calculation отсутствует или неверна")
            missing_columns.append('commission_calculation')
        
        conn.close()
        
        if not missing_columns:
            print("🎉 Схема базы данных полностью корректна!")
            return True
        else:
            print(f"⚠️  Обнаружены проблемы: {missing_columns}")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка проверки схемы: {e}")
        return False

def main():
    """Основная функция обновления"""
    print("🚀 Обновление базы данных VHM24R")
    print("=" * 50)
    
    # Создаем резервную копию
    backup_file = backup_database()
    
    # Применяем новую схему
    if apply_new_schema():
        # Проверяем результат
        if verify_schema():
            print("\n🎉 ОБНОВЛЕНИЕ ЗАВЕРШЕНО УСПЕШНО!")
            print("База данных готова к работе с новыми требованиями.")
            
            if backup_file:
                print(f"💾 Резервная копия сохранена как: {backup_file}")
            
            return True
        else:
            print("\n❌ ОБНОВЛЕНИЕ ЗАВЕРШЕНО С ОШИБКАМИ!")
            return False
    else:
        print("\n❌ КРИТИЧЕСКАЯ ОШИБКА ОБНОВЛЕНИЯ!")
        
        if backup_file:
            print(f"🔄 Восстановление из резервной копии: {backup_file}")
            os.system(f'copy {backup_file} orders.db')
        
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
