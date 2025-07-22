from flask import Flask, render_template, request, jsonify
import os
from werkzeug.utils import secure_filename
from models import Database
from file_detector import FileTypeDetector
from processors import OrderProcessor
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# Создаем папку uploads если её нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = Database()
detector = FileTypeDetector()
processor = OrderProcessor(db)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_files():
    if 'files' not in request.files:
        return jsonify({'error': 'No files provided'}), 400
    
    files = request.files.getlist('files')
    session_id = db.create_session()
    results = []
    
    for file in files:
        if file.filename == '':
            continue
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Определяем тип файла
        file_type = detector.detect_type(filepath)
        
        # Обрабатываем файл
        processed = processor.process_file(filepath, file_type)
        
        results.append({
            'filename': filename,
            'type': file_type,
            'processed': processed
        })
    
    # Запускаем сопоставление
    stats = processor.run_matching()
    
    return render_template('report.html', 
                         results=results, 
                         stats=stats,
                         session_id=session_id)

@app.route('/api/orders/details')
def get_order_details():
    filter_type = request.args.get('filter', 'matched')
    limit = int(request.args.get('limit', 100))
    
    orders = db.get_orders_by_filter(filter_type, limit)
    
    return jsonify({
        'orders': orders,
        'count': len(orders),
        'filter': filter_type
    })

@app.route('/api/orders/export')
def export_orders():
    filter_type = request.args.get('filter', 'all')
    format_type = request.args.get('format', 'csv')
    
    orders = db.get_orders_by_filter(filter_type, 10000)
    
    if format_type == 'csv':
        # Простой CSV экспорт
        import csv
        import io
        
        output = io.StringIO()
        if orders:
            writer = csv.DictWriter(output, fieldnames=orders[0].keys())
            writer.writeheader()
            writer.writerows(orders)
        
        return output.getvalue(), 200, {
            'Content-Type': 'text/csv',
            'Content-Disposition': f'attachment; filename=orders_{filter_type}.csv'
        }
    
    return jsonify(orders)

if __name__ == '__main__':
    app.run(debug=True)