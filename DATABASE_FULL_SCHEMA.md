# VHM24R Orders Database

**Файл базы данных:** orders.db
**Всего таблиц:** 8

## Общая статистика

| Таблица | Записей | Колонок |
|---------|---------|----------|
| conflicts | 0 | 9 |
| file_metadata | 5 | 16 |
| order_changes | 0 | 9 |
| orders | 1,194 | 63 |
| processing_logs | 0 | 6 |
| sqlite_sequence | 4 | 2 |
| system_config | 13 | 5 |
| unmatched_records | 1,272 | 8 |

**Общее количество записей:** 2,488

## Таблица: conflicts

**Записей:** 0

### Структура

| Колонка | Тип | Обязательная | По умолчанию | Первичный ключ |
|---------|-----|--------------|--------------|----------------|
| id | INTEGER | Нет | - | Да |
| conflict_type | TEXT | Нет | - | Нет |
| order_id_1 | INTEGER | Нет | - | Нет |
| order_id_2 | INTEGER | Нет | - | Нет |
| conflict_data | TEXT | Нет | - | Нет |
| resolution_status | TEXT | Нет | 'pending' | Нет |
| resolved_by | TEXT | Нет | - | Нет |
| resolved_at | TIMESTAMP | Нет | - | Нет |
| created_at | TIMESTAMP | Нет | CURRENT_TIMESTAMP | Нет |

### SQL создания

```sql
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
)
```

## Таблица: file_metadata

**Записей:** 5

### Структура

| Колонка | Тип | Обязательная | По умолчанию | Первичный ключ |
|---------|-----|--------------|--------------|----------------|
| id | INTEGER | Нет | - | Да |
| filename | TEXT | Да | - | Нет |
| original_filename | TEXT | Нет | - | Нет |
| file_type | TEXT | Нет | - | Нет |
| file_path | TEXT | Нет | - | Нет |
| remote_key | TEXT | Нет | - | Нет |
| file_size | INTEGER | Нет | - | Нет |
| file_hash | TEXT | Нет | - | Нет |
| session_id | TEXT | Нет | - | Нет |
| storage_status | TEXT | Нет | 'local' | Нет |
| processing_status | TEXT | Нет | 'pending' | Нет |
| upload_time | TIMESTAMP | Нет | CURRENT_TIMESTAMP | Нет |
| processed_at | TIMESTAMP | Нет | - | Нет |
| records_processed | INTEGER | Нет | 0 | Нет |
| records_matched | INTEGER | Нет | 0 | Нет |
| processing_errors | TEXT | Нет | - | Нет |

### SQL создания

```sql
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
)
```

### Примеры данных

| id | filename | original_filename | file_type | file_path |
|--|--------|-----------------|---------|---------|
| 1 | 20250724_051533_unknown_fis... | fiscal_bills.xlsx | fiscal_bills | uploads\20250724_051533_unk... |
| 2 | 20250724_051533_unknown_fis... | fiscal_bills.xlsx | fiscal_bills | uploads\20250724_051533_unk... |
| 3 | 20250724_051627_unknown_HW.... | HW.xlsx | happy_workers | uploads\20250724_051627_unk... |

## Таблица: order_changes

**Записей:** 0

### Структура

| Колонка | Тип | Обязательная | По умолчанию | Первичный ключ |
|---------|-----|--------------|--------------|----------------|
| id | INTEGER | Нет | - | Да |
| order_id | INTEGER | Нет | - | Нет |
| field_name | TEXT | Нет | - | Нет |
| old_value | TEXT | Нет | - | Нет |
| new_value | TEXT | Нет | - | Нет |
| change_source | TEXT | Нет | - | Нет |
| change_type | TEXT | Нет | - | Нет |
| change_time | TIMESTAMP | Нет | CURRENT_TIMESTAMP | Нет |
| change_details | TEXT | Нет | - | Нет |

### SQL создания

```sql
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
)
```

## Таблица: orders

**Записей:** 1,194

### Структура

| Колонка | Тип | Обязательная | По умолчанию | Первичный ключ |
|---------|-----|--------------|--------------|----------------|
| id | INTEGER | Нет | - | Да |
| uuid | TEXT | Нет | lower(hex(randomblob(16))) | Нет |
| order_number | TEXT | Да | - | Нет |
| machine_code | TEXT | Нет | - | Нет |
| creation_time | TIMESTAMP | Нет | - | Нет |
| paying_time | TIMESTAMP | Нет | - | Нет |
| brewing_time | TIMESTAMP | Нет | - | Нет |
| delivery_time | TIMESTAMP | Нет | - | Нет |
| refund_time | TIMESTAMP | Нет | - | Нет |
| event_time | TIMESTAMP | Нет | - | Нет |
| fiscal_time | TIMESTAMP | Нет | - | Нет |
| gateway_time | TIMESTAMP | Нет | - | Нет |
| order_price | DECIMAL(10,2) | Нет | - | Нет |
| fiscal_amount | DECIMAL(10,2) | Нет | - | Нет |
| gateway_amount | DECIMAL(10,2) | Нет | - | Нет |
| bonus_amount | DECIMAL(10,2) | Нет | - | Нет |
| cashback_amount | DECIMAL(10,2) | Нет | - | Нет |
| goods_name | TEXT | Нет | - | Нет |
| goods_id | TEXT | Нет | - | Нет |
| taste_name | TEXT | Нет | - | Нет |
| ikpu | TEXT | Нет | - | Нет |
| barcode | TEXT | Нет | - | Нет |
| marking | TEXT | Нет | - | Нет |
| packaging | TEXT | Нет | - | Нет |
| address | TEXT | Нет | - | Нет |
| machine_category | TEXT | Нет | - | Нет |
| order_type | TEXT | Нет | - | Нет |
| order_resource | TEXT | Нет | - | Нет |
| payment_type | TEXT | Нет | - | Нет |
| payment_status | TEXT | Нет | - | Нет |
| payment_gateway | TEXT | Нет | - | Нет |
| fiscal_check_number | TEXT | Нет | - | Нет |
| taxpayer_id | TEXT | Нет | - | Нет |
| cash_register_id | TEXT | Нет | - | Нет |
| shift_number | INTEGER | Нет | - | Нет |
| receipt_type | TEXT | Нет | - | Нет |
| transaction_id | TEXT | Нет | - | Нет |
| payme_transaction_id | TEXT | Нет | - | Нет |
| click_transaction_id | TEXT | Нет | - | Нет |
| uzum_transaction_id | TEXT | Нет | - | Нет |
| click_trans_id | TEXT | Нет | - | Нет |
| card_number | TEXT | Нет | - | Нет |
| merchant_id | TEXT | Нет | - | Нет |
| terminal_id | TEXT | Нет | - | Нет |
| service_id | TEXT | Нет | - | Нет |
| shop_id | TEXT | Нет | - | Нет |
| phone_number | TEXT | Нет | - | Нет |
| username | TEXT | Нет | - | Нет |
| gateway_username | TEXT | Нет | - | Нет |
| brew_status | TEXT | Нет | - | Нет |
| gateway_status | TEXT | Нет | - | Нет |
| reason | TEXT | Нет | - | Нет |
| match_status | TEXT | Нет | 'unmatched' | Нет |
| source | TEXT | Нет | - | Нет |
| matched_sources | TEXT | Нет | - | Нет |
| fiscal_matched | BOOLEAN | Нет | FALSE | Нет |
| gateway_matched | BOOLEAN | Нет | FALSE | Нет |
| mismatch_details | TEXT | Нет | - | Нет |
| conflict_details | TEXT | Нет | - | Нет |
| match_candidates | TEXT | Нет | - | Нет |
| created_at | TIMESTAMP | Нет | CURRENT_TIMESTAMP | Нет |
| updated_at | TIMESTAMP | Нет | CURRENT_TIMESTAMP | Нет |
| last_modified_by | TEXT | Нет | - | Нет |

### SQL создания

```sql
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
)
```

### Примеры данных

| id | uuid | order_number | machine_code | creation_time |
|--|----|------------|------------|-------------|
| 1196 | 338303c58191822e9d24af1f72c... | ff0000025520250701025853a7c... | a7ca181f0000 | 2025-06-30 23:59:06 |
| 1198 | e5edfea1e3cf2f7cf559805c265... | ff0000003c2025070102040072a... | 72ac181f0000 | 2025-06-30 23:04:15 |
| 1199 | 7461f9820efec961c748672a1e8... | ff000002e22025070100444224a... | 24a8181f0000 | 2025-06-30 21:44:45 |

## Таблица: processing_logs

**Записей:** 0

### Структура

| Колонка | Тип | Обязательная | По умолчанию | Первичный ключ |
|---------|-----|--------------|--------------|----------------|
| id | INTEGER | Нет | - | Да |
| session_id | TEXT | Нет | - | Нет |
| log_level | TEXT | Нет | - | Нет |
| message | TEXT | Нет | - | Нет |
| details | TEXT | Нет | - | Нет |
| created_at | TIMESTAMP | Нет | CURRENT_TIMESTAMP | Нет |

### SQL создания

```sql
CREATE TABLE processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    log_level TEXT,
    message TEXT,
    details TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

## Таблица: sqlite_sequence

**Записей:** 4

### Структура

| Колонка | Тип | Обязательная | По умолчанию | Первичный ключ |
|---------|-----|--------------|--------------|----------------|
| name |  | Нет | - | Нет |
| seq |  | Нет | - | Нет |

### SQL создания

```sql
CREATE TABLE sqlite_sequence(name,seq)
```

### Примеры данных

| name | seq |
|----|---|
| system_config | 145 |
| file_metadata | 5 |
| unmatched_records | 1272 |

## Таблица: system_config

**Записей:** 13

### Структура

| Колонка | Тип | Обязательная | По умолчанию | Первичный ключ |
|---------|-----|--------------|--------------|----------------|
| id | INTEGER | Нет | - | Да |
| config_key | TEXT | Да | - | Нет |
| config_value | TEXT | Нет | - | Нет |
| description | TEXT | Нет | - | Нет |
| updated_at | TIMESTAMP | Нет | CURRENT_TIMESTAMP | Нет |

### SQL создания

```sql
CREATE TABLE system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT UNIQUE NOT NULL,
    config_value TEXT,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Примеры данных

| id | config_key | config_value | description | updated_at |
|--|----------|------------|-----------|----------|
| 1 | time_tolerance_seconds | 60 | Допустимое отклонение време... | 2025-07-23 23:58:28 |
| 2 | amount_tolerance | 0.01 | Допустимое отклонение суммы | 2025-07-23 23:58:28 |
| 3 | hw_vendhub_time_window | 60 | Временное окно для сопостав... | 2025-07-23 23:58:28 |

## Таблица: unmatched_records

**Записей:** 1,272

### Структура

| Колонка | Тип | Обязательная | По умолчанию | Первичный ключ |
|---------|-----|--------------|--------------|----------------|
| id | INTEGER | Нет | - | Да |
| record_type | TEXT | Нет | - | Нет |
| record_data | TEXT | Нет | - | Нет |
| record_time | TIMESTAMP | Нет | - | Нет |
| record_amount | DECIMAL(10,2) | Нет | - | Нет |
| attempts | INTEGER | Нет | 0 | Нет |
| last_attempt | TIMESTAMP | Нет | - | Нет |
| created_at | TIMESTAMP | Нет | CURRENT_TIMESTAMP | Нет |

### SQL создания

```sql
CREATE TABLE unmatched_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type TEXT,            -- fiscal/payme/click/uzum
    record_data TEXT,            -- JSON с полными данными записи
    record_time TIMESTAMP,       -- время из записи для поиска
    record_amount DECIMAL(10,2), -- сумма для поиска
    attempts INTEGER DEFAULT 0,  -- количество попыток сопоставления
    last_attempt TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### Примеры данных

| id | record_type | record_data | record_time | record_amount |
|--|-----------|-----------|-----------|-------------|
| 1 | fiscal | {"\u0414\u0430\u0442\u0430 ... | 2025-06-16 07:06:42 | 15000 |
| 2 | fiscal | {"\u0414\u0430\u0442\u0430 ... | 2025-06-16 07:06:42 | 15000 |
| 3 | fiscal | {"\u0414\u0430\u0442\u0430 ... | 2025-06-16 07:09:15 | 20000 |

