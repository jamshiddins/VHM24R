#!/usr/bin/env python3
"""
VHM24R - Скрипт проверки зависимостей
Проверяет все зависимости проекта и их корректность
"""

import sys
import importlib
import subprocess
from typing import List, Tuple, Dict, Any, Optional

def check_package(package_name: str, import_name: Optional[str] = None) -> Tuple[bool, str]:
    """Проверка установки и импорта пакета"""
    actual_import_name = import_name if import_name is not None else package_name
    
    try:
        module = importlib.import_module(actual_import_name)
        version = getattr(module, '__version__', 'Unknown')
        return True, f"✅ {package_name}: {version}"
    except ImportError as e:
        return False, f"❌ {package_name}: {str(e)}"
    except Exception as e:
        return False, f"⚠️  {package_name}: {str(e)}"

def check_psycopg2_specific() -> Tuple[bool, str]:
    """Специальная проверка для psycopg2"""
    try:
        import psycopg2  # type: ignore
        from psycopg2.extras import RealDictCursor  # type: ignore
        from psycopg2.extensions import connection, cursor  # type: ignore
        
        version = psycopg2.__version__  # type: ignore
        
        # Проверяем основные атрибуты
        checks = [
            hasattr(psycopg2, 'connect'),
            hasattr(psycopg2, 'extras'),  # type: ignore
            hasattr(psycopg2.extras, 'RealDictCursor'),  # type: ignore
            hasattr(psycopg2, 'extensions'),
        ]
        
        if all(checks):
            return True, f"✅ psycopg2: {version} (all features available)"
        else:
            return False, f"⚠️  psycopg2: {version} (some features missing)"
            
    except ImportError as e:
        return False, f"❌ psycopg2: {str(e)}"
    except Exception as e:
        return False, f"⚠️  psycopg2: {str(e)}"

def main():
    """Основная функция проверки"""
    print("🔍 VHM24R Dependencies Check")
    print("=" * 50)
    
    # Список основных зависимостей для проверки
    dependencies = [
        ('Flask', 'flask'),
        ('gunicorn', 'gunicorn'),
        ('python-dotenv', 'dotenv'),
        ('SQLAlchemy', 'sqlalchemy'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('openpyxl', 'openpyxl'),
        ('xlrd', 'xlrd'),
        ('PyPDF2', 'PyPDF2'),
        ('pdfplumber', 'pdfplumber'),
        ('Pillow', 'PIL'),
        ('pytesseract', 'pytesseract'),
        ('opencv-python', 'cv2'),
        ('python-docx', 'docx'),
        ('python-dateutil', 'dateutil'),
        ('requests', 'requests'),
        ('boto3', 'boto3'),
        ('botocore', 'botocore'),
        ('python-telegram-bot', 'telegram'),
        ('matplotlib', 'matplotlib'),
        ('chardet', 'chardet'),
        ('Werkzeug', 'werkzeug'),
        ('cryptography', 'cryptography'),
        ('APScheduler', 'apscheduler'),
        ('ujson', 'ujson'),
        ('pytest', 'pytest'),
        ('pytest-flask', 'pytest_flask'),
        ('sentry-sdk', 'sentry_sdk'),
        ('psutil', 'psutil'),
    ]
    
    print("\n📦 Checking Python packages...")
    
    success_count = 0
    total_count = len(dependencies) + 1  # +1 для psycopg2
    
    # Специальная проверка для psycopg2
    success, message = check_psycopg2_specific()
    print(message)
    if success:
        success_count += 1
    
    # Проверка остальных пакетов
    for package_name, import_name in dependencies:
        success, message = check_package(package_name, import_name)
        print(message)
        if success:
            success_count += 1
    
    print(f"\n📊 Summary: {success_count}/{total_count} packages available")
    
    if success_count == total_count:
        print("🎉 All dependencies are installed and working correctly!")
        return True
    else:
        missing_count = total_count - success_count
        print(f"⚠️  {missing_count} dependencies have issues")
        print("\n💡 To install missing dependencies:")
        print("   pip install -r requirements.txt")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
