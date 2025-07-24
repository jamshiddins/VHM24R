"""
Простой веб-интерфейс для просмотра базы данных SQLite
Запустите этот скрипт и откройте http://localhost:8080 в браузере
"""

import sqlite3
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import html

class DatabaseViewerHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query_params = parse_qs(parsed_path.query)
        
        if path == '/':
            self.serve_main_page()
        elif path == '/api/tables':
            self.serve_tables_list()
        elif path == '/api/table':
            table_name = query_params.get('name', [''])[0]
            limit = int(query_params.get('limit', ['100'])[0])
            offset = int(query_params.get('offset', ['0'])[0])
            self.serve_table_data(table_name, limit, offset)
        else:
            self.send_error(404)
    
    def serve_main_page(self):
        html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>VHM24R Database Viewer</title>
    <meta charset="utf-8">
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .container { max-width: 1200px; margin: 0 auto; }
        .table-list { margin-bottom: 20px; }
        .table-button { 
            display: inline-block; 
            margin: 5px; 
            padding: 10px 15px; 
            background: #007bff; 
            color: white; 
            text-decoration: none; 
            border-radius: 5px; 
            cursor: pointer;
            border: none;
        }
        .table-button:hover { background: #0056b3; }
        .table-data { margin-top: 20px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .pagination { margin: 20px 0; }
        .pagination button { margin: 0 5px; padding: 5px 10px; }
        .stats { background: #f8f9fa; padding: 15px; border-radius: 5px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>VHM24R Database Viewer</h1>
        
        <div class="stats" id="stats">
            <h3>Статистика базы данных</h3>
            <div id="stats-content">Загрузка...</div>
        </div>
        
        <div class="table-list">
            <h3>Таблицы:</h3>
            <div id="tables">Загрузка...</div>
        </div>
        
        <div class="table-data" id="table-data" style="display: none;">
            <h3 id="table-title"></h3>
            <div class="pagination" id="pagination"></div>
            <div id="table-content"></div>
        </div>
    </div>

    <script>
        let currentTable = '';
        let currentOffset = 0;
        const limit = 50;

        // Загружаем список таблиц
        fetch('/api/tables')
            .then(response => response.json())
            .then(data => {
                const tablesDiv = document.getElementById('tables');
                const statsDiv = document.getElementById('stats-content');
                
                // Показываем статистику
                let statsHtml = '';
                for (const table of data.tables) {
                    statsHtml += `<strong>${table.name}:</strong> ${table.count} записей<br>`;
                }
                statsDiv.innerHTML = statsHtml;
                
                // Показываем кнопки таблиц
                let buttonsHtml = '';
                for (const table of data.tables) {
                    buttonsHtml += `<button class="table-button" onclick="loadTable('${table.name}')">${table.name} (${table.count})</button>`;
                }
                tablesDiv.innerHTML = buttonsHtml;
            });

        function loadTable(tableName, offset = 0) {
            currentTable = tableName;
            currentOffset = offset;
            
            fetch(`/api/table?name=${tableName}&limit=${limit}&offset=${offset}`)
                .then(response => response.json())
                .then(data => {
                    document.getElementById('table-title').textContent = `Таблица: ${tableName}`;
                    document.getElementById('table-data').style.display = 'block';
                    
                    // Создаем таблицу
                    let tableHtml = '<table><thead><tr>';
                    for (const column of data.columns) {
                        tableHtml += `<th>${column}</th>`;
                    }
                    tableHtml += '</tr></thead><tbody>';
                    
                    for (const row of data.rows) {
                        tableHtml += '<tr>';
                        for (const cell of row) {
                            const cellValue = cell === null ? '<em>NULL</em>' : String(cell);
                            tableHtml += `<td>${cellValue}</td>`;
                        }
                        tableHtml += '</tr>';
                    }
                    tableHtml += '</tbody></table>';
                    
                    document.getElementById('table-content').innerHTML = tableHtml;
                    
                    // Создаем пагинацию
                    let paginationHtml = '';
                    if (offset > 0) {
                        paginationHtml += `<button onclick="loadTable('${tableName}', ${Math.max(0, offset - limit)})">← Предыдущие</button>`;
                    }
                    paginationHtml += `<span>Записи ${offset + 1}-${offset + data.rows.length} из ${data.total}</span>`;
                    if (offset + limit < data.total) {
                        paginationHtml += `<button onclick="loadTable('${tableName}', ${offset + limit})">Следующие →</button>`;
                    }
                    
                    document.getElementById('pagination').innerHTML = paginationHtml;
                });
        }
    </script>
</body>
</html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html_content.encode('utf-8'))
    
    def serve_tables_list(self):
        try:
            conn = sqlite3.connect('orders.db')
            cursor = conn.cursor()
            
            # Получаем список таблиц
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
            tables = cursor.fetchall()
            
            # Получаем количество записей в каждой таблице
            table_info = []
            for table in tables:
                table_name = table[0]
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
                    count = cursor.fetchone()[0]
                    table_info.append({'name': table_name, 'count': count})
                except:
                    table_info.append({'name': table_name, 'count': 0})
            
            conn.close()
            
            response_data = {'tables': table_info}
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def serve_table_data(self, table_name, limit, offset):
        try:
            conn = sqlite3.connect('orders.db')
            cursor = conn.cursor()
            
            # Получаем общее количество записей
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            total = cursor.fetchone()[0]
            
            # Получаем структуру таблицы
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns_info = cursor.fetchall()
            columns = [col[1] for col in columns_info]
            
            # Получаем данные с пагинацией
            cursor.execute(f'SELECT * FROM {table_name} LIMIT {limit} OFFSET {offset}')
            rows = cursor.fetchall()
            
            conn.close()
            
            response_data = {
                'columns': columns,
                'rows': rows,
                'total': total,
                'limit': limit,
                'offset': offset
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json; charset=utf-8')
            self.end_headers()
            self.wfile.write(json.dumps(response_data, ensure_ascii=False, default=str).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))

if __name__ == '__main__':
    server = HTTPServer(('localhost', 8080), DatabaseViewerHandler)
    print("Database viewer запущен на http://localhost:8080")
    print("Нажмите Ctrl+C для остановки")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nСервер остановлен")
        server.shutdown()
