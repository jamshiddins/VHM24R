#!/usr/bin/env python3
"""
Создание страницы просмотра базы данных
"""

import os
from flask import Flask, render_template, request, jsonify
from models import get_database

def create_database_viewer_page():
    """Создает HTML страницу для просмотра базы данных"""
    
    html_content = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>База данных - ODUS-RFM</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        body { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; }
        .card { box-shadow: 0 10px 30px rgba(0,0,0,0.1); border: none; }
        .table-container { max-height: 600px; overflow-y: auto; }
        .btn-filter { margin: 2px; }
        .stats-card { background: linear-gradient(45deg, #f093fb 0%, #f5576c 100%); color: white; }
        .column-toggle { font-size: 0.8rem; }
    </style>
</head>
<body>
    <div class="container-fluid py-4">
        <div class="row">
            <div class="col-12">
                <div class="card">
                    <div class="card-header bg-primary text-white">
                        <h4 class="mb-0">
                            <i class="fas fa-database me-2"></i>
                            База данных заказов
                        </h4>
                    </div>
                    <div class="card-body">
                        <!-- Статистика -->
                        <div class="row mb-4">
                            <div class="col-md-3">
                                <div class="card stats-card">
                                    <div class="card-body text-center">
                                        <h3 id="totalOrders">0</h3>
                                        <p class="mb-0">Всего заказов</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-success text-white">
                                    <div class="card-body text-center">
                                        <h3 id="okOrders">0</h3>
                                        <p class="mb-0">Успешно обработано</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-warning text-white">
                                    <div class="card-body text-center">
                                        <h3 id="errorOrders">0</h3>
                                        <p class="mb-0">С ошибками</p>
                                    </div>
                                </div>
                            </div>
                            <div class="col-md-3">
                                <div class="card bg-info text-white">
                                    <div class="card-body text-center">
                                        <h3 id="successRate">0%</h3>
                                        <p class="mb-0">Процент успеха</p>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Фильтры -->
                        <div class="row mb-3">
                            <div class="col-md-3">
                                <label>Период:</label>
                                <select id="periodFilter" class="form-select">
                                    <option value="all">Все время</option>
                                    <option value="today">Сегодня</option>
                                    <option value="week">Неделя</option>
                                    <option value="month">Месяц</option>
                                </select>
                            </div>
                            <div class="col-md-3">
                                <label>Автомат:</label>
                                <select id="machineFilter" class="form-select">
                                    <option value="all">Все автоматы</option>
                                </select>
                            </div>
                            <div class="col-md-3">
                                <label>Статус:</label>
                                <select id="statusFilter" class="form-select">
                                    <option value="all">Все статусы</option>
                                    <option value="OK">OK</option>
                                    <option value="NO_MATCH_IN_REPORT">Нет в отчете</option>
                                    <option value="NO_PAYMENT_FOUND">Нет платежа</option>
                                    <option value="FISCAL_MISSING">Нет фискального</option>
                                </select>
                            </div>
                            <div class="col-md-3">
                                <label>&nbsp;</label>
                                <button class="btn btn-primary d-block w-100" onclick="loadData()">
                                    <i class="fas fa-search me-1"></i>Применить фильтры
                                </button>
                            </div>
                        </div>

                        <!-- Управление колонками -->
                        <div class="mb-3">
                            <label class="form-label">Показать колонки:</label>
                            <div id="columnToggles" class="d-flex flex-wrap gap-2">
                                <!-- Динамически заполняется -->
                            </div>
                        </div>

                        <!-- Таблица данных -->
                        <div class="table-container">
                            <table class="table table-striped table-hover" id="ordersTable">
                                <thead class="table-dark sticky-top">
                                    <tr id="tableHeader">
                                        <!-- Динамически заполняется -->
                                    </tr>
                                </thead>
                                <tbody id="tableBody">
                                    <!-- Динамически заполняется -->
                                </tbody>
                            </table>
                        </div>

                        <!-- Пагинация -->
                        <div class="d-flex justify-content-between align-items-center mt-3">
                            <div>
                                <span id="recordsInfo">Показано 0 из 0 записей</span>
                            </div>
                            <div>
                                <button class="btn btn-outline-primary" onclick="exportData()">
                                    <i class="fas fa-download me-1"></i>Экспорт Excel
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let currentData = [];
        let visibleColumns = new Set();

        // Инициализация
        document.addEventListener('DOMContentLoaded', function() {
            loadMachines();
            loadData();
        });

        // Загрузка списка автоматов
        async function loadMachines() {
            try {
                const response = await fetch('/api/machines');
                const machines = await response.json();
                
                const select = document.getElementById('machineFilter');
                machines.forEach(machine => {
                    const option = document.createElement('option');
                    option.value = machine.machine_code;
                    option.textContent = machine.machine_code;
                    select.appendChild(option);
                });
            } catch (error) {
                console.error('Ошибка загрузки автоматов:', error);
            }
        }

        // Загрузка данных
        async function loadData() {
            try {
                const filters = {
                    period: document.getElementById('periodFilter').value,
                    machine: document.getElementById('machineFilter').value,
                    status: document.getElementById('statusFilter').value
                };

                const params = new URLSearchParams();
                Object.keys(filters).forEach(key => {
                    if (filters[key] !== 'all') {
                        params.append(key, filters[key]);
                    }
                });

                const response = await fetch(`/api/database/orders?${params}`);
                const data = await response.json();
                
                currentData = data.orders;
                updateStats(data.stats);
                updateTable(data.orders);
                
            } catch (error) {
                console.error('Ошибка загрузки данных:', error);
            }
        }

        // Обновление статистики
        function updateStats(stats) {
            document.getElementById('totalOrders').textContent = stats.total || 0;
            document.getElementById('okOrders').textContent = stats.OK || 0;
            document.getElementById('errorOrders').textContent = (stats.total - stats.OK) || 0;
            
            const successRate = stats.total > 0 ? Math.round((stats.OK / stats.total) * 100) : 0;
            document.getElementById('successRate').textContent = successRate + '%';
        }

        // Обновление таблицы
        function updateTable(orders) {
            if (orders.length === 0) {
                document.getElementById('tableBody').innerHTML = 
                    '<tr><td colspan="100%" class="text-center">Нет данных</td></tr>';
                return;
            }

            // Определяем колонки
            const columns = Object.keys(orders[0]);
            
            // Создаем переключатели колонок
            createColumnToggles(columns);
            
            // Создаем заголовок таблицы
            updateTableHeader(columns);
            
            // Заполняем данные
            const tbody = document.getElementById('tableBody');
            tbody.innerHTML = '';
            
            orders.forEach(order => {
                const row = document.createElement('tr');
                columns.forEach(column => {
                    if (visibleColumns.has(column)) {
                        const cell = document.createElement('td');
                        let value = order[column];
                        
                        // Форматирование значений
                        if (column === 'error_type') {
                            cell.innerHTML = `<span class="badge bg-${getStatusColor(value)}">${value || 'OK'}</span>`;
                        } else if (column === 'order_price' && value) {
                            cell.textContent = parseFloat(value).toLocaleString('ru-RU') + ' сум';
                        } else if (column.includes('time') && value) {
                            cell.textContent = new Date(value).toLocaleString('ru-RU');
                        } else {
                            cell.textContent = value || '-';
                        }
                        
                        row.appendChild(cell);
                    }
                });
                tbody.appendChild(row);
            });

            // Обновляем информацию о записях
            document.getElementById('recordsInfo').textContent = 
                `Показано ${orders.length} записей`;
        }

        // Создание переключателей колонок
        function createColumnToggles(columns) {
            const container = document.getElementById('columnToggles');
            container.innerHTML = '';
            
            // Основные колонки показываем по умолчанию
            const defaultColumns = ['order_number', 'machine_code', 'order_price', 'error_type', 'creation_time'];
            
            columns.forEach(column => {
                const isVisible = defaultColumns.includes(column);
                if (isVisible) visibleColumns.add(column);
                
                const toggle = document.createElement('div');
                toggle.className = 'form-check form-check-inline column-toggle';
                toggle.innerHTML = `
                    <input class="form-check-input" type="checkbox" id="col_${column}" 
                           ${isVisible ? 'checked' : ''} onchange="toggleColumn('${column}')">
                    <label class="form-check-label" for="col_${column}">${getColumnName(column)}</label>
                `;
                container.appendChild(toggle);
            });
        }

        // Обновление заголовка таблицы
        function updateTableHeader(columns) {
            const header = document.getElementById('tableHeader');
            header.innerHTML = '';
            
            columns.forEach(column => {
                if (visibleColumns.has(column)) {
                    const th = document.createElement('th');
                    th.textContent = getColumnName(column);
                    header.appendChild(th);
                }
            });
        }

        // Переключение видимости колонки
        function toggleColumn(column) {
            const checkbox = document.getElementById(`col_${column}`);
            if (checkbox.checked) {
                visibleColumns.add(column);
            } else {
                visibleColumns.delete(column);
            }
            updateTable(currentData);
        }

        // Получение читаемого имени колонки
        function getColumnName(column) {
            const names = {
                'order_number': 'Номер заказа',
                'machine_code': 'Код автомата',
                'order_price': 'Цена',
                'error_type': 'Статус',
                'creation_time': 'Время создания',
                'paying_time': 'Время оплаты',
                'delivery_time': 'Время выдачи',
                'goods_name': 'Товар',
                'payment_type': 'Тип оплаты',
                'username': 'Пользователь'
            };
            return names[column] || column;
        }

        // Получение цвета статуса
        function getStatusColor(status) {
            const colors = {
                'OK': 'success',
                'NO_MATCH_IN_REPORT': 'warning',
                'NO_PAYMENT_FOUND': 'danger',
                'FISCAL_MISSING': 'info',
                'UNPROCESSED': 'secondary'
            };
            return colors[status] || 'secondary';
        }

        // Экспорт данных
        function exportData() {
            const filters = {
                period: document.getElementById('periodFilter').value,
                machine: document.getElementById('machineFilter').value,
                status: document.getElementById('statusFilter').value
            };

            const params = new URLSearchParams();
            Object.keys(filters).forEach(key => {
                if (filters[key] !== 'all') {
                    params.append(key, filters[key]);
                }
            });

            window.location.href = `/api/orders/export?${params}`;
        }
    </script>
</body>
</html>'''
    
    # Создаем папку templates если не существует
    os.makedirs('templates', exist_ok=True)
    
    # Сохраняем файл
    with open('templates/database.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print("✅ Создана страница просмотра базы данных: templates/database.html")

def add_database_routes_to_app():
    """Добавляет маршруты для работы с базой данных в app.py"""
    
    routes_code = '''
# Добавить эти маршруты в app.py

@app.route('/database')
def database_viewer():
    """Страница просмотра базы данных"""
    return render_template('database.html')

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
'''
    
    print("📝 Код маршрутов для добавления в app.py:")
    print(routes_code)
    
    return routes_code

if __name__ == '__main__':
    create_database_viewer_page()
    add_database_routes_to_app()
