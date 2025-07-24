import sqlite3
import os

# Проверяем размер файла базы данных
db_path = 'orders.db'
if os.path.exists(db_path):
    size = os.path.getsize(db_path)
    print(f'База данных orders.db существует, размер: {size} байт')
    
    # Подключаемся к базе данных
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Получаем список таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print(f'Таблицы в базе данных: {[table[0] for table in tables]}')
    
    # Проверяем количество записей в основных таблицах
    for table in tables:
        table_name = table[0]
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = cursor.fetchone()[0]
            print(f'Таблица {table_name}: {count} записей')
        except Exception as e:
            print(f'Ошибка при проверке таблицы {table_name}: {e}')
    
    # Показываем структуру таблицы orders если она есть
    if 'orders' in [table[0] for table in tables]:
        print('\nСтруктура таблицы orders:')
        cursor.execute("PRAGMA table_info(orders);")
        columns = cursor.fetchall()
        for col in columns:
            print(f'  {col[1]} ({col[2]})')
        
        # Показываем несколько примеров записей
        print('\nПримеры записей из таблицы orders (первые 5):')
        cursor.execute("SELECT order_number, machine_code, goods_name, order_price, creation_time FROM orders LIMIT 5")
        rows = cursor.fetchall()
        for row in rows:
            print(f'  {row}')
    
    conn.close()
else:
    print('Файл orders.db не найден')
