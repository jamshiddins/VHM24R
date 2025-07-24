-- ============================================================================
-- VHM24R - Система сверки заказов, платежей и фискализации
-- Схема базы данных для интеллектуального модуля сверки продаж
-- ============================================================================

-- ============================================================================
-- ОСНОВНАЯ ТАБЛИЦА ЗАКАЗОВ С ПОЛНОЙ ЛОГИКОЙ СВЕРКИ
-- ============================================================================

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    
    -- Основные идентификаторы
    order_number TEXT NOT NULL,
    machine_code TEXT,
    
    -- Временные метки (согласно промту)
    creation_time TIMESTAMP,
    paying_time TIMESTAMP,
    brewing_time TIMESTAMP,
    delivery_time TIMESTAMP,
    refund_time TIMESTAMP,
    
    -- Основная информация о заказе
    goods_name TEXT,
    order_price REAL DEFAULT 0,
    payment_type TEXT, -- Cash, Custom payment, Card
    payment_gateway TEXT, -- payme, click, uzum
    reason TEXT, -- причина отмены/ошибки
    
    -- JSON данные из источников (HW.xlsx, report.xlsx, fiscal_bills.xlsx, платежки)
    hw_data TEXT, -- данные из HW.xlsx
    vendhub_data TEXT, -- данные из report.xlsx (внутренний учет)
    fiscal_data TEXT, -- данные из fiscal_bills.xlsx
    gateway_data TEXT, -- данные из Payme.xlsx, Click.xlsx, Uzum.xlsx
    
    -- Фискальные данные
    fiscal_check_number TEXT,
    taxpayer_id TEXT,
    cash_register TEXT,
    
    -- Платежные данные
    transaction_id TEXT,
    card_number TEXT,
    merchant_id TEXT,
    terminal_id TEXT,
    
    -- ТИПЫ ОШИБОК СОГЛАСНО ПРОМТУ
    error_type TEXT DEFAULT 'UNPROCESSED' CHECK (error_type IN (
        'OK',                    -- Всё совпадает
        'NO_MATCH_IN_REPORT',   -- Заказ в HW не найден в report.xlsx
        'NO_PAYMENT_FOUND',     -- Заказ есть, оплаты нет
        'EXCESS_PAYMENT',       -- Оплата есть, заказа нет
        'PAYMENT_MISMATCH',     -- Заказ и оплата есть, но сумма не совпадает
        'FISCAL_MISSING',       -- Оплата есть, но нет чека
        'UNPROCESSED'           -- Еще не обработано
    )),
    
    -- Статусы сопоставления
    match_status TEXT DEFAULT 'unmatched',
    matched_payment BOOLEAN DEFAULT FALSE,
    matched_fiscal BOOLEAN DEFAULT FALSE,
    payment_source TEXT, -- Payme / Click / Uzum
    
    -- Детали ошибок и отклонений
    details TEXT,
    
    -- Системные поля
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(order_number, machine_code)
);

-- ============================================================================
-- ТАБЛИЦА ОБРАБОТАННЫХ ФАЙЛОВ
-- ============================================================================

CREATE TABLE IF NOT EXISTS processed_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL, -- hw, vendhub, fiscal_bills, payme, click, uzum
    file_path TEXT, -- путь к файлу в DigitalOcean Spaces
    file_size INTEGER,
    processed_records INTEGER DEFAULT 0,
    processing_errors INTEGER DEFAULT 0,
    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id TEXT,
    
    -- Метаданные файла
    original_name TEXT,
    upload_source TEXT, -- web, api, cron
    checksum TEXT -- для проверки дубликатов
);

-- ============================================================================
-- СЕССИИ ОБРАБОТКИ
-- ============================================================================

CREATE TABLE IF NOT EXISTS processing_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    files_processed INTEGER DEFAULT 0,
    orders_processed INTEGER DEFAULT 0,
    
    -- Статистика по типам ошибок
    stats_ok INTEGER DEFAULT 0,
    stats_no_match_in_report INTEGER DEFAULT 0,
    stats_no_payment_found INTEGER DEFAULT 0,
    stats_excess_payment INTEGER DEFAULT 0,
    stats_payment_mismatch INTEGER DEFAULT 0,
    stats_fiscal_missing INTEGER DEFAULT 0,
    stats_unprocessed INTEGER DEFAULT 0,
    
    status TEXT DEFAULT 'processing' CHECK (status IN ('processing', 'completed', 'failed')),
    error_message TEXT
);

-- ============================================================================
-- ЖУРНАЛ СВЕРКИ (для отслеживания изменений)
-- ============================================================================

CREATE TABLE IF NOT EXISTS reconciliation_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    previous_error_type TEXT,
    new_error_type TEXT,
    change_reason TEXT,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT, -- система, пользователь
    
    FOREIGN KEY (order_id) REFERENCES orders(id)
);

-- ============================================================================
-- УВЕДОМЛЕНИЯ И АЛЕРТЫ
-- ============================================================================

CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    notification_type TEXT NOT NULL, -- error_threshold, critical_mismatch, system_alert
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    severity TEXT DEFAULT 'info' CHECK (severity IN ('info', 'warning', 'error', 'critical')),
    
    -- Данные для отправки
    telegram_sent BOOLEAN DEFAULT FALSE,
    email_sent BOOLEAN DEFAULT FALSE,
    telegram_chat_id TEXT,
    email_recipients TEXT, -- JSON массив
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    sent_at TIMESTAMP,
    
    -- Связанные данные
    related_order_id INTEGER,
    related_session_id TEXT,
    
    FOREIGN KEY (related_order_id) REFERENCES orders(id)
);

-- ============================================================================
-- КОНФИГУРАЦИЯ СИСТЕМЫ
-- ============================================================================

CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    config_type TEXT DEFAULT 'string' CHECK (config_type IN ('string', 'integer', 'float', 'boolean', 'json')),
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- ИНДЕКСЫ ДЛЯ ОПТИМИЗАЦИИ СВЕРКИ
-- ============================================================================

-- Основные индексы для поиска и сопоставления
CREATE INDEX IF NOT EXISTS idx_orders_number_machine ON orders(order_number, machine_code);
CREATE INDEX IF NOT EXISTS idx_orders_creation_time ON orders(creation_time);
CREATE INDEX IF NOT EXISTS idx_orders_paying_time ON orders(paying_time);
CREATE INDEX IF NOT EXISTS idx_orders_error_type ON orders(error_type);
CREATE INDEX IF NOT EXISTS idx_orders_payment_type ON orders(payment_type);
CREATE INDEX IF NOT EXISTS idx_orders_machine_code ON orders(machine_code);

-- Индексы для временного сопоставления
CREATE INDEX IF NOT EXISTS idx_orders_time_price ON orders(creation_time, order_price);
CREATE INDEX IF NOT EXISTS idx_orders_machine_time_price ON orders(machine_code, creation_time, order_price);

-- Индексы для отчетности
CREATE INDEX IF NOT EXISTS idx_orders_created_at ON orders(created_at);
CREATE INDEX IF NOT EXISTS idx_orders_match_status ON orders(match_status);

-- Индексы для файлов и сессий
CREATE INDEX IF NOT EXISTS idx_processed_files_type ON processed_files(file_type);
CREATE INDEX IF NOT EXISTS idx_processed_files_session ON processed_files(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON processing_sessions(status);

-- ============================================================================
-- НАЧАЛЬНАЯ КОНФИГУРАЦИЯ
-- ============================================================================

-- Настройки системы сверки
INSERT OR IGNORE INTO system_config (config_key, config_value, config_type, description) VALUES
('time_window_minutes', '3', 'integer', 'Временное окно для сопоставления заказов (минуты)'),
('price_tolerance_sum', '1', 'float', 'Допустимое расхождение в цене (сум)'),
('fiscal_time_window_minutes', '5', 'integer', 'Временное окно для сопоставления фискальных чеков (минуты)'),
('gateway_time_window_minutes', '10', 'integer', 'Временное окно для сопоставления платежных шлюзов (минуты)'),
('auto_reconcile_enabled', 'true', 'boolean', 'Автоматическая сверка при загрузке файлов'),
('notification_error_threshold', '10', 'integer', 'Порог ошибок для отправки уведомлений'),
('telegram_bot_token', '', 'string', 'Токен Telegram бота для уведомлений'),
('telegram_chat_id', '', 'string', 'ID чата для уведомлений'),
('digitalocean_spaces_key', '', 'string', 'Ключ доступа к DigitalOcean Spaces'),
('digitalocean_spaces_secret', '', 'string', 'Секретный ключ DigitalOcean Spaces'),
('digitalocean_spaces_bucket', 'vhm24r-files', 'string', 'Имя bucket в DigitalOcean Spaces'),
('digitalocean_spaces_region', 'fra1', 'string', 'Регион DigitalOcean Spaces');

-- ============================================================================
-- ТРИГГЕРЫ ДЛЯ АВТОМАТИЧЕСКОГО ОБНОВЛЕНИЯ
-- ============================================================================

-- Триггер для обновления updated_at
CREATE TRIGGER IF NOT EXISTS update_orders_timestamp 
    AFTER UPDATE ON orders
    FOR EACH ROW
BEGIN
    UPDATE orders SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Триггер для логирования изменений типа ошибки
CREATE TRIGGER IF NOT EXISTS log_error_type_changes
    AFTER UPDATE OF error_type ON orders
    FOR EACH ROW
    WHEN OLD.error_type != NEW.error_type
BEGIN
    INSERT INTO reconciliation_log (order_id, previous_error_type, new_error_type, change_reason, changed_by)
    VALUES (NEW.id, OLD.error_type, NEW.error_type, 'Automatic reconciliation', 'system');
END;

-- ============================================================================
-- ПРЕДСТАВЛЕНИЯ ДЛЯ ОТЧЕТНОСТИ
-- ============================================================================

-- Представление для отчета о сверке
CREATE VIEW IF NOT EXISTS reconciliation_report AS
SELECT 
    o.order_number,
    o.machine_code,
    o.creation_time as order_time,
    o.order_price,
    o.goods_name,
    CASE WHEN o.matched_payment THEN 'Да' ELSE 'Нет' END as matched_payment,
    o.payment_source,
    CASE WHEN o.matched_fiscal THEN 'Да' ELSE 'Нет' END as matched_fiscal,
    o.error_type,
    o.details,
    o.created_at
FROM orders o
ORDER BY o.created_at DESC;

-- Представление для статистики ошибок
CREATE VIEW IF NOT EXISTS error_statistics AS
SELECT 
    error_type,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM orders), 2) as percentage
FROM orders 
GROUP BY error_type
ORDER BY count DESC;

-- Представление для ежедневной статистики
CREATE VIEW IF NOT EXISTS daily_statistics AS
SELECT 
    DATE(creation_time) as date,
    COUNT(*) as total_orders,
    SUM(order_price) as total_amount,
    COUNT(CASE WHEN error_type = 'OK' THEN 1 END) as successful_orders,
    COUNT(CASE WHEN error_type != 'OK' AND error_type != 'UNPROCESSED' THEN 1 END) as error_orders,
    COUNT(CASE WHEN payment_type = 'Cash' THEN 1 END) as cash_orders,
    COUNT(CASE WHEN payment_type != 'Cash' THEN 1 END) as card_orders
FROM orders 
WHERE creation_time IS NOT NULL
GROUP BY DATE(creation_time)
ORDER BY date DESC;
