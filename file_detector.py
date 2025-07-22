import pandas as pd

class FileTypeDetector:
    def __init__(self):
        self.templates = {
            'happy_workers': {
                'columns': ['order number', 'machine code', 'creation time', 
                           'order price', 'payment status'],
                'threshold': 0.7
            },
            'vendhub': {
                'columns': ['order number', 'time', 'machine code', 
                           'order price', 'payment type'],
                'threshold': 0.7
            },
            'fiscal_bills': {
                'columns': ['fiscal_check_number', 'fiscal_time', 
                           'amount', 'taxpayer_id'],
                'threshold': 0.8
            },
            'payme': {
                'columns': ['transaction_id', 'transaction_time', 
                           'amount', 'masked_pan', 'merchant_id'],
                'threshold': 0.8
            },
            'click': {
                'columns': ['transaction_id', 'transaction_time', 
                           'amount', 'card_number', 'merchant_id'],
                'threshold': 0.8
            },
            'uzum': {
                'columns': ['transaction_id', 'transaction_time', 
                           'amount', 'masked_pan', 'shop_id'],
                'threshold': 0.8
            }
        }
    
    def detect_type(self, file_path):
        # Читаем первые строки файла
        try:
            if file_path.endswith('.xlsx'):
                df = pd.read_excel(file_path, nrows=5)
            else:
                df = pd.read_csv(file_path, nrows=5)
            
            # Нормализуем названия колонок
            file_columns = [col.lower().strip() for col in df.columns]
            
            # Проверяем совпадения с каждым шаблоном
            best_match = None
            best_score = 0
            
            for file_type, config in self.templates.items():
                template_columns = [col.lower() for col in config['columns']]
                
                # Подсчет совпадений
                matches = sum(1 for col in template_columns 
                            if any(col in fcol for fcol in file_columns))
                
                score = matches / len(template_columns)
                
                if score >= config['threshold'] and score > best_score:
                    best_match = file_type
                    best_score = score
            
            return best_match or 'unknown'
            
        except Exception as e:
            print(f"Error detecting file type: {e}")
            return 'unknown'