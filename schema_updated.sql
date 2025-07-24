-- VHM24R - Обновленная схема базы данных согласно ТЗ
-- Полная структура всех таблиц и логика объединения данных

-- ========================================================================
-- ОСНОВНАЯ ТАБЛИЦА ЗАКАЗОВ (согласно ТЗ)
-- ========================================================================

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

-- ========================================================================
-- ТАБЛИЦА ИСТОРИИ ИЗМЕНЕНИЙ
-- ========================================================================

CREATE TABLE IF NOT EXISTS order_changes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER REFERENCES orders(id),
    field_name TEXT,
    old_value TEXT,
    new_value TEXT,
    change_source TEXT,          -- какой файл/процесс внес изменение
    change_type TEXT,            -- create/update/merge/conflict
    change_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    change_details TEXT          -- JSON с дополнительной информацией
);

-- ========================================================================
-- ТАБЛИЦА НЕСОПОСТАВЛЕННЫХ ЗАПИСЕЙ
-- ========================================================================

CREATE TABLE IF NOT EXISTS unmatched_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type TEXT,            -- fiscal/payme/click/uzum
    record_data TEXT,            -- JSON с полными данными записи
    record_time TIMESTAMP,       -- время из записи для поиска
    record_amount DECIMAL(10,2), -- сумма для поиска
    attempts INTEGER DEFAULT 0,  -- количество попыток сопоставления
    last_attempt TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================================================
-- ТАБЛИЦА КОНФЛИКТОВ
-- ========================================================================

CREATE TABLE IF NOT EXISTS conflicts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conflict_type TEXT,          -- number_mismatch/time_mismatch/amount_mismatch
    order_id_1 INTEGER,
    order_id_2 INTEGER,
    conflict_data TEXT,          -- JSON с деталями конфликта
    resolution_status TEXT DEFAULT 'pending', -- pending/resolved/ignored
    resolved_by TEXT,
    resolved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================================================
-- МЕТАДАННЫЕ ФАЙЛОВ (обновленная)
-- ========================================================================

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
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    records_processed INTEGER DEFAULT 0,
    records_matched INTEGER DEFAULT 0,
    processing_errors TEXT        -- JSON с ошибками обработки
);

-- ========================================================================
-- КОНФИГУРАЦИЯ СИСТЕМЫ
-- ========================================================================

CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================================================
-- ЛОГИ ОБРАБОТКИ
-- ========================================================================

CREATE TABLE IF NOT EXISTS processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    log_level TEXT,
    message TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ========================================================================
-- ИНДЕКСЫ ДЛЯ ОПТИМИЗАЦИИ
-- ========================================================================

-- Основные индексы для поиска
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_orders_machine_code ON orders(machine_code);
CREATE INDEX IF NOT EXISTS idx_orders_creation_time ON orders(creation_time);
CREATE INDEX IF NOT EXISTS idx_orders_paying_time ON orders(paying_time);
CREATE INDEX IF NOT EXISTS idx_orders_order_price ON orders(order_price);
CREATE INDEX IF NOT EXISTS idx_orders_match_status ON orders(match_status);
CREATE INDEX IF NOT EXISTS idx_orders_payment_type ON orders(payment_type);
CREATE INDEX IF NOT EXISTS idx_orders_order_resource ON orders(order_resource);

-- Индексы для временных полей
CREATE INDEX IF NOT EXISTS idx_orders_fiscal_time ON orders(fiscal_time);
CREATE INDEX IF NOT EXISTS idx_orders_gateway_time ON orders(gateway_time);
CREATE INDEX IF NOT EXISTS idx_orders_event_time ON orders(event_time);

-- Индексы для сопоставления
CREATE INDEX IF NOT EXISTS idx_orders_fiscal_matched ON orders(fiscal_matched);
CREATE INDEX IF NOT EXISTS idx_orders_gateway_matched ON orders(gateway_matched);

-- Составные индексы для быстрого поиска
CREATE INDEX IF NOT EXISTS idx_orders_number_machine ON orders(order_number, machine_code);
CREATE INDEX IF NOT EXISTS idx_orders_time_price ON orders(paying_time, order_price);
CREATE INDEX IF NOT EXISTS idx_orders_gateway_time_amount ON orders(gateway_time, gateway_amount);
CREATE INDEX IF NOT EXISTS idx_orders_fiscal_time_amount ON orders(fiscal_time, fiscal_amount);

-- Индексы для связанных таблиц
CREATE INDEX IF NOT EXISTS idx_order_changes_order_id ON order_changes(order_id);
CREATE INDEX IF NOT EXISTS idx_order_changes_change_time ON order_changes(change_time);
CREATE INDEX IF NOT EXISTS idx_unmatched_records_type ON unmatched_records(record_type);
CREATE INDEX IF NOT EXISTS idx_unmatched_records_time_amount ON unmatched_records(record_time, record_amount);
CREATE INDEX IF NOT EXISTS idx_conflicts_status ON conflicts(resolution_status);
CREATE INDEX IF NOT EXISTS idx_file_metadata_session_id ON file_metadata(session_id);
CREATE INDEX IF NOT EXISTS idx_file_metadata_file_hash ON file_metadata(file_hash);

-- ========================================================================
-- НАЧАЛЬНАЯ КОНФИГУРАЦИЯ
-- ========================================================================

INSERT OR IGNORE INTO system_config (config_key, config_value, description) VALUES
('time_tolerance_seconds', '60', 'Допустимое отклонение времени в секундах'),
('amount_tolerance', '0.01', 'Допустимое отклонение суммы'),
('hw_vendhub_time_window', '60', 'Временное окно для сопоставления HW-VendHub (секунды)'),
('fiscal_time_window', '60', 'Временное окно для фискальных чеков (секунды)'),
('gateway_time_window', '60', 'Временное окно для платежных шлюзов (секунды)'),
('auto_resolve_conflicts', 'true', 'Автоматическое разрешение конфликтов'),
('max_match_candidates', '5', 'Максимальное количество кандидатов для сопоставления'),
('enable_detailed_logging', 'true', 'Включить детальное логирование'),
('backup_processing_results', 'true', 'Резервное копирование результатов обработки');

-- ========================================================================
-- ПРЕДСТАВЛЕНИЯ ДЛЯ УДОБСТВА РАБОТЫ
-- ========================================================================

-- Представление для полной информации о заказах
CREATE VIEW IF NOT EXISTS orders_full AS
SELECT 
    o.*,
    CASE 
        WHEN o.match_status = 'fully_matched' THEN 'Полностью сопоставлен'
        WHEN o.match_status = 'matched' THEN 'Частично сопоставлен'
        WHEN o.match_status = 'hw_only' THEN 'Только Happy Workers'
        WHEN o.match_status = 'vendhub_only' THEN 'Только VendHub'
        WHEN o.match_status = 'fiscal_mismatch' THEN 'Нет фискального чека'
        WHEN o.match_status = 'gateway_mismatch' THEN 'Нет транзакции шлюза'
        WHEN o.match_status = 'time_out_of_range' THEN 'Время вне окна'
        WHEN o.match_status = 'price_mismatch' THEN 'Расхождение в цене'
        WHEN o.match_status = 'number_conflict' THEN 'Конфликт номеров'
        WHEN o.match_status = 'ambiguous_match' THEN 'Неоднозначное сопоставление'
        ELSE 'Не обработан'
    END as match_status_description,
    
    CASE 
        WHEN o.order_resource = 'Cash payment' AND o.fiscal_matched = 1 THEN 'OK'
        WHEN o.order_resource = 'Custom payment' AND o.gateway_matched = 1 THEN 'OK'
        WHEN o.order_resource IN ('Test Shipment', 'VIP') THEN 'OK'
        ELSE 'MISMATCH'
    END as final_status
    
FROM orders o;

-- Представление для статистики сопоставления
CREATE VIEW IF NOT EXISTS matching_statistics AS
SELECT 
    match_status,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM orders), 2) as percentage
FROM orders 
GROUP BY match_status
ORDER BY count DESC;

-- Представление для проблемных заказов
CREATE VIEW IF NOT EXISTS problematic_orders AS
SELECT 
    o.*,
    CASE 
        WHEN o.match_status = 'fiscal_mismatch' THEN 'Отсутствует фискальный чек для Cash заказа'
        WHEN o.match_status = 'gateway_mismatch' THEN 'Отсутствует транзакция для Custom payment'
        WHEN o.match_status = 'time_out_of_range' THEN 'Время события вне допустимого окна'
        WHEN o.match_status = 'price_mismatch' THEN 'Расхождение в сумме заказа'
        WHEN o.match_status = 'number_conflict' THEN 'Конфликт номеров заказов'
        WHEN o.match_status = 'ambiguous_match' THEN 'Найдено несколько кандидатов для сопоставления'
        ELSE o.mismatch_details
    END as problem_description
FROM orders o
WHERE o.match_status NOT IN ('fully_matched', 'matched', 'hw_only', 'vendhub_only')
ORDER BY o.created_at DESC;
