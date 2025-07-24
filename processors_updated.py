"""
VHM24R - Обновленные процессоры согласно ТЗ
Реализация правильной логики сопоставления заказов
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

class OrderProcessor:
    """
    Основной процессор сверки заказов согласно ТЗ:
    
    ЭТАП 1: Создание основы из Happy Workers
    ЭТАП 2: Обогащение данными из VendHub  
    ЭТАП 3: Добавление фискальных данных (для Cash)
    ЭТАП 4: Добавление данных платежных шлюзов (для Custom payment)
    ЭТАП 5: Финальная классификация и установка статусов
    """
    
    def __init__(self, db):
        self.db = db
        
        # Настройки временных окон согласно ТЗ (±1 минута для всех)
        self.time_tolerance = 60  # секунд
        self.amount_tolerance = 0.01  # сумм
        
        # Статусы заказов согласно ТЗ
        self.ORDER_STATUSES = {
            'hw_only': 'Только данные Happy Workers',
            'vendhub_only': 'Только данные VendHub',
            'payme_only': 'Только транзакция Payme',
            'click_only': 'Только транзакция Click',
            'uzum_only': 'Только транзакция Uzum',
            'matched': 'HW + VendHub сопоставлены',
            'fully_matched': 'Все данные сопоставлены',
            'fiscal_mismatch': 'Не найден фискальный чек',
            'gateway_mismatch': 'Не найдена транзакция шлюза',
            'ambiguous_match': 'Неоднозначное сопоставление',
            'number_conflict': 'Конфликт номеров заказов',
            'time_out_of_range': 'Время вне допустимого окна',
            'price_mismatch': 'Расхождение в сумме'
        }
        
        # Маппинг колонок согласно ТЗ
        self.COLUMN_MAPPINGS = self._init_column_mappings()
    
    def _init_column_mappings(self) -> Dict[str, Dict[str, List[str]]]:
        """Инициализация маппинга колонок согласно ТЗ"""
        return {
            'happy_workers': {
                'order_number': ['order number', 'номер заказа', 'order_number'],
                'machine_code': ['machine code', 'код автомата', 'machine_code'],
                'address': ['address', 'адрес', 'address'],
                'goods_name': ['goods name', 'название товара', 'goods_name'],
                'taste_name': ['taste name', 'вкус', 'taste_name'],
                'order_type': ['order type', 'тип заказа', 'order_type'],
                'order_resource': ['order resource', 'источник заказа', 'order_resource'],
                'order_price': ['order price', 'цена заказа', 'order_price', 'price'],
                'creation_time': ['creation time', 'время создания', 'creation_time'],
                'paying_time': ['paying time', 'время оплаты', 'paying_time'],
                'brewing_time': ['brewing time', 'время приготовления', 'brewing_time'],
                'delivery_time': ['delivery time', 'время выдачи', 'delivery_time'],
                'refund_time': ['refund time', 'время возврата', 'refund_time'],
                'payment_status': ['payment status', 'статус платежа', 'payment_status'],
                'brew_status': ['brew status', 'статус приготовления', 'brew_status'],
                'reason': ['reason', 'причина', 'reason']
            },
            'vendhub': {
                'order_number': ['order number', 'номер заказа', 'order_number'],
                'event_time': ['time', 'время', 'event_time', 'order_time'],
                'goods_name': ['goods name', 'название товара', 'goods_name'],
                'order_price': ['order price', 'цена заказа', 'order_price', 'price'],
                'machine_code': ['machine code', 'код автомата', 'machine_code'],
                'machine_category': ['machine category', 'категория автомата', 'machine_category'],
                'payment_type': ['payment type', 'тип платежа', 'payment_type'],
                'order_resource': ['order resource', 'ресурс заказа', 'order_resource'],
                'goods_id': ['goods id', 'ид товара', 'goods_id'],
                'username': ['username', 'имя пользователя', 'username'],
                'bonus_amount': ['amount of accrued bonus', 'размер бонуса', 'bonus_amount'],
                'ikpu': ['икпу', 'ikpu'],
                'barcode': ['штрихкод', 'barcode'],
                'marking': ['маркировка', 'marking'],
                'packaging': ['упаковка', 'packaging']
            },
            'fiscal_bills': {
                'fiscal_check_number': ['fiscal_check_number', 'номер чека', 'fiscal id'],
                'fiscal_time': ['fiscal_time', 'время фискализации', 'time', 'дата'],
                'amount': ['amount', 'сумма', 'price'],
                'taxpayer_id': ['taxpayer_id', 'инн', 'taxpayer id'],
                'cash_register_id': ['cash_register_id', 'ид кассы', 'cash register id'],
                'shift_number': ['shift_number', 'номер смены', 'shift number'],
                'receipt_type': ['receipt_type', 'тип чека', 'receipt type']
            },
            'payme': {
                'transaction_id': ['transaction_id', 'ид транзакции', 'transaction id'],
                'transaction_time': ['transaction_time', 'время транзакции', 'time'],
                'amount': ['amount', 'сумма', 'transaction amount'],
                'masked_pan': ['masked_pan', 'номер карты', 'card'],
                'merchant_id': ['merchant_id', 'ид мерчанта', 'merchant id'],
                'terminal_id': ['terminal_id', 'ид терминала', 'terminal id'],
                'commission': ['commission', 'комиссия'],
                'status': ['status', 'статус'],
                'username': ['username', 'имя пользователя'],
                'phone_number': ['phone_number', 'номер телефона', 'phone'],
                'reference_number': ['reference_number', 'референс номер']
            },
            'click': {
                'transaction_id': ['transaction_id', 'ид транзакции', 'transaction id'],
                'transaction_time': ['transaction_time', 'время транзакции', 'time'],
                'amount': ['amount', 'сумма', 'transaction amount'],
                'card_number': ['card_number', 'номер карты', 'card'],
                'merchant_id': ['merchant_id', 'ид мерчанта', 'merchant id'],
                'service_id': ['service_id', 'ид сервиса', 'service id'],
                'commission': ['commission', 'комиссия'],
                'status': ['status', 'статус'],
                'error_code': ['error_code', 'код ошибки'],
                'click_trans_id': ['click_trans_id', 'внутренний ид'],
                'merchant_trans_id': ['merchant_trans_id', 'ид транзакции мерчанта']
            },
            'uzum': {
                'transaction_id': ['transaction_id', 'ид транзакции', 'transaction id'],
                'transaction_time': ['transaction_time', 'время транзакции', 'time'],
                'amount': ['amount', 'сумма', 'transaction amount'],
                'masked_pan': ['masked_pan', 'номер карты', 'card'],
                'shop_id': ['shop_id', 'ид магазина', 'shop id'],
                'merchant_id': ['merchant_id', 'ид мерчанта', 'merchant id'],
                'commission': ['commission', 'комиссия'],
                'status': ['status', 'статус'],
                'username': ['username', 'имя пользователя'],
                'order_id': ['order_id', 'ид заказа'],
                'cashback_amount': ['cashback_amount', 'сумма кэшбэка', 'cashback']
            }
        }
    
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
        ЭТАП 1: Создание основы из Happy Workers
        Все заказы создаются из HW как основа со статусом 'hw_only'
        """
        try:
            processed = 0
            df = self._read_file(file_path)
            
            if df is None or df.empty:
                return 0
            
            # Маппинг колонок
            column_mapping = self._map_columns(df.columns, 'happy_workers')
            if not column_mapping:
                print("No recognizable HW columns found")
                return 0
            
            for _, row in df.iterrows():
                order_number = str(row.get(column_mapping.get('order_number', ''), ''))
                if not order_number or order_number == 'nan':
                    continue
                
                # Проверяем на отмененные заказы (есть Refund time)
                refund_time = row.get(column_mapping.get('refund_time', ''))
                if refund_time and not pd.isna(refund_time):
                    print(f"Skipping refunded order: {order_number}")
                    continue
                
                # Создаем заказ согласно новой структуре БД
                order_data = {
                    'order_number': order_number,
                    'machine_code': str(row.get(column_mapping.get('machine_code', ''), '')),
                    'address': str(row.get(column_mapping.get('address', ''), '')),
                    'goods_name': str(row.get(column_mapping.get('goods_name', ''), '')),
                    'taste_name': str(row.get(column_mapping.get('taste_name', ''), '')),
                    'order_type': str(row.get(column_mapping.get('order_type', ''), '')),
                    'order_resource': str(row.get(column_mapping.get('order_resource', ''), '')),
                    'order_price': self._safe_float(row.get(column_mapping.get('order_price', ''), 0)),
                    'creation_time': self._parse_datetime(row.get(column_mapping.get('creation_time', ''))),
                    'paying_time': self._parse_datetime(row.get(column_mapping.get('paying_time', ''))),
                    'brewing_time': self._parse_datetime(row.get(column_mapping.get('brewing_time', ''))),
                    'delivery_time': self._parse_datetime(row.get(column_mapping.get('delivery_time', ''))),
                    'refund_time': self._parse_datetime(refund_time),
                    'payment_status': str(row.get(column_mapping.get('payment_status', ''), '')),
                    'brew_status': str(row.get(column_mapping.get('brew_status', ''), '')),
                    'reason': str(row.get(column_mapping.get('reason', ''), '')),
                    
                    # Статусы согласно ТЗ
                    'match_status': 'hw_only',
                    'source': 'happy_workers',
                    'matched_sources': json.dumps(['happy_workers']),
                    'fiscal_matched': False,
                    'gateway_matched': False
                }
                
                # Нормализуем тип платежа
                order_data['payment_type'] = self._normalize_payment_type(order_data['order_resource'])
                
                self._insert_or_update_order(order_data)
                processed += 1
            
            print(f"Processed {processed} HW records")
            return processed
            
        except Exception as e:
            print(f"Error processing HW file: {e}")
            return 0
    
    def process_vendhub_file(self, file_path: str) -> int:
        """
        ЭТАП 2: Обогащение данными из VendHub
        Поиск по order_number + machine_code, проверка временного окна и цены
        """
        try:
            processed = 0
            df = self._read_file(file_path)
            
            if df is None or df.empty:
                return 0
            
            column_mapping = self._map_columns(df.columns, 'vendhub')
            if not column_mapping:
                print("No recognizable VendHub columns found")
                return 0
            
            for _, row in df.iterrows():
                order_number = str(row.get(column_mapping.get('order_number', ''), ''))
                if not order_number or order_number == 'nan':
                    continue
                
                machine_code = str(row.get(column_mapping.get('machine_code', ''), ''))
                event_time = self._parse_datetime(row.get(column_mapping.get('event_time', '')))
                order_price = self._safe_float(row.get(column_mapping.get('order_price', ''), 0))
                
                if not event_time or order_price <= 0:
                    continue
                
                # Ищем соответствующий HW заказ
                existing_order = self._find_hw_order(order_number, machine_code)
                
                if existing_order:
                    # Проверяем временное окно согласно ТЗ
                    if self._validate_vendhub_time_window(existing_order, event_time):
                        # Проверяем цену (точное совпадение)
                        if abs(existing_order['order_price'] - order_price) <= self.amount_tolerance:
                            # Обогащаем данными из VendHub
                            vendhub_data = {
                                'event_time': event_time,
                                'machine_category': str(row.get(column_mapping.get('machine_category', ''), '')),
                                'payment_type': str(row.get(column_mapping.get('payment_type', ''), '')),
                                'goods_id': str(row.get(column_mapping.get('goods_id', ''), '')),
                                'username': str(row.get(column_mapping.get('username', ''), '')),
                                'bonus_amount': self._safe_float(row.get(column_mapping.get('bonus_amount', ''), 0)),
                                'ikpu': str(row.get(column_mapping.get('ikpu', ''), '')),
                                'barcode': str(row.get(column_mapping.get('barcode', ''), '')),
                                'marking': str(row.get(column_mapping.get('marking', ''), '')),
                                'packaging': str(row.get(column_mapping.get('packaging', ''), '')),
                                'match_status': 'matched',
                                'matched_sources': json.dumps(['happy_workers', 'vendhub'])
                            }
                            
                            self._update_order(existing_order['id'], vendhub_data)
                            processed += 1
                        else:
                            # Расхождение в цене
                            self._log_mismatch(existing_order['id'], 'price_mismatch', 
                                             f"HW price: {existing_order['order_price']}, VH price: {order_price}")
                    else:
                        # Время вне окна
                        self._log_mismatch(existing_order['id'], 'time_out_of_range', 
                                         f"VendHub time {event_time} outside HW window")
                else:
                    # Создаем новый заказ только из VendHub
                    vendhub_order = {
                        'order_number': order_number,
                        'machine_code': machine_code,
                        'event_time': event_time,
                        'order_price': order_price,
                        'goods_name': str(row.get(column_mapping.get('goods_name', ''), '')),
                        'payment_type': str(row.get(column_mapping.get('payment_type', ''), '')),
                        'match_status': 'vendhub_only',
                        'source': 'vendhub',
                        'matched_sources': json.dumps(['vendhub'])
                    }
                    
                    self._insert_or_update_order(vendhub_order)
                    processed += 1
            
            print(f"Processed {processed} VendHub records")
            return processed
            
        except Exception as e:
            print(f"Error processing VendHub file: {e}")
            return 0
    
    def process_fiscal_file(self, file_path: str) -> int:
        """
        ЭТАП 3: Добавление фискальных данных
        Только для Cash payment заказов, временное окно ±1 минута от paying_time
        """
        try:
            processed = 0
            df = self._read_file(file_path)
            
            if df is None or df.empty:
                return 0
            
            column_mapping = self._map_columns(df.columns, 'fiscal_bills')
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
                    fiscal_data = {
                        'fiscal_time': fiscal_time,
                        'fiscal_amount': amount,
                        'fiscal_check_number': str(row.get(column_mapping.get('fiscal_check_number', ''), '')),
                        'taxpayer_id': str(row.get(column_mapping.get('taxpayer_id', ''), '')),
                        'cash_register_id': str(row.get(column_mapping.get('cash_register_id', ''), '')),
                        'shift_number': self._safe_int(row.get(column_mapping.get('shift_number', ''), 0)),
                        'receipt_type': str(row.get(column_mapping.get('receipt_type', ''), '')),
                        'fiscal_matched': True
                    }
                    
                    # Обновляем статус
                    if order['match_status'] == 'matched':
                        fiscal_data['match_status'] = 'fully_matched'
                    
                    self._update_order(order['id'], fiscal_data)
                    processed += 1
                else:
                    # Сохраняем несопоставленную запись
                    self._save_unmatched_record('fiscal', row.to_dict(), fiscal_time, amount)
            
            print(f"Processed {processed} fiscal records")
            return processed
            
        except Exception as e:
            print(f"Error processing fiscal file: {e}")
            return 0
    
    def process_gateway_file(self, file_path: str, gateway_type: str) -> int:
        """
        ЭТАП 4: Добавление данных платежных шлюзов
        Только для Custom payment заказов, ПРЯМОЕ сравнение сумм (БЕЗ вычитания комиссии!)
        """
        try:
            processed = 0
            df = self._read_file(file_path)
            
            if df is None or df.empty:
                return 0
            
            column_mapping = self._map_columns(df.columns, gateway_type)
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
                    gateway_data = {
                        'gateway_time': transaction_time,
                        'gateway_amount': amount,  # ПРЯМОЕ сравнение согласно ТЗ!
                        'payment_gateway': gateway_type,
                        'transaction_id': str(row.get(column_mapping.get('transaction_id', ''), '')),
                        'gateway_status': str(row.get(column_mapping.get('status', ''), '')),
                        'gateway_matched': True
                    }
                    
                    # Специфичные поля для каждого шлюза
                    if gateway_type == 'payme':
                        gateway_data.update({
                            'payme_transaction_id': gateway_data['transaction_id'],
                            'card_number': str(row.get(column_mapping.get('masked_pan', ''), '')),
                            'terminal_id': str(row.get(column_mapping.get('terminal_id', ''), '')),
                            'phone_number': str(row.get(column_mapping.get('phone_number', ''), '')),
                            'gateway_username': str(row.get(column_mapping.get('username', ''), ''))
                        })
                    elif gateway_type == 'click':
                        gateway_data.update({
                            'click_transaction_id': gateway_data['transaction_id'],
                            'card_number': str(row.get(column_mapping.get('card_number', ''), '')),
                            'service_id': str(row.get(column_mapping.get('service_id', ''), '')),
                            'click_trans_id': str(row.get(column_mapping.get('click_trans_id', ''), ''))
                        })
                    elif gateway_type == 'uzum':
                        gateway_data.update({
                            'uzum_transaction_id': gateway_data['transaction_id'],
                            'card_number': str(row.get(column_mapping.get('masked_pan', ''), '')),
                            'shop_id': str(row.get(column_mapping.get('shop_id', ''), '')),
                            'cashback_amount': self._safe_float(row.get(column_mapping.get('cashback_amount', ''), 0)),
                            'gateway_username': str(row.get(column_mapping.get('username', ''), ''))
                        })
                    
                    # Добавляем общие поля
                    gateway_data['merchant_id'] = str(row.get(column_mapping.get('merchant_id', ''), ''))
                    
                    # Обновляем статус
                    if order['match_status'] == 'matched':
                        gateway_data['match_status'] = 'fully_matched'
                    
                    self._update_order(order['id'], gateway_data)
                    processed += 1
                else:
                    # Создаем новый заказ только из шлюза
                    gateway_order = {
                        'gateway_time': transaction_time,
                        'gateway_amount': amount,
                        'payment_gateway': gateway_type,
                        'transaction_id': str(row.get(column_mapping.get('transaction_id', ''), '')),
                        'order_resource': 'Custom payment',
                        'payment_type': gateway_type.capitalize(),
                        'match_status': f'{gateway_type}_only',
                        'source': gateway_type,
                        'matched_sources': json.dumps([gateway_type])
                    }
                    
                    self._insert_or_update_order(gateway_order)
                    processed += 1
            
            print(f"Processed {processed} {gateway_type} records")
            return processed
            
        except Exception as e:
            print(f"Error processing {gateway_type} file: {e}")
            return 0
    
    def run_matching(self) -> Dict[str, int]:
        """
        ЭТАП 5: Финальная классификация и установка статусов
        Определение финального статуса каждого заказа
        """
        print("Running final matching and status classification...")
        
        try:
            # Получаем все заказы для финальной классификации
            orders = self.db.execute_query("SELECT * FROM orders")
            
            for order in orders:
                final_status = self._determine_final_status(order)
                details = self._generate_status_details(order, final_status)
                
                self._update_order(order['id'], {
                    'match_status': final_status,
                    'mismatch_details': details
                })
            
            # Получаем финальную статистику
            stats = self._get_final_statistics()
            
            print("Final matching completed successfully")
            return stats
            
        except Exception as e:
            print(f"Error in final matching: {e}")
            return {'total': 0}
    
    def _determine_final_status(self, order: Dict[str, Any]) -> str:
        """
        Определение финального статуса заказа согласно ТЗ
        """
        current_status = order.get('match_status', 'unmatched')
        order_resource = order.get('order_resource', '')
        payment_type = order.get('payment_type', '')
        
        # Если уже fully_matched, оставляем как есть
        if current_status == 'fully_matched':
            return 'fully_matched'
        
        # Для заказов только из одного источника
        if current_status in ['hw_only', 'vendhub_only', 'payme_only', 'click_only', 'uzum_only']:
            return current_status
        
        # Для сопоставленных HW + VendHub заказов
        if current_status == 'matched':
            # Проверяем необходимость дополнительных данных
            if order_resource == 'Cash payment' or payment_type == 'Cash':
                if order.get('fiscal_matched', False):
                    return 'fully_matched'
                else:
                    return 'fiscal_mismatch'
            
            elif order_resource == 'Custom payment' or payment_type in ['Payme', 'Click', 'Uzum']:
                if order.get('gateway_matched', False):
                    return 'fully_matched'
                else:
                    return 'gateway_mismatch'
            
            elif order_resource in ['Test Shipment', 'VIP']:
                return 'fully_matched'
            
            else:
                return 'matched'
        
        # Для проблемных статусов
        if current_status in ['time_out_of_range', 'price_mismatch', 'number_conflict', 'ambiguous_match']:
            return current_status
        
        return 'unmatched'
    
    def _generate_status_details(self, order: Dict[str, Any], status: str) -> str:
        """Генерация детального описания статуса"""
        details = []
        
        if status == 'fully_matched':
            details.append("Все данные корректно сопоставлены")
        elif status == 'matched':
            details.append("HW и VendHub сопоставлены, дополнительные данные не требуются")
        elif status == 'fiscal_mismatch':
            details.append("Cash заказ без соответствующего фискального чека")
        elif status == 'gateway_mismatch':
            details.append("Custom payment заказ без соответствующей транзакции в платежном шлюзе")
        elif status == 'hw_only':
            details.append("Заказ найден только в Happy Workers")
        elif status == 'vendhub_only':
            details.append("Заказ найден только в VendHub")
        elif status in ['payme_only', 'click_only', 'uzum_only']:
            details.append(f"Найдена только транзакция в {status.replace('_only', '').title()}")
        elif status == 'time_out_of_range':
            details.append("Время события вне допустимого временного окна")
        elif status == 'price_mismatch':
            details.append("Расхождение в сумме заказа между источниками")
        elif status == 'number_conflict':
            details.append("Конфликт номеров заказов при совпадении времени и суммы")
        elif status == 'ambiguous_match':
            details.append("Найдено несколько кандидатов для сопоставления")
        
        return "; ".join(details)
    
    # ========================================================================
    # ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    # ========================================================================
    
    def _read_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """Чтение файла с обработкой ошибок"""
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
    
    def _map_columns(self, columns, file_type: str) -> Optional[Dict[str, str]]:
        """Маппинг колонок файла"""
        column_mapping = {}
        columns_lower = [str(col).lower() for col in columns]
        
        mappings = self.COLUMN_MAPPINGS.get(file_type, {})
        
        for field, keywords in mappings.items():
            for i, col in enumerate(columns_lower):
                if any(keyword.lower() in col for keyword in keywords):
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
    
    def _safe_int(self, value) -> int:
        """Безопасное преобразование в int"""
        if pd.isna(value) or value is None or value == '':
            return 0
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return 0
    
    def _normalize_payment_type(self, payment_type: str) -> str:
        """Нормализация типа платежа согласно ТЗ"""
        if not payment_type or pd.isna(payment_type):
            return 'Unknown'
        
        payment_type = str(payment_type).lower().strip()
        
        if 'cash' in payment_type or 'наличные' in payment_type:
            return 'Cash'
        elif 'custom' in payment_type or 'кастом' in payment_type:
            return 'Custom payment'
        elif 'test' in payment_type or 'тест' in payment_type:
            return 'Test'
        elif 'vip' in payment_type:
            return 'VIP'
        else:
            return 'Custom payment'  # По умолчанию
    
    def _insert_or_update_order(self, order_data: Dict[str, Any]):
        """Вставка или обновление заказа в БД"""
        try:
            # Подготавливаем данные для вставки
            fields = []
            values = []
            placeholders = []
            
            for key, value in order_data.items():
                if value is not None:
                    fields.append(key)
                    values.append(value)
                    placeholders.append('?')
            
            # Формируем запрос UPSERT
            query = f"""
            INSERT OR REPLACE INTO orders ({', '.join(fields)})
            VALUES ({', '.join(placeholders)})
            """
            
            self.db.execute_query(query, tuple(values))
            
        except Exception as e:
            print(f"Error inserting/updating order: {e}")
    
    def _update_order(self, order_id: int, update_data: Dict[str, Any]):
        """Обновление существующего заказа"""
        try:
            set_clauses = []
            values = []
            
            for key, value in update_data.items():
                if value is not None:
                    set_clauses.append(f"{key} = ?")
                    values.append(value)
            
            if set_clauses:
                query = f"""
                UPDATE orders 
                SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """
                values.append(order_id)
                
                self.db.execute_query(query, tuple(values))
            
        except Exception as e:
            print(f"Error updating order {order_id}: {e}")
    
    def _find_hw_order(self, order_number: str, machine_code: str) -> Optional[Dict[str, Any]]:
        """Поиск заказа Happy Workers по ключам"""
        try:
            query = """
            SELECT * FROM orders 
            WHERE order_number = ? AND machine_code = ?
            AND source = 'happy_workers'
            LIMIT 1
            """
            
            results = self.db.execute_query(query, (order_number, machine_code))
            return results[0] if results else None
            
        except Exception as e:
            print(f"Error finding HW order: {e}")
            return None
    
    def _validate_vendhub_time_window(self, hw_order: Dict[str, Any], event_time: datetime) -> bool:
        """
        Проверка временного окна VendHub согласно ТЗ:
        Creation time ≤ Event time ≤ Delivery time (±1 мин)
        """
        try:
            creation_time = hw_order.get('creation_time')
            delivery_time = hw_order.get('delivery_time')
            refund_time = hw_order.get('refund_time')
            
            if not creation_time:
                return False
            
            # Определяем конец временного окна
            end_time = refund_time if refund_time else delivery_time
            if not end_time:
                # Если нет delivery_time, даем окно 10 минут от creation
                end_time = creation_time + timedelta(minutes=10)
            
            # Проверяем с допуском ±1 минута
            window_start = creation_time - timedelta(seconds=self.time_tolerance)
            window_end = end_time + timedelta(seconds=self.time_tolerance)
            
            return window_start <= event_time <= window_end
            
        except Exception as e:
            print(f"Error validating VendHub time window: {e}")
            return False
    
    def _find_cash_orders_for_fiscal(self, fiscal_time: datetime, amount: float) -> List[Dict[str, Any]]:
        """Поиск Cash заказов для фискального чека"""
        try:
            time_start = fiscal_time - timedelta(seconds=self.time_tolerance)
            time_end = fiscal_time + timedelta(seconds=self.time_tolerance)
            
            query = """
            SELECT * FROM orders 
            WHERE (order_resource = 'Cash payment' OR payment_type = 'Cash')
            AND paying_time BETWEEN ? AND ?
            AND ABS(order_price - ?) <= ?
            AND (fiscal_matched = 0 OR fiscal_matched IS NULL)
            ORDER BY ABS(julianday(paying_time) - julianday(?)) ASC
            LIMIT 1
            """
            
            return self.db.execute_query(query, (time_start, time_end, amount, self.amount_tolerance, fiscal_time))
            
        except Exception as e:
            print(f"Error finding cash orders for fiscal: {e}")
            return []
    
    def _find_custom_payment_orders_for_gateway(self, transaction_time: datetime, amount: float) -> List[Dict[str, Any]]:
        """Поиск Custom payment заказов для платежного шлюза"""
        try:
            time_start = transaction_time - timedelta(seconds=self.time_tolerance)
            time_end = transaction_time + timedelta(seconds=self.time_tolerance)
            
            query = """
            SELECT * FROM orders 
            WHERE (order_resource = 'Custom payment' OR payment_type IN ('Payme', 'Click', 'Uzum'))
            AND paying_time BETWEEN ? AND ?
            AND ABS(order_price - ?) <= ?
            AND (gateway_matched = 0 OR gateway_matched IS NULL)
            ORDER BY ABS(julianday(paying_time) - julianday(?)) ASC
            LIMIT 1
            """
            
            return self.db.execute_query(query, (time_start, time_end, amount, self.amount_tolerance, transaction_time))
            
        except Exception as e:
            print(f"Error finding custom payment orders for gateway: {e}")
            return []
    
    def _log_mismatch(self, order_id: int, mismatch_type: str, details: str):
        """Логирование несоответствия"""
        try:
            mismatch_data = {
                'match_status': mismatch_type,
                'mismatch_details': details
            }
            
            self._update_order(order_id, mismatch_data)
            
        except Exception as e:
            print(f"Error logging mismatch: {e}")
    
    def _save_unmatched_record(self, record_type: str, record_data: Dict[str, Any], 
                              record_time: datetime, amount: float):
        """Сохранение несопоставленной записи"""
        try:
            query = """
            INSERT INTO unmatched_records (record_type, record_data, record_time, record_amount)
            VALUES (?, ?, ?, ?)
            """
            
            self.db.execute_query(query, (
                record_type,
                json.dumps(record_data, default=str),
                record_time,
                amount
            ))
            
        except Exception as e:
            print(f"Error saving unmatched record: {e}")
    
    def _get_final_statistics(self) -> Dict[str, int]:
        """Получение финальной статистики"""
        try:
            stats_query = """
            SELECT 
                match_status,
                COUNT(*) as count
            FROM orders 
            GROUP BY match_status
            """
            
            results = self.db.execute_query(stats_query)
            stats = {result['match_status']: result['count'] for result in results}
            
            # Добавляем общее количество
            total = sum(stats.values())
            stats['total'] = total
            
            return stats
            
        except Exception as e:
            print(f"Error getting final statistics: {e}")
            return {'total': 0}


# Сохраняем существующие процессоры для совместимости
class RecipeProcessor:
    """Процессор управления рецептурой и ингредиентами"""
    
    def __init__(self, db):
        self.db = db
    
    def get_products(self):
        """Получение списка продуктов"""
        return []
    
    def get_ingredients(self):
        """Получение списка ингредиентов"""
        return []
    
    def get_recipe_stats(self):
        """Статистика рецептур"""
        return {
            'products_count': 0,
            'ingredients_count': 0,
            'recipes_count': 0
        }


class FinanceProcessor:
    """Процессор финансовой сверки и инкассации"""
    
    def __init__(self, db):
        self.db = db
    
    def get_finance_stats(self):
        """Статистика финансового модуля"""
        return {
            'bank_transactions': 0,
            'cash_collections': 0
        }
    
    def get_cash_balances(self):
        """Получение кассовых остатков по автоматам"""
        return []
    
    def get_machines_cash_status(self):
        """Получение состояния касс автоматов"""
        return []
    
    def get_recent_collections(self):
        """Получение последних инкассаций"""
        return []
