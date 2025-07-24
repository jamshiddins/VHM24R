# VHM24R - Railway Procfile
# Определяет как запускать приложение на Railway

# Основной веб-процесс с Gunicorn
web: gunicorn --bind 0.0.0.0:$PORT --workers $WEB_CONCURRENCY --timeout $WORKER_TIMEOUT --max-requests $MAX_REQUESTS app:app

# Альтернативный запуск для разработки (закомментирован)
# web: python app.py

# Worker процесс для фоновых задач (если нужен отдельный процесс)
# worker: python -c "from scheduler import vhm_scheduler; import time; time.sleep(86400)"

# Инициализация базы данных (запускается один раз)
# release: python init_db.py
