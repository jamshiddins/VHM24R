# Railway - Настройка переменных окружения для VHM24R

## 🚀 Пошаговая инструкция

### 1. Обязательные переменные

#### DATABASE_URL
Railway автоматически создаст PostgreSQL базу данных и установит эту переменную.

**Действия:**
1. В Railway dashboard перейдите в ваш проект
2. Нажмите "Add Service" → "Database" → "PostgreSQL"
3. Railway автоматически создаст `DATABASE_URL`

**Формат:** `postgresql://username:password@host:port/database`

#### SECRET_KEY
Секретный ключ для Flask сессий и безопасности.

**Установить в Railway:**
```
Имя: SECRET_KEY
Значение: vhm24r-production-secret-key-2025-change-this-to-random-string
```

**Рекомендация:** Сгенерируйте случайную строку длиной 50+ символов:
```python
import secrets
print(secrets.token_urlsafe(50))
```

### 2. Настройка в Railway Dashboard

1. **Откройте ваш проект в Railway**
2. **Перейдите в раздел "Variables"**
3. **Добавьте переменные одну за другой:**

```env
# Обязательные переменные
SECRET_KEY=vhm24r-production-secret-key-2025-change-this-to-random-string
FLASK_ENV=production

# Настройки приложения
PORT=5000
WEB_CONCURRENCY=2
WORKER_TIMEOUT=120
MAX_REQUESTS=1000

# Настройки сверки
TIME_WINDOW_MINUTES=3
PRICE_TOLERANCE_SUM=1
FISCAL_TIME_WINDOW_MINUTES=5
GATEWAY_TIME_WINDOW_MINUTES=10
CRITICAL_ERROR_THRESHOLD=10

# Настройки файлов
MAX_FILE_SIZE=104857600
FILE_RETENTION_DAYS=30
ALLOWED_EXTENSIONS=xlsx,xls,csv,pdf,jpg,jpeg,png,txt
MAX_FILES_PER_UPLOAD=10

# Настройки планировщика
SCHEDULER_ENABLED=true
TIMEZONE=Asia/Tashkent

# Настройки резервного копирования
BACKUP_ENABLED=false
BACKUP_FREQUENCY=daily
BACKUP_RETENTION_COUNT=30
```

### 3. Опциональные переменные (для расширенной функциональности)

#### DigitalOcean Spaces (для хранения файлов)
```env
DIGITALOCEAN_SPACES_KEY=your-spaces-access-key
DIGITALOCEAN_SPACES_SECRET=your-spaces-secret-key
DIGITALOCEAN_SPACES_BUCKET=vhm24r-files
DIGITALOCEAN_SPACES_REGION=fra1
```

**Как получить:**
1. Зарегистрируйтесь в DigitalOcean
2. Создайте Spaces bucket
3. Сгенерируйте API ключи в разделе API

#### Telegram уведомления
```env
TELEGRAM_BOT_TOKEN=your-bot-token-from-botfather
TELEGRAM_CHAT_ID=your-chat-id-or-group-id
```

**Как получить:**
1. Создайте бота через @BotFather в Telegram
2. Получите токен бота
3. Узнайте chat_id через @userinfobot

### 4. Проверка настройки

После добавления переменных Railway автоматически перезапустит приложение.

**Проверьте деплой:**
1. Откройте URL вашего приложения
2. Перейдите на `/health` - должен показать статус "healthy"
3. Главная страница должна загрузиться без ошибок

### 5. Минимальная конфигурация для запуска

Если хотите запустить с минимальными настройками:

```env
# Только эти 2 переменные обязательны:
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://... (автоматически создается Railway)
```

Все остальные переменные имеют значения по умолчанию.

### 6. Расширенная конфигурация

Для полной функциональности добавьте все переменные из пункта 2.

### 7. Мониторинг

После деплоя проверьте логи в Railway:
- Должно появиться сообщение "VHM24R application initialized successfully"
- База данных должна инициализироваться автоматически
- Все компоненты должны загрузиться без ошибок

## 🔧 Troubleshooting

### Проблема: Ошибка подключения к БД
**Решение:** Убедитесь, что PostgreSQL сервис добавлен и `DATABASE_URL` установлена

### Проблема: Ошибка импорта модулей
**Решение:** Проверьте, что все файлы загружены в GitHub и Railway синхронизирован

### Проблема: 500 ошибка
**Решение:** Проверьте логи Railway, возможно не хватает переменных окружения

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи в Railway Dashboard
2. Убедитесь, что все обязательные переменные установлены
3. Проверьте статус всех сервисов (Web + Database)

---

*VHM24R готов к работе после настройки этих переменных!*
