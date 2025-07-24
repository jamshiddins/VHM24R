"""
VHM24R - Планировщик задач для работы 24/7
Автоматические задачи согласно промту: ежедневный парсинг, уведомления, очистка
"""

import os
import asyncio
import schedule
import time
import threading
from datetime import datetime, date, timedelta
from typing import Dict, List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

class VHMScheduler:
    """
    Планировщик задач для VHM24R
    Согласно промту: работает 24/7, автоматические задачи
    """
    
    def __init__(self, db, order_processor, telegram_notifier=None, file_manager=None):
        self.db = db
        self.order_processor = order_processor
        self.telegram_notifier = telegram_notifier
        self.file_manager = file_manager
        
        # Инициализируем планировщик
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # Настраиваем задачи
        self._setup_scheduled_tasks()
        
        print("VHM Scheduler initialized and started")
    
    def _setup_scheduled_tasks(self):
        """Настройка всех запланированных задач"""
        
        # 1. Ежедневная сверка в 02:00
        self.scheduler.add_job(
            func=self.daily_reconciliation,
            trigger=CronTrigger(hour=2, minute=0),
            id='daily_reconciliation',
            name='Ежедневная сверка заказов',
            replace_existing=True
        )
        
        # 2. Ежедневный отчет в 09:00
        self.scheduler.add_job(
            func=self.send_daily_report,
            trigger=CronTrigger(hour=9, minute=0),
            id='daily_report',
            name='Ежедневный отчет',
            replace_existing=True
        )
        
        # 3. Проверка критических ошибок каждый час
        self.scheduler.add_job(
            func=self.check_critical_errors,
            trigger=IntervalTrigger(hours=1),
            id='critical_errors_check',
            name='Проверка критических ошибок',
            replace_existing=True
        )
        
        # 4. Очистка старых файлов еженедельно (воскресенье в 03:00)
        self.scheduler.add_job(
            func=self.cleanup_old_files,
            trigger=CronTrigger(day_of_week=6, hour=3, minute=0),
            id='weekly_cleanup',
            name='Еженедельная очистка файлов',
            replace_existing=True
        )
        
        # 5. Проверка состояния автоматов каждые 4 часа
        self.scheduler.add_job(
            func=self.check_machine_health,
            trigger=IntervalTrigger(hours=4),
            id='machine_health_check',
            name='Проверка состояния автоматов',
            replace_existing=True
        )
        
        # 6. Резервное копирование данных ежедневно в 04:00
        self.scheduler.add_job(
            func=self.backup_data,
            trigger=CronTrigger(hour=4, minute=0),
            id='daily_backup',
            name='Ежедневное резервное копирование',
            replace_existing=True
        )
        
        # 7. Мониторинг системы каждые 30 минут
        self.scheduler.add_job(
            func=self.system_health_check,
            trigger=IntervalTrigger(minutes=30),
            id='system_health',
            name='Мониторинг системы',
            replace_existing=True
        )
    
    def daily_reconciliation(self):
        """
        Ежедневная автоматическая сверка
        Согласно промту: ежедневный парсинг
        """
        try:
            print(f"Starting daily reconciliation at {datetime.now()}")
            
            # Получаем все необработанные заказы за последние 2 дня
            cutoff_date = datetime.now() - timedelta(days=2)
            
            unprocessed_orders = self.db.execute_query("""
                SELECT COUNT(*) as count FROM orders 
                WHERE error_type = 'UNPROCESSED' 
                AND created_at >= ?
            """, (cutoff_date,))
            
            if unprocessed_orders and unprocessed_orders[0]['count'] > 0:
                print(f"Found {unprocessed_orders[0]['count']} unprocessed orders")
                
                # Запускаем сверку
                stats = self.order_processor.run_matching()
                
                # Отправляем уведомление о результатах
                if self.telegram_notifier:
                    asyncio.run(self.telegram_notifier.send_processing_complete(
                        session_id=f"daily_{datetime.now().strftime('%Y%m%d')}",
                        stats=stats,
                        files_count=0
                    ))
                
                print(f"Daily reconciliation completed. Stats: {stats}")
            else:
                print("No unprocessed orders found for daily reconciliation")
                
        except Exception as e:
            print(f"Error in daily reconciliation: {e}")
            if self.telegram_notifier:
                asyncio.run(self.telegram_notifier.send_message(
                    f"🚨 Ошибка ежедневной сверки: {str(e)}"
                ))
    
    def send_daily_report(self):
        """Отправка ежедневного отчета"""
        try:
            if self.telegram_notifier:
                asyncio.run(self.telegram_notifier.send_daily_report())
                print(f"Daily report sent at {datetime.now()}")
        except Exception as e:
            print(f"Error sending daily report: {e}")
    
    def check_critical_errors(self):
        """
        Проверка критических ошибок
        Согласно промту: ошибки выше критического уровня → Telegram
        """
        try:
            # Получаем статистику ошибок за последний час
            one_hour_ago = datetime.now() - timedelta(hours=1)
            
            recent_errors = self.db.execute_query("""
                SELECT 
                    error_type,
                    COUNT(*) as count
                FROM orders 
                WHERE updated_at >= ? 
                AND error_type != 'OK' 
                AND error_type != 'UNPROCESSED'
                GROUP BY error_type
            """, (one_hour_ago,))
            
            if recent_errors:
                total_errors = sum(error['count'] for error in recent_errors)
                
                # Получаем порог из конфигурации
                critical_threshold = 5  # По умолчанию 5 ошибок в час
                try:
                    config = self.db.execute_query(
                        "SELECT config_value FROM system_config WHERE config_key = 'critical_error_threshold'"
                    )
                    if config:
                        critical_threshold = int(config[0]['config_value'])
                except:
                    pass
                
                if total_errors >= critical_threshold:
                    error_stats = {error['error_type']: error['count'] for error in recent_errors}
                    
                    if self.telegram_notifier:
                        asyncio.run(self.telegram_notifier.send_critical_errors_alert(
                            session_id=f"hourly_{datetime.now().strftime('%Y%m%d_%H')}",
                            stats=error_stats
                        ))
                    
                    print(f"Critical errors detected: {total_errors} errors in last hour")
                
        except Exception as e:
            print(f"Error checking critical errors: {e}")
    
    def cleanup_old_files(self):
        """Еженедельная очистка старых файлов"""
        try:
            if self.file_manager:
                cleanup_stats = self.file_manager.cleanup_old_files(days_to_keep=30)
                
                message = f"""
🧹 Еженедельная очистка файлов завершена:
• Локальных файлов удалено: {cleanup_stats['local_deleted']}
• Файлов из хранилища удалено: {cleanup_stats['remote_deleted']}
• Записей из БД очищено: {cleanup_stats['db_cleaned']}
• Ошибок: {cleanup_stats['errors']}
                """.strip()
                
                if self.telegram_notifier:
                    asyncio.run(self.telegram_notifier.send_message(message))
                
                print(f"File cleanup completed: {cleanup_stats}")
            
        except Exception as e:
            print(f"Error in file cleanup: {e}")
    
    def check_machine_health(self):
        """Проверка состояния автоматов"""
        try:
            # Получаем автоматы с высоким процентом ошибок за последние 24 часа
            yesterday = datetime.now() - timedelta(days=1)
            
            machine_issues = self.db.execute_query("""
                SELECT 
                    machine_code,
                    COUNT(*) as total_orders,
                    COUNT(CASE WHEN error_type != 'OK' THEN 1 END) as error_orders,
                    ROUND(
                        COUNT(CASE WHEN error_type != 'OK' THEN 1 END) * 100.0 / COUNT(*), 
                        1
                    ) as error_rate
                FROM orders 
                WHERE machine_code IS NOT NULL 
                    AND creation_time >= ?
                GROUP BY machine_code
                HAVING COUNT(CASE WHEN error_type != 'OK' THEN 1 END) > 0
                    AND COUNT(*) >= 5
                    AND (COUNT(CASE WHEN error_type != 'OK' THEN 1 END) * 100.0 / COUNT(*)) > 50
                ORDER BY error_rate DESC
            """, (yesterday,))
            
            for issue in machine_issues:
                if self.telegram_notifier:
                    asyncio.run(self.telegram_notifier.send_machine_issues_alert(
                        machine_code=issue['machine_code'],
                        error_count=issue['error_orders'],
                        error_rate=issue['error_rate']
                    ))
                
                print(f"Machine health issue: {issue['machine_code']} - {issue['error_rate']}% error rate")
            
        except Exception as e:
            print(f"Error checking machine health: {e}")
    
    def backup_data(self):
        """Ежедневное резервное копирование данных"""
        try:
            if self.file_manager:
                # Создаем резервную копию статистики за вчера
                yesterday = date.today() - timedelta(days=1)
                
                backup_data = {
                    'date': yesterday.isoformat(),
                    'summary': self._get_daily_summary(yesterday),
                    'orders': self._get_orders_for_backup(yesterday),
                    'backup_type': 'daily_backup',
                    'created_at': datetime.now().isoformat()
                }
                
                session_id = f"backup_{yesterday.strftime('%Y%m%d')}"
                success = self.file_manager.backup_processing_results(session_id, backup_data)
                
                if success:
                    print(f"Daily backup completed for {yesterday}")
                else:
                    print(f"Daily backup failed for {yesterday}")
            
        except Exception as e:
            print(f"Error in daily backup: {e}")
    
    def system_health_check(self):
        """Мониторинг состояния системы"""
        try:
            # Проверяем подключение к БД
            db_status = self._check_database_health()
            
            # Проверяем использование диска
            disk_usage = self._check_disk_usage()
            
            # Проверяем последнюю активность
            last_activity = self._check_last_activity()
            
            # Если есть проблемы, отправляем уведомление
            issues = []
            
            if not db_status:
                issues.append("❌ Проблемы с подключением к БД")
            
            if disk_usage > 90:
                issues.append(f"💾 Диск заполнен на {disk_usage}%")
            
            if last_activity and (datetime.now() - last_activity).total_seconds() > 7200:  # 2 часа
                issues.append("⏰ Нет активности более 2 часов")
            
            if issues and self.telegram_notifier:
                message = "🚨 <b>ПРОБЛЕМЫ СИСТЕМЫ</b>\n\n" + "\n".join(issues)
                asyncio.run(self.telegram_notifier.send_message(message))
            
        except Exception as e:
            print(f"Error in system health check: {e}")
    
    def _get_daily_summary(self, target_date: date) -> Dict:
        """Получение сводки за день для резервного копирования"""
        try:
            summary = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_orders,
                    COUNT(CASE WHEN error_type = 'OK' THEN 1 END) as successful_orders,
                    COUNT(CASE WHEN error_type = 'NO_MATCH_IN_REPORT' THEN 1 END) as no_match_in_report,
                    COUNT(CASE WHEN error_type = 'NO_PAYMENT_FOUND' THEN 1 END) as no_payment_found,
                    COUNT(CASE WHEN error_type = 'FISCAL_MISSING' THEN 1 END) as fiscal_missing,
                    SUM(order_price) as total_amount
                FROM orders 
                WHERE DATE(creation_time) = ?
            """, (target_date,))
            
            return summary[0] if summary else {}
        except:
            return {}
    
    def _get_orders_for_backup(self, target_date: date) -> List[Dict]:
        """Получение заказов за день для резервного копирования"""
        try:
            orders = self.db.execute_query("""
                SELECT 
                    order_number, machine_code, creation_time, order_price,
                    error_type, payment_type, matched_payment, matched_fiscal
                FROM orders 
                WHERE DATE(creation_time) = ?
                ORDER BY creation_time
            """, (target_date,))
            
            return orders[:1000]  # Ограничиваем количество для экономии места
        except:
            return []
    
    def _check_database_health(self) -> bool:
        """Проверка состояния БД"""
        try:
            result = self.db.execute_query("SELECT 1")
            return bool(result)
        except:
            return False
    
    def _check_disk_usage(self) -> float:
        """Проверка использования диска"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            return (used / total) * 100
        except:
            return 0
    
    def _check_last_activity(self) -> datetime | None:
        """Проверка последней активности в системе"""
        try:
            result = self.db.execute_query("""
                SELECT MAX(created_at) as last_activity 
                FROM orders 
                WHERE created_at >= ?
            """, (datetime.now() - timedelta(days=1),))
            
            if result and result[0]['last_activity']:
                return datetime.fromisoformat(result[0]['last_activity']) if isinstance(result[0]['last_activity'], str) else result[0]['last_activity']
            return None
        except:
            return None
    
    def stop(self):
        """Остановка планировщика"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            print("VHM Scheduler stopped")
    
    def get_job_status(self) -> List[Dict]:
        """Получение статуса всех задач"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def run_job_manually(self, job_id: str) -> bool:
        """Ручной запуск задачи"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.func()
                return True
            return False
        except Exception as e:
            print(f"Error running job {job_id}: {e}")
            return False


# Глобальный экземпляр планировщика
vhm_scheduler = None

def init_scheduler(db, order_processor, telegram_notifier=None, file_manager=None):
    """Инициализация планировщика задач"""
    global vhm_scheduler
    vhm_scheduler = VHMScheduler(db, order_processor, telegram_notifier, file_manager)
    return vhm_scheduler

def stop_scheduler():
    """Остановка планировщика"""
    global vhm_scheduler
    if vhm_scheduler:
        vhm_scheduler.stop()
        vhm_scheduler = None
