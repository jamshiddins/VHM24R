# 🚀 Railway Production Configuration - VHM24R 24/7

## 📋 ПОЛНАЯ КОНФИГУРАЦИЯ ДЛЯ PRODUCTION

### 🔑 ОБЯЗАТЕЛЬНЫЕ ПЕРЕМЕННЫЕ

#### SECRET_KEY
```
gr-qp2_wZ8cFtLS-0Uat6oWYweWf8PZpRuS3wHMawyQAMilAYZ0axbYjnl7vxKzJfEo
```

#### FLASK_ENV
```
production
```

### ⚙️ PRODUCTION НАСТРОЙКИ

#### WEB_CONCURRENCY (количество worker процессов)
```
4
```

#### WORKER_TIMEOUT (таймаут worker в секундах)
```
300
```

#### MAX_REQUESTS (максимум запросов на worker)
```
2000
```

#### PORT (порт приложения)
```
5000
```

### 🕐 ПЛАНИРОВЩИК И АВТОМАТИЗАЦИЯ

#### SCHEDULER_ENABLED (включить автоматические задачи)
```
true
```

#### TIMEZONE (часовой пояс)
```
Asia/Tashkent
```

### 📊 НАСТРОЙКИ СВЕРКИ ДАННЫХ

#### TIME_WINDOW_MINUTES (окно сопоставления заказов)
```
5
```

#### PRICE_TOLERANCE_SUM (допустимое расхождение в цене)
```
1
```

#### FISCAL_TIME_WINDOW_MINUTES (окно для фискальных чеков)
```
10
```

#### GATEWAY_TIME_WINDOW_MINUTES (окно для платежных шлюзов)
```
15
```

#### CRITICAL_ERROR_THRESHOLD (порог критических ошибок)
```
20
```

### 📁 НАСТРОЙКИ ФАЙЛОВ

#### MAX_FILE_SIZE (максимальный размер файла в байтах)
```
209715200
```

#### FILE_RETENTION_DAYS (дни хранения файлов)
```
90
```

#### ALLOWED_EXTENSIONS (разрешенные расширения)
```
xlsx,xls,csv,pdf,jpg,jpeg,png,txt,docx
```

#### MAX_FILES_PER_UPLOAD (максимум файлов за раз)
```
20
```

### 💾 РЕЗЕРВНОЕ КОПИРОВАНИЕ

#### BACKUP_ENABLED (включить резервное копирование)
```
true
```

#### BACKUP_FREQUENCY (частота резервного копирования)
```
daily
```

#### BACKUP_RETENTION_COUNT (количество резервных копий)
```
30
```

### 🔒 БЕЗОПАСНОСТЬ

#### DEBUG (отключить отладку в production)
```
false
```

#### SQL_DEBUG (отключить SQL логи)
```
false
```

#### PROFILING_ENABLED (отключить профилирование)
```
false
```

---

## 🎯 ОПЦИОНАЛЬНЫЕ ИНТЕГРАЦИИ

### 📱 Telegram уведомления (рекомендуется)

#### TELEGRAM_BOT_TOKEN
```
your-bot-token-from-botfather
```

#### TELEGRAM_CHAT_ID
```
your-chat-id
```

**Как получить:**
1. Создайте бота через @BotFather
2. Получите токен
3. Узнайте chat_id через @userinfobot

### ☁️ DigitalOcean Spaces (рекомендуется для файлов)

#### DIGITALOCEAN_SPACES_KEY
```
your-spaces-key
```

#### DIGITALOCEAN_SPACES_SECRET
```
your-spaces-secret
```

#### DIGITALOCEAN_SPACES_BUCKET
```
vhm24r-production
```

#### DIGITALOCEAN_SPACES_REGION
```
fra1
```

---

## 🚀 ПОРЯДОК ДОБАВЛЕНИЯ В RAILWAY

### 1. Основные переменные (добавить первыми):
- SECRET_KEY
- FLASK_ENV
- WEB_CONCURRENCY
- WORKER_TIMEOUT

### 2. Настройки приложения:
- SCHEDULER_ENABLED
- TIMEZONE
- MAX_FILE_SIZE
- BACKUP_ENABLED

### 3. Настройки сверки:
- TIME_WINDOW_MINUTES
- PRICE_TOLERANCE_SUM
- FISCAL_TIME_WINDOW_MINUTES
- GATEWAY_TIME_WINDOW_MINUTES

### 4. Опциональные интеграции:
- TELEGRAM_BOT_TOKEN (если есть)
- TELEGRAM_CHAT_ID (если есть)
- DIGITALOCEAN_SPACES_* (если нужно)

---

## ✅ ПРОВЕРКА ПОСЛЕ ДЕПЛОЯ

### 1. Health Check
```
GET /health
```
Должен вернуть:
```json
{
  "status": "healthy",
  "database": "connected",
  "total_orders": 0,
  "version": "1.0.0"
}
```

### 2. Основные страницы
- `/` - Главная с аналитикой
- `/upload` - Загрузка файлов
- `/orders` - Управление заказами

### 3. Логи Railway
Должны показать:
```
Database initialized
Processors initialized
File detector initialized
Telegram initialized
Scheduler initialized
VHM24R application initialized successfully
```

---

## 🔧 МОНИТОРИНГ 24/7

### Автоматические задачи:
- ✅ Ежедневная сверка данных
- ✅ Очистка старых файлов
- ✅ Резервное копирование
- ✅ Отправка отчетов в Telegram

### Health checks:
- ✅ Проверка БД каждые 5 минут
- ✅ Мониторинг памяти и CPU
- ✅ Автоматический перезапуск при ошибках

---

**VHM24R готов к работе 24/7 в production!** 🎯
