"""
Создание системы просмотра отчетов по типам
Каждый тип отчета сохраняется в отдельную таблицу
"""

import os
import sqlite3
from datetime import datetime

def create_reports_tables():
    """Создание таблиц для каждого типа отчета"""
    
    # Подключение к базе данных
    db_path = 'orders.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 1. Таблица для отчетов Happy Workers
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports_happy_workers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Данные из файла Happy Workers
            order_number TEXT,
            machine_code TEXT,
            address TEXT,
            goods_name TEXT,
            taste_name TEXT,
            order_type TEXT,
            order_resource TEXT,
            order_price REAL,
            creation_time TIMESTAMP,
            paying_time TIMESTAMP,
            brewing_time TIMESTAMP,
            delivery_time TIMESTAMP,
            refund_time TIMESTAMP,
            payment_status TEXT,
            brew_status TEXT,
            reason TEXT,
            
            -- Служебные поля
            processed BOOLEAN DEFAULT FALSE,
            processing_date TIMESTAMP,
            row_number INTEGER
        )
    """)
    
    # 2. Таблица для отчетов VendHub
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports_vendhub (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Данные из файла VendHub
            order_number TEXT,
            time_event TIMESTAMP,
            goods_name TEXT,
            order_price REAL,
            machine_code TEXT,
            machine_category TEXT,
            payment_type TEXT,
            order_resource TEXT,
            goods_id TEXT,
            username TEXT,
            amount_of_accrued_bonus REAL,
            ikpu TEXT,
            barcode TEXT,
            marking TEXT,
            packaging TEXT,
            
            -- Служебные поля
            processed BOOLEAN DEFAULT FALSE,
            processing_date TIMESTAMP,
            row_number INTEGER
        )
    """)
    
    # 3. Таблица для фискальных чеков
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports_fiscal_bills (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Данные из фискальных чеков
            fiscal_check_number TEXT,
            fiscal_time TIMESTAMP,
            amount REAL,
            taxpayer_id TEXT,
            cash_register_id TEXT,
            shift_number INTEGER,
            receipt_type TEXT,
            
            -- Служебные поля
            processed BOOLEAN DEFAULT FALSE,
            processing_date TIMESTAMP,
            row_number INTEGER
        )
    """)
    
    # 4. Таблица для отчетов Payme
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports_payme (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Данные из Payme
            transaction_id TEXT,
            transaction_time TIMESTAMP,
            amount REAL,
            masked_pan TEXT,
            merchant_id TEXT,
            terminal_id TEXT,
            commission REAL,
            status TEXT,
            username TEXT,
            
            -- Служебные поля
            processed BOOLEAN DEFAULT FALSE,
            processing_date TIMESTAMP,
            row_number INTEGER
        )
    """)
    
    # 5. Таблица для отчетов Click
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports_click (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Данные из Click
            transaction_id TEXT,
            transaction_time TIMESTAMP,
            amount REAL,
            card_number TEXT,
            merchant_id TEXT,
            service_id TEXT,
            commission REAL,
            status TEXT,
            error_code TEXT,
            
            -- Служебные поля
            processed BOOLEAN DEFAULT FALSE,
            processing_date TIMESTAMP,
            row_number INTEGER
        )
    """)
    
    # 6. Таблица для отчетов Uzum
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports_uzum (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Данные из Uzum
            transaction_id TEXT,
            transaction_time TIMESTAMP,
            amount REAL,
            masked_pan TEXT,
            merchant_id TEXT,
            shop_id TEXT,
            commission REAL,
            status TEXT,
            username TEXT,
            
            -- Служебные поля
            processed BOOLEAN DEFAULT FALSE,
            processing_date TIMESTAMP,
            row_number INTEGER
        )
    """)
    
    # 7. Таблица для банковских выписок
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports_bank_statements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Данные из банковской выписки
            transaction_date DATE,
            transaction_time TIME,
            amount REAL,
            transaction_type TEXT,
            description TEXT,
            counterparty TEXT,
            payment_system TEXT,
            reference_number TEXT,
            bank_account TEXT,
            
            -- Служебные поля
            processed BOOLEAN DEFAULT FALSE,
            processing_date TIMESTAMP,
            row_number INTEGER
        )
    """)
    
    # 8. Таблица для отслеживания загруженных файлов
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS uploaded_files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name TEXT NOT NULL,
            original_name TEXT NOT NULL,
            file_type TEXT NOT NULL,
            file_size INTEGER,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed BOOLEAN DEFAULT FALSE,
            processing_date TIMESTAMP,
            records_count INTEGER DEFAULT 0,
            error_message TEXT
        )
    """)
    
    # Создание индексов для быстрого поиска
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_hw_order_number ON reports_happy_workers(order_number)",
        "CREATE INDEX IF NOT EXISTS idx_hw_machine_code ON reports_happy_workers(machine_code)",
        "CREATE INDEX IF NOT EXISTS idx_hw_creation_time ON reports_happy_workers(creation_time)",
        
        "CREATE INDEX IF NOT EXISTS idx_vh_order_number ON reports_vendhub(order_number)",
        "CREATE INDEX IF NOT EXISTS idx_vh_machine_code ON reports_vendhub(machine_code)",
        "CREATE INDEX IF NOT EXISTS idx_vh_time_event ON reports_vendhub(time_event)",
        
        "CREATE INDEX IF NOT EXISTS idx_fiscal_check_number ON reports_fiscal_bills(fiscal_check_number)",
        "CREATE INDEX IF NOT EXISTS idx_fiscal_time ON reports_fiscal_bills(fiscal_time)",
        
        "CREATE INDEX IF NOT EXISTS idx_payme_transaction_id ON reports_payme(transaction_id)",
        "CREATE INDEX IF NOT EXISTS idx_payme_time ON reports_payme(transaction_time)",
        
        "CREATE INDEX IF NOT EXISTS idx_click_transaction_id ON reports_click(transaction_id)",
        "CREATE INDEX IF NOT EXISTS idx_click_time ON reports_click(transaction_time)",
        
        "CREATE INDEX IF NOT EXISTS idx_uzum_transaction_id ON reports_uzum(transaction_id)",
        "CREATE INDEX IF NOT EXISTS idx_uzum_time ON reports_uzum(transaction_time)",
        
        "CREATE INDEX IF NOT EXISTS idx_bank_date ON reports_bank_statements(transaction_date)",
        "CREATE INDEX IF NOT EXISTS idx_bank_amount ON reports_bank_statements(amount)",
        
        "CREATE INDEX IF NOT EXISTS idx_files_type ON uploaded_files(file_type)",
        "CREATE INDEX IF NOT EXISTS idx_files_date ON uploaded_files(upload_date)"
    ]
    
    for index_sql in indexes:
        cursor.execute(index_sql)
    
    conn.commit()
    conn.close()
    
    print("✅ Таблицы для отчетов созданы успешно!")

def create_reports_views():
    """Создание представлений для удобного просмотра данных"""
    
    conn = sqlite3.connect('orders.db')
    cursor = conn.cursor()
    
    # Представление для статистики по файлам
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS v_files_statistics AS
        SELECT 
            file_type,
            COUNT(*) as files_count,
            SUM(records_count) as total_records,
            MAX(upload_date) as last_upload,
            COUNT(CASE WHEN processed = 1 THEN 1 END) as processed_files,
            COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as error_files
        FROM uploaded_files
        GROUP BY file_type
    """)
    
    # Представление для последних загрузок
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS v_recent_uploads AS
        SELECT 
            file_name,
            original_name,
            file_type,
            file_size,
            upload_date,
            processed,
            records_count,
            error_message
        FROM uploaded_files
        ORDER BY upload_date DESC
        LIMIT 50
    """)
    
    conn.commit()
    conn.close()
    
    print("✅ Представления созданы успешно!")

if __name__ == '__main__':
    print("🚀 Создание системы отчетов...")
    create_reports_tables()
    create_reports_views()
    print("✅ Система отчетов создана!")
