"""
VHM24R - Модели данных и работа с базой данных
Поддержка SQLite (локально) и PostgreSQL (Railway)
"""

import os
import sqlite3
import json
from typing import Dict, List, Optional, Any

# Импорт psycopg2 с обработкой ошибок для статического анализа
try:
    import psycopg2  # type: ignore
    from psycopg2.extras import RealDictCursor  # type: ignore
except ImportError:
    # Fallback для статического анализа
    psycopg2 = None  # type: ignore
    RealDictCursor = None  # type: ignore


class Database:
    """
    Универсальный класс для работы с БД
    Автоматически определяет тип БД по DATABASE_URL
    """

    def __init__(self):
        self.database_url = os.environ.get('DATABASE_URL')
        self.is_postgres = bool(self.database_url and 'postgresql' in self.database_url)
        self.connection = None
        
        if self.is_postgres:
            self._init_postgres()
        else:
            self._init_sqlite()
        
        self.init_database()
    
    def _init_postgres(self):
        """Инициализация PostgreSQL подключения"""
        if psycopg2 is None or RealDictCursor is None:
            print("psycopg2 not available, falling back to SQLite")
            self.is_postgres = False
            self._init_sqlite()
            return
            
        try:
            # Парсим URL для Railway
            if self.database_url.startswith('postgresql://'):
                self.database_url = self.database_url.replace('postgresql://', 'postgres://', 1)
            
            self.connection = psycopg2.connect(
                self.database_url,
                cursor_factory=RealDictCursor
            )
            print("Connected to PostgreSQL database")
        except Exception as e:
            print(f"PostgreSQL connection failed: {e}")
            print("Falling back to SQLite")
            self.is_postgres = False
            self._init_sqlite()
    
    def _init_sqlite(self):
        """Инициализация SQLite подключения"""
        try:
            db_path = os.environ.get('SQLITE_DB_PATH', 'orders.db')
            self.connection = sqlite3.connect(db_path, check_same_thread=False)
            self.connection.row_factory = sqlite3.Row
            print(f"Connected to SQLite database: {db_path}")
        except Exception as e:
            print(f"SQLite connection failed: {e}")
            raise
    
    def init_database(self):
        """Инициализация схемы базы данных"""
        try:
            if self.is_postgres:
                self._create_postgres_schema()
            else:
                self._create_sqlite_schema()
            print("Database schema initialized")
        except Exception as e:
            print(f"Error initializing database schema: {e}")
            raise
    
    def _create_postgres_schema(self):
        """Создание схемы PostgreSQL"""
        schema_sql = """
        -- Основная таблица заказов
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            order_number VARCHAR(100) NOT NULL,
            machine_code VARCHAR(50),
            creation_time TIMESTAMP,
            paying_time TIMESTAMP,
            brewing_time TIMESTAMP,
            delivery_time TIMESTAMP,
            order_price DECIMAL(10,2),
            goods_name TEXT,
            payment_type VARCHAR(50),
            refund_time TIMESTAMP,
            reason TEXT,
            
            -- Данные из разных источников (JSON)
            hw_data JSONB,
            vendhub_data JSONB,
            gateway_data JSONB,
            fiscal_data JSONB,
            
            -- Статус сопоставления
            matched_payment BOOLEAN DEFAULT FALSE,
            matched_fiscal BOOLEAN DEFAULT FALSE,
            payment_gateway VARCHAR(50),
            payment_source VARCHAR(50),
            transaction_id VARCHAR(100),
            card_number VARCHAR(50),
            merchant_id VARCHAR(50),
            fiscal_check_number VARCHAR(100),
            taxpayer_id VARCHAR(50),
            
            -- Классификация ошибок
            error_type VARCHAR(50) DEFAULT 'UNPROCESSED',
            error_details TEXT,
            
            -- Метаданные
            session_id VARCHAR(100),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- Индексы
            UNIQUE(order_number, machine_code)
        );
        
        -- Метаданные файлов
        CREATE TABLE IF NOT EXISTS file_metadata (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            original_filename VARCHAR(255),
            file_type VARCHAR(50),
            file_path TEXT,
            remote_key TEXT,
            file_size BIGINT,
            file_hash VARCHAR(64),
            session_id VARCHAR(100),
            storage_status VARCHAR(50) DEFAULT 'local',
            processing_status VARCHAR(50) DEFAULT 'pending',
            upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            processed_at TIMESTAMP
        );
        
        -- Конфигурация системы
        CREATE TABLE IF NOT EXISTS system_config (
            id SERIAL PRIMARY KEY,
            config_key VARCHAR(100) UNIQUE NOT NULL,
            config_value TEXT,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Логи обработки
        CREATE TABLE IF NOT EXISTS processing_logs (
            id SERIAL PRIMARY KEY,
            session_id VARCHAR(100),
            log_level VARCHAR(20),
            message TEXT,
            details JSONB,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Индексы для производительности
        CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
        CREATE INDEX IF NOT EXISTS idx_orders_machine_code ON orders(machine_code);
        CREATE INDEX IF NOT EXISTS idx_orders_creation_time ON orders(creation_time);
        CREATE INDEX IF NOT EXISTS idx_orders_error_type ON orders(error_type);
        CREATE INDEX IF NOT EXISTS idx_orders_session_id ON orders(session_id);
        CREATE INDEX IF NOT EXISTS idx_file_metadata_session_id ON file_metadata(session_id);
        CREATE INDEX IF NOT EXISTS idx_file_metadata_file_hash ON file_metadata(file_hash);
        
        -- Триггер для обновления updated_at
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
        
        CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
        """
        
        cursor = self.connection.cursor()
        cursor.execute(schema_sql)
        cursor.close()
    
    def _create_sqlite_schema(self):
        """Создание схемы SQLite согласно обновленному ТЗ"""
        # Читаем схему из файла
        try:
            with open('schema_final.sql', 'r', encoding='utf-8') as f:
                schema_sql = f.read()
        except FileNotFoundError:
            # Fallback к встроенной схеме
            schema_sql = """
            -- Основная таблица заказов (согласно ТЗ)
            CREATE TABLE IF NOT EXISTS orders (
                -- Системные идентификаторы
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                uuid TEXT UNIQUE DEFAULT (lower(hex(randomblob(16)))),
                
                -- Ключевые поля для сопоставления
                order_number TEXT NOT NULL,
                machine_code TEXT,
                
                -- Временные метки (критически важные для сопоставления)
                creation_time TIMESTAMP,
                paying_time TIMESTAMP,
                brewing_time TIMESTAMP,
                delivery_time TIMESTAMP,
                refund_time TIMESTAMP,
                event_time TIMESTAMP,        -- из VendHub
                fiscal_time TIMESTAMP,       -- из Fiscal Bills
                gateway_time TIMESTAMP,      -- из Payment Gateways
                
                -- Финансовые данные
                order_price DECIMAL(10,2),   -- основная цена заказа
                fiscal_amount DECIMAL(10,2), -- сумма в фискальном чеке
                gateway_amount DECIMAL(10,2),-- сумма в платежном шлюзе
                bonus_amount DECIMAL(10,2),  -- начисленные бонусы
                cashback_amount DECIMAL(10,2),-- кэшбэк (для Uzum)
                
                -- Информация о товаре
                goods_name TEXT,
                goods_id TEXT,
                taste_name TEXT,
                ikpu TEXT,
                barcode TEXT,
                marking TEXT,
                packaging TEXT,
                
                -- Информация о местоположении
                address TEXT,
                machine_category TEXT,
                
                -- Платежная информация
                order_type TEXT,
                order_resource TEXT,         -- Cash payment/Custom payment/Test/VIP
                payment_type TEXT,           -- Payme/Click/Uzum/Cash/Test/VIP
                payment_status TEXT,
                payment_gateway TEXT,        -- payme/click/uzum (определенный шлюз)
                
                -- Фискальная информация
                fiscal_check_number TEXT,
                taxpayer_id TEXT,
                cash_register_id TEXT,
                shift_number INTEGER,
                receipt_type TEXT,
                
                -- Информация о транзакциях платежных шлюзов
                transaction_id TEXT,         -- универсальный ID транзакции
                payme_transaction_id TEXT,   -- специфичный для Payme
                click_transaction_id TEXT,   -- специфичный для Click
                uzum_transaction_id TEXT,    -- специфичный для Uzum
                click_trans_id TEXT,         -- внутренний ID Click
                
                -- Платежные реквизиты
                card_number TEXT,            -- маскированный номер карты
                merchant_id TEXT,
                terminal_id TEXT,            -- для Payme
                service_id TEXT,             -- для Click
                shop_id TEXT,                -- для Uzum
                phone_number TEXT,           -- для Payme
                
                -- Пользовательская информация
                username TEXT,
                gateway_username TEXT,       -- username из платежного шлюза
                
                -- Статусы процессов
                brew_status TEXT,
                gateway_status TEXT,
                reason TEXT,                 -- причина возврата/ошибки
                
                -- Статусы сопоставления
                match_status TEXT DEFAULT 'unmatched',
                source TEXT,                 -- откуда первично загружен заказ
                matched_sources TEXT,        -- JSON массив сопоставленных источников
                fiscal_matched BOOLEAN DEFAULT FALSE,
                gateway_matched BOOLEAN DEFAULT FALSE,
                
                -- Детали несоответствий
                mismatch_details TEXT,       -- JSON с деталями расхождений
                conflict_details TEXT,       -- JSON с деталями конфликтов
                match_candidates TEXT,       -- JSON массив ID кандидатов при неоднозначности
                
                -- Служебные поля
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_modified_by TEXT,
                
                -- Индексы для оптимизации
                CONSTRAINT unique_order UNIQUE(order_number, machine_code)
            );
        
        -- Метаданные файлов
        CREATE TABLE IF NOT EXISTS file_metadata (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            original_filename TEXT,
            file_type TEXT,
            file_path TEXT,
            remote_key TEXT,
            file_size INTEGER,
            file_hash TEXT,
            session_id TEXT,
            storage_status TEXT DEFAULT 'local',
            processing_status TEXT DEFAULT 'pending',
            upload_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            processed_at DATETIME
        );
        
        -- Конфигурация системы
        CREATE TABLE IF NOT EXISTS system_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            config_key TEXT UNIQUE NOT NULL,
            config_value TEXT,
            description TEXT,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Логи обработки
        CREATE TABLE IF NOT EXISTS processing_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            log_level TEXT,
            message TEXT,
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        -- Индексы для производительности
        CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
        CREATE INDEX IF NOT EXISTS idx_orders_machine_code ON orders(machine_code);
        CREATE INDEX IF NOT EXISTS idx_orders_creation_time ON orders(creation_time);
        CREATE INDEX IF NOT EXISTS idx_orders_error_type ON orders(error_type);
        CREATE INDEX IF NOT EXISTS idx_orders_session_id ON orders(session_id);
        CREATE INDEX IF NOT EXISTS idx_file_metadata_session_id ON file_metadata(session_id);
        CREATE INDEX IF NOT EXISTS idx_file_metadata_file_hash ON file_metadata(file_hash);
        """
        
        # Выполняем каждую команду отдельно для SQLite
        commands = [cmd.strip() for cmd in schema_sql.split(';') if cmd.strip()]
        cursor = self.connection.cursor()
        for command in commands:
            if command and not command.startswith('--'):
                try:
                    cursor.execute(command)
                except sqlite3.OperationalError as e:
                    if "already exists" not in str(e):
                        print(f"Warning: SQL command failed: {e}")
        self.connection.commit()
        cursor.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[Dict]:
        """Выполнение SQL запроса с возвратом результата"""
        try:
            cursor = self.connection.cursor()
            
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if query.strip().upper().startswith('SELECT'):
                if self.is_postgres:
                    result = [dict(row) for row in cursor.fetchall()]
                else:
                    result = [dict(row) for row in cursor.fetchall()]
            else:
                result = []
                if not self.is_postgres:
                    self.connection.commit()
            
            cursor.close()
            return result
            
        except Exception as e:
            print(f"Database query error: {e}")
            print(f"Query: {query}")
            print(f"Params: {params}")
            return []
    
    def upsert_order(self, order_data: Dict[str, Any]) -> int:
        """Вставка или обновление заказа"""
        try:
            # Подготавливаем JSON данные
            for json_field in ['hw_data', 'vendhub_data', 'gateway_data', 'fiscal_data']:
                if json_field in order_data and isinstance(order_data[json_field], dict):
                    order_data[json_field] = json.dumps(order_data[json_field], default=str)
            
            if self.is_postgres:
                query = """
                INSERT INTO orders (
                    order_number, machine_code, creation_time, paying_time, brewing_time,
                    delivery_time, order_price, goods_name, payment_type, refund_time,
                    reason, hw_data, vendhub_data, gateway_data, fiscal_data,
                    matched_payment, matched_fiscal, payment_gateway, payment_source,
                    transaction_id, card_number, merchant_id, fiscal_check_number,
                    taxpayer_id, error_type, error_details, session_id
                ) VALUES (
                    %(order_number)s, %(machine_code)s, %(creation_time)s, %(paying_time)s,
                    %(brewing_time)s, %(delivery_time)s, %(order_price)s, %(goods_name)s,
                    %(payment_type)s, %(refund_time)s, %(reason)s, %(hw_data)s,
                    %(vendhub_data)s, %(gateway_data)s, %(fiscal_data)s, %(matched_payment)s,
                    %(matched_fiscal)s, %(payment_gateway)s, %(payment_source)s,
                    %(transaction_id)s, %(card_number)s, %(merchant_id)s,
                    %(fiscal_check_number)s, %(taxpayer_id)s, %(error_type)s,
                    %(error_details)s, %(session_id)s
                )
                ON CONFLICT (order_number, machine_code) 
                DO UPDATE SET
                    creation_time = COALESCE(EXCLUDED.creation_time, orders.creation_time),
                    paying_time = COALESCE(EXCLUDED.paying_time, orders.paying_time),
                    brewing_time = COALESCE(EXCLUDED.brewing_time, orders.brewing_time),
                    delivery_time = COALESCE(EXCLUDED.delivery_time, orders.delivery_time),
                    order_price = COALESCE(EXCLUDED.order_price, orders.order_price),
                    goods_name = COALESCE(EXCLUDED.goods_name, orders.goods_name),
                    payment_type = COALESCE(EXCLUDED.payment_type, orders.payment_type),
                    refund_time = COALESCE(EXCLUDED.refund_time, orders.refund_time),
                    reason = COALESCE(EXCLUDED.reason, orders.reason),
                    hw_data = COALESCE(EXCLUDED.hw_data, orders.hw_data),
                    vendhub_data = COALESCE(EXCLUDED.vendhub_data, orders.vendhub_data),
                    gateway_data = COALESCE(EXCLUDED.gateway_data, orders.gateway_data),
                    fiscal_data = COALESCE(EXCLUDED.fiscal_data, orders.fiscal_data),
                    matched_payment = COALESCE(EXCLUDED.matched_payment, orders.matched_payment),
                    matched_fiscal = COALESCE(EXCLUDED.matched_fiscal, orders.matched_fiscal),
                    payment_gateway = COALESCE(EXCLUDED.payment_gateway, orders.payment_gateway),
                    payment_source = COALESCE(EXCLUDED.payment_source, orders.payment_source),
                    transaction_id = COALESCE(EXCLUDED.transaction_id, orders.transaction_id),
                    card_number = COALESCE(EXCLUDED.card_number, orders.card_number),
                    merchant_id = COALESCE(EXCLUDED.merchant_id, orders.merchant_id),
                    fiscal_check_number = COALESCE(EXCLUDED.fiscal_check_number, orders.fiscal_check_number),
                    taxpayer_id = COALESCE(EXCLUDED.taxpayer_id, orders.taxpayer_id),
                    error_type = EXCLUDED.error_type,
                    error_details = COALESCE(EXCLUDED.error_details, orders.error_details),
                    session_id = COALESCE(EXCLUDED.session_id, orders.session_id),
                    updated_at = CURRENT_TIMESTAMP
                RETURNING id
                """
                
                cursor = self.connection.cursor()
                cursor.execute(query, order_data)
                result = cursor.fetchone()
                order_id = dict(result)['id'] if result else -1
                cursor.close()
                
            else:
                # SQLite UPSERT
                query = """
                INSERT OR REPLACE INTO orders (
                    order_number, machine_code, creation_time, paying_time, brewing_time,
                    delivery_time, order_price, goods_name, payment_type, refund_time,
                    reason, hw_data, vendhub_data, gateway_data, fiscal_data,
                    matched_payment, matched_fiscal, payment_gateway, payment_source,
                    transaction_id, card_number, merchant_id, fiscal_check_number,
                    taxpayer_id, error_type, error_details, session_id, updated_at
                ) VALUES (
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP
                )
                """
                
                params = (
                    order_data.get('order_number'), order_data.get('machine_code'),
                    order_data.get('creation_time'), order_data.get('paying_time'),
                    order_data.get('brewing_time'), order_data.get('delivery_time'),
                    order_data.get('order_price'), order_data.get('goods_name'),
                    order_data.get('payment_type'), order_data.get('refund_time'),
                    order_data.get('reason'), order_data.get('hw_data'),
                    order_data.get('vendhub_data'), order_data.get('gateway_data'),
                    order_data.get('fiscal_data'), order_data.get('matched_payment'),
                    order_data.get('matched_fiscal'), order_data.get('payment_gateway'),
                    order_data.get('payment_source'), order_data.get('transaction_id'),
                    order_data.get('card_number'), order_data.get('merchant_id'),
                    order_data.get('fiscal_check_number'), order_data.get('taxpayer_id'),
                    order_data.get('error_type'), order_data.get('error_details'),
                    order_data.get('session_id')
                )
                
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                order_id = cursor.lastrowid or -1
                self.connection.commit()
                cursor.close()
            
            return order_id
            
        except Exception as e:
            print(f"Error upserting order: {e}")
            return -1
    
    def save_file_metadata_extended(self, file_data: Dict[str, Any]) -> Optional[int]:
        """Сохранение расширенных метаданных файла"""
        try:
            if self.is_postgres:
                query = """
                INSERT INTO file_metadata (
                    filename, original_filename, file_type, file_path, remote_key,
                    file_size, file_hash, session_id, storage_status, processing_status
                ) VALUES (
                    %(filename)s, %(original_filename)s, %(file_type)s, %(file_path)s,
                    %(remote_key)s, %(file_size)s, %(file_hash)s, %(session_id)s,
                    %(storage_status)s, %(processing_status)s
                ) RETURNING id
                """
                
                cursor = self.connection.cursor()
                cursor.execute(query, file_data)
                result = cursor.fetchone()
                file_id = dict(result)['id'] if result else None
                cursor.close()
                
            else:
                query = """
                INSERT INTO file_metadata (
                    filename, original_filename, file_type, file_path, remote_key,
                    file_size, file_hash, session_id, storage_status, processing_status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                
                params = (
                    file_data.get('filename'), file_data.get('original_filename'),
                    file_data.get('file_type'), file_data.get('file_path'),
                    file_data.get('remote_key'), file_data.get('file_size'),
                    file_data.get('file_hash'), file_data.get('session_id'),
                    file_data.get('storage_status'), file_data.get('processing_status', 'pending')
                )
                
                cursor = self.connection.cursor()
                cursor.execute(query, params)
                file_id = cursor.lastrowid
                self.connection.commit()
                cursor.close()
            
            return file_id
            
        except Exception as e:
            print(f"Error saving file metadata: {e}")
            return None
    
    def update_order_error_type(self, order_id: int, error_type: str, details: Optional[str] = None):
        """Обновление типа ошибки заказа"""
        try:
            if self.is_postgres:
                query = """
                UPDATE orders 
                SET error_type = %s, error_details = %s, updated_at = CURRENT_TIMESTAMP
                WHERE id = %s
                """
                params = (error_type, details, order_id)
            else:
                query = """
                UPDATE orders 
                SET error_type = ?, error_details = ?, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """
                params = (error_type, details, order_id)
            
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            
            if not self.is_postgres:
                self.connection.commit()
            
            cursor.close()
            
        except Exception as e:
            print(f"Error updating order error type: {e}")
    
    def get_processing_stats(self) -> Dict[str, int]:
        """Получение статистики обработки согласно новой схеме"""
        try:
            stats_query = """
            SELECT 
                match_status,
                COUNT(*) as count
            FROM orders 
            GROUP BY match_status
            """
            
            results = self.execute_query(stats_query)
            stats = {}
            
            # Маппим новые статусы на старые для совместимости
            status_mapping = {
                'fully_matched': 'OK',
                'vendhub_only': 'NO_MATCH_IN_REPORT',
                'gateway_mismatch': 'NO_PAYMENT_FOUND', 
                'fiscal_mismatch': 'FISCAL_MISSING',
                'hw_only': 'UNPROCESSED',
                'matched': 'OK',  # Частично сопоставленные тоже считаем OK
                'unmatched': 'UNPROCESSED'
            }
            
            for result in results:
                match_status = result['match_status'] or 'unmatched'
                mapped_status = status_mapping.get(match_status, 'UNPROCESSED')
                
                if mapped_status in stats:
                    stats[mapped_status] += result['count']
                else:
                    stats[mapped_status] = result['count']
            
            # Добавляем общее количество
            total = sum(stats.values())
            stats['total'] = total
            
            # Устанавливаем значения по умолчанию
            for status in ['OK', 'NO_MATCH_IN_REPORT', 'NO_PAYMENT_FOUND', 'FISCAL_MISSING', 'UNPROCESSED']:
                if status not in stats:
                    stats[status] = 0
            
            return stats
            
        except Exception as e:
            print(f"Error getting processing stats: {e}")
            return {'total': 0, 'OK': 0, 'NO_MATCH_IN_REPORT': 0, 'NO_PAYMENT_FOUND': 0, 'FISCAL_MISSING': 0, 'UNPROCESSED': 0}
    
    def get_orders_with_filters(self, filters: Optional[Dict[str, Any]] = None, limit: int = 1000) -> List[Dict]:
        """Получение заказов с фильтрами согласно новой схеме БД"""
        try:
            base_query = """
            SELECT 
                id, order_number, machine_code, creation_time, order_price,
                payment_type, match_status, mismatch_details, fiscal_matched, gateway_matched,
                payment_gateway, transaction_id, fiscal_check_number, goods_name, address
            FROM orders
            """
            
            where_conditions = []
            params = []
            
            if filters:
                if 'error_type' in filters:
                    # Маппим старые error_type на новые match_status
                    error_mapping = {
                        'OK': 'fully_matched',
                        'NO_MATCH_IN_REPORT': 'vendhub_only', 
                        'NO_PAYMENT_FOUND': 'gateway_mismatch',
                        'FISCAL_MISSING': 'fiscal_mismatch',
                        'UNPROCESSED': 'hw_only'
                    }
                    mapped_status = error_mapping.get(filters['error_type'], filters['error_type'])
                    where_conditions.append("match_status = ?")
                    params.append(mapped_status)
                
                if 'machine_code' in filters:
                    where_conditions.append("machine_code = ?")
                    params.append(filters['machine_code'])
                
                if 'date_from' in filters:
                    where_conditions.append("DATE(creation_time) >= ?")
                    params.append(filters['date_from'])
                
                if 'date_to' in filters:
                    where_conditions.append("DATE(creation_time) <= ?")
                    params.append(filters['date_to'])
            
            if where_conditions:
                base_query += " WHERE " + " AND ".join(where_conditions)
            
            base_query += " ORDER BY creation_time DESC"
            
            if limit and limit > 0:
                base_query += f" LIMIT {limit}"
            
            if self.is_postgres:
                # Заменяем ? на %s для PostgreSQL
                base_query = base_query.replace('?', '%s')
            
            return self.execute_query(base_query, tuple(params))
            
        except Exception as e:
            print(f"Error getting orders with filters: {e}")
            return []
    
    def log_processing_event(self, session_id: str, level: str, message: str, details: Optional[Dict] = None):
        """Логирование событий обработки"""
        try:
            if self.is_postgres:
                query = """
                INSERT INTO processing_logs (session_id, log_level, message, details)
                VALUES (%s, %s, %s, %s)
                """
                params = (session_id, level, message, json.dumps(details, default=str) if details else None)
            else:
                query = """
                INSERT INTO processing_logs (session_id, log_level, message, details)
                VALUES (?, ?, ?, ?)
                """
                params = (session_id, level, message, json.dumps(details, default=str) if details else None)
            
            cursor = self.connection.cursor()
            cursor.execute(query, params)
            
            if not self.is_postgres:
                self.connection.commit()
            
            cursor.close()
            
        except Exception as e:
            print(f"Error logging processing event: {e}")
    
    def close(self):
        """Закрытие подключения к БД"""
        if self.connection:
            self.connection.close()
            print("Database connection closed")


# Глобальный экземпляр базы данных
db_instance = None


def get_database():
    """Получение экземпляра базы данных"""
    global db_instance
    if db_instance is None:
        db_instance = Database()
    return db_instance


def init_database():
    """Инициализация базы данных"""
    return get_database()
