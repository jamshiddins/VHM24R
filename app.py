"""
VHM24R - Основное Flask приложение
Интеллектуальная система сверки заказов, платежей и фискализации
"""

import os
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
import pandas as pd

# Импорт модулей проекта
from models import get_database
from processors_updated import OrderProcessor, RecipeProcessor, FinanceProcessor
from file_detector_updated import AdvancedFileTypeDetector
from storage import init_storage
from telegram_bot import init_telegram
from scheduler import init_scheduler
from reports_api import reports_bp

# Инициализация Flask приложения
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'vhm24r-dev-key-change-in-production')

# Конфигурация
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads'

# Глобальные переменные для компонентов системы
db = None
order_processor = None
recipe_processor = None
finance_processor = None
file_detector = None
file_manager = None
telegram_notifier = None
scheduler = None

def init_app():
    """Инициализация всех компонентов приложения"""
    global db, order_processor, recipe_processor, finance_processor
    global file_detector, file_manager, telegram_notifier, scheduler
    
    try:
        # Инициализация базы данных
        db = get_database()
        print("Database initialized")
        
        # Инициализация процессоров
        order_processor = OrderProcessor(db)
        recipe_processor = RecipeProcessor(db)
        finance_processor = FinanceProcessor(db)
        print("Processors initialized")
        
        # Инициализация детектора файлов
        file_detector = AdvancedFileTypeDetector()
        print("File detector initialized")
        
        # Инициализация файлового менеджера
        file_manager = init_storage(db, app.config['UPLOAD_FOLDER'])
        print("File manager initialized")
        
        # Инициализация Telegram
        telegram_notifier, _ = init_telegram(db)
        print("Telegram initialized")
        
        # Инициализация планировщика (только в production)
        if not app.debug:
            scheduler = init_scheduler(db, order_processor, telegram_notifier, file_manager)
            print("Scheduler initialized")
        
        print("VHM24R application initialized successfully")
        
    except Exception as e:
        print(f"Error initializing application: {e}")
        raise

# Инициализация при запуске
init_app()

# Регистрация Blueprint для API отчетов
app.register_blueprint(reports_bp)

@app.route('/')
def index():
    """Главная страница с общей статистикой"""
    try:
        # Получаем общую статистику
        stats = db.get_processing_stats()
        
        # Получаем последние заказы
        recent_orders = db.get_orders_with_filters(limit=10)
        
        # Статистика по типам ошибок
        error_stats = {
            'OK': stats.get('OK', 0),
            'NO_MATCH_IN_REPORT': stats.get('NO_MATCH_IN_REPORT', 0),
            'NO_PAYMENT_FOUND': stats.get('NO_PAYMENT_FOUND', 0),
            'FISCAL_MISSING': stats.get('FISCAL_MISSING', 0),
            'UNPROCESSED': stats.get('UNPROCESSED', 0)
        }
        
        # Процент успешности
        total_processed = stats.get('total', 0) - error_stats['UNPROCESSED']
        success_rate = (error_stats['OK'] / total_processed * 100) if total_processed > 0 else 0
        
        return render_template('index.html', 
                             stats=stats,
                             error_stats=error_stats,
                             recent_orders=recent_orders,
                             success_rate=success_rate)
    
    except Exception as e:
        print(f"Error in index route: {e}")
        return render_template('index.html', 
                             stats={'total': 0},
                             error_stats={},
                             recent_orders=[],
                             success_rate=0)

@app.route('/upload', methods=['GET', 'POST'])
def upload_files():
    """Загрузка и обработка файлов"""
    if request.method == 'GET':
        return render_template('upload.html')
    
    try:
        # Генерируем ID сессии
        session_id = str(uuid.uuid4())
        
        processing_results = []
        
        # Обрабатываем каждый загруженный файл
        for file_key in request.files:
            file = request.files[file_key]
            
            if file and file.filename:
                try:
                    # Создаем временный файл с уникальным именем
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    temp_filename = f"{timestamp}_{secure_filename(file.filename)}"
                    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
                    
                    # Сохраняем файл
                    file.save(temp_path)
                    
                    # Определяем тип файла
                    file_type = file_detector.detect_type(temp_path)
                    
                    # Обрабатываем файл если тип определен
                    if file_type != 'unknown':
                        try:
                            processed_count = order_processor.process_file(temp_path, file_type)
                            
                            processing_results.append({
                                'filename': file.filename,
                                'file_type': file_type,
                                'processed_count': processed_count,
                                'status': 'success'
                            })
                        except Exception as process_error:
                            print(f"Error processing file {file.filename}: {process_error}")
                            processing_results.append({
                                'filename': file.filename,
                                'file_type': file_type,
                                'processed_count': 0,
                                'status': 'error',
                                'error': str(process_error)
                            })
                    else:
                        processing_results.append({
                            'filename': file.filename,
                            'file_type': 'unknown',
                            'processed_count': 0,
                            'status': 'unknown_type'
                        })
                    
                    # Удаляем временный файл после обработки
                    try:
                        if os.path.exists(temp_path):
                            os.remove(temp_path)
                    except Exception as cleanup_error:
                        print(f"Warning: Could not remove temp file {temp_path}: {cleanup_error}")
                        
                except Exception as file_error:
                    print(f"Error handling file {file.filename}: {file_error}")
                    processing_results.append({
                        'filename': file.filename,
                        'file_type': 'error',
                        'processed_count': 0,
                        'status': 'error',
                        'error': str(file_error)
                    })
        
        # Запускаем сверку если есть обработанные файлы
        if any(r['status'] == 'success' for r in processing_results):
            matching_stats = order_processor.run_matching()
            
            # Отправляем уведомление о завершении
            if telegram_notifier:
                import asyncio
                asyncio.run(telegram_notifier.send_processing_complete(
                    session_id=session_id,
                    stats=matching_stats,
                    files_count=len([r for r in processing_results if r['status'] == 'success'])
                ))
            
            # Сохраняем результаты в DigitalOcean
            if file_manager:
                file_manager.backup_processing_results(session_id, {
                    'processing_results': processing_results,
                    'matching_stats': matching_stats,
                    'session_id': session_id
                })
        else:
            matching_stats = {'total': 0}
        
        return render_template('upload_results.html',
                             session_id=session_id,
                             processing_results=processing_results,
                             matching_stats=matching_stats)
    
    except Exception as e:
        print(f"Error in upload route: {e}")
        flash(f'Ошибка при обработке файлов: {str(e)}', 'error')
        return redirect(url_for('upload_files'))

@app.route('/orders')
def orders_list():
    """Список заказов с фильтрацией"""
    try:
        # Получаем параметры фильтрации
        filters = {}
        
        if request.args.get('error_type'):
            filters['error_type'] = request.args.get('error_type')
        
        if request.args.get('machine_code'):
            filters['machine_code'] = request.args.get('machine_code')
        
        if request.args.get('date_from'):
            filters['date_from'] = request.args.get('date_from')
        
        if request.args.get('date_to'):
            filters['date_to'] = request.args.get('date_to')
        
        # Получаем заказы
        orders = db.get_orders_with_filters(filters, limit=500)
        
        # Получаем уникальные коды автоматов для фильтра
        machine_codes = db.execute_query("""
            SELECT DISTINCT machine_code 
            FROM orders 
            WHERE machine_code IS NOT NULL 
            ORDER BY machine_code
        """)
        
        return render_template('orders.html',
                             orders=orders,
                             machine_codes=[m['machine_code'] for m in machine_codes],
                             current_filters=filters)
    
    except Exception as e:
        print(f"Error in orders route: {e}")
        return render_template('orders.html', orders=[], machine_codes=[], current_filters={})

@app.route('/api/orders/export')
def export_orders():
    """Экспорт заказов в Excel"""
    try:
        # Получаем параметры фильтрации
        filters = {}
        
        if request.args.get('error_type'):
            filters['error_type'] = request.args.get('error_type')
        
        if request.args.get('machine_code'):
            filters['machine_code'] = request.args.get('machine_code')
        
        if request.args.get('date_from'):
            filters['date_from'] = request.args.get('date_from')
        
        if request.args.get('date_to'):
            filters['date_to'] = request.args.get('date_to')
        
        # Получаем все заказы без лимита
        orders = db.get_orders_with_filters(filters, limit=10000)
        
        # Создаем DataFrame
        df = pd.DataFrame(orders)
        
        # Форматируем данные
        if not df.empty:
            if 'creation_time' in df.columns:
                df['creation_time'] = pd.to_datetime(df['creation_time']).dt.strftime('%Y-%m-%d %H:%M:%S')
        
        # Сохраняем в Excel
        filename = f"orders_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        df.to_excel(filepath, index=False, engine='openpyxl')
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        print(f"Error in export route: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/recipes')
def recipes_index():
    """Главная страница рецептур"""
    try:
        stats = recipe_processor.get_recipe_stats()
        return render_template('recipes/index.html', stats=stats)
    except Exception as e:
        print(f"Error in recipes route: {e}")
        return render_template('recipes/index.html', stats={})

@app.route('/recipes/products')
def recipes_products():
    """Управление продуктами"""
    try:
        products = recipe_processor.get_products()
        return render_template('recipes/products.html', products=products)
    except Exception as e:
        print(f"Error in products route: {e}")
        return render_template('recipes/products.html', products=[])

@app.route('/recipes/ingredients')
def recipes_ingredients():
    """Управление ингредиентами"""
    try:
        ingredients = recipe_processor.get_ingredients()
        return render_template('recipes/ingredients.html', ingredients=ingredients)
    except Exception as e:
        print(f"Error in ingredients route: {e}")
        return render_template('recipes/ingredients.html', ingredients=[])

@app.route('/finance')
def finance_index():
    """Главная страница финансов"""
    try:
        stats = finance_processor.get_finance_stats()
        cash_balances = finance_processor.get_cash_balances()
        return render_template('finance/index.html', stats=stats, cash_balances=cash_balances)
    except Exception as e:
        print(f"Error in finance route: {e}")
        return render_template('finance/index.html', stats={}, cash_balances=[])

@app.route('/finance/cash_collection')
def finance_cash_collection():
    """Управление инкассацией"""
    try:
        machines_status = finance_processor.get_machines_cash_status()
        recent_collections = finance_processor.get_recent_collections()
        return render_template('finance/cash_collection.html', 
                             machines_status=machines_status,
                             recent_collections=recent_collections)
    except Exception as e:
        print(f"Error in cash collection route: {e}")
        return render_template('finance/cash_collection.html', 
                             machines_status=[], recent_collections=[])

@app.route('/api/orders/details')
def api_orders_details():
    """API для получения деталей заказов"""
    try:
        filters = {}
        
        if request.args.get('filter'):
            filters['error_type'] = request.args.get('filter')
        
        orders = db.get_orders_with_filters(filters, limit=100)
        
        return jsonify({
            'success': True,
            'orders': orders,
            'count': len(orders)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/health')
def health_check():
    """Health check для мониторинга"""
    try:
        # Проверяем подключение к БД
        db.execute_query("SELECT 1")
        
        # Получаем базовую статистику
        stats = db.get_processing_stats()
        
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database': 'connected',
            'total_orders': stats.get('total', 0),
            'version': '1.0.0'
        })
    
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found_error(error):
    """Обработка ошибки 404"""
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Обработка ошибки 500"""
    return render_template('errors/500.html'), 500

@app.errorhandler(413)
def too_large(error):
    """Обработка ошибки превышения размера файла"""
    flash('Файл слишком большой. Максимальный размер: 100MB', 'error')
    return redirect(url_for('upload_files'))

# Контекстные процессоры для шаблонов
@app.context_processor
def inject_current_time():
    """Добавляем текущее время в контекст шаблонов"""
    return {'current_time': datetime.now()}

@app.context_processor
def inject_app_info():
    """Добавляем информацию о приложении"""
    return {
        'app_name': 'VHM24R',
        'app_version': '1.0.0',
        'app_description': 'Интеллектуальная система сверки заказов'
    }

@app.route('/database')
def database_viewer():
    """Страница просмотра базы данных"""
    return render_template('database.html')

@app.route('/reports')
def reports_viewer():
    """Страница системы отчетов"""
    return render_template('reports_viewer.html')

@app.route('/api/database/orders')
def api_database_orders():
    """API для получения данных заказов с фильтрацией"""
    try:
        filters = {}
        
        # Фильтр по периоду
        period = request.args.get('period', 'all')
        if period != 'all':
            from datetime import datetime, timedelta
            now = datetime.now()
            
            if period == 'today':
                filters['date_from'] = now.strftime('%Y-%m-%d')
                filters['date_to'] = now.strftime('%Y-%m-%d')
            elif period == 'week':
                week_ago = now - timedelta(days=7)
                filters['date_from'] = week_ago.strftime('%Y-%m-%d')
                filters['date_to'] = now.strftime('%Y-%m-%d')
            elif period == 'month':
                month_ago = now - timedelta(days=30)
                filters['date_from'] = month_ago.strftime('%Y-%m-%d')
                filters['date_to'] = now.strftime('%Y-%m-%d')
        
        # Фильтр по автомату
        machine = request.args.get('machine', 'all')
        if machine != 'all':
            filters['machine_code'] = machine
        
        # Фильтр по статусу
        status = request.args.get('status', 'all')
        if status != 'all':
            filters['error_type'] = status
        
        # Получаем данные
        orders = db.get_orders_with_filters(filters, limit=1000)
        stats = db.get_processing_stats()
        
        return jsonify({
            'success': True,
            'orders': orders,
            'stats': stats
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/machines')
def api_machines():
    """API для получения списка автоматов"""
    try:
        machines = db.execute_query("""
            SELECT DISTINCT machine_code 
            FROM orders 
            WHERE machine_code IS NOT NULL 
            ORDER BY machine_code
        """)
        
        return jsonify([{'machine_code': m['machine_code']} for m in machines])
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Запуск в режиме разработки
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)
