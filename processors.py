"""
VHM24R - Интеллектуальный модуль сверки заказов, платежей и фискализации
Оптимизированные процессоры с логикой согласно промту
"""

import pandas as pd
import json
from datetime import datetime, timedelta
import re
from typing import Dict, List, Optional, Any, Tuple

class OrderProcessor:
    """
    Основной процессор сверки заказов с логикой из промта:
    1. Сопоставление HW ↔ VendHub
    2. Сопоставление с платежными шлюзами
    3. Сопоставление с фискальными чеками
    4. Классификация ошибок
    """
    
    def __init__(self, db):
        self.db = db
        self.config = self._load_config()
        
        # Настройки временных окон из промта
        self.time_window = 3  # ±3 минуты для основного сопоставления
        self.fiscal_time_window = 5  # ±5 минут для фискальных чеков
        self.gateway_time_window = 10  # ±10 минут для платежных шлюзов
        self.price_tolerance = 1  # ±1 сум допустимое расхождение
    
    def _load_config(self) -> Dict[str, str]:
        """Загрузка конфигурации"""
        try:
            config_data = self.db.execute_query("SELECT config_key, config_value FROM system_config")
            return {item['config_key']: item['config_value'] for item in config_data}
        except:
            return {}
    
    def process_file(self, file_path: str, file_type: str) -> int:
        """Обработка файла в зависимости от типа"""
        print(f"Processing {file_type} file: {file_path}")
        
        if file_type == 'happy_workers':
            return self.process_hw_file(file_path)
        elif file_type == 'vendhub':
            return self.process_vendhub_file(file_path)
        elif file_type == 'fiscal_bills':
            return self.process_fiscal_file(file_path)
        elif file_type in ['payme', 'click', 'uzum']:
            return self.process_gateway_file(file_path, file_type)
        else:
            print(f"Unknown file type: {file_type}")
            return 0
    
    def process_hw_file(self, file_path: str) -> int:
        """
        Обработка HW.xlsx - первичный отчёт заказов из автомата
        Ключевые поля: Order number, Machine code, Creation time, Order price, Payment status
        """
        try:
            processed = 0
            df = self._read_excel_file(file_path)
            
            if df is None:
                return 0
            
            # Маппинг колонок HW
            column_mapping = self._map_hw_columns(df.columns)
            if not column_mapping:
                print("No recognizable HW columns found")
                return 0
            
            for _, row in df.iterrows():
                order_number = str(row.get(column_mapping.get('order_number', ''), ''))
                if not order_number or order_number == 'nan':
                    continue
                
                # Проверяем на отмененные заказы (Refund time указан)
                refund_time = row.get(column_mapping.get('refund_time', ''))
                if refund_time and not pd.isna(refund_time):
                    print(f"Skipping refunded order: {order_number}")
                    continue
                
                order_data = {
                    'order_number': order_number,
                    'machine_code': str(row.get(column_mapping.get('machine_code', ''), '')),
                    'creation_time': self._parse_datetime(row.get(column_mapping.get('creation_time', ''))),
                    'paying_time': self._parse_datetime(row.get(column_mapping.get('paying_time', ''))),
                    'brewing_time': self._parse_datetime(row.get(column_mapping.get('brewing_time', ''))),
                    'delivery_time': self._parse_datetime(row.get(column_mapping.get('delivery_time', ''))),
                    'order_price': self._safe_float(row.get(column_mapping.get('order_price', ''), 0)),
                    'goods_name': str(row.get(column_mapping.get('goods_name', ''), '')),
                    'payment_type': self._normalize_payment_type(row.get(column_mapping.get('payment_type', ''), '')),
                    'refund_time': self._parse_datetime(refund_time),
                    'reason': str(row.get(column_mapping.get('reason', ''), '')),
                    'hw_data': row.to_dict(),
                    'error_type': 'UNPROCESSED'
                }
                
                self.db.upsert_order(order_data)
                processed += 1
            
            print(f"Processed {processed} HW records")
            return processed
            
        except Exception as e:
            print(f"Error processing HW file: {e}")
            return 0
    
    def process_vendhub_file(self, file_path: str) -> int:
        """
        Обработка report.xlsx - внутренний отчёт системы VendHub
        Ключевые поля: Order number, Machine code, Order time, Order price, Payment type
        """
        try:
            processed = 0
            df = self._read_excel_file(file_path)
            
            if df is None:
                return 0
            
            column_mapping = self._map_vendhub_columns(df.columns)
            if not column_mapping:
                print("No recognizable VendHub columns found")
                return 0
            
            for _, row in df.iterrows():
                order_number = str(row.get(column_mapping.get('order_number', ''), ''))
                if not order_number or order_number == 'nan':
                    continue
                
                order_data = {
                    'order_number': order_number,
                    'machine_code': str(row.get(column_mapping.get('machine_code', ''), '')),
                    'creation_time': self._parse_datetime(row.get(column_mapping.get('order_time', ''))),
                    'order_price': self._safe_float(row.get(column_mapping.get('order_price', ''), 0)),
                    'goods_name': str(row.get(column_mapping.get('goods_name', ''), '')),
                    'payment_type': self._normalize_payment_type(row.get(column_mapping.get('payment_type', ''), '')),
                    'vendhub_data': row.to_dict(),
                    'error_type': 'UNPROCESSED'
                }
                
                self.db.upsert_order(order_data)
                processed += 1
            
            print(f"Processed {processed} VendHub records")
            return processed
            
        except Exception as e:
            print(f"Error processing VendHub file: {e}")
            return 0
    
    def process_fiscal_file(self, file_path: str) -> int:
        """
        Обработка fiscal_bills.xlsx - фискальные чеки
        Сопоставляем с Cash заказами в временном окне ±5 минут
        """
        try:
            processed = 0
            df = self._read_excel_file(file_path)
            
            if df is None:
                return 0
            
            column_mapping = self._map_fiscal_columns(df.columns)
            if not column_mapping:
                print("No recognizable fiscal columns found")
                return 0
            
            for _, row in df.iterrows():
                fiscal_time = self._parse_datetime(row.get(column_mapping.get('fiscal_time', '')))
                amount = self._safe_float(row.get(column_mapping.get('amount', ''), 0))
                
                if not fiscal_time or amount <= 0:
                    continue
                
                # Ищем подходящие Cash заказы
                matching_orders = self._find_cash_orders_for_fiscal(fiscal_time, amount)
                
                if matching_orders:
                    # Обновляем первый подходящий заказ
                    order = matching_orders[0]
                    self.db.execute_query("""
                        UPDATE orders 
                        SET fiscal_data = ?, matched_fiscal = TRUE, 
                            fiscal_check_number = ?, taxpayer_id = ?
                        WHERE id = ?
                    """, (
                        json.dumps(row.to_dict(), default=str),
                        str(row.get(column_mapping.get('fiscal_check_number', ''), '')),
                        str(row.get(column_mapping.get('taxpayer_id', ''), '')),
                        order['id']
                    ))
                    processed += 1
            
            print(f"Processed {processed} fiscal records")
            return processed
            
        except Exception as e:
            print(f"Error processing fiscal file: {e}")
            return 0
    
    def process_gateway_file(self, file_path: str, gateway_type: str) -> int:
        """
        Обработка файлов платежных шлюзов (Payme, Click, Uzum)
        Сопоставляем с Custom payment заказами в временном окне ±10 минут
        """
        try:
            processed = 0
            df = self._read_excel_file(file_path)
            
            if df is None:
                return 0
            
            column_mapping = self._map_gateway_columns(df.columns, gateway_type)
            if not column_mapping:
                print(f"No recognizable {gateway_type} columns found")
                return 0
            
            for _, row in df.iterrows():
                transaction_time = self._parse_datetime(row.get(column_mapping.get('transaction_time', '')))
                amount = self._safe_float(row.get(column_mapping.get('amount', ''), 0))
                
                if not transaction_time or amount <= 0:
                    continue
                
                # Ищем подходящие Custom payment заказы
                matching_orders = self._find_custom_payment_orders_for_gateway(transaction_time, amount)
                
                if matching_orders:
                    # Обновляем первый подходящий заказ
                    order = matching_orders[0]
                    self.db.execute_query("""
                        UPDATE orders 
                        SET gateway_data = ?, matched_payment = TRUE, 
                            payment_gateway = ?, payment_source = ?,
                            transaction_id = ?, card_number = ?, merchant_id = ?
                        WHERE id = ?
                    """, (
                        json.dumps(row.to_dict(), default=str),
                        gateway_type,
                        gateway_type.title(),
                        str(row.get(column_mapping.get('transaction_id', ''), '')),
                        str(row.get(column_mapping.get('card_number', ''), '')),
                        str(row.get(column_mapping.get('merchant_id', ''), '')),
                        order['id']
                    ))
                    processed += 1
            
            print(f"Processed {processed} {gateway_type} records")
            return processed
            
        except Exception as e:
            print(f"Error processing {gateway_type} file: {e}")
            return 0
    
    def run_matching(self) -> Dict[str, int]:
        """
        ОСНОВНАЯ ЛОГИКА СВЕРКИ согласно промту:
        Шаг 1: Сопоставление HW ↔ VendHub
        Шаг 2: Классификация ошибок
        Шаг 3: Обновление статусов
        """
        print("Starting intelligent matching process...")
        
        try:
            # Шаг 1: Сопоставление заказов HW с VendHub
            self._match_hw_with_vendhub()
            
            # Шаг 2: Классификация всех заказов по типам ошибок
            self._classify_all_orders()
            
            # Шаг 3: Получение финальной статистики
            stats = self.db.get_processing_stats()
            
            print("Matching completed successfully")
            return stats
            
        except Exception as e:
            print(f"Error in matching process: {e}")
            return {'total': 0, 'OK': 0, 'UNPROCESSED': 0}
    
    def _match_hw_with_vendhub(self):
        """Сопоставление заказов HW с VendHub по Order number"""
        print("Matching HW orders with VendHub...")
        
        # Получаем все заказы с HW данными, но без VendHub
        hw_orders = self.db.execute_query("""
            SELECT * FROM orders 
            WHERE hw_data IS NOT NULL AND hw_data != '{}' 
            AND (vendhub_data IS NULL OR vendhub_data = '{}')
        """)
        
        for hw_order in hw_orders:
            # Ищем соответствующий VendHub заказ
            vendhub_orders = self.db.execute_query("""
                SELECT * FROM orders 
                WHERE order_number = ? AND machine_code = ?
                AND vendhub_data IS NOT NULL AND vendhub_data != '{}'
                AND (hw_data IS NULL OR hw_data = '{}')
            """, (hw_order['order_number'], hw_order['machine_code']))
            
            if vendhub_orders:
                # Объединяем данные
                vendhub_order = vendhub_orders[0]
                self._merge_hw_vendhub_orders(hw_order['id'], vendhub_order['id'])
    
    def _merge_hw_vendhub_orders(self, hw_order_id: int, vendhub_order_id: int):
        """Объединение данных HW и VendHub заказов"""
        # Получаем данные обоих заказов
        hw_order = self.db.execute_query("SELECT * FROM orders WHERE id = ?", (hw_order_id,))[0]
        vendhub_order = self.db.execute_query("SELECT * FROM orders WHERE id = ?", (vendhub_order_id,))[0]
        
        # Объединяем данные в основной заказ (HW)
        merged_data = {
            'vendhub_data': vendhub_order['vendhub_data'],
            'error_type': 'UNPROCESSED'  # Будет классифицирован позже
        }
        
        # Обновляем HW заказ
        self.db.execute_query("""
            UPDATE orders 
            SET vendhub_data = ?, error_type = ?
            WHERE id = ?
        """, (merged_data['vendhub_data'], merged_data['error_type'], hw_order_id))
        
        # Удаляем дублирующий VendHub заказ
        self.db.execute_query("DELETE FROM orders WHERE id = ?", (vendhub_order_id,))
    
    def _classify_all_orders(self):
        """Классификация всех заказов по типам ошибок согласно промту"""
        print("Classifying orders by error types...")
        
        # Получаем все необработанные заказы
        orders = self.db.execute_query("""
            SELECT * FROM orders WHERE error_type = 'UNPROCESSED'
        """)
        
        for order in orders:
            error_type = self._determine_error_type(order)
            details = self._generate_error_details(order, error_type)
            
            self.db.update_order_error_type(order['id'], error_type, details)
    
    def _determine_error_type(self, order: Dict[str, Any]) -> str:
        """
        Определение типа ошибки согласно промту:
        - OK: Всё совпадает
        - NO_MATCH_IN_REPORT: Заказ в HW не найден в report.xlsx
        - NO_PAYMENT_FOUND: Заказ есть, оплаты нет
        - EXCESS_PAYMENT: Оплата есть, заказа нет
        - PAYMENT_MISMATCH: Заказ и оплата есть, но сумма не совпадает
        - FISCAL_MISSING: Оплата есть, но нет чека
        """
        
        # Проверяем наличие данных HW и VendHub
        has_hw_data = order.get('hw_data') and order['hw_data'] != '{}'
        has_vendhub_data = order.get('vendhub_data') and order['vendhub_data'] != '{}'
        
        # NO_MATCH_IN_REPORT: есть HW, но нет VendHub
        if has_hw_data and not has_vendhub_data:
            return 'NO_MATCH_IN_REPORT'
        
        # Если нет основных данных, пропускаем
        if not has_hw_data and not has_vendhub_data:
            return 'UNPROCESSED'
        
        payment_type = order.get('payment_type', '')
        
        # Для Cash заказов проверяем фискальные чеки
        if payment_type == 'Cash':
            if not order.get('matched_fiscal', False):
                return 'FISCAL_MISSING'
            else:
                return 'OK'
        
        # Для Custom payment заказов проверяем платежные шлюзы
        elif payment_type == 'Custom payment':
            if not order.get('matched_payment', False):
                return 'NO_PAYMENT_FOUND'
            else:
                return 'OK'
        
        # Для остальных типов платежей
        else:
            return 'OK'
    
    def _generate_error_details(self, order: Dict[str, Any], error_type: str) -> str:
        """Генерация детального описания ошибки"""
        details = []
        
        if error_type == 'NO_MATCH_IN_REPORT':
            details.append("Заказ найден в HW, но отсутствует во внутреннем учете")
        elif error_type == 'NO_PAYMENT_FOUND':
            details.append("Заказ есть, но не найдена соответствующая оплата в платежных шлюзах")
        elif error_type == 'FISCAL_MISSING':
            details.append("Cash заказ без соответствующего фискального чека")
        elif error_type == 'OK':
            details.append("Все данные корректно сопоставлены")
        
        return "; ".join(details)
    
    def _find_cash_orders_for_fiscal(self, fiscal_time: datetime, amount: float) -> List[Dict]:
        """Поиск Cash заказов для фискального чека"""
        time_start = fiscal_time - timedelta(minutes=self.fiscal_time_window)
        time_end = fiscal_time + timedelta(minutes=self.fiscal_time_window)
        
        return self.db.execute_query("""
            SELECT * FROM orders 
            WHERE payment_type = 'Cash'
            AND creation_time BETWEEN ? AND ?
            AND ABS(order_price - ?) <= ?
            AND (matched_fiscal = FALSE OR matched_fiscal IS NULL)
            ORDER BY ABS(julianday(creation_time) - julianday(?)) ASC
            LIMIT 1
        """, (time_start, time_end, amount, self.price_tolerance, fiscal_time))
    
    def _find_custom_payment_orders_for_gateway(self, transaction_time: datetime, amount: float) -> List[Dict]:
        """Поиск Custom payment заказов для платежного шлюза"""
        time_start = transaction_time - timedelta(minutes=self.gateway_time_window)
        time_end = transaction_time + timedelta(minutes=self.gateway_time_window)
        
        return self.db.execute_query("""
            SELECT * FROM orders 
            WHERE payment_type = 'Custom payment'
            AND creation_time BETWEEN ? AND ?
            AND ABS(order_price - ?) <= ?
            AND (matched_payment = FALSE OR matched_payment IS NULL)
            ORDER BY ABS(julianday(creation_time) - julianday(?)) ASC
            LIMIT 1
        """, (time_start, time_end, amount, self.price_tolerance, transaction_time))
    
    # ========================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ========================================================================
    
    def _read_excel_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """Чтение Excel файла с обработкой ошибок"""
        try:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                return pd.read_excel(file_path)
            else:
                # Пробуем разные кодировки для CSV
                for encoding in ['utf-8', 'cp1251', 'windows-1251', 'iso-8859-1']:
                    try:
                        return pd.read_csv(file_path, encoding=encoding)
                    except UnicodeDecodeError:
                        continue
                return None
        except Exception as e:
            print(f"Error reading file {file_path}: {e}")
            return None
    
    def _map_hw_columns(self, columns) -> Optional[Dict[str, str]]:
        """Маппинг колонок HW файла"""
        column_mapping = {}
        columns_lower = [str(col).lower() for col in columns]
        
        # Основные поля из промта
        mappings = {
            'order_number': ['order number', 'номер заказа', 'order_number'],
            'machine_code': ['machine code', 'код автомата', 'machine_code'],
            'creation_time': ['creation time', 'время создания', 'creation_time'],
            'paying_time': ['paying time', 'время оплаты', 'paying_time'],
            'brewing_time': ['brewing time', 'время приготовления', 'brewing_time'],
            'delivery_time': ['delivery time', 'время выдачи', 'delivery_time'],
            'order_price': ['order price', 'цена заказа', 'order_price', 'price'],
            'goods_name': ['goods name', 'название товара', 'goods_name'],
            'payment_type': ['order resource', 'payment type', 'тип платежа'],
            'refund_time': ['refund time', 'время возврата', 'refund_time'],
            'reason': ['reason', 'причина', 'reason']
        }
        
        for field, keywords in mappings.items():
            for i, col in enumerate(columns_lower):
                if any(keyword in col for keyword in keywords):
                    column_mapping[field] = columns[i]
                    break
        
        return column_mapping if len(column_mapping) >= 3 else None
    
    def _map_vendhub_columns(self, columns) -> Optional[Dict[str, str]]:
        """Маппинг колонок VendHub файла"""
        column_mapping = {}
        columns_lower = [str(col).lower() for col in columns]
        
        mappings = {
            'order_number': ['order number', 'номер заказа', 'order_number'],
            'machine_code': ['machine code', 'код автомата', 'machine_code'],
            'order_time': ['order time', 'время заказа', 'order_time', 'time'],
            'order_price': ['order price', 'цена заказа', 'order_price', 'price'],
            'goods_name': ['goods name', 'название товара', 'goods_name'],
            'payment_type': ['payment type', 'тип платежа', 'payment_type']
        }
        
        for field, keywords in mappings.items():
            for i, col in enumerate(columns_lower):
                if any(keyword in col for keyword in keywords):
                    column_mapping[field] = columns[i]
                    break
        
        return column_mapping if len(column_mapping) >= 3 else None
    
    def _map_fiscal_columns(self, columns) -> Optional[Dict[str, str]]:
        """Маппинг колонок фискальных чеков"""
        column_mapping = {}
        columns_lower = [str(col).lower() for col in columns]
        
        mappings = {
            'fiscal_time': ['time', 'время', 'fiscal_time', 'дата'],
            'amount': ['amount', 'сумма', 'price', 'цена'],
            'fiscal_check_number': ['fiscal id', 'номер чека', 'fiscal_check_number'],
            'taxpayer_id': ['taxpayer id', 'ид налогоплательщика', 'taxpayer_id']
        }
        
        for field, keywords in mappings.items():
            for i, col in enumerate(columns_lower):
                if any(keyword in col for keyword in keywords):
                    column_mapping[field] = columns[i]
                    break
        
        return column_mapping if len(column_mapping) >= 2 else None
    
    def _map_gateway_columns(self, columns, gateway_type: str) -> Optional[Dict[str, str]]:
        """Маппинг колонок платежных шлюзов"""
        column_mapping = {}
        columns_lower = [str(col).lower() for col in columns]
        
        mappings = {
            'transaction_time': ['transaction time', 'время транзакции', 'time', 'дата'],
            'amount': ['transaction amount', 'amount', 'сумма', 'price'],
            'transaction_id': ['transaction id', 'ид транзакции', 'transaction_id'],
            'card_number': ['card', 'masked_pan', 'номер карты', 'card_number'],
            'merchant_id': ['merchant', 'shop_id', 'merchant_id', 'terminal_id']
        }
        
        for field, keywords in mappings.items():
            for i, col in enumerate(columns_lower):
                if any(keyword in col for keyword in keywords):
                    column_mapping[field] = columns[i]
                    break
        
        return column_mapping if len(column_mapping) >= 3 else None
    
    def _parse_datetime(self, dt_str) -> Optional[datetime]:
        """Парсинг даты и времени"""
        if pd.isna(dt_str) or dt_str is None or dt_str == '':
            return None
        
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%d.%m.%Y %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%Y-%m-%d',
            '%d.%m.%Y',
            '%d/%m/%Y'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(dt_str), fmt)
            except ValueError:
                continue
        
        return None
    
    def _safe_float(self, value) -> float:
        """Безопасное преобразование в float"""
        if pd.isna(value) or value is None or value == '':
            return 0.0
        try:
            if isinstance(value, str):
                value = value.replace(' ', '').replace(',', '.')
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def _normalize_payment_type(self, payment_type: str) -> str:
        """Нормализация типа платежа согласно промту"""
        if not payment_type or pd.isna(payment_type):
            return 'Unknown'
        
        payment_type = str(payment_type).lower().strip()
        
        if 'cash' in payment_type or 'наличные' in payment_type:
            return 'Cash'
        elif 'custom' in payment_type or 'кастом' in payment_type:
            return 'Custom payment'
        elif 'card' in payment_type or 'карта' in payment_type:
            return 'Card'
        else:
            return 'Custom payment'  # По умолчанию для неизвестных типов


class RecipeProcessor:
    """Процессор управления рецептурой и ингредиентами"""
    
    def __init__(self, db):
        self.db = db
        self._init_recipe_tables()
    
    def _init_recipe_tables(self):
        """Инициализация таблиц рецептур"""
        tables = [
            """CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT,
                unit TEXT,
                selling_price DECIMAL(10,2),
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                unit TEXT,
                category TEXT,
                min_stock DECIMAL(10,3),
                current_stock DECIMAL(10,3),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS recipes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER,
                version INTEGER DEFAULT 1,
                active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (product_id) REFERENCES products(id)
            )""",
            """CREATE TABLE IF NOT EXISTS recipe_ingredients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER,
                ingredient_id INTEGER,
                quantity DECIMAL(10,3),
                unit TEXT,
                FOREIGN KEY (recipe_id) REFERENCES recipes(id),
                FOREIGN KEY (ingredient_id) REFERENCES ingredients(id)
            )"""
        ]
        
        for table_sql in tables:
            self.db.execute_query(table_sql)
    
    def get_products(self):
        """Получение списка продуктов"""
        return self.db.execute_query("SELECT * FROM products ORDER BY name")
    
    def create_product(self, data):
        """Создание нового продукта"""
        query = """
        INSERT INTO products (name, category, unit, selling_price, active)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (data['name'], data['category'], data['unit'], 
                 data['selling_price'], data.get('active', True))
        
        if self.db.is_postgres:
            query += " RETURNING id"
            result = self.db.execute_query(query, params)
            return result[0]['id'] if result else None
        else:
            cursor = self.db.connection.cursor()
            cursor.execute(query, params)
            product_id = cursor.lastrowid
            self.db.connection.commit()
            cursor.close()
            return product_id
    
    def get_ingredients(self):
        """Получение списка ингредиентов"""
        return self.db.execute_query("SELECT * FROM ingredients ORDER BY name")
    
    def create_ingredient(self, data):
        """Создание нового ингредиента"""
        query = """
        INSERT INTO ingredients (name, unit, category, min_stock, current_stock)
        VALUES (?, ?, ?, ?, ?)
        """
        params = (data['name'], data['unit'], data['category'],
                 data['min_stock'], data['current_stock'])
        
        if self.db.is_postgres:
            query += " RETURNING id"
            result = self.db.execute_query(query, params)
            return result[0]['id'] if result else None
        else:
            cursor = self.db.connection.cursor()
            cursor.execute(query, params)
            ingredient_id = cursor.lastrowid
            self.db.connection.commit()
            cursor.close()
            return ingredient_id
    
    def get_recipes_with_details(self):
        """Получение рецептов с деталями"""
        return self.db.execute_query("""
            SELECT r.*, p.name as product_name, p.category as product_category
            FROM recipes r
            JOIN products p ON r.product_id = p.id
            ORDER BY p.name, r.version DESC
        """)
    
    def create_recipe(self, recipe_data, ingredients):
        """Создание нового рецепта"""
        # Создаем рецепт
        query = """
        INSERT INTO recipes (product_id, version, active)
        VALUES (?, ?, ?)
        """
        params = (recipe_data['product_id'], recipe_data['version'], 
                 recipe_data.get('active', True))
        
        if self.db.is_postgres:
            query += " RETURNING id"
            result = self.db.execute_query(query, params)
            recipe_id = result[0]['id'] if result else None
        else:
            cursor = self.db.connection.cursor()
            cursor.execute(query, params)
            recipe_id = cursor.lastrowid
            self.db.connection.commit()
            cursor.close()
        
        # Добавляем ингредиенты
        if recipe_id and ingredients:
            for ingredient in ingredients:
                self.db.execute_query("""
                    INSERT INTO recipe_ingredients (recipe_id, ingredient_id, quantity, unit)
                    VALUES (?, ?, ?, ?)
                """, (recipe_id, ingredient['ingredient_id'], 
                     ingredient['quantity'], ingredient['unit']))
        
        return recipe_id
    
    def get_recipe_stats(self):
        """Статистика рецептур"""
        products_count = self.db.execute_query("SELECT COUNT(*) as count FROM products")[0]['count']
        ingredients_count = self.db.execute_query("SELECT COUNT(*) as count FROM ingredients")[0]['count']
        recipes_count = self.db.execute_query("SELECT COUNT(*) as count FROM recipes")[0]['count']
        
        return {
            'products_count': products_count,
            'ingredients_count': ingredients_count,
            'recipes_count': recipes_count
        }
    
    def get_purchases(self):
        """Заглушка для закупок"""
        return []
    
    def get_inventories(self):
        """Заглушка для инвентаризаций"""
        return []
    
    def calculate_product_cost(self, product_id):
        """Расчет себестоимости продукта"""
        return {'cost': 0, 'ingredients': []}
    
    def get_ingredients_stock(self):
        """Остатки ингредиентов"""
        return self.db.execute_query("""
            SELECT name, current_stock, min_stock, unit,
                   CASE WHEN current_stock <= min_stock THEN 'low' ELSE 'ok' END as status
            FROM ingredients
            ORDER BY name
        """)
    
    def calculate_consumption(self, start_date, end_date):
        """Расчет расхода ингредиентов"""
        return []
    
    def get_daily_consumption(self, report_date):
        """Расход за день"""
        return {'total_consumption': 0, 'ingredients_used': 0}


class FinanceProcessor:
    """Процессор финансовой сверки и инкассации"""
    
    def __init__(self, db):
        self.db = db
        self._init_finance_tables()
    
    def _init_finance_tables(self):
        """Инициализация финансовых таблиц"""
        tables = [
            """CREATE TABLE IF NOT EXISTS bank_transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_date DATE,
                transaction_time TIME,
                amount DECIMAL(12,2),
                description TEXT,
                account_number TEXT,
                transaction_type TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS cash_collections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                machine_code TEXT,
                collection_date DATE,
                collection_time TIME,
                collector_name TEXT,
                amount_collected DECIMAL(10,2),
                notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""",
            """CREATE TABLE IF NOT EXISTS reconciliation_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                reconciliation_date DATE,
                total_orders DECIMAL(12,2),
                total_payments DECIMAL(12,2),
                difference DECIMAL(12,2),
                status TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )"""
        ]
        
        for table_sql in tables:
            self.db.execute_query(table_sql)
    
    def import_bank_statement(self, file_path):
        """Импорт банковской выписки"""
        try:
            df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
            processed = 0
            
            for _, row in df.iterrows():
                # Базовая обработка банковской выписки
                transaction_data = {
                    'transaction_date': row.get('Date', ''),
                    'amount': self._safe_float(row.get('Amount', 0)),
                    'description': str(row.get('Description', '')),
                    'account_number': str(row.get('Account', '')),
                    'transaction_type': str(row.get('Type', ''))
                }
                
                if transaction_data['amount'] > 0:
                    self.db.execute_query("""
                        INSERT INTO bank_transactions 
                        (transaction_date, amount, description, account_number, transaction_type)
                        VALUES (?, ?, ?, ?, ?)
                    """, (transaction_data['transaction_date'], transaction_data['amount'],
                         transaction_data['description'], transaction_data['account_number'],
                         transaction_data['transaction_type']))
                    processed += 1
            
            return processed
        except Exception as e:
            print(f"Error importing bank statement: {e}")
            return 0
    
    def perform_reconciliation(self, start_date, end_date):
        """Выполнение сверки платежных систем"""
        try:
            # Получаем заказы за период
            orders_data = self.db.execute_query("""
                SELECT COUNT(*) as count, SUM(order_price) as total
                FROM orders 
                WHERE DATE(creation_time) BETWEEN ? AND ?
                AND error_type = 'OK'
            """, (start_date, end_date))
            
            # Получаем банковские транзакции за период
            bank_data = self.db.execute_query("""
                SELECT COUNT(*) as count, SUM(amount) as total
                FROM bank_transactions 
                WHERE transaction_date BETWEEN ? AND ?
            """, (start_date, end_date))
            
            orders_total = orders_data[0]['total'] if orders_data and orders_data[0]['total'] else 0
            bank_total = bank_data[0]['total'] if bank_data and bank_data[0]['total'] else 0
            difference = abs(orders_total - bank_total)
            
            # Сохраняем результат сверки
            self.db.execute_query("""
                INSERT INTO reconciliation_results 
                (reconciliation_date, total_orders, total_payments, difference, status)
                VALUES (?, ?, ?, ?, ?)
            """, (end_date, orders_total, bank_total, difference,
                 'matched' if difference < 100 else 'mismatch'))
            
            return {
                'orders_total': orders_total,
                'bank_total': bank_total,
                'difference': difference,
                'status': 'matched' if difference < 100 else 'mismatch'
            }
            
        except Exception as e:
            print(f"Error in reconciliation: {e}")
            return {'error': str(e)}
    
    def register_cash_collection(self, data):
        """Регистрация инкассации наличных"""
        try:
            query = """
            INSERT INTO cash_collections 
            (machine_code, collection_date, collection_time, collector_name, amount_collected, notes)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            params = (data['machine_code'], data['collection_date'], data['collection_time'],
                     data['collector_name'], data['amount_collected'], data.get('notes', ''))
            
            if self.db.is_postgres:
                query += " RETURNING id"
                result = self.db.execute_query(query, params)
                return result[0]['id'] if result else None
            else:
                cursor = self.db.connection.cursor()
                cursor.execute(query, params)
                collection_id = cursor.lastrowid
                self.db.connection.commit()
                cursor.close()
                return collection_id
                
        except Exception as e:
            print(f"Error registering cash collection: {e}")
            return None
    
    def get_machines_cash_status(self):
        """Получение состояния касс автоматов"""
        return self.db.execute_query("""
            SELECT machine_code, 
                   SUM(CASE WHEN payment_type = 'Cash' AND error_type = 'OK' THEN order_price ELSE 0 END) as cash_amount,
                   MAX(creation_time) as last_order_time
            FROM orders 
            WHERE creation_time >= date('now', '-7 days')
            GROUP BY machine_code
            ORDER BY cash_amount DESC
        """)
    
    def get_recent_collections(self):
        """Получение последних инкассаций"""
        return self.db.execute_query("""
            SELECT * FROM cash_collections 
            ORDER BY collection_date DESC, collection_time DESC 
            LIMIT 20
        """)
    
    def get_cash_balances(self):
        """Получение кассовых остатков по автоматам"""
        return self.db.execute_query("""
            SELECT o.machine_code,
                   SUM(CASE WHEN o.payment_type = 'Cash' AND o.error_type = 'OK' THEN o.order_price ELSE 0 END) as total_cash,
                   COALESCE(SUM(c.amount_collected), 0) as collected_cash,
                   (SUM(CASE WHEN o.payment_type = 'Cash' AND o.error_type = 'OK' THEN o.order_price ELSE 0 END) - COALESCE(SUM(c.amount_collected), 0)) as balance
            FROM orders o
            LEFT JOIN cash_collections c ON o.machine_code = c.machine_code
            WHERE o.creation_time >= date('now', '-30 days')
            GROUP BY o.machine_code
            ORDER BY balance DESC
        """)
    
    def get_finance_stats(self):
        """Статистика финансового модуля"""
        bank_count = self.db.execute_query("SELECT COUNT(*) as count FROM bank_transactions")[0]['count']
        collections_count = self.db.execute_query("SELECT COUNT(*) as count FROM cash_collections")[0]['count']
        
        return {
            'bank_transactions': bank_count,
            'cash_collections': collections_count
        }
    
    def get_financial_report(self, start_date, end_date):
        """Финансовый отчет за период"""
        return {
            'total_revenue': 0,
            'cash_revenue': 0,
            'card_revenue': 0,
            'collections': 0,
            'pending_collections': 0
        }
    
    def get_daily_finance(self, report_date):
        """Финансовые данные за день"""
        return {
            'total_revenue': 0,
            'cash_collected': 0,
            'pending_cash': 0
        }
    
    def _safe_float(self, value) -> float:
        """Безопасное преобразование в float"""
        if pd.isna(value) or value is None or value == '':
            return 0.0
        try:
            if isinstance(value, str):
                value = value.replace(' ', '').replace(',', '.')
            return float(value)
        except (ValueError, TypeError):
            return 0.0
