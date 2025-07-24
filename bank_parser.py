"""
VHM24R - Модуль парсинга банковских выписок
Обработка банковских выписок различных форматов для финансовой сверки
"""

import pandas as pd
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Any, Tuple
import json

class BankStatementParser:
    """
    Парсер банковских выписок различных форматов
    Автоматическое определение платежных систем и извлечение данных
    """
    
    def __init__(self):
        # Паттерны для определения платежных систем
        self.payment_patterns = {
            'payme': [
                r'PAYME\s*TASHKENT',
                r'OOO\s*PAYME',
                r'ПЭЙМИ',
                r'PAYME\s*UZ',
                r'PAYME.*UZBEKISTAN'
            ],
            'click': [
                r'CLICK\s*UZBEKISTAN',
                r'ООО\s*КЛИК',
                r'CLICK\s*EVOLUTION',
                r'CLICK\s*UZ',
                r'INFINITY\s*CLICK'
            ],
            'uzum': [
                r'UZUM\s*BANK',
                r'UZUM\s*NASIYA',
                r'УЗУМ',
                r'UZUM\s*PAY',
                r'UZUM.*TASHKENT'
            ],
            'cash': [
                r'ИНКАССАЦИЯ',
                r'НАЛИЧНЫЕ',
                r'CASH\s*COLLECTION',
                r'СДАЧА\s*ВЫРУЧКИ',
                r'ТОРГОВАЯ\s*ВЫРУЧКА'
            ]
        }
        
        # Комиссии платежных систем (согласно ТЗ)
        self.commission_rates = {
            'payme': 0.02,  # 2%
            'click': 0.02,  # 2%
            'uzum': 0.02    # 2%
        }
    
    def parse_statement(self, file_path: str, bank_account: Optional[str] = None) -> Dict[str, Any]:
        """
        Основной метод парсинга банковской выписки
        """
        try:
            # Определяем формат файла и читаем данные
            df = self._read_statement_file(file_path)
            
            if df is None or df.empty:
                return {
                    'status': 'error',
                    'message': 'Could not read or empty file',
                    'transactions': []
                }
            
            # Нормализуем названия колонок
            df = self._normalize_columns(df)
            
            # Парсим транзакции
            transactions = []
            for _, row in df.iterrows():
                transaction = self._parse_transaction(row, bank_account)
                if transaction:
                    transactions.append(transaction)
            
            # Группируем по платежным системам
            grouped_stats = self._group_by_payment_system(transactions)
            
            return {
                'status': 'success',
                'total_transactions': len(transactions),
                'transactions': transactions,
                'grouped_stats': grouped_stats,
                'file_path': file_path
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'Error parsing statement: {str(e)}',
                'transactions': []
            }
    
    def _read_statement_file(self, file_path: str) -> Optional[pd.DataFrame]:
        """
        Чтение файла выписки в зависимости от формата
        """
        try:
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                return pd.read_excel(file_path)
            elif file_path.endswith('.csv'):
                # Пробуем разные кодировки и разделители
                for encoding in ['utf-8', 'cp1251', 'windows-1251', 'iso-8859-1']:
                    for sep in [',', ';', '\t']:
                        try:
                            df = pd.read_csv(file_path, encoding=encoding, sep=sep)
                            if len(df.columns) > 3:  # Минимум 3 колонки для банковской выписки
                                return df
                        except:
                            continue
            elif file_path.endswith('.txt'):
                # Для текстовых файлов пробуем табуляцию
                return pd.read_csv(file_path, sep='\t', encoding='utf-8')
            
            return None
            
        except Exception as e:
            print(f"Error reading statement file: {e}")
            return None
    
    def _normalize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Нормализация названий колонок
        """
        # Создаем маппинг стандартных названий
        column_mapping = {}
        
        for col in df.columns:
            col_lower = str(col).lower().strip()
            
            # Дата
            if any(word in col_lower for word in ['дата', 'date', 'время', 'time']):
                column_mapping[col] = 'transaction_date'
            
            # Сумма
            elif any(word in col_lower for word in ['сумма', 'amount', 'sum', 'деbet', 'credit', 'дебет', 'кредит']):
                if 'дебет' in col_lower or 'debit' in col_lower:
                    column_mapping[col] = 'debit_amount'
                elif 'кредит' in col_lower or 'credit' in col_lower:
                    column_mapping[col] = 'credit_amount'
                else:
                    column_mapping[col] = 'amount'
            
            # Описание
            elif any(word in col_lower for word in ['описание', 'description', 'назначение', 'purpose', 'детали', 'details']):
                column_mapping[col] = 'description'
            
            # Контрагент
            elif any(word in col_lower for word in ['контрагент', 'counterparty', 'получатель', 'отправитель', 'плательщик']):
                column_mapping[col] = 'counterparty'
            
            # Номер счета
            elif any(word in col_lower for word in ['счет', 'account', 'номер']):
                column_mapping[col] = 'account_number'
            
            # Референс
            elif any(word in col_lower for word in ['референс', 'reference', 'номер документа', 'doc_number']):
                column_mapping[col] = 'reference_number'
        
        # Переименовываем колонки
        df_renamed = df.rename(columns=column_mapping)
        
        return df_renamed
    
    def _parse_transaction(self, row: pd.Series, bank_account: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Парсинг одной транзакции
        """
        try:
            # Извлекаем основные поля
            transaction_date = self._extract_date(row)
            amount = self._extract_amount(row)
            description = self._extract_description(row)
            counterparty = self._extract_counterparty(row)
            reference = self._extract_reference(row)
            
            if not transaction_date or amount == 0:
                return None
            
            # Определяем тип транзакции
            transaction_type = self._determine_transaction_type(row, amount)
            
            # Определяем платежную систему
            payment_system = self._identify_payment_system(description, counterparty)
            
            # Рассчитываем комиссию
            commission_info = self._calculate_commission(amount, payment_system)
            
            return {
                'transaction_date': transaction_date,
                'transaction_time': self._extract_time(row),
                'amount': abs(amount),
                'transaction_type': transaction_type,
                'description': description,
                'counterparty': counterparty,
                'reference_number': reference,
                'payment_system': payment_system,
                'bank_account': bank_account,
                'commission_rate': commission_info['rate'],
                'commission_amount': commission_info['amount'],
                'net_amount': commission_info['net_amount'],
                'raw_data': row.to_dict()
            }
            
        except Exception as e:
            print(f"Error parsing transaction: {e}")
            return None
    
    def _extract_date(self, row: pd.Series) -> Optional[str]:
        """
        Извлечение даты транзакции
        """
        date_fields = ['transaction_date', 'дата', 'date']
        
        for field in date_fields:
            if field in row and pd.notna(row[field]):
                date_value = row[field]
                
                # Если уже datetime
                if isinstance(date_value, (datetime, date)):
                    return date_value.strftime('%Y-%m-%d')
                
                # Парсим строку
                if isinstance(date_value, str):
                    return self._parse_date_string(date_value)
        
        return None
    
    def _extract_time(self, row: pd.Series) -> Optional[str]:
        """
        Извлечение времени транзакции
        """
        # Ищем время в дате или отдельном поле
        date_fields = ['transaction_date', 'дата', 'date', 'время', 'time']
        
        for field in date_fields:
            if field in row and pd.notna(row[field]):
                value = row[field]
                
                if isinstance(value, datetime):
                    return value.strftime('%H:%M:%S')
                elif isinstance(value, str):
                    # Ищем время в строке
                    time_match = re.search(r'(\d{2}:\d{2}:\d{2})', value)
                    if time_match:
                        return time_match.group(1)
                    
                    time_match = re.search(r'(\d{2}:\d{2})', value)
                    if time_match:
                        return time_match.group(1) + ':00'
        
        return None
    
    def _extract_amount(self, row: pd.Series) -> float:
        """
        Извлечение суммы транзакции
        """
        amount_fields = ['amount', 'сумма', 'credit_amount', 'debit_amount', 'кредит', 'дебет']
        
        for field in amount_fields:
            if field in row and pd.notna(row[field]):
                amount_value = row[field]
                
                if isinstance(amount_value, (int, float)):
                    return float(amount_value)
                elif isinstance(amount_value, str):
                    # Очищаем строку и парсим
                    clean_amount = re.sub(r'[^\d\.,\-]', '', amount_value)
                    clean_amount = clean_amount.replace(',', '.')
                    
                    try:
                        return float(clean_amount)
                    except ValueError:
                        continue
        
        return 0.0
    
    def _extract_description(self, row: pd.Series) -> str:
        """
        Извлечение описания транзакции
        """
        desc_fields = ['description', 'описание', 'назначение', 'purpose', 'детали']
        
        for field in desc_fields:
            if field in row and pd.notna(row[field]):
                return str(row[field]).strip()
        
        return ''
    
    def _extract_counterparty(self, row: pd.Series) -> str:
        """
        Извлечение контрагента
        """
        counterparty_fields = ['counterparty', 'контрагент', 'получатель', 'отправитель']
        
        for field in counterparty_fields:
            if field in row and pd.notna(row[field]):
                return str(row[field]).strip()
        
        return ''
    
    def _extract_reference(self, row: pd.Series) -> str:
        """
        Извлечение номера документа/референса
        """
        ref_fields = ['reference_number', 'референс', 'номер документа', 'doc_number']
        
        for field in ref_fields:
            if field in row and pd.notna(row[field]):
                return str(row[field]).strip()
        
        return ''
    
    def _determine_transaction_type(self, row: pd.Series, amount: float) -> str:
        """
        Определение типа транзакции (приход/расход)
        """
        # Если есть отдельные колонки дебет/кредит
        if 'debit_amount' in row and pd.notna(row['debit_amount']) and row['debit_amount'] != 0:
            return 'debit'
        elif 'credit_amount' in row and pd.notna(row['credit_amount']) and row['credit_amount'] != 0:
            return 'credit'
        
        # По знаку суммы
        return 'credit' if amount > 0 else 'debit'
    
    def _identify_payment_system(self, description: str, counterparty: str) -> str:
        """
        Определение платежной системы по описанию и контрагенту
        """
        text = f"{description} {counterparty}".upper()
        
        for system, patterns in self.payment_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    return system
        
        return 'other'
    
    def _calculate_commission(self, amount: float, payment_system: str) -> Dict[str, float]:
        """
        Расчет комиссии платежной системы
        """
        if payment_system in self.commission_rates:
            rate = self.commission_rates[payment_system]
            commission = amount * rate
            net_amount = amount - commission
            
            return {
                'rate': rate,
                'amount': commission,
                'net_amount': net_amount
            }
        
        return {
            'rate': 0.0,
            'amount': 0.0,
            'net_amount': amount
        }
    
    def _parse_date_string(self, date_str: str) -> Optional[str]:
        """
        Парсинг строки даты в различных форматах
        """
        date_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%d.%m.%Y %H:%M:%S',
            '%d/%m/%Y %H:%M:%S',
            '%Y-%m-%d',
            '%d.%m.%Y',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%m/%d/%Y',
            '%Y.%m.%d'
        ]
        
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(date_str.strip(), fmt)
                return parsed_date.strftime('%Y-%m-%d')
            except ValueError:
                continue
        
        return None
    
    def _group_by_payment_system(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Группировка транзакций по платежным системам
        """
        grouped = {}
        
        for transaction in transactions:
            system = transaction['payment_system']
            
            if system not in grouped:
                grouped[system] = {
                    'count': 0,
                    'total_amount': 0.0,
                    'total_commission': 0.0,
                    'net_amount': 0.0,
                    'transactions': []
                }
            
            grouped[system]['count'] += 1
            grouped[system]['total_amount'] += transaction['amount']
            grouped[system]['total_commission'] += transaction['commission_amount']
            grouped[system]['net_amount'] += transaction['net_amount']
            grouped[system]['transactions'].append(transaction)
        
        return grouped
    
    def reconcile_with_orders(self, transactions: List[Dict[str, Any]], 
                            orders_data: List[Dict[str, Any]], 
                            time_tolerance_minutes: int = 10) -> Dict[str, Any]:
        """
        Сверка банковских транзакций с данными заказов
        """
        reconciliation_results = {
            'matched': [],
            'unmatched_transactions': [],
            'unmatched_orders': [],
            'summary': {
                'total_transactions': len(transactions),
                'total_orders': len(orders_data),
                'matched_count': 0,
                'amount_difference': 0.0
            }
        }
        
        # Создаем копии для работы
        remaining_transactions = transactions.copy()
        remaining_orders = orders_data.copy()
        
        # Сопоставляем транзакции с заказами
        for transaction in transactions:
            best_match = None
            best_score = 0
            
            for order in remaining_orders:
                score = self._calculate_match_score(transaction, order, time_tolerance_minutes)
                if score > best_score and score >= 0.7:  # Минимальный порог совпадения
                    best_match = order
                    best_score = score
            
            if best_match:
                reconciliation_results['matched'].append({
                    'transaction': transaction,
                    'order': best_match,
                    'match_score': best_score,
                    'amount_difference': abs(transaction['net_amount'] - best_match.get('order_price', 0))
                })
                
                remaining_transactions.remove(transaction)
                remaining_orders.remove(best_match)
                reconciliation_results['summary']['matched_count'] += 1
        
        reconciliation_results['unmatched_transactions'] = remaining_transactions
        reconciliation_results['unmatched_orders'] = remaining_orders
        
        # Расчет общей разности
        total_transactions_amount = sum(t['net_amount'] for t in transactions)
        total_orders_amount = sum(o.get('order_price', 0) for o in orders_data)
        reconciliation_results['summary']['amount_difference'] = total_transactions_amount - total_orders_amount
        
        return reconciliation_results
    
    def _calculate_match_score(self, transaction: Dict[str, Any], 
                             order: Dict[str, Any], 
                             time_tolerance_minutes: int) -> float:
        """
        Расчет степени совпадения транзакции с заказом
        """
        score = 0.0
        
        # Проверка платежной системы
        if transaction['payment_system'] == order.get('payment_gateway', ''):
            score += 0.4
        
        # Проверка суммы (с учетом комиссии)
        transaction_amount = transaction['net_amount']
        order_amount = order.get('order_price', 0)
        
        if order_amount > 0:
            amount_diff_percent = abs(transaction_amount - order_amount) / order_amount
            if amount_diff_percent <= 0.01:  # 1% допуск
                score += 0.4
            elif amount_diff_percent <= 0.05:  # 5% допуск
                score += 0.2
        
        # Проверка времени
        transaction_date = transaction.get('transaction_date')
        order_date = order.get('paying_time') or order.get('creation_time')
        
        if transaction_date and order_date:
            try:
                trans_dt = datetime.strptime(transaction_date, '%Y-%m-%d')
                order_dt = datetime.fromisoformat(str(order_date).replace('Z', '+00:00'))
                
                time_diff_minutes = abs((trans_dt - order_dt).total_seconds()) / 60
                
                if time_diff_minutes <= time_tolerance_minutes:
                    score += 0.2
                elif time_diff_minutes <= time_tolerance_minutes * 2:
                    score += 0.1
            except:
                pass
        
        return score
    
    def generate_reconciliation_report(self, reconciliation_results: Dict[str, Any]) -> str:
        """
        Генерация отчета по сверке
        """
        report_lines = []
        
        summary = reconciliation_results['summary']
        report_lines.append("=== ОТЧЕТ ПО СВЕРКЕ БАНКОВСКИХ ОПЕРАЦИЙ ===")
        report_lines.append(f"Дата формирования: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        report_lines.append("СВОДНАЯ ИНФОРМАЦИЯ:")
        report_lines.append(f"- Всего транзакций в банке: {summary['total_transactions']}")
        report_lines.append(f"- Всего заказов в системе: {summary['total_orders']}")
        report_lines.append(f"- Успешно сопоставлено: {summary['matched_count']}")
        report_lines.append(f"- Разность по сумме: {summary['amount_difference']:.2f} сум")
        report_lines.append("")
        
        # Несопоставленные транзакции
        if reconciliation_results['unmatched_transactions']:
            report_lines.append("НЕСОПОСТАВЛЕННЫЕ БАНКОВСКИЕ ТРАНЗАКЦИИ:")
            for trans in reconciliation_results['unmatched_transactions']:
                report_lines.append(f"- {trans['transaction_date']} | {trans['amount']:.2f} | {trans['payment_system']} | {trans['description'][:50]}")
            report_lines.append("")
        
        # Несопоставленные заказы
        if reconciliation_results['unmatched_orders']:
            report_lines.append("НЕСОПОСТАВЛЕННЫЕ ЗАКАЗЫ:")
            for order in reconciliation_results['unmatched_orders']:
                report_lines.append(f"- {order.get('order_number', 'N/A')} | {order.get('order_price', 0):.2f} | {order.get('payment_gateway', 'N/A')}")
        
        return "\n".join(report_lines)
