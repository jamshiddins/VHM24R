# 🚀 VHM24R - Интеллектуальная система сверки заказов

**Order Data Unification System with Recipe & Finance Management**

[![Railway Deploy](https://img.shields.io/badge/Deploy%20on-Railway-0B0D0E.svg)](https://railway.app)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3.2-green.svg)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-13+-blue.svg)](https://www.postgresql.org/)

## 📋 Описание

VHM24R - это комплексная веб-система для автоматической сверки и объединения данных о заказах из различных источников. Система включает три интегрированных модуля:

- 🔄 **Модуль сверки заказов** - автоматическое сопоставление данных из разных систем
- 📊 **Модуль управления рецептурой** - учет ингредиентов и расчет себестоимости  
- 💰 **Модуль финансовой сверки** - контроль денежных потоков и платежей

## ✨ Ключевые возможности

### 🎯 Интеллектуальная обработка файлов
- **15+ форматов файлов**: CSV, XLSX, XLS, PDF, JPG, PNG, TXT
- **Автоопределение типа**: По структуре колонок, не по имени файла
- **OCR обработка**: Извлечение данных из изображений чеков
- **Пакетная загрузка**: До 10 файлов одновременно

### 🔍 Автоматическая сверка данных
- **6 типов источников**: Happy Workers, VendHub, Fiscal Bills, Payment Gateways
- **Многоэтапный алгоритм**: HW ↔ VendHub → Fiscal → Gateways
- **Временная валидация**: ±1 минута точность
- **Ценовая валидация**: <1% отклонение

### 📈 Система отчетов и аналитики
- **Интерактивные графики**: Chart.js визуализация
- **Кликабельная статистика**: Детализация по клику
- **Экспорт данных**: Excel, CSV форматы
- **Фильтрация**: По периоду, автомату, статусу

### 🤖 Telegram интеграция
- **Уведомления в реальном времени**: О завершении обработки
- **Критические алерты**: Мгновенные уведомления об ошибках
- **Ежедневные отчеты**: Автоматическая отправка статистики

## 🚀 Быстрый старт

### Развертывание на Railway (5 минут)

1. **Создайте проект в Railway**
   ```bash
   # Откройте https://railway.app
   # New Project → Deploy from GitHub repo
   # Выберите: jamshiddins/VHM24R
   ```

2. **Добавьте PostgreSQL**
   ```bash
   # New Service → Database → Add PostgreSQL
   ```

3. **Настройте переменные окружения**
   ```bash
   SECRET_KEY=vhm24r-production-secret-key-2025
   SCHEDULER_ENABLED=true
   DEBUG=false
   ```

4. **Готово!** 
   - Railway автоматически развернет приложение
   - Откройте URL и начните работу

### Локальная разработка

```bash
# Клонирование репозитория
git clone https://github.com/jamshiddins/VHM24R.git
cd VHM24R

# Создание виртуального окружения
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка переменных окружения
cp .env.example .env
# Отредактируйте .env файл

# Инициализация базы данных
python init_db.py

# Запуск приложения
python app.py
```

## 🏗️ Архитектура системы

### Модуль 1: Сверка заказов
```
Загрузка файлов → Автоопределение типа → Обработка данных → 
Сопоставление → Валидация → Отчеты
```

**Поддерживаемые источники:**
- Happy Workers (внешняя система)
- VendHub (внутренняя система)
- Fiscal Bills (фискальные чеки)
- Payment Gateways (Payme, Click, Uzum)

### Модуль 2: Управление рецептурой
```
Продукты → Ингредиенты → Рецепты → Закупки → 
Расчет расхода → Инвентаризация → Анализ отклонений
```

### Модуль 3: Финансовая сверка
```
Банковские выписки → Сверка платежных систем → 
Учет комиссий → Инкассация → Кассовые остатки
```

## 📊 База данных

### Основные таблицы
- **orders** - Центральная таблица заказов
- **products** - Справочник продуктов
- **ingredients** - Справочник ингредиентов
- **recipes** - Рецепты продуктов
- **bank_transactions** - Банковские операции
- **cash_collection** - Инкассация наличных

### Схема БД
Полная схема PostgreSQL находится в файле `schema_final.sql`

## 🌐 API Endpoints

### Основные маршруты
```
GET  /                    # Главная страница с статистикой
POST /upload              # Загрузка и обработка файлов
GET  /orders              # Список заказов с фильтрацией
GET  /database            # Просмотр базы данных
GET  /reports             # Система отчетов
GET  /health              # Health check
```

### API для данных
```
GET  /api/orders/details  # Детали заказов
GET  /api/orders/export   # Экспорт в Excel
GET  /api/reports/*       # API системы отчетов
```

## 🔧 Конфигурация

### Переменные окружения

#### Обязательные
```bash
DATABASE_URL=postgresql://...  # URL базы данных
SECRET_KEY=your-secret-key     # Секретный ключ Flask
```

#### Опциональные
```bash
# Telegram интеграция
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# DigitalOcean Spaces (для файлового хранилища)
DO_SPACES_KEY=your_spaces_key
DO_SPACES_SECRET=your_spaces_secret

# Планировщик задач
SCHEDULER_ENABLED=true

# Режим отладки
DEBUG=false
```

## 📁 Структура проекта

```
VHM24R/
├── 🚀 Основные файлы
│   ├── app.py                    # Главное Flask приложение
│   ├── models.py                 # Модели данных и БД
│   ├── railway_init.py           # Автоинициализация для Railway
│   └── Procfile                  # Конфигурация запуска
│
├── 🔄 Процессоры данных
│   ├── processors_updated.py     # Обработчики файлов
│   ├── file_detector_updated.py  # Детектор типов файлов
│   ├── ocr_processor.py          # OCR обработка
│   └── bank_parser.py            # Парсер банковских выписок
│
├── 🤖 Интеграции
│   ├── telegram_bot.py           # Telegram уведомления
│   ├── scheduler.py              # Планировщик задач
│   ├── storage.py                # Файловое хранилище
│   └── reports_api.py            # API отчетов
│
├── 🎨 Веб-интерфейс
│   ├── templates/                # HTML шаблоны
│   └── static/                   # CSS, JS, изображения
│
└── 📊 База данных
    ├── schema_final.sql          # Схема PostgreSQL
    ├── init_db.py               # Инициализация БД
    └── migrations/               # Миграции
```

## 🧪 Тестирование

### Запуск тестов
```bash
# Тестирование системы
python test_system.py

# Тестирование базы данных
python test_psycopg2_import.py

# Тестирование OCR
python test_pytesseract.py

# Проверка схемы БД
python check_database.py
```

### Тестовые данные
В папке `test_data/` находятся примеры файлов для тестирования всех поддерживаемых форматов.

## 📈 Производительность

- **Обработка файлов**: До 100,000 записей за 2 минуты
- **Память**: Оптимизировано для Railway (512MB-1GB)
- **Параллельность**: Асинхронная обработка файлов
- **Кэширование**: Результаты запросов и вычислений

## 🔐 Безопасность

- ✅ Валидация всех входных данных
- ✅ Защита от SQL инъекций
- ✅ Ограничение размера файлов (100MB)
- ✅ Автоматическая очистка временных файлов
- ✅ Обработка ошибок для всех операций

## 📚 Документация

- [Техническое задание](FINAL_SYSTEM_DEPLOYMENT_REPORT.md) - Полное описание системы
- [Быстрый деплой](QUICK_DEPLOY_GUIDE.md) - Инструкция по развертыванию
- [API документация](docs/API.md) - Описание всех endpoints
- [Схема БД](docs/DATABASE.md) - Структура базы данных

## 🤝 Участие в разработке

1. Форкните репозиторий
2. Создайте ветку для новой функции (`git checkout -b feature/amazing-feature`)
3. Зафиксируйте изменения (`git commit -m 'Add amazing feature'`)
4. Отправьте в ветку (`git push origin feature/amazing-feature`)
5. Откройте Pull Request

## 📝 Лицензия

Этот проект лицензирован под MIT License - см. файл [LICENSE](LICENSE) для деталей.

## 📞 Поддержка

- **GitHub Issues**: [Создать issue](https://github.com/jamshiddins/VHM24R/issues)
- **Email**: support@vhm24r.com
- **Telegram**: @vhm24r_support

## 🎉 Благодарности

- [Flask](https://flask.palletsprojects.com/) - веб-фреймворк
- [Bootstrap](https://getbootstrap.com/) - UI компоненты
- [Chart.js](https://www.chartjs.org/) - графики и диаграммы
- [Railway](https://railway.app/) - платформа для деплоя
- [PostgreSQL](https://www.postgresql.org/) - база данных

---

**VHM24R v1.0.0** - Готово к production использованию! 🚀

*Создано с ❤️ для автоматизации бизнес-процессов*
