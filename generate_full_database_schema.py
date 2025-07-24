import sqlite3
import json

def generate_full_database_schema():
    """Генерирует полную схему базы данных с детальной информацией о всех таблицах"""
    
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    
    # Получаем список всех таблиц
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()
    
    schema_info = {
        'database_name': 'VHM24R Orders Database',
        'database_file': 'orders.db',
        'total_tables': len(tables),
        'tables': {}
    }
    
    for table in tables:
        table_name = table[0]
        print(f"\n=== Анализ таблицы: {table_name} ===")
        
        # Получаем информацию о структуре таблицы
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns_info = cursor.fetchall()
        
        # Получаем количество записей
        cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
        record_count = cursor.fetchone()[0]
        
        # Получаем SQL создания таблицы
        cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}';")
        create_sql = cursor.fetchone()
        create_sql = create_sql[0] if create_sql else None
        
        table_info = {
            'record_count': record_count,
            'columns': [],
            'create_sql': create_sql,
            'sample_data': []
        }
        
        # Обрабатываем информацию о колонках
        for col in columns_info:
            column_info = {
                'name': col[1],
                'type': col[2],
                'not_null': bool(col[3]),
                'default_value': col[4],
                'primary_key': bool(col[5])
            }
            table_info['columns'].append(column_info)
            print(f"  {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'} {'PK' if col[5] else ''}")
        
        # Получаем примеры данных (первые 3 записи)
        if record_count > 0:
            cursor.execute(f'SELECT * FROM {table_name} LIMIT 3')
            sample_rows = cursor.fetchall()
            
            for row in sample_rows:
                row_data = {}
                for i, col_info in enumerate(columns_info):
                    col_name = col_info[1]
                    row_data[col_name] = str(row[i]) if row[i] is not None else None
                table_info['sample_data'].append(row_data)
        
        schema_info['tables'][table_name] = table_info
        print(f"  Записей: {record_count}")
    
    conn.close()
    return schema_info

def save_schema_to_files(schema_info):
    """Сохраняет схему в различных форматах"""
    
    # 1. JSON файл
    with open('database_schema.json', 'w', encoding='utf-8') as f:
        json.dump(schema_info, f, ensure_ascii=False, indent=2)
    
    # 2. Markdown файл
    with open('DATABASE_FULL_SCHEMA.md', 'w', encoding='utf-8') as f:
        f.write(f"# {schema_info['database_name']}\n\n")
        f.write(f"**Файл базы данных:** {schema_info['database_file']}\n")
        f.write(f"**Всего таблиц:** {schema_info['total_tables']}\n\n")
        
        # Общая статистика
        f.write("## Общая статистика\n\n")
        f.write("| Таблица | Записей | Колонок |\n")
        f.write("|---------|---------|----------|\n")
        
        total_records = 0
        for table_name, table_info in schema_info['tables'].items():
            record_count = table_info['record_count']
            column_count = len(table_info['columns'])
            total_records += record_count
            f.write(f"| {table_name} | {record_count:,} | {column_count} |\n")
        
        f.write(f"\n**Общее количество записей:** {total_records:,}\n\n")
        
        # Детальная информация по каждой таблице
        for table_name, table_info in schema_info['tables'].items():
            f.write(f"## Таблица: {table_name}\n\n")
            f.write(f"**Записей:** {table_info['record_count']:,}\n\n")
            
            # Структура таблицы
            f.write("### Структура\n\n")
            f.write("| Колонка | Тип | Обязательная | По умолчанию | Первичный ключ |\n")
            f.write("|---------|-----|--------------|--------------|----------------|\n")
            
            for col in table_info['columns']:
                not_null = "Да" if col['not_null'] else "Нет"
                default = col['default_value'] if col['default_value'] else "-"
                pk = "Да" if col['primary_key'] else "Нет"
                f.write(f"| {col['name']} | {col['type']} | {not_null} | {default} | {pk} |\n")
            
            # SQL создания таблицы
            if table_info['create_sql']:
                f.write(f"\n### SQL создания\n\n```sql\n{table_info['create_sql']}\n```\n\n")
            
            # Примеры данных
            if table_info['sample_data']:
                f.write("### Примеры данных\n\n")
                if table_info['sample_data']:
                    # Показываем первые несколько колонок для читаемости
                    sample = table_info['sample_data'][0]
                    key_columns = list(sample.keys())[:5]  # Первые 5 колонок
                    
                    f.write("| " + " | ".join(key_columns) + " |\n")
                    f.write("|" + "|".join(["-" * len(col) for col in key_columns]) + "|\n")
                    
                    for row in table_info['sample_data'][:3]:
                        values = []
                        for col in key_columns:
                            value = row.get(col, "")
                            if value and len(str(value)) > 30:
                                value = str(value)[:27] + "..."
                            values.append(str(value) if value else "-")
                        f.write("| " + " | ".join(values) + " |\n")
                f.write("\n")
    
    # 3. SQL файл со всеми CREATE TABLE
    with open('database_create_tables.sql', 'w', encoding='utf-8') as f:
        f.write("-- VHM24R Database Schema\n")
        f.write("-- Полная схема базы данных\n\n")
        
        for table_name, table_info in schema_info['tables'].items():
            if table_info['create_sql']:
                f.write(f"-- Таблица: {table_name} ({table_info['record_count']} записей)\n")
                f.write(f"{table_info['create_sql']};\n\n")

if __name__ == '__main__':
    print("Генерация полной схемы базы данных VHM24R...")
    schema_info = generate_full_database_schema()
    save_schema_to_files(schema_info)
    
    print(f"\nСхема базы данных сохранена в файлы:")
    print("- database_schema.json (JSON формат)")
    print("- DATABASE_FULL_SCHEMA.md (Markdown документация)")
    print("- database_create_tables.sql (SQL схема)")
    
    print(f"\nОбщая статистика:")
    print(f"- Всего таблиц: {schema_info['total_tables']}")
    total_records = sum(table['record_count'] for table in schema_info['tables'].values())
    print(f"- Всего записей: {total_records:,}")
