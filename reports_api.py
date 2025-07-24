"""
API для работы с системой отчетов по типам
"""

from flask import Blueprint, request, jsonify, send_file
from reports_processor import ReportsProcessor
import sqlite3
import os
from datetime import datetime
import tempfile

# Создаем Blueprint для API отчетов
reports_bp = Blueprint('reports_api', __name__, url_prefix='/api/reports')

def get_db_connection():
    """Получение подключения к базе данных"""
    db_path = os.environ.get('DATABASE_URL', 'orders.db')
    if db_path.startswith('sqlite:///'):
        db_path = db_path[10:]
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@reports_bp.route('/statistics', methods=['GET'])
def get_statistics():
    """Получение статистики по всем отчетам"""
    try:
        db = get_db_connection()
        processor = ReportsProcessor(db)
        
        stats = processor.get_report_statistics()
        
        db.close()
        
        return jsonify({
            'success': True,
            'total': dict(stats['total']),
            'by_type': [dict(row) for row in stats['by_type']]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/data/<report_type>', methods=['GET'])
def get_report_data(report_type):
    """Получение данных отчета по типу"""
    try:
        # Получаем фильтры из параметров запроса
        filters = {}
        
        if request.args.get('date_from'):
            filters['date_from'] = request.args.get('date_from')
        
        if request.args.get('date_to'):
            filters['date_to'] = request.args.get('date_to')
        
        if request.args.get('file_name'):
            filters['file_name'] = request.args.get('file_name')
        
        # Пагинация
        limit = int(request.args.get('limit', 50))
        offset = int(request.args.get('offset', 0))
        
        filters['limit'] = limit
        
        db = get_db_connection()
        processor = ReportsProcessor(db)
        
        # Получаем данные
        data = processor.get_report_data(report_type, filters)
        
        # Получаем общее количество для пагинации
        total_count = len(processor.get_report_data(report_type, {
            k: v for k, v in filters.items() if k != 'limit'
        }))
        
        # Применяем offset
        if offset > 0:
            data = data[offset:]
        
        db.close()
        
        return jsonify({
            'success': True,
            'data': [dict(row) for row in data],
            'total': total_count,
            'limit': limit,
            'offset': offset
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/export/<report_type>', methods=['GET'])
def export_report(report_type):
    """Экспорт данных отчета"""
    try:
        # Получаем фильтры
        filters = {}
        
        if request.args.get('date_from'):
            filters['date_from'] = request.args.get('date_from')
        
        if request.args.get('date_to'):
            filters['date_to'] = request.args.get('date_to')
        
        if request.args.get('file_name'):
            filters['file_name'] = request.args.get('file_name')
        
        format_type = request.args.get('format', 'excel')
        
        db = get_db_connection()
        processor = ReportsProcessor(db)
        
        # Экспортируем данные
        file_path = processor.export_report_data(report_type, filters, format_type)
        
        db.close()
        
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'Нет данных для экспорта'
            }), 404
        
        # Определяем MIME тип
        if format_type == 'excel':
            mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        else:
            mimetype = 'text/csv'
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=os.path.basename(file_path),
            mimetype=mimetype
        )
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/recent', methods=['GET'])
def get_recent_uploads():
    """Получение последних загрузок"""
    try:
        limit = int(request.args.get('limit', 20))
        
        db = get_db_connection()
        processor = ReportsProcessor(db)
        
        recent = processor.get_recent_uploads(limit)
        
        db.close()
        
        return jsonify({
            'success': True,
            'data': [dict(row) for row in recent]
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/process', methods=['POST'])
def process_uploaded_file():
    """Обработка загруженного файла"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Файл не найден'
            }), 400
        
        file = request.files['file']
        file_type = request.form.get('file_type')
        
        if not file or file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Файл не выбран'
            }), 400
        
        if not file_type:
            return jsonify({
                'success': False,
                'error': 'Тип файла не указан'
            }), 400
        
        # Сохраняем файл во временную папку
        temp_dir = tempfile.mkdtemp()
        filename = file.filename or 'temp_file'
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        try:
            db = get_db_connection()
            processor = ReportsProcessor(db)
            
            # Обрабатываем файл
            processed_count = processor.process_file(file_path, file_type, file.filename)
            
            db.close()
            
            return jsonify({
                'success': True,
                'processed_count': processed_count,
                'message': f'Обработано {processed_count} записей'
            })
            
        finally:
            # Удаляем временный файл
            if os.path.exists(file_path):
                os.remove(file_path)
            os.rmdir(temp_dir)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/file-types', methods=['GET'])
def get_supported_file_types():
    """Получение списка поддерживаемых типов файлов"""
    try:
        file_types = {
            'happy_workers': {
                'name': 'Happy Workers',
                'description': 'Отчеты из системы Happy Workers',
                'icon': 'file-earmark-check',
                'color': 'primary'
            },
            'vendhub': {
                'name': 'VendHub',
                'description': 'Отчеты из системы VendHub',
                'icon': 'file-earmark-code',
                'color': 'success'
            },
            'fiscal_bills': {
                'name': 'Фискальные чеки',
                'description': 'Данные фискальных чеков',
                'icon': 'receipt',
                'color': 'warning'
            },
            'payme': {
                'name': 'Payme',
                'description': 'Отчеты платежной системы Payme',
                'icon': 'credit-card',
                'color': 'info'
            },
            'click': {
                'name': 'Click',
                'description': 'Отчеты платежной системы Click',
                'icon': 'credit-card-2-front',
                'color': 'secondary'
            },
            'uzum': {
                'name': 'Uzum',
                'description': 'Отчеты платежной системы Uzum',
                'icon': 'credit-card-2-back',
                'color': 'dark'
            },
            'bank_statement': {
                'name': 'Банковские выписки',
                'description': 'Банковские выписки и операции',
                'icon': 'bank',
                'color': 'danger'
            }
        }
        
        return jsonify({
            'success': True,
            'file_types': file_types
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/validate-file', methods=['POST'])
def validate_file():
    """Валидация файла перед обработкой"""
    try:
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'Файл не найден'
            }), 400
        
        file = request.files['file']
        
        if not file or file.filename == '':
            return jsonify({
                'success': False,
                'error': 'Файл не выбран'
            }), 400
        
        # Проверяем расширение файла
        allowed_extensions = ['.csv', '.xlsx', '.xls']
        filename = file.filename or 'temp_file'
        file_ext = os.path.splitext(filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False,
                'error': f'Неподдерживаемый формат файла. Разрешены: {", ".join(allowed_extensions)}'
            }), 400
        
        # Проверяем размер файла (максимум 100 МБ)
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        max_size = 100 * 1024 * 1024  # 100 МБ
        if file_size > max_size:
            return jsonify({
                'success': False,
                'error': f'Файл слишком большой. Максимальный размер: {max_size // (1024*1024)} МБ'
            }), 400
        
        # Пытаемся определить тип файла по содержимому
        temp_dir = tempfile.mkdtemp()
        file_path = os.path.join(temp_dir, filename)
        file.save(file_path)
        
        try:
            from file_detector import FileTypeDetector
            detector = FileTypeDetector()
            detected_type = detector.detect_type(file_path)
            
            return jsonify({
                'success': True,
                'file_size': file_size,
                'detected_type': detected_type,
                'message': 'Файл прошел валидацию'
            })
            
        finally:
            # Удаляем временный файл
            if os.path.exists(file_path):
                os.remove(file_path)
            os.rmdir(temp_dir)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/cleanup', methods=['POST'])
def cleanup_old_files():
    """Очистка старых файлов и записей"""
    try:
        days_old = int(request.json.get('days_old', 30))
        
        db = get_db_connection()
        cursor = db.cursor()
        
        # Удаляем старые записи из uploaded_files
        cursor.execute("""
            DELETE FROM uploaded_files 
            WHERE upload_date < datetime('now', '-{} days')
        """.format(days_old))
        
        deleted_files = cursor.rowcount
        
        # Удаляем старые записи из отчетных таблиц
        report_tables = [
            'reports_happy_workers',
            'reports_vendhub', 
            'reports_fiscal_bills',
            'reports_payme',
            'reports_click',
            'reports_uzum',
            'reports_bank_statements'
        ]
        
        deleted_records = 0
        for table in report_tables:
            try:
                cursor.execute(f"""
                    DELETE FROM {table} 
                    WHERE upload_date < datetime('now', '-{days_old} days')
                """)
                deleted_records += cursor.rowcount
            except sqlite3.OperationalError:
                # Таблица может не существовать
                continue
        
        db.commit()
        db.close()
        
        # Очищаем папку uploads от старых файлов
        uploads_dir = 'uploads'
        deleted_physical_files = 0
        
        if os.path.exists(uploads_dir):
            cutoff_time = datetime.now().timestamp() - (days_old * 24 * 60 * 60)
            
            for filename in os.listdir(uploads_dir):
                file_path = os.path.join(uploads_dir, filename)
                if os.path.isfile(file_path):
                    if os.path.getmtime(file_path) < cutoff_time:
                        try:
                            os.remove(file_path)
                            deleted_physical_files += 1
                        except OSError:
                            pass
        
        return jsonify({
            'success': True,
            'deleted_files': deleted_files,
            'deleted_records': deleted_records,
            'deleted_physical_files': deleted_physical_files,
            'message': f'Очистка завершена. Удалено файлов: {deleted_files}, записей: {deleted_records}'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@reports_bp.route('/health', methods=['GET'])
def health_check():
    """Проверка состояния системы отчетов"""
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        # Проверяем доступность основных таблиц
        tables_status = {}
        required_tables = [
            'uploaded_files',
            'reports_happy_workers',
            'reports_vendhub',
            'reports_fiscal_bills',
            'reports_payme',
            'reports_click',
            'reports_uzum'
        ]
        
        for table in required_tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                tables_status[table] = {
                    'exists': True,
                    'records': count
                }
            except sqlite3.OperationalError:
                tables_status[table] = {
                    'exists': False,
                    'records': 0
                }
        
        # Проверяем доступность папки uploads
        uploads_dir = 'uploads'
        uploads_status = {
            'exists': os.path.exists(uploads_dir),
            'writable': os.access(uploads_dir, os.W_OK) if os.path.exists(uploads_dir) else False
        }
        
        db.close()
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'tables': tables_status,
            'uploads_directory': uploads_status,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500
