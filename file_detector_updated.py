"""
VHM24R - Улучшенный детектор типов файлов
Определение типов файлов согласно новой документации
"""

import pandas as pd
from typing import Dict, List, Optional, Tuple

class AdvancedFileTypeDetector:
    """
    Улучшенный детектор типов файлов для системы VHM24R
    Поддерживает все 6 типов файлов согласно документации
    """
    
    def __init__(self):
        self.file_signatures = {
            'happy_workers': {
                'required_columns': [
                    'Order number', 'Machine code', 'Creation time', 
                    'Order price', 'Payment status', 'Goods name'
                ],
                'unique_columns': [
                    'Brewing time', 'Brew status', 'Delivery time', 'Taste name'
                ],
                'threshold': 0.75,
                'description': 'Отчёт заказов из автомата Happy Workers'
            },
            'vendhub': {
                'required_columns': [
                    'Order number', 'Time', 'Machine Code', 
                    'Order price', 'Payment type'
                ],
                'unique_columns': [
                    'ИКПУ', 'Штрихкод', 'Маркировка', 'Упаковка',
                    'Amount of accrued bonus'
                ],
                'threshold': 0.75,
                'description': 'Внутренний отчёт системы VendHub'
            },
            'fiscal_bills': {
                'required_columns': [
                    'fiscal_check_number', 'fiscal_time', 
                    'amount', 'taxpayer_id'
                ],
                'unique_columns': [
                    'cash_register_id', 'shift_number', 'receipt_type'
                ],
                'threshold': 0.8,
                'description': 'Фискальные чеки'
            },
            'payme': {
                'required_columns': [
                    'transaction_id', 'transaction_time', 
                    'amount', 'masked_pan'
                ],
                'unique_columns': [
                    'terminal_id', 'merchant_id', 'phone_number',
                    'reference_number'
                ],
                'threshold': 0.8,
                'description': 'Транзакции Payme'
            },
            'click': {
                'required_columns': [
                    'transaction_id', 'transaction_time', 
                    'amount', 'card_number'
                ],
                'unique_columns': [
                    'click_trans_id', 'service_id', 'merchant_trans_id',
                    'error_code'
                ],
                'threshold': 0.8,
                'description': 'Транзакции Click'
            },
            'uzum': {
                'required_columns': [
                    'transaction_id', 'transaction_time', 
                    'amount', 'masked_pan'
                ],
                'unique_columns': [
                    'shop_id', 'cashback_amount', 'order_id'
                ],
                'threshold': 0.8,
                'description': 'Транзакции Uzum'
            }
        }
    
    def normalize_column_name(self, column: str) -> str:
        """Нормализация названий колонок для сравнения"""
        return column.lower().strip().replace(' ', '_').replace('-', '_')
    
    def calculate_match_score(self, columns: List[str], file_type: str) -> Tuple[float, Dict]:
        """
        Вычисление степени соответствия колонок типу файла
        
        Returns:
            Tuple[float, Dict]: (score, details)
        """
        signature = self.file_signatures[file_type]
        normalized_columns = [self.normalize_column_name(col) for col in columns]
        
        # Проверяем обязательные колонки
        required_matches = 0
        required_details = []
        
        for req_col in signature['required_columns']:
            normalized_req = self.normalize_column_name(req_col)
            
            # Ищем точное совпадение или частичное
            found = False
            for norm_col, orig_col in zip(normalized_columns, columns):
                if (normalized_req in norm_col or 
                    norm_col in normalized_req or
                    self._fuzzy_match(normalized_req, norm_col)):
                    required_matches += 1
                    required_details.append({
                        'required': req_col,
                        'found': orig_col,
                        'match_type': 'exact' if normalized_req == norm_col else 'partial'
                    })
                    found = True
                    break
            
            if not found:
                required_details.append({
                    'required': req_col,
                    'found': None,
                    'match_type': 'missing'
                })
        
        # Проверяем уникальные колонки (бонус к точности)
        unique_matches = 0
        unique_details = []
        
        for uniq_col in signature['unique_columns']:
            normalized_uniq = self.normalize_column_name(uniq_col)
            
            for norm_col, orig_col in zip(normalized_columns, columns):
                if (normalized_uniq in norm_col or 
                    norm_col in normalized_uniq or
                    self._fuzzy_match(normalized_uniq, norm_col)):
                    unique_matches += 1
                    unique_details.append({
                        'unique': uniq_col,
                        'found': orig_col
                    })
                    break
        
        # Расчет итогового score
        required_score = required_matches / len(signature['required_columns'])
        unique_bonus = min(unique_matches * 0.1, 0.3)  # максимум 30% бонуса
        total_score = min(required_score + unique_bonus, 1.0)
        
        details = {
            'required_matches': required_matches,
            'required_total': len(signature['required_columns']),
            'unique_matches': unique_matches,
            'required_details': required_details,
            'unique_details': unique_details,
            'required_score': required_score,
            'unique_bonus': unique_bonus,
            'total_score': total_score
        }
        
        return total_score, details
    
    def _fuzzy_match(self, str1: str, str2: str, threshold: float = 0.8) -> bool:
        """Нечеткое сравнение строк"""
        if not str1 or not str2:
            return False
        
        # Простая проверка на включение подстрок
        if len(str1) > len(str2):
            return str2 in str1
        else:
            return str1 in str2
    
    def detect_file_type(self, file_path: str) -> Tuple[str, Dict]:
        """
        Определение типа файла с детальной информацией
        
        Returns:
            Tuple[str, Dict]: (file_type, analysis_details)
        """
        try:
            # Читаем файл
            if file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path, nrows=0)  # Только заголовки
            elif file_path.endswith('.csv'):
                df = pd.read_csv(file_path, nrows=0)
            else:
                return 'unknown', {'error': 'Unsupported file format'}
            
            columns = df.columns.tolist()
            
            if not columns:
                return 'unknown', {'error': 'No columns found'}
            
            # Анализируем каждый тип файла
            analysis_results = {}
            
            for file_type in self.file_signatures.keys():
                score, details = self.calculate_match_score(columns, file_type)
                analysis_results[file_type] = {
                    'score': score,
                    'details': details,
                    'threshold': self.file_signatures[file_type]['threshold'],
                    'passes_threshold': score >= self.file_signatures[file_type]['threshold'],
                    'description': self.file_signatures[file_type]['description']
                }
            
            # Находим лучшее совпадение
            best_match = max(analysis_results.items(), key=lambda x: x[1]['score'])
            best_type, best_analysis = best_match
            
            # Проверяем, проходит ли лучшее совпадение порог
            if best_analysis['passes_threshold']:
                detected_type = best_type
            else:
                detected_type = 'unknown'
            
            return detected_type, {
                'detected_type': detected_type,
                'confidence': best_analysis['score'],
                'columns_found': columns,
                'analysis_results': analysis_results,
                'best_match': best_analysis
            }
        
        except Exception as e:
            return 'unknown', {'error': str(e)}
    
    def detect_type(self, file_path: str) -> str:
        """Упрощенный метод для обратной совместимости"""
        detected_type, _ = self.detect_file_type(file_path)
        return detected_type
    
    def get_file_requirements(self, file_type: str) -> Optional[Dict]:
        """Получение требований для типа файла"""
        return self.file_signatures.get(file_type)
    
    def validate_file_structure(self, file_path: str, expected_type: str) -> Dict:
        """
        Валидация структуры файла для ожидаемого типа
        
        Returns:
            Dict: Результат валидации
        """
        detected_type, analysis = self.detect_file_type(file_path)
        
        if expected_type not in self.file_signatures:
            return {
                'valid': False,
                'error': f'Unknown expected type: {expected_type}'
            }
        
        expected_analysis = analysis['analysis_results'].get(expected_type, {})
        
        return {
            'valid': detected_type == expected_type,
            'detected_type': detected_type,
            'expected_type': expected_type,
            'confidence': expected_analysis.get('score', 0),
            'passes_threshold': expected_analysis.get('passes_threshold', False),
            'missing_columns': [
                detail['required'] for detail in 
                expected_analysis.get('details', {}).get('required_details', [])
                if detail['match_type'] == 'missing'
            ],
            'analysis': analysis
        }
    
    def get_supported_types(self) -> Dict[str, str]:
        """Получение списка поддерживаемых типов файлов"""
        return {
            file_type: signature['description']
            for file_type, signature in self.file_signatures.items()
        }
    
    def generate_template_info(self, file_type: str) -> Optional[Dict]:
        """Генерация информации о шаблоне для типа файла"""
        if file_type not in self.file_signatures:
            return None
        
        signature = self.file_signatures[file_type]
        
        return {
            'file_type': file_type,
            'description': signature['description'],
            'required_columns': signature['required_columns'],
            'optional_columns': signature['unique_columns'],
            'example_filename': f"{file_type}.xlsx",
            'notes': self._get_file_type_notes(file_type)
        }
    
    def _get_file_type_notes(self, file_type: str) -> List[str]:
        """Получение заметок для типа файла"""
        notes = {
            'happy_workers': [
                "Основной файл с данными заказов из автоматов",
                "Содержит временные метки создания, оплаты, приготовления и выдачи",
                "Ключевые поля: Order number + Machine code"
            ],
            'vendhub': [
                "Внутренний отчет системы VendHub",
                "Должен содержать те же заказы что и Happy Workers",
                "Время события должно быть между Creation и Delivery time"
            ],
            'fiscal_bills': [
                "Фискальные чеки для Cash платежей",
                "Время фискализации должно быть ≈ Paying time (±1 мин)",
                "Сумма должна точно совпадать с Order price"
            ],
            'payme': [
                "Транзакции платежной системы Payme",
                "Сумма = полная сумма заказа (комиссия уже включена)",
                "Время транзакции ≈ Paying time (±1 мин)"
            ],
            'click': [
                "Транзакции платежной системы Click",
                "Сумма = полная сумма заказа (комиссия уже включена)",
                "Время транзакции ≈ Paying time (±1 мин)"
            ],
            'uzum': [
                "Транзакции платежной системы Uzum",
                "Сумма = полная сумма заказа (комиссия уже включена)",
                "Время транзакции ≈ Paying time (±1 мин)"
            ]
        }
        
        return notes.get(file_type, [])


# Глобальный экземпляр для использования в приложении
advanced_detector = AdvancedFileTypeDetector()

def detect_file_type_advanced(file_path: str) -> Tuple[str, Dict]:
    """Функция для использования улучшенного детектора"""
    return advanced_detector.detect_file_type(file_path)

def get_file_type_info(file_type: str) -> Optional[Dict]:
    """Получение информации о типе файла"""
    return advanced_detector.generate_template_info(file_type)
