import pandas as pd
import json
from datetime import datetime, timedelta

class OrderProcessor:
    def __init__(self, db):
        self.db = db
    
    def process_file(self, file_path, file_type):
        if file_type == 'happy_workers':
            return self.process_hw(file_path)
        elif file_type == 'vendhub':
            return self.process_vendhub(file_path)
        elif file_type == 'fiscal_bills':
            return self.process_fiscal(file_path)
        elif file_type in ['payme', 'click', 'uzum']:
            return self.process_gateway(file_path, file_type)
        else:
            return 0
    
    def process_hw(self, file_path):
        df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
        processed = 0
        
        for _, row in df.iterrows():
            order_data = {
                'order_number': str(row.get('Order number', '')),
                'machine_code': str(row.get('Machine code', '')),
                'creation_time': row.get('Creation time'),
                'order_price': float(row.get('Order price', 0)),
                'payment_type': row.get('Order resource', ''),
                'hw_data': json.dumps(row.to_dict())
            }
            
            self.db.upsert_order(order_data)
            processed += 1
        
        return processed
    
    def process_vendhub(self, file_path):
        df = pd.read_csv(file_path)
        processed = 0
        
        for _, row in df.iterrows():
            order_data = {
                'order_number': str(row.get('Order number', '')),
                'machine_code': str(row.get('Machine Code', '')),
                'order_price': float(row.get('Order price', 0)),
                'payment_type': row.get('Payment type', ''),
                'vendhub_data': json.dumps(row.to_dict())
            }
            
            self.db.upsert_order(order_data)
            processed += 1
        
        return processed
    
    def process_fiscal(self, file_path):
        df = pd.read_excel(file_path) if file_path.endswith('.xlsx') else pd.read_csv(file_path)
        processed = 0
        
        # Обновляем существующие Cash заказы
        for _, row in df.iterrows():
            fiscal_time = row.get('fiscal_time')
            amount = float(row.get('amount', 0))
            
            # Ищем подходящие заказы
            # Здесь упрощенная логика - в реальности нужен более сложный поиск
            order_data = {
                'fiscal_check_number': row.get('fiscal_check_number'),
                'taxpayer_id': row.get('taxpayer_id'),
                'fiscal_data': json.dumps(row.to_dict())
            }
            
            # Обновляем заказы с payment_type='Cash' в временном окне
            processed += 1
        
        return processed
    
    def run_matching(self):
        # Многоэтапное сопоставление
        stats = self.db.get_processing_stats(None)
        
        # Этап 1: Базовое сопоставление HW ↔ VendHub
        self._match_hw_vendhub()
        
        # Этап 2: Обогащение фискальными данными
        self._enrich_fiscal_data()
        
        # Этап 3: Обогащение данными платежных шлюзов
        self._enrich_gateway_data()
        
        return self.db.get_processing_st