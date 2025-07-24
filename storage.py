"""
VHM24R - Модуль интеграции с DigitalOcean Spaces
Хранение файлов и данных согласно промту: Railway + DigitalOcean
"""

import os
import boto3
import hashlib
import json
from datetime import datetime
from typing import Optional, Dict, List
from botocore.exceptions import ClientError, NoCredentialsError

class DigitalOceanStorage:
    """
    Класс для работы с DigitalOcean Spaces (S3-совместимое хранилище)
    Согласно промту: хранение оригинальных файлов в DigitalOcean Spaces
    """
    
    def __init__(self):
        self.access_key = os.environ.get('DIGITALOCEAN_SPACES_KEY')
        self.secret_key = os.environ.get('DIGITALOCEAN_SPACES_SECRET')
        self.bucket_name = os.environ.get('DIGITALOCEAN_SPACES_BUCKET', 'vhm24r-files')
        self.region = os.environ.get('DIGITALOCEAN_SPACES_REGION', 'fra1')
        self.endpoint_url = f'https://{self.region}.digitaloceanspaces.com'
        
        self.enabled = bool(self.access_key and self.secret_key)
        
        if self.enabled:
            try:
                self.client = boto3.client(
                    's3',
                    endpoint_url=self.endpoint_url,
                    aws_access_key_id=self.access_key,
                    aws_secret_access_key=self.secret_key,
                    region_name=self.region
                )
                
                # Проверяем подключение
                self._ensure_bucket_exists()
                print(f"DigitalOcean Spaces connected: {self.bucket_name}")
                
            except Exception as e:
                print(f"DigitalOcean Spaces connection failed: {e}")
                self.enabled = False
        else:
            print("DigitalOcean Spaces disabled: missing credentials")
    
    def _ensure_bucket_exists(self):
        """Проверка и создание bucket если необходимо"""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                # Bucket не существует, создаем его
                try:
                    self.client.create_bucket(
                        Bucket=self.bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': self.region}
                    )
                    print(f"Created bucket: {self.bucket_name}")
                except Exception as create_error:
                    print(f"Failed to create bucket: {create_error}")
                    raise
            else:
                raise
    
    def upload_file(self, local_file_path: str, remote_key: str, metadata: Optional[Dict] = None) -> bool:
        """
        Загрузка файла в DigitalOcean Spaces
        
        Args:
            local_file_path: Путь к локальному файлу
            remote_key: Ключ (путь) в хранилище
            metadata: Дополнительные метаданные
        
        Returns:
            bool: Успешность загрузки
        """
        if not self.enabled:
            print(f"Storage disabled. Would upload: {local_file_path} -> {remote_key}")
            return False
        
        try:
            # Подготавливаем метаданные
            extra_args = {}
            if metadata and isinstance(metadata, dict):
                extra_args['Metadata'] = {k: str(v) for k, v in metadata.items()}
            else:
                extra_args['Metadata'] = {}
            
            # Определяем Content-Type
            if remote_key.endswith('.xlsx'):
                extra_args['ContentType'] = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            elif remote_key.endswith('.csv'):
                extra_args['ContentType'] = 'text/csv'
            elif remote_key.endswith('.json'):
                extra_args['ContentType'] = 'application/json'
            
            # Загружаем файл
            self.client.upload_file(
                local_file_path,
                self.bucket_name,
                remote_key,
                ExtraArgs=extra_args
            )
            
            print(f"File uploaded successfully: {remote_key}")
            return True
            
        except Exception as e:
            print(f"Error uploading file {local_file_path}: {e}")
            return False
    
    def download_file(self, remote_key: str, local_file_path: str) -> bool:
        """
        Скачивание файла из DigitalOcean Spaces
        
        Args:
            remote_key: Ключ файла в хранилище
            local_file_path: Путь для сохранения локально
        
        Returns:
            bool: Успешность скачивания
        """
        if not self.enabled:
            print(f"Storage disabled. Would download: {remote_key} -> {local_file_path}")
            return False
        
        try:
            self.client.download_file(
                self.bucket_name,
                remote_key,
                local_file_path
            )
            
            print(f"File downloaded successfully: {remote_key}")
            return True
            
        except Exception as e:
            print(f"Error downloading file {remote_key}: {e}")
            return False
    
    def upload_json_data(self, data: Dict, remote_key: str) -> bool:
        """
        Загрузка JSON данных в хранилище
        
        Args:
            data: Данные для сохранения
            remote_key: Ключ в хранилище
        
        Returns:
            bool: Успешность загрузки
        """
        if not self.enabled:
            print(f"Storage disabled. Would upload JSON: {remote_key}")
            return False
        
        try:
            json_data = json.dumps(data, ensure_ascii=False, indent=2, default=str)
            
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=remote_key,
                Body=json_data.encode('utf-8'),
                ContentType='application/json',
                Metadata={
                    'upload_time': datetime.now().isoformat(),
                    'data_type': 'reconciliation_result'
                }
            )
            
            print(f"JSON data uploaded successfully: {remote_key}")
            return True
            
        except Exception as e:
            print(f"Error uploading JSON data {remote_key}: {e}")
            return False
    
    def get_file_info(self, remote_key: str) -> Optional[Dict]:
        """
        Получение информации о файле
        
        Args:
            remote_key: Ключ файла в хранилище
        
        Returns:
            Dict: Информация о файле или None
        """
        if not self.enabled:
            return None
        
        try:
            response = self.client.head_object(
                Bucket=self.bucket_name,
                Key=remote_key
            )
            
            return {
                'size': response.get('ContentLength', 0),
                'last_modified': response.get('LastModified'),
                'content_type': response.get('ContentType'),
                'metadata': response.get('Metadata', {})
            }
            
        except Exception as e:
            print(f"Error getting file info {remote_key}: {e}")
            return None
    
    def list_files(self, prefix: str = '', limit: int = 1000) -> List[Dict]:
        """
        Получение списка файлов
        
        Args:
            prefix: Префикс для фильтрации
            limit: Максимальное количество файлов
        
        Returns:
            List[Dict]: Список файлов
        """
        if not self.enabled:
            return []
        
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=limit
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag'].strip('"')
                })
            
            return files
            
        except Exception as e:
            print(f"Error listing files: {e}")
            return []
    
    def delete_file(self, remote_key: str) -> bool:
        """
        Удаление файла из хранилища
        
        Args:
            remote_key: Ключ файла в хранилище
        
        Returns:
            bool: Успешность удаления
        """
        if not self.enabled:
            print(f"Storage disabled. Would delete: {remote_key}")
            return False
        
        try:
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=remote_key
            )
            
            print(f"File deleted successfully: {remote_key}")
            return True
            
        except Exception as e:
            print(f"Error deleting file {remote_key}: {e}")
            return False
    
    def generate_presigned_url(self, remote_key: str, expiration: int = 3600) -> Optional[str]:
        """
        Генерация подписанной URL для доступа к файлу
        
        Args:
            remote_key: Ключ файла в хранилище
            expiration: Время жизни URL в секундах
        
        Returns:
            str: Подписанная URL или None
        """
        if not self.enabled:
            return None
        
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': remote_key},
                ExpiresIn=expiration
            )
            
            return url
            
        except Exception as e:
            print(f"Error generating presigned URL for {remote_key}: {e}")
            return None


class FileManager:
    """
    Менеджер файлов для VHM24R
    Управляет локальными файлами и синхронизацией с DigitalOcean Spaces
    """
    
    def __init__(self, db, local_upload_dir: str = 'uploads'):
        self.db = db
        self.local_upload_dir = local_upload_dir
        self.storage = DigitalOceanStorage()
        
        # Создаем локальную директорию если не существует
        os.makedirs(local_upload_dir, exist_ok=True)
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Вычисление хеша файла для предотвращения дублирования"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            print(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def save_uploaded_file(self, file, session_id: str, file_type: str) -> Dict:
        """
        Сохранение загруженного файла локально и в DigitalOcean Spaces
        
        Args:
            file: Загруженный файл
            session_id: ID сессии обработки
            file_type: Тип файла (hw, vendhub, fiscal_bills, etc.)
        
        Returns:
            Dict: Информация о сохраненном файле
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{file_type}_{file.filename}"
        local_path = os.path.join(self.local_upload_dir, filename)
        
        # Сохраняем локально
        file.save(local_path)
        
        # Вычисляем хеш
        file_hash = self.calculate_file_hash(local_path)
        file_size = os.path.getsize(local_path)
        
        # Проверяем на дублирование
        existing_file = self.db.execute_query(
            "SELECT id FROM file_metadata WHERE file_hash = ? AND file_size = ?",
            (file_hash, file_size)
        )
        
        if existing_file:
            print(f"Duplicate file detected: {filename}")
            os.remove(local_path)  # Удаляем дубликат
            return {
                'status': 'duplicate',
                'message': 'Файл уже был загружен ранее',
                'existing_id': existing_file[0]['id']
            }
        
        # Загружаем в DigitalOcean Spaces
        remote_key = f"uploads/{session_id}/{filename}"
        metadata = {
            'session_id': session_id,
            'file_type': file_type,
            'original_filename': file.filename,
            'upload_time': datetime.now().isoformat()
        }
        
        storage_success = self.storage.upload_file(local_path, remote_key, metadata)
        
        # Сохраняем метаданные в БД
        file_metadata = {
            'filename': filename,
            'original_filename': file.filename,
            'file_type': file_type,
            'file_path': local_path,
            'remote_key': remote_key if storage_success else None,
            'file_size': file_size,
            'file_hash': file_hash,
            'session_id': session_id,
            'storage_status': 'uploaded' if storage_success else 'local_only'
        }
        
        file_id = self.db.save_file_metadata_extended(file_metadata)
        
        return {
            'status': 'success',
            'file_id': file_id,
            'local_path': local_path,
            'remote_key': remote_key if storage_success else None,
            'file_size': file_size,
            'storage_uploaded': storage_success
        }
    
    def backup_processing_results(self, session_id: str, results: Dict) -> bool:
        """
        Резервное копирование результатов обработки в DigitalOcean Spaces
        
        Args:
            session_id: ID сессии
            results: Результаты обработки
        
        Returns:
            bool: Успешность резервного копирования
        """
        remote_key = f"results/{session_id}/processing_results.json"
        
        # Добавляем метаданные к результатам
        backup_data = {
            'session_id': session_id,
            'backup_time': datetime.now().isoformat(),
            'results': results,
            'system_info': {
                'version': 'VHM24R-1.0',
                'backup_type': 'processing_results'
            }
        }
        
        return self.storage.upload_json_data(backup_data, remote_key)
    
    def cleanup_old_files(self, days_to_keep: int = 30) -> Dict:
        """
        Очистка старых файлов (локальных и в хранилище)
        
        Args:
            days_to_keep: Количество дней для хранения файлов
        
        Returns:
            Dict: Статистика очистки
        """
        from datetime import timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        # Получаем старые файлы из БД
        old_files = self.db.execute_query("""
            SELECT * FROM file_metadata 
            WHERE upload_time < ? 
            AND processing_status = 'completed'
        """, (cutoff_date,))
        
        cleanup_stats = {
            'local_deleted': 0,
            'remote_deleted': 0,
            'db_cleaned': 0,
            'errors': 0
        }
        
        for file_record in old_files:
            try:
                # Удаляем локальный файл
                if file_record['file_path'] and os.path.exists(file_record['file_path']):
                    os.remove(file_record['file_path'])
                    cleanup_stats['local_deleted'] += 1
                
                # Удаляем из DigitalOcean Spaces
                if file_record['remote_key']:
                    if self.storage.delete_file(file_record['remote_key']):
                        cleanup_stats['remote_deleted'] += 1
                
                # Удаляем запись из БД
                self.db.execute_query(
                    "DELETE FROM file_metadata WHERE id = ?",
                    (file_record['id'],)
                )
                cleanup_stats['db_cleaned'] += 1
                
            except Exception as e:
                print(f"Error cleaning up file {file_record['filename']}: {e}")
                cleanup_stats['errors'] += 1
        
        return cleanup_stats
    
    def get_file_download_url(self, file_id: int, expiration: int = 3600) -> Optional[str]:
        """
        Получение URL для скачивания файла
        
        Args:
            file_id: ID файла в БД
            expiration: Время жизни URL в секундах
        
        Returns:
            str: URL для скачивания или None
        """
        file_record = self.db.execute_query(
            "SELECT * FROM file_metadata WHERE id = ?",
            (file_id,)
        )
        
        if not file_record:
            return None
        
        file_info = file_record[0]
        
        # Если файл есть в DigitalOcean Spaces, генерируем подписанную URL
        if file_info['remote_key']:
            return self.storage.generate_presigned_url(file_info['remote_key'], expiration)
        
        # Если файл только локальный, возвращаем None (нужно реализовать локальную отдачу)
        return None


# Глобальный экземпляр для использования в приложении
file_manager = None

def init_storage(db, upload_dir: str = 'uploads'):
    """Инициализация модуля хранения файлов"""
    global file_manager
    file_manager = FileManager(db, upload_dir)
    return file_manager
