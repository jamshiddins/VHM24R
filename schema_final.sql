-- VHM24R Database Schema - Финальная версия
-- Полная схема базы данных согласно новым требованиям

-- Основная таблица заказов
CREATE TABLE orders (
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
    gateway_amount DECIMAL(10,2),-- сумма в платежном шлюзе (ПОЛНАЯ сумма!)
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

-- Индексы для быстрого поиска
CREATE INDEX idx_order_number ON orders(order_number);
CREATE INDEX idx_machine_code ON orders(machine_code);
CREATE INDEX idx_creation_time ON orders(creation_time);
CREATE INDEX idx_paying_time ON orders(paying_time);
CREATE INDEX idx_order_price ON orders(order_price);
CREATE INDEX idx_match_status ON orders(match_status);
CREATE INDEX idx_payment_type ON orders(payment_type);
CREATE INDEX idx_order_resource ON orders(order_resource);
CREATE INDEX idx_fiscal_time ON orders(fiscal_time);
CREATE INDEX idx_gateway_time ON orders(gateway_time);

-- Таблица истории изменений
CREATE TABLE order_changes (
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

-- Таблица несопоставленных записей
CREATE TABLE unmatched_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type TEXT,            -- fiscal/payme/click/uzum
    record_data TEXT,            -- JSON с полными данными записи
    record_time TIMESTAMP,       -- время из записи для поиска
    record_amount DECIMAL(10,2), -- сумма для поиска
    attempts INTEGER DEFAULT 0,  -- количество попыток сопоставления
    last_attempt TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица конфликтов
CREATE TABLE conflicts (
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

-- Таблица метаданных файлов
CREATE TABLE file_metadata (
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

-- Таблица конфигурации системы
CREATE TABLE system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица логов обработки
CREATE TABLE processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    log_level TEXT,
    message TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Вставка базовой конфигурации
INSERT INTO system_config (config_key, config_value, description) VALUES
('time_tolerance_seconds', '60', 'Допустимое отклонение времени в секундах для сопоставления'),
('amount_tolerance', '0.01', 'Допустимое отклонение суммы для сопоставления'),
('hw_vendhub_time_window', '60', 'Временное окно для сопоставления HW и VendHub в секундах'),
('fiscal_time_window', '60', 'Временное окно для сопоставления фискальных чеков в секундах'),
('gateway_time_window', '60', 'Временное окно для сопоставления платежных шлюзов в секундах'),
('max_file_size_mb', '100', 'Максимальный размер загружаемого файла в МБ'),
('auto_matching_enabled', 'true', 'Включено ли автоматическое сопоставление'),
('telegram_notifications', 'true', 'Включены ли уведомления в Telegram'),
('backup_to_cloud', 'true', 'Включено ли резервное копирование в облако'),
('debug_mode', 'false', 'Режим отладки'),
('app_version', '2.0.0', 'Версия приложения'),
('last_update', datetime('now'), 'Время последнего обновления конфигурации'),
('commission_calculation', 'direct_comparison', 'Метод расчета комиссии: direct_comparison (прямое сравнение сумм)');
