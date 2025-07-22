CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_number TEXT NOT NULL,
    machine_code TEXT,
    
    -- JSON данные из источников
    hw_data TEXT,
    vendhub_data TEXT,
    fiscal_data TEXT,
    gateway_data TEXT,
    
    -- Основные поля
    creation_time TIMESTAMP,
    order_price REAL,
    payment_type TEXT,
    payment_gateway TEXT,
    
    -- Фискальные данные
    fiscal_check_number TEXT,
    taxpayer_id TEXT,
    
    -- Платежные данные
    transaction_id TEXT,
    card_number TEXT,
    merchant_id TEXT,
    
    -- Статусы
    match_status TEXT DEFAULT 'unmatched',
    mismatch_details TEXT,
    
    -- Системные поля
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(order_number, machine_code)
);

CREATE TABLE IF NOT EXISTS processing_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    files_processed INTEGER DEFAULT 0,
    orders_processed INTEGER DEFAULT 0,
    stats TEXT,
    status TEXT DEFAULT 'processing'
);