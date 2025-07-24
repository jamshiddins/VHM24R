# 🚂 Railway Deployment Guide для VHM24R

## Подключение к существующему проекту Railway

**ID проекта:** `d347d814-8f9e-470b-8a6b-47b72689a976`

### Способ 1: Через Railway CLI

```bash
# Установите Railway CLI если еще не установлен
npm install -g @railway/cli

# Войдите в аккаунт
railway login

# Подключитесь к существующему проекту
railway link d347d814-8f9e-470b-8a6b-47b72689a976

# Проверьте подключение
railway status

# Деплой проекта
railway up
```

### Способ 2: Через веб-интерфейс Railway

1. Зайдите на [railway.app](https://railway.app)
2. Войдите в свой аккаунт
3. Найдите проект с ID `d347d814-8f9e-470b-8a6b-47b72689a976`
4. В настройках проекта подключите GitHub репозиторий
5. Выберите ветку `main` для автоматического деплоя

### Способ 3: Через Git Remote

```bash
# Добавьте Railway как remote
git remote add railway https://railway.app/project/d347d814-8f9e-470b-8a6b-47b72689a976.git

# Пуш в Railway для деплоя
git push railway main
```

## Настройка переменных окружения

После подключения установите следующие переменные в Railway Dashboard:

### Обязательные переменные:
```
SECRET_KEY=your-production-secret-key-here
FLASK_ENV=production
```

### Опциональные переменные:
```
DIGITALOCEAN_SPACES_KEY=your-spaces-key
DIGITALOCEAN_SPACES_SECRET=your-spaces-secret
DIGITALOCEAN_SPACES_BUCKET=vhm24r-files
DIGITALOCEAN_SPACES_REGION=fra1

TELEGRAM_BOT_TOKEN=your-bot-token
TELEGRAM_CHAT_ID=your-chat-id

WEB_CONCURRENCY=2
WORKER_TIMEOUT=300
MAX_REQUESTS=1000
```

## Проверка деплоя

После успешного деплоя:

1. **Проверьте логи:**
   ```bash
   railway logs
   ```

2. **Откройте приложение:**
   ```bash
   railway open
   ```

3. **Проверьте health check:**
   ```
   https://your-app-url.railway.app/health
   ```

## Автоматическая настройка Railway

Railway автоматически:
- ✅ Определит Python проект
- ✅ Установит Python 3.11.8 (из runtime.txt)
- ✅ Установит зависимости (из requirements.txt)
- ✅ Создаст PostgreSQL базу данных
- ✅ Запустит приложение через Gunicorn (из Procfile)
- ✅ Предоставит HTTPS домен

## Мониторинг

После деплоя вы можете:
- Просматривать логи в реальном времени
- Мониторить использование ресурсов
- Настроить алерты
- Просматривать метрики производительности

## Troubleshooting

Если возникают проблемы:

1. **Проверьте логи:**
   ```bash
   railway logs --tail
   ```

2. **Проверьте переменные окружения:**
   ```bash
   railway variables
   ```

3. **Перезапустите сервис:**
   ```bash
   railway restart
   ```

4. **Проверьте статус:**
   ```bash
   railway status
   ```

## Полезные команды Railway CLI

```bash
# Просмотр всех проектов
railway projects

# Подключение к проекту
railway link [PROJECT_ID]

# Просмотр переменных
railway variables

# Установка переменной
railway variables set KEY=value

# Просмотр логов
railway logs

# Открытие приложения
railway open

# Информация о проекте
railway status
```

---

**Примечание:** Убедитесь, что у вас есть права доступа к проекту `d347d814-8f9e-470b-8a6b-47b72689a976` в Railway.
