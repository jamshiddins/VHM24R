import cv2
import numpy as np
import pytesseract

def test_pytesseract():
    """
    Тестирование pytesseract с созданием простого изображения
    """
    print("Тестирование pytesseract...")
    
    # Создаем простое изображение с текстом
    img = np.zeros((200, 400, 3), dtype=np.uint8)
    img.fill(255)  # Белый фон
    
    # Добавляем текст с помощью OpenCV
    cv2.putText(img, 'Test Text', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), 2)
    
    try:
        # Тестируем OCR
        text = pytesseract.image_to_string(img)
        print(f"Распознанный текст: '{text.strip()}'")
        
        # Проверяем, что текст был распознан
        if 'Test' in text or 'Text' in text:
            print("✅ Тест пройден успешно!")
            return True
        else:
            print("❌ Текст не был распознан корректно")
            return False
            
    except Exception as e:
        print(f"❌ Ошибка при тестировании pytesseract: {e}")
        return False

if __name__ == "__main__":
    test_pytesseract()
