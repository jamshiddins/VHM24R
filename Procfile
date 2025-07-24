# VHM24R - Railway Procfile для Production 24/7
# Определяет как запускать приложение на Railway

# Основной веб-процесс с Gunicorn и автоинициализацией
web: python railway_init.py && gunicorn --bind 0.0.0.0:$PORT --workers ${WEB_CONCURRENCY:-4} --timeout ${WORKER_TIMEOUT:-300} --max-requests ${MAX_REQUESTS:-2000} --preload --access-logfile - --error-logfile - app:app

# Альтернативный запуск для разработки (закомментирован)
# web: python app.py

# Worker процесс для фоновых задач (если нужен отдельный процесс)
# worker: python -c "from scheduler import vhm_scheduler; import time; time.sleep(86400)"

# Инициализация базы данных (автоматически выполняется в web процессе)
# release: python railway_init.py
