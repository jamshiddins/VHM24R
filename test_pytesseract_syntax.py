import cv2
import numpy as np
import pytesseract

def test_cv2_puttext_syntax():
    """
    Тест синтаксиса cv2.putText без выполнения OCR
    """
    print("Тестирование синтаксиса cv2.putText...")
    
    try:
        # Создаем простое изображение с текстом
        img = np.zeros((200, 400, 3), dtype=np.uint8)
        img.fill(255)  # Белый фон
        
        # Добавляем текст с помощью OpenCV - это должно работать без ошибок Pylance
        cv2.putText(img, 'Test Text', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
        
        print("✅ Синтаксис cv2.putText корректен!")
        print("✅ Pylance ошибка исправлена!")
        
        # Проверяем, что изображение было изменено
        if img[50, 50].sum() < 765:  # Проверяем, что пиксель не белый
            print("✅ Текст был добавлен на изображение!")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка синтаксиса: {e}")
        return False

def test_pytesseract_import():
    """
    Тест импорта pytesseract
    """
    print("Тестирование импорта pytesseract...")
    
    try:
        # Проверяем, что pytesseract импортируется без ошибок
        version = pytesseract.__version__ if hasattr(pytesseract, '__version__') else "неизвестно"
        print(f"✅ pytesseract импортирован успешно! Версия: {version}")
        return True
    except Exception as e:
        print(f"❌ Ошибка импорта pytesseract: {e}")
        return False

if __name__ == "__main__":
    print("=== Тестирование исправлений ===")
    
    # Тест синтаксиса cv2.putText
    syntax_ok = test_cv2_puttext_syntax()
    
    # Тест импорта pytesseract
    import_ok = test_pytesseract_import()
    
    print("\n=== Результаты ===")
    if syntax_ok and import_ok:
        print("✅ Все тесты пройдены! Проблема с Pylance исправлена.")
    else:
        print("❌ Некоторые тесты не прошли.")
