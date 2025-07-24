"""
VHM24R - Инициализация базы данных
Создание схемы и начальных данных
"""

import sys
from models import get_database

def main():
    """Основная функция инициализации"""
    try:
        print("🚀 Initializing VHM24R database...")
        
        # Получаем экземпляр базы данных
        db = get_database()
        
        print("✅ Database connection established")
        print(f"   Database type: {'PostgreSQL' if db.is_postgres else 'SQLite'}")
        
        # Проверяем создание таблиц
        tables_check = db.execute_query("""
            SELECT name FROM sqlite_master WHERE type='table'
        """ if not db.is_postgres else """
            SELECT tablename FROM pg_tables WHERE schemaname = 'public'
        """)
        
        print(f"✅ Tables created: {len(tables_check)} tables found")
        for table in tables_check:
            table_name = table['name'] if not db.is_postgres else table['tablename']
            print(f"   - {table_name}")
        
        # Добавляем начальную конфигурацию
        initial_config = [
            ('app_version', '1.0.0', 'Application version'),
            ('max_file_size', '104857600', 'Maximum file size in bytes (100MB)'),
            ('supported_formats', 'xlsx,xls,csv', 'Supported file formats'),
            ('time_tolerance', '60', 'Time tolerance for matching in seconds'),
            ('amount_tolerance', '0.01', 'Amount tolerance for matching')
        ]
        
        for key, value, description in initial_config:
            try:
                if db.is_postgres:
                    db.execute_query("""
                        INSERT INTO system_config (config_key, config_value, description)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (config_key) DO NOTHING
                    """, (key, value, description))
                else:
                    db.execute_query("""
                        INSERT OR IGNORE INTO system_config (config_key, config_value, description)
                        VALUES (?, ?, ?)
                    """, (key, value, description))
            except Exception as e:
                print(f"   Warning: Could not insert config {key}: {e}")
        
        print("✅ Initial configuration added")
        
        # Проверяем работу основных методов
        stats = db.get_processing_stats()
        print(f"✅ Statistics method working: {stats}")
        
        orders = db.get_orders_with_filters(limit=1)
        print(f"✅ Orders query working: {len(orders)} orders found")
        
        print("\n🎉 Database initialization completed successfully!")
        print("   The system is ready to use.")
        
        return True
        
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
