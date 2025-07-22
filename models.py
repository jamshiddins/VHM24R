import sqlite3
import json
from datetime import datetime
import uuid

class Database:
    def __init__(self, db_path='orders.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        with open('schema.sql', 'r') as f:
            schema = f.read()
        
        conn = sqlite3.connect(self.db_path)
        conn.executescript(schema)
        conn.commit()
        conn.close()
    
    def create_session(self):
        session_id = str(uuid.uuid4())
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO processing_sessions (session_id) VALUES (?)",
            (session_id,)
        )
        conn.commit()
        conn.close()
        return session_id
    
    def upsert_order(self, order_data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Проверяем существование
        cursor.execute(
            """SELECT id FROM orders 
               WHERE order_number = ? AND 
                     (machine_code = ? OR machine_code IS NULL)""",
            (order_data.get('order_number'), order_data.get('machine_code'))
        )
        existing = cursor.fetchone()
        
        if existing:
            # Обновляем существующий
            self._update_order(cursor, existing[0], order_data)
        else:
            # Создаем новый
            self._insert_order(cursor, order_data)
        
        conn.commit()
        conn.close()
    
    def get_orders_by_filter(self, filter_type, limit=100):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = "SELECT * FROM orders WHERE match_status = ? LIMIT ?"
        cursor.execute(query, (filter_type, limit))
        
        orders = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return orders
    
    def get_processing_stats(self, session_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Подсчет статистики
        stats = {
            'total': 0,
            'matched': 0,
            'time_mismatch': 0,
            'price_mismatch': 0,
            'fiscal_matched': 0,
            'fiscal_mismatch': 0,
            'gateway_matched': 0,
            'gateway_mismatch': 0
        }
        
        cursor.execute("SELECT COUNT(*) FROM orders")
        stats['total'] = cursor.fetchone()[0]
        
        for status in ['matched', 'time_mismatch', 'price_mismatch', 
                      'fiscal_mismatch', 'gateway_mismatch']:
            cursor.execute(
                "SELECT COUNT(*) FROM orders WHERE match_status = ?",
                (status,)
            )
            stats[status] = cursor.fetchone()[0]
        
        conn.close()
        return stats