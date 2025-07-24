-- VHM24R - Интеллектуальная система сверки заказов, платежей и фискализации
-- PostgreSQL схема для Railway deployment

-- Создание расширений
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- Таблица сессий обработки
CREATE TABLE IF NOT EXISTS processing_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID DEFAULT uuid_generate_v4() UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20) DEFAULT 'processing',
    files_processed INTEGER DEFAULT 0,
    orders_processed INTEGER DEFAULT 0,
    error_message TEXT,
    
    -- Статистика по типам ошибок согласно промту
    stats_ok INTEGER DEFAULT 0,
    stats_no_match_in_report INTEGER DEFAULT 0,
    stats_no_payment_found INTEGER DEFAULT 0,
    stats_excess_payment INTEGER DEFAULT 0,
    stats_payment_mismatch INTEGER DEFAULT 0,
    stats_fiscal_missing INTEGER DEFAULT 0,
    stats_unprocessed INTEGER DEFAULT 0
);

-- Основная таблица заказов (объединенные данные)
CREATE TABLE IF NOT EXISTS orders (
    id SERIAL PRIMARY KEY,
    order_number VARCHAR(100) NOT NULL,
    machine_code VARCHAR(50),
    creation_time TIMESTAMP,
    paying_time TIMESTAMP,
    brewing_time TIMESTAMP,
    delivery_time TIMESTAMP,
    order_price DECIMAL(10,2) DEFAULT 0,
    goods_name VARCHAR(200),
    payment_type VARCHAR(50),
    refund_time TIMESTAMP,
    reason TEXT,
    
    -- Флаги сопоставления согласно промту
    matched_payment BOOLEAN DEFAULT FALSE,
    matched_fiscal BOOLEAN DEFAULT FALSE,
    
    -- Данные платежных шлюзов
    payment_gateway VARCHAR(20), -- payme, click, uzum
    payment_source VARCHAR(50),
    transaction_id VARCHAR(100),
    card_number VARCHAR(20),
    merchant_id VARCHAR(50),
    
    -- Фискальные данные
    fiscal_check_number VARCHAR(100),
    taxpayer_id VARCHAR(50),
    
    -- Классификация ошибок согласно промту
    error_type VARCHAR(30) DEFAULT 'UNPROCESSED',
    details TEXT,
    
    -- JSON данные из исходных файлов
    hw_data JSONB,
    vendhub_data JSONB,
    gateway_data JSONB,
    fiscal_data JSONB,
    
    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id UUID REFERENCES processing_sessions(session_id)
);

-- Таблица метаданных файлов
CREATE TABLE IF NOT EXISTS file_metadata (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    file_type VARCHAR(50) NOT NULL,
    file_path VARCHAR(500),
    file_size BIGINT,
    records_processed INTEGER DEFAULT 0,
    upload_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    session_id UUID REFERENCES processing_sessions(session_id),
    
    -- Хеш файла для предотвращения дублирования
    file_hash VARCHAR(64),
    
    -- Статус обработки
    processing_status VARCHAR(20) DEFAULT 'pending'
);

-- Таблица системной конфигурации
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица логов для мониторинга
CREATE TABLE IF NOT EXISTS processing_logs (
    id SERIAL PRIMARY KEY,
    session_id UUID REFERENCES processing_sessions(session_id),
    log_level VARCHAR(10) DEFAULT 'INFO',
    message TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы для оптимизации производительности
CREATE INDEX IF NOT EXISTS idx_orders_order_number ON orders(order_number);
CREATE INDEX IF NOT EXISTS idx_orders_machine_code ON orders(machine_code);
CREATE INDEX IF NOT EXISTS idx_orders_creation_time ON orders(creation_time);
CREATE INDEX IF NOT EXISTS idx_orders_error_type ON orders(error_type);
CREATE INDEX IF NOT EXISTS idx_orders_payment_type ON orders(payment_type);
CREATE INDEX IF NOT EXISTS idx_orders_session_id ON orders(session_id);

-- Индексы для поиска по JSON полям
CREATE INDEX IF NOT EXISTS idx_orders_hw_data_gin ON orders USING GIN(hw_data);
CREATE INDEX IF NOT EXISTS idx_orders_vendhub_data_gin ON orders USING GIN(vendhub_data);
CREATE INDEX IF NOT EXISTS idx_orders_gateway_data_gin ON orders USING GIN(gateway_data);

-- Индексы для файлов
CREATE INDEX IF NOT EXISTS idx_file_metadata_session_id ON file_metadata(session_id);
CREATE INDEX IF NOT EXISTS idx_file_metadata_file_type ON file_metadata(file_type);
CREATE INDEX IF NOT EXISTS idx_file_metadata_upload_time ON file_metadata(upload_time);

-- Функция для автоматического обновления updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Триггер для автоматического обновления updated_at в таблице orders
CREATE TRIGGER update_orders_updated_at 
    BEFORE UPDATE ON orders 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Вставка базовой конфигурации
INSERT INTO system_config (config_key, config_value, description) VALUES
('time_window_minutes', '3', 'Временное окно для сопоставления заказов (минуты)'),
('price_tolerance_sum', '1', 'Допустимое расхождение в цене (сум)'),
('fiscal_time_window_minutes', '5', 'Временное окно для фискальных чеков (минуты)'),
('gateway_time_window_minutes', '10', 'Временное окно для платежных шлюзов (минуты)'),
('telegram_notifications_enabled', 'true', 'Включить уведомления в Telegram'),
('critical_error_threshold', '10', 'Порог критических ошибок для уведомлений')
ON CONFLICT (config_key) DO NOTHING;

-- Создание представлений для отчетности
CREATE OR REPLACE VIEW v_reconciliation_summary AS
SELECT 
    DATE(creation_time) as report_date,
    COUNT(*) as total_orders,
    COUNT(CASE WHEN error_type = 'OK' THEN 1 END) as successful_orders,
    COUNT(CASE WHEN error_type = 'NO_MATCH_IN_REPORT' THEN 1 END) as no_match_in_report,
    COUNT(CASE WHEN error_type = 'NO_PAYMENT_FOUND' THEN 1 END) as no_payment_found,
    COUNT(CASE WHEN error_type = 'EXCESS_PAYMENT' THEN 1 END) as excess_payment,
    COUNT(CASE WHEN error_type = 'PAYMENT_MISMATCH' THEN 1 END) as payment_mismatch,
    COUNT(CASE WHEN error_type = 'FISCAL_MISSING' THEN 1 END) as fiscal_missing,
    COUNT(CASE WHEN error_type = 'UNPROCESSED' THEN 1 END) as unprocessed,
    SUM(order_price) as total_amount,
    SUM(CASE WHEN error_type = 'OK' THEN order_price ELSE 0 END) as successful_amount
FROM orders 
WHERE creation_time IS NOT NULL
GROUP BY DATE(creation_time)
ORDER BY report_date DESC;

-- Представление для машин с проблемами
CREATE OR REPLACE VIEW v_machine_issues AS
SELECT 
    machine_code,
    COUNT(*) as total_orders,
    COUNT(CASE WHEN error_type != 'OK' THEN 1 END) as error_orders,
    ROUND(
        COUNT(CASE WHEN error_type != 'OK' THEN 1 END) * 100.0 / COUNT(*), 
        2
    ) as error_rate_percent,
    MAX(creation_time) as last_order_time
FROM orders 
WHERE machine_code IS NOT NULL 
    AND creation_time >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY machine_code
HAVING COUNT(CASE WHEN error_type != 'OK' THEN 1 END) > 0
ORDER BY error_rate_percent DESC;

-- Комментарии к таблицам
COMMENT ON TABLE processing_sessions IS 'Сессии обработки файлов с метриками';
COMMENT ON TABLE orders IS 'Основная таблица заказов с результатами сверки';
COMMENT ON TABLE file_metadata IS 'Метаданные загруженных файлов';
COMMENT ON TABLE system_config IS 'Системная конфигурация';
COMMENT ON TABLE processing_logs IS 'Логи обработки для мониторинга';

COMMENT ON COLUMN orders.error_type IS 'Тип ошибки: OK, NO_MATCH_IN_REPORT, NO_PAYMENT_FOUND, EXCESS_PAYMENT, PAYMENT_MISMATCH, FISCAL_MISSING, UNPROCESSED';
COMMENT ON COLUMN orders.hw_data IS 'JSON данные из HW.xlsx файла';
COMMENT ON COLUMN orders.vendhub_data IS 'JSON данные из report.xlsx файла';
COMMENT ON COLUMN orders.gateway_data IS 'JSON данные из платежных шлюзов';
COMMENT ON COLUMN orders.fiscal_data IS 'JSON данные из фискальных чеков';
