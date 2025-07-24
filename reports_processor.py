"""
Процессор для работы с отчетами по типам
Сохраняет каждый тип отчета в отдельную таблицу
"""

import pandas as pd
import sqlite3
from datetime import datetime
import os
import json

class ReportsProcessor:
    """Процессор для работы с отчетами по типам"""
    
    def __init__(self, db_connection):
        self.db = db_connection
        
        # Маппинг типов файлов к таблицам
        self.table_mapping = {
            'happy_workers': 'reports_happy_workers',
            'vendhub': 'reports_vendhub',
            'fiscal_bills': 'reports_fiscal_bills',
            'payme': 'reports_payme',
            'click': 'reports_click',
            'uzum': 'reports_uzum',
            'bank_statement': 'reports_bank_statements'
        }
        
        # Маппинг колонок для каждого типа
        self.column_mapping = {
            'happy_workers': {
                'Order number': 'order_number',
                'Machine code': 'machine_code',
                'Address': 'address',
                'Goods name': 'goods_name',
                'Taste name': 'taste_name',
                'Order type': 'order_type',
                'Order resource': 'order_resource',
                'Order price': 'order_price',
                'Creation time': 'creation_time',
                'Paying time': 'paying_time',
                'Brewing time': 'brewing_time',
                'Delivery time': 'delivery_time',
                'Refund time': 'refund_time',
                'Payment status': 'payment_status',
                'Brew status': 'brew_status',
                'Reason': 'reason'
            },
            'vendhub': {
                'Order number': 'order_number',
                'Time': 'time_event',
                'Goods name': 'goods_name',
                'Order price': 'order_price',
                'Machine Code': 'machine_code',
                'Machine category': 'machine_category',
                'Payment type': 'payment_type',
                'Order resource': 'order_resource',
                'Goods ID': 'goods_id',
                'Username': 'username',
                'Amount of accrued bonus': 'amount_of_accrued_bonus',
                'ИКПУ': 'ikpu',
                'Штрихкод': 'barcode',
                'Маркировка': 'marking',
                'Упаковка': 'packaging'
            },
            'fiscal_bills': {
                'fiscal_check_number': 'fiscal_check_number',
                'fiscal_time': 'fiscal_time',
                'amount': 'amount',
                'taxpayer_id': 'taxpayer_id',
                'cash_register_id': 'cash_register_id',
                'shift_number': 'shift_number',
                'receipt_type': 'receipt_type'
            },
            'payme': {
                'transaction_id': 'transaction_id',
                'transaction_time': 'transaction_time',
                'amount': 'amount',
                'masked_pan': 'masked_pan',
                'merchant_id': 'merchant_id',
                'terminal_id': 'terminal_id',
                'commission': 'commission',
                'status': 'status',
                'username': 'username'
            },
            'click': {
                'transaction_id': 'transaction_id',
                'transaction_time': 'transaction_time',
                'amount': 'amount',
                'card_number': 'card_number',
                'merchant_id': 'merchant_id',
                'service_id': 'service_id',
                'commission': 'commission',
                'status': 'status',
                'error_code': 'error_code'
            },
            'uzum': {
                'transaction_id': 'transaction_id',
                'transaction_time': 'transaction_time',
                'amount': 'amount',
                'masked_pan': 'masked_pan',
                'merchant_id': 'merchant_id',
                'shop_id': 'shop_id',
                'commission': 'commission',
                'status': 'status',
                'username': 'username'
            }
        }
    
    def process_file(self, file_path, file_type, original_filename):
        """Обработка файла и сохранение в соответствующую таблицу"""
        
        try:
            # Регистрируем файл
            file_id = self._register_file(original_filename, file_type, file_path)
            
            # Читаем файл
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path)
            else:
                df = pd.read_csv(file_path, encoding='utf-8-sig')
            
            # Обрабатываем данные
            processed_count = self._save_to_report_table(df, file_type, original_filename)
            
            # Обновляем информацию о файле
            self._update_file_status(file_id, True, processed_count)
            
            # После сохранения в отчетную таблицу, обновляем основную таблицу orders
            self._update_main_orders_table(file_type)
            
            return processed_count
            
        except Exception as e:
            print(f"Error processing file {original_filename}: {e}")
            if 'file_id' in locals():
                self._update_file_status(file_id, False, 0, str(e))
            raise
    
    def _register_file(self, original_filename, file_type, file_path):
        """Регистрация загруженного файла"""
        
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        cursor = self.db.cursor()
        cursor.execute("""
            INSERT INTO uploaded_files 
            (file_name, original_name, file_type, file_size)
            VALUES (?, ?, ?, ?)
        """, (os.path.basename(file_path), original_filename, file_type, file_size))
        
        file_id = cursor.lastrowid
        self.db.commit()
        
        return file_id
    
    def _update_file_status(self, file_id, processed, records_count, error_message=None):
        """Обновление статуса обработки файла"""
        
        cursor = self.db.cursor()
        cursor.execute("""
            UPDATE uploaded_files 
            SET processed = ?, processing_date = ?, records_count = ?, error_message = ?
            WHERE id = ?
        """, (processed, datetime.now(), records_count, error_message, file_id))
        
        self.db.commit()
    
    def _save_to_report_table(self, df, file_type, filename):
        """Сохранение данных в таблицу отчета"""
        
        if file_type not in self.table_mapping:
            raise ValueError(f"Unknown file type: {file_type}")
        
        table_name = self.table_mapping[file_type]
        column_map = self.column_mapping.get(file_type, {})
        
        # Подготавливаем данные
        processed_data = []
        
        for index, row in df.iterrows():
            record = {
                'file_name': filename,
                'upload_date': datetime.now(),
                'row_number': index + 1
            }
            
            # Маппим колонки
            for original_col, mapped_col in column_map.items():
                if original_col in df.columns:
                    value = row[original_col]
                    
                    # Обработка пустых значений
                    if pd.isna(value):
                        value = None
                    elif isinstance(value, str) and value.strip() == '':
                        value = None
                    
                    record[mapped_col] = value
            
            processed_data.append(record)
        
        # Сохраняем в базу
        if processed_data:
            self._bulk_insert(table_name, processed_data)
        
        return len(processed_data)
    
    def _bulk_insert(self, table_name, data):
        """Массовая вставка данных"""
        
        if not data:
            return
        
        # Получаем колонки из первой записи
        columns = list(data[0].keys())
        placeholders = ', '.join(['?' for _ in columns])
        columns_str = ', '.join(columns)
        
        sql = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        
        # Подготавливаем данные для вставки
        values = []
        for record in data:
            values.append([record.get(col) for col in columns])
        
        cursor = self.db.cursor()
        cursor.executemany(sql, values)
        self.db.commit()
    
    def _update_main_orders_table(self, file_type):
        """Обновление основной таблицы orders на основе данных из отчетных таблиц"""
        
        if file_type == 'happy_workers':
            self._merge_happy_workers_data()
        elif file_type == 'vendhub':
            self._merge_vendhub_data()
        elif file_type in ['fiscal_bills', 'payme', 'click', 'uzum']:
            self._merge_additional_data(file_type)
    
    def _merge_happy_workers_data(self):
        """Объединение данных Happy Workers с основной таблицей"""
        
        cursor = self.db.cursor()
        
        # Получаем необработанные записи Happy Workers
        cursor.execute("""
            SELECT * FROM reports_happy_workers 
            WHERE processed = FALSE
        """)
        
        hw_records = cursor.fetchall()
        
        for record in hw_records:
            # Проверяем, есть ли уже такой заказ
            cursor.execute("""
                SELECT id FROM orders 
                WHERE order_number = ? AND machine_code = ?
            """, (record['order_number'], record['machine_code']))
            
            existing = cursor.fetchone()
            
            if existing:
                # Обновляем существующий заказ
                cursor.execute("""
                    UPDATE orders SET
                        goods_name = COALESCE(?, goods_name),
                        order_price = COALESCE(?, order_price),
                        creation_time = COALESCE(?, creation_time),
                        paying_time = COALESCE(?, paying_time),
                        delivery_time = COALESCE(?, delivery_time),
                        payment_status = COALESCE(?, payment_status),
                        hw_source = TRUE,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    record['goods_name'], record['order_price'],
                    record['creation_time'], record['paying_time'],
                    record['delivery_time'], record['payment_status'],
                    datetime.now(), existing['id']
                ))
            else:
                # Создаем новый заказ
                cursor.execute("""
                    INSERT INTO orders (
                        order_number, machine_code, goods_name, order_price,
                        creation_time, paying_time, delivery_time, payment_status,
                        hw_source, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, TRUE, ?)
                """, (
                    record['order_number'], record['machine_code'],
                    record['goods_name'], record['order_price'],
                    record['creation_time'], record['paying_time'],
                    record['delivery_time'], record['payment_status'],
                    datetime.now()
                ))
            
            # Отмечаем запись как обработанную
            cursor.execute("""
                UPDATE reports_happy_workers 
                SET processed = TRUE, processing_date = ?
                WHERE id = ?
            """, (datetime.now(), record['id']))
        
        self.db.commit()
    
    def _merge_vendhub_data(self):
        """Объединение данных VendHub с основной таблицей"""
        
        cursor = self.db.cursor()
        
        # Получаем необработанные записи VendHub
        cursor.execute("""
            SELECT * FROM reports_vendhub 
            WHERE processed = FALSE
        """)
        
        vh_records = cursor.fetchall()
        
        for record in vh_records:
            # Ищем соответствующий заказ
            cursor.execute("""
                SELECT id FROM orders 
                WHERE order_number = ? AND machine_code = ?
            """, (record['order_number'], record['machine_code']))
            
            existing = cursor.fetchone()
            
            if existing:
                # Обновляем существующий заказ
                cursor.execute("""
                    UPDATE orders SET
                        payment_type = COALESCE(?, payment_type),
                        username = COALESCE(?, username),
                        goods_id = COALESCE(?, goods_id),
                        vh_source = TRUE,
                        updated_at = ?
                    WHERE id = ?
                """, (
                    record['payment_type'], record['username'],
                    record['goods_id'], datetime.now(), existing['id']
                ))
            else:
                # Создаем новый заказ
                cursor.execute("""
                    INSERT INTO orders (
                        order_number, machine_code, goods_name, order_price,
                        payment_type, username, goods_id, vh_source, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, TRUE, ?)
                """, (
                    record['order_number'], record['machine_code'],
                    record['goods_name'], record['order_price'],
                    record['payment_type'], record['username'],
                    record['goods_id'], datetime.now()
                ))
            
            # Отмечаем запись как обработанную
            cursor.execute("""
                UPDATE reports_vendhub 
                SET processed = TRUE, processing_date = ?
                WHERE id = ?
            """, (datetime.now(), record['id']))
        
        self.db.commit()
    
    def _merge_additional_data(self, file_type):
        """Объединение дополнительных данных (фискальные, платежные системы)"""
        
        cursor = self.db.cursor()
        
        if file_type == 'fiscal_bills':
            # Обрабатываем фискальные чеки
            cursor.execute("""
                SELECT * FROM reports_fiscal_bills 
                WHERE processed = FALSE
            """)
            
            fiscal_records = cursor.fetchall()
            
            for record in fiscal_records:
                # Ищем заказы с наличной оплатой в подходящем временном окне
                cursor.execute("""
                    SELECT id FROM orders 
                    WHERE payment_type = 'Cash'
                    AND ABS(julianday(paying_time) - julianday(?)) * 24 * 60 <= 5
                    AND ABS(order_price - ?) <= 0.01
                    AND fiscal_check_number IS NULL
                    LIMIT 1
                """, (record['fiscal_time'], record['amount']))
                
                matching_order = cursor.fetchone()
                
                if matching_order:
                    cursor.execute("""
                        UPDATE orders SET
                            fiscal_check_number = ?,
                            taxpayer_id = ?,
                            updated_at = ?
                        WHERE id = ?
                    """, (
                        record['fiscal_check_number'],
                        record['taxpayer_id'],
                        datetime.now(),
                        matching_order['id']
                    ))
                
                # Отмечаем запись как обработанную
                cursor.execute("""
                    UPDATE reports_fiscal_bills 
                    SET processed = TRUE, processing_date = ?
                    WHERE id = ?
                """, (datetime.now(), record['id']))
        
        elif file_type in ['payme', 'click', 'uzum']:
            # Обрабатываем платежные системы
            table_name = self.table_mapping[file_type]
            
            cursor.execute(f"""
                SELECT * FROM {table_name} 
                WHERE processed = FALSE
            """)
            
            payment_records = cursor.fetchall()
            
            for record in payment_records:
                # Ищем заказы с соответствующим типом оплаты
                cursor.execute("""
                    SELECT id FROM orders 
                    WHERE payment_type LIKE ?
                    AND ABS(julianday(paying_time) - julianday(?)) * 24 * 60 <= 5
                    AND ABS(order_price - ?) <= 0.01
                    AND transaction_id IS NULL
                    LIMIT 1
                """, (f'%{file_type}%', record['transaction_time'], record['amount']))
                
                matching_order = cursor.fetchone()
                
                if matching_order:
                    cursor.execute("""
                        UPDATE orders SET
                            transaction_id = ?,
                            payment_gateway = ?,
                            updated_at = ?
                        WHERE id = ?
                    """, (
                        record['transaction_id'],
                        file_type,
                        datetime.now(),
                        matching_order['id']
                    ))
                
                # Отмечаем запись как обработанную
                cursor.execute(f"""
                    UPDATE {table_name} 
                    SET processed = TRUE, processing_date = ?
                    WHERE id = ?
                """, (datetime.now(), record['id']))
        
        self.db.commit()
    
    def get_report_data(self, report_type, filters=None):
        """Получение данных отчета по типу"""
        
        if report_type not in self.table_mapping:
            raise ValueError(f"Unknown report type: {report_type}")
        
        table_name = self.table_mapping[report_type]
        
        # Базовый запрос
        sql = f"SELECT * FROM {table_name}"
        params = []
        conditions = []
        
        # Применяем фильтры
        if filters:
            if filters.get('date_from'):
                conditions.append("DATE(upload_date) >= ?")
                params.append(filters['date_from'])
            
            if filters.get('date_to'):
                conditions.append("DATE(upload_date) <= ?")
                params.append(filters['date_to'])
            
            if filters.get('file_name'):
                conditions.append("file_name LIKE ?")
                params.append(f"%{filters['file_name']}%")
        
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        sql += " ORDER BY upload_date DESC, id DESC"
        
        # Лимит
        limit = filters.get('limit', 1000) if filters else 1000
        sql += f" LIMIT {limit}"
        
        cursor = self.db.cursor()
        cursor.execute(sql, params)
        
        return cursor.fetchall()
    
    def get_report_statistics(self):
        """Получение статистики по всем отчетам"""
        
        cursor = self.db.cursor()
        
        # Статистика по типам файлов
        cursor.execute("""
            SELECT 
                file_type,
                COUNT(*) as files_count,
                SUM(records_count) as total_records,
                MAX(upload_date) as last_upload,
                COUNT(CASE WHEN processed = 1 THEN 1 END) as processed_files,
                COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as error_files
            FROM uploaded_files
            GROUP BY file_type
            ORDER BY last_upload DESC
        """)
        
        stats_by_type = cursor.fetchall()
        
        # Общая статистика
        cursor.execute("""
            SELECT 
                COUNT(*) as total_files,
                SUM(records_count) as total_records,
                COUNT(CASE WHEN processed = 1 THEN 1 END) as processed_files,
                COUNT(CASE WHEN error_message IS NOT NULL THEN 1 END) as error_files
            FROM uploaded_files
        """)
        
        total_stats = cursor.fetchone()
        
        return {
            'by_type': stats_by_type,
            'total': total_stats
        }
    
    def get_recent_uploads(self, limit=20):
        """Получение последних загрузок"""
        
        cursor = self.db.cursor()
        cursor.execute("""
            SELECT 
                original_name,
                file_type,
                file_size,
                upload_date,
                processed,
                records_count,
                error_message
            FROM uploaded_files
            ORDER BY upload_date DESC
            LIMIT ?
        """, (limit,))
        
        return cursor.fetchall()
    
    def export_report_data(self, report_type, filters=None, format='excel'):
        """Экспорт данных отчета"""
        
        data = self.get_report_data(report_type, filters)
        
        if not data:
            return None
        
        # Создаем DataFrame
        df = pd.DataFrame(data)
        
        # Генерируем имя файла
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"report_{report_type}_{timestamp}"
        
        if format == 'excel':
            filename += '.xlsx'
            filepath = os.path.join('uploads', filename)
            df.to_excel(filepath, index=False, engine='openpyxl')
        else:
            filename += '.csv'
            filepath = os.path.join('uploads', filename)
            df.to_csv(filepath, index=False, encoding='utf-8-sig')
        
        return filepath
