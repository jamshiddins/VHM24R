"""
VHM24R - OCR модуль для обработки изображений чеков и документов
Извлечение структурированных данных из изображений
"""

import re
from datetime import datetime
from typing import Dict, List, Any

# Опциональные импорты для OCR
try:
    import cv2
    import numpy as np
    import pytesseract
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False
    cv2 = None
    np = None
    pytesseract = None

class OCRProcessor:
    """
    Процессор OCR для извлечения данных из изображений чеков и документов
    """
    
    def __init__(self):
        # Настройка языков OCR
        self.languages = ['rus', 'eng']
        
        # Паттерны для извлечения данных
        self.patterns = {
            'amount': [
                r'ИТОГО[:\s]*(\d+[\.,]\d+)',
                r'СУММА[:\s]*(\d+[\.,]\d+)',
                r'TOTAL[:\s]*(\d+[\.,]\d+)',
                r'(\d+[\.,]\d+)\s*сум',
                r'(\d+[\.,]\d+)\s*UZS'
            ],
            'date': [
                r'(\d{2}[\./-]\d{2}[\./-]\d{4})',
                r'(\d{4}[\./-]\d{2}[\./-]\d{2})',
                r'(\d{2}\.\d{2}\.\d{4})',
                r'(\d{4}-\d{2}-\d{2})'
            ],
            'time': [
                r'(\d{2}:\d{2}:\d{2})',
                r'(\d{2}:\d{2})'
            ],
            'receipt_number': [
                r'ЧЕК\s*№\s*(\d+)',
                r'RECEIPT\s*№\s*(\d+)',
                r'№\s*(\d+)',
                r'ID[:\s]*(\d+)'
            ],
            'fiscal_number': [
                r'ФИСКАЛЬНЫЙ\s*№\s*(\d+)',
                r'FISCAL\s*№\s*(\d+)',
                r'ФП[:\s]*(\d+)'
            ],
            'transaction_id': [
                r'TRANSACTION\s*ID[:\s]*(\w+)',
                r'ID\s*ТРАНЗАКЦИИ[:\s]*(\w+)',
                r'TXN[:\s]*(\w+)'
            ]
        }
    
    def process_image(self, image_path: str) -> Dict[str, Any]:
        """
        Основной метод обработки изображения
        """
        if not OCR_AVAILABLE:
            return {
                'status': 'error',
                'message': 'OCR libraries not available. Install opencv-python, pytesseract and tesseract-ocr.'
            }
        
        try:
            # Предобработка изображения
            processed_image = self._preprocess_image(image_path)
            
            # OCR извлечение текста
            text = self._extract_text(processed_image)
            
            if not text.strip():
                return {'status': 'error', 'message': 'No text extracted'}
            
            # Парсинг структурированных данных
            parsed_data = self._parse_receipt_data(text)
            
            # Определение типа документа
            document_type = self._classify_document_type(text, parsed_data)
            
            return {
                'status': 'success',
                'document_type': document_type,
                'raw_text': text,
                'parsed_data': parsed_data,
                'confidence': self._calculate_confidence(parsed_data)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'message': f'OCR processing failed: {str(e)}'
            }
    
    def _preprocess_image(self, image_path: str):
        """
        Предобработка изображения для улучшения качества OCR
        """
        if not OCR_AVAILABLE:
            raise ValueError("OCR libraries not available")
        
        # Загрузка изображения
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Cannot load image: {image_path}")
        
        # Конвертация в оттенки серого
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Увеличение размера для лучшего распознавания
        height, width = gray.shape
        if width < 1000:
            scale_factor = 1000 / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            gray = cv2.resize(gray, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
        
        # Размытие для удаления шума
        gray = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Бинаризация (черно-белое изображение)
        _, binary = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Морфологические операции для очистки
        kernel = np.ones((2, 2), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        
        return binary
    
    def _extract_text(self, image) -> str:
        """
        Извлечение текста из предобработанного изображения
        """
        if not OCR_AVAILABLE:
            raise ValueError("OCR libraries not available")
        
        # Настройки Tesseract для лучшего распознавания
        custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя.,:-№ '
        
        # Извлечение текста
        text = pytesseract.image_to_string(
            image, 
            lang='+'.join(self.languages),
            config=custom_config
        )
        
        return text
    
    def _parse_receipt_data(self, text: str) -> Dict[str, Any]:
        """
        Парсинг структурированных данных из текста чека
        """
        data = {
            'items': [],
            'total_amount': None,
            'date': None,
            'time': None,
            'receipt_number': None,
            'fiscal_number': None,
            'transaction_id': None,
            'payment_method': None
        }
        
        lines = text.split('\n')
        
        # Извлечение основных полей
        for field, patterns in self.patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    if field == 'amount':
                        data['total_amount'] = self._parse_amount(value)
                    elif field == 'date':
                        data['date'] = self._parse_date(value)
                    elif field == 'time':
                        data['time'] = value
                    elif field == 'receipt_number':
                        data['receipt_number'] = value
                    elif field == 'fiscal_number':
                        data['fiscal_number'] = value
                    elif field == 'transaction_id':
                        data['transaction_id'] = value
                    break
        
        # Извлечение товарных позиций
        data['items'] = self._extract_items(lines)
        
        # Определение способа оплаты
        data['payment_method'] = self._detect_payment_method(text)
        
        return data
    
    def _extract_items(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Извлечение товарных позиций из строк текста
        """
        items = []
        
        # Паттерны для товарных позиций
        item_patterns = [
            r'(.+?)\s+(\d+[\.,]\d+)\s*[xх]\s*(\d+[\.,]\d+)',  # Название Кол-во x Цена
            r'(.+?)\s+(\d+[\.,]\d+)\s*шт\s*(\d+[\.,]\d+)',    # Название Кол-во шт Цена
            r'(.+?)\s+(\d+[\.,]\d+)$'                         # Название Цена
        ]
        
        for line in lines:
            line = line.strip()
            if not line or len(line) < 5:
                continue
            
            for pattern in item_patterns:
                match = re.search(pattern, line)
                if match:
                    if len(match.groups()) == 3:
                        name, quantity, price = match.groups()
                        items.append({
                            'name': name.strip(),
                            'quantity': self._parse_float(quantity),
                            'price': self._parse_float(price),
                            'total': self._parse_float(quantity) * self._parse_float(price)
                        })
                    elif len(match.groups()) == 2:
                        name, price = match.groups()
                        items.append({
                            'name': name.strip(),
                            'quantity': 1.0,
                            'price': self._parse_float(price),
                            'total': self._parse_float(price)
                        })
                    break
        
        return items
    
    def _detect_payment_method(self, text: str) -> str:
        """
        Определение способа оплаты
        """
        text_lower = text.lower()
        
        payment_methods = {
            'cash': ['наличные', 'cash', 'наличными', 'кэш'],
            'card': ['карта', 'card', 'картой', 'безнал'],
            'payme': ['payme', 'пейми', 'пэйми'],
            'click': ['click', 'клик'],
            'uzum': ['uzum', 'узум']
        }
        
        for method, keywords in payment_methods.items():
            if any(keyword in text_lower for keyword in keywords):
                return method
        
        return 'unknown'
    
    def _classify_document_type(self, text: str, parsed_data: Dict[str, Any]) -> str:
        """
        Классификация типа документа
        """
        text_lower = text.lower()
        
        # Фискальный чек
        if any(word in text_lower for word in ['фискальный', 'fiscal', 'чек', 'receipt']):
            if parsed_data.get('fiscal_number') or parsed_data.get('receipt_number'):
                return 'fiscal_receipt'
        
        # Банковский чек
        if any(word in text_lower for word in ['банк', 'bank', 'терминал', 'terminal']):
            if parsed_data.get('transaction_id'):
                return 'bank_receipt'
        
        # Чек платежной системы
        if any(word in text_lower for word in ['payme', 'click', 'uzum']):
            return 'payment_receipt'
        
        # Обычный товарный чек
        if parsed_data.get('items') and parsed_data.get('total_amount'):
            return 'sales_receipt'
        
        return 'unknown_document'
    
    def _calculate_confidence(self, parsed_data: Dict[str, Any]) -> float:
        """
        Расчет уверенности в правильности распознавания
        """
        confidence = 0.0
        
        # Проверяем наличие ключевых полей
        if parsed_data.get('total_amount'):
            confidence += 0.3
        if parsed_data.get('date'):
            confidence += 0.2
        if parsed_data.get('time'):
            confidence += 0.1
        if parsed_data.get('receipt_number') or parsed_data.get('fiscal_number'):
            confidence += 0.2
        if parsed_data.get('items'):
            confidence += 0.1
        if parsed_data.get('payment_method') != 'unknown':
            confidence += 0.1
        
        return min(confidence, 1.0)
    
    def _parse_amount(self, amount_str: str) -> float:
        """
        Парсинг суммы из строки
        """
        try:
            # Заменяем запятую на точку и удаляем пробелы
            clean_amount = amount_str.replace(',', '.').replace(' ', '')
            return float(clean_amount)
        except (ValueError, TypeError):
            return 0.0
    
    def _parse_date(self, date_str: str) -> str:
        """
        Парсинг и нормализация даты
        """
        try:
            # Пробуем разные форматы даты
            formats = [
                '%d.%m.%Y',
                '%d/%m/%Y',
                '%d-%m-%Y',
                '%Y-%m-%d',
                '%Y.%m.%d',
                '%Y/%m/%d'
            ]
            
            for fmt in formats:
                try:
                    parsed_date = datetime.strptime(date_str, fmt)
                    return parsed_date.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            
            return date_str  # Возвращаем как есть, если не удалось распарсить
            
        except Exception:
            return date_str
    
    def _parse_float(self, value_str: str) -> float:
        """
        Безопасный парсинг float значений
        """
        try:
            clean_value = str(value_str).replace(',', '.').replace(' ', '')
            return float(clean_value)
        except (ValueError, TypeError):
            return 0.0
    
    def process_batch_images(self, image_paths: List[str]) -> List[Dict[str, Any]]:
        """
        Пакетная обработка изображений
        """
        results = []
        
        for image_path in image_paths:
            try:
                result = self.process_image(image_path)
                result['image_path'] = image_path
                results.append(result)
            except Exception as e:
                results.append({
                    'image_path': image_path,
                    'status': 'error',
                    'message': str(e)
                })
        
        return results
    
    def extract_table_from_image(self, image_path: str) -> List[List[str]]:
        """
        Извлечение табличных данных из изображения
        """
        if not OCR_AVAILABLE:
            print("OCR libraries not available")
            return []
        
        try:
            # Предобработка изображения
            processed_image = self._preprocess_image(image_path)
            
            # Специальная конфигурация для таблиц
            table_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
            
            # Извлечение текста
            text = pytesseract.image_to_string(
                processed_image,
                lang='+'.join(self.languages),
                config=table_config
            )
            
            # Разбиение на строки и столбцы
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            table_data = []
            
            for line in lines:
                # Разделяем по пробелам (можно улучшить)
                columns = [col.strip() for col in re.split(r'\s{2,}', line) if col.strip()]
                if columns:
                    table_data.append(columns)
            
            return table_data
            
        except Exception as e:
            print(f"Error extracting table from image: {e}")
            return []
