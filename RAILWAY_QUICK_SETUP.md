# 🚀 Railway - Быстрая настройка VHM24R

## Шаг 1: Добавить PostgreSQL базу данных

1. В Railway dashboard вашего проекта
2. Нажмите **"Add Service"** → **"Database"** → **"PostgreSQL"**
3. Railway автоматически создаст `DATABASE_URL`

## Шаг 2: Добавить переменные окружения

Перейдите в раздел **"Variables"** и добавьте:

### Обязательные переменные:

```
SECRET_KEY
gr-qp2_wZ8cFtLS-0Uat6oWYweWf8PZpRuS3wHMawyQAMilAYZ0axbYjnl7vxKzJfEo
```

```
FLASK_ENV
production
```

### Рекомендуемые переменные:

```
WEB_CONCURRENCY
2
```

```
WORKER_TIMEOUT
120
```

```
SCHEDULER_ENABLED
true
```

```
TIMEZONE
Asia/Tashkent
```

## Шаг 3: Проверить деплой

1. Railway автоматически перезапустит приложение
2. Откройте URL вашего приложения
3. Перейдите на `/health` - должен показать `{"status": "healthy"}`
4. Главная страница должна загрузиться

## ✅ Готово!

VHM24R развернут и готов к использованию!

### Основные URL:
- `/` - Главная страница с аналитикой
- `/upload` - Загрузка файлов
- `/orders` - Управление заказами
- `/health` - Проверка статуса

---

**Если нужны дополнительные функции** (Telegram, DigitalOcean), смотрите `RAILWAY_ENV_SETUP.md`
