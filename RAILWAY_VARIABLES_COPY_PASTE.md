# Railway Variables - Копировать и вставить

## 🔑 Обязательные переменные

### SECRET_KEY
```
gr-qp2_wZ8cFtLS-0Uat6oWYweWf8PZpRuS3wHMawyQAMilAYZ0axbYjnl7vxKzJfEo
```

### FLASK_ENV
```
production
```

## ⚙️ Рекомендуемые переменные

### WEB_CONCURRENCY
```
2
```

### WORKER_TIMEOUT
```
120
```

### SCHEDULER_ENABLED
```
true
```

### TIMEZONE
```
Asia/Tashkent
```

### MAX_REQUESTS
```
1000
```

### TIME_WINDOW_MINUTES
```
3
```

### PRICE_TOLERANCE_SUM
```
1
```

### FISCAL_TIME_WINDOW_MINUTES
```
5
```

### GATEWAY_TIME_WINDOW_MINUTES
```
10
```

### CRITICAL_ERROR_THRESHOLD
```
10
```

### MAX_FILE_SIZE
```
104857600
```

### FILE_RETENTION_DAYS
```
30
```

### ALLOWED_EXTENSIONS
```
xlsx,xls,csv,pdf,jpg,jpeg,png,txt
```

### MAX_FILES_PER_UPLOAD
```
10
```

### BACKUP_ENABLED
```
false
```

### BACKUP_FREQUENCY
```
daily
```

### BACKUP_RETENTION_COUNT
```
30
```

---

## 📋 Как добавить в Railway:

1. Откройте ваш проект в Railway
2. Перейдите в раздел **"Variables"**
3. Нажмите **"Add Variable"**
4. Скопируйте имя переменной (например: `SECRET_KEY`)
5. Скопируйте значение переменной
6. Нажмите **"Add"**
7. Повторите для всех переменных

## ✅ Минимум для запуска:
Достаточно добавить только:
- `SECRET_KEY`
- `FLASK_ENV`

Остальные переменные опциональны и имеют значения по умолчанию.

---

**После добавления переменных Railway автоматически перезапустит приложение!**
