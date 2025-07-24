"""
VHM24R - Telegram Bot для уведомлений и управления
Модуль для отправки уведомлений о критических ошибках и статистике
"""

import os
import asyncio
import json
from datetime import datetime, date
from typing import Dict, List, Optional
import requests
from telegram import Bot
from telegram.error import TelegramError

class TelegramNotifier:
    """
    Класс для отправки уведомлений в Telegram согласно промту:
    - Ошибки выше критического уровня
    - Ежедневные отчеты
    - Статистика сверки
    """
    
    def __init__(self, db=None):
        self.bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.db = db
        self.enabled = bool(self.bot_token and self.chat_id)
        
        if self.enabled:
            self.bot = Bot(token=self.bot_token)
        else:
            print("Telegram notifications disabled: missing bot token or chat ID")
    
    async def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Отправка сообщения в Telegram"""
        if not self.enabled:
            print(f"Telegram disabled. Would send: {message}")
            return False
        
        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
        except TelegramError as e:
            print(f"Telegram error: {e}")
            return False
    
    async def send_critical_errors_alert(self, session_id: str, stats: Dict[str, int]):
        """
        Отправка уведомления о критических ошибках
        Согласно промту: ошибки выше критического уровня
        """
        if not self.enabled:
            return
        
        # Получаем порог критических ошибок из конфигурации
        critical_threshold = 10
        if self.db:
            try:
                config = self.db.execute_query(
                    "SELECT config_value FROM system_config WHERE config_key = 'critical_error_threshold'"
                )
                if config:
                    critical_threshold = int(config[0]['config_value'])
            except:
                pass
        
        # Подсчитываем общее количество ошибок
        total_errors = (
            stats.get('NO_MATCH_IN_REPORT', 0) +
            stats.get('NO_PAYMENT_FOUND', 0) +
            stats.get('EXCESS_PAYMENT', 0) +
            stats.get('PAYMENT_MISMATCH', 0) +
            stats.get('FISCAL_MISSING', 0)
        )
        
        if total_errors >= critical_threshold:
            message = f"""
🚨 <b>КРИТИЧЕСКИЕ ОШИБКИ СВЕРКИ</b>

📊 <b>Сессия:</b> {session_id[:8]}...
⚠️ <b>Всего ошибок:</b> {total_errors}
✅ <b>Успешных:</b> {stats.get('OK', 0)}

<b>Детализация ошибок:</b>
• Нет во внутреннем учете: {stats.get('NO_MATCH_IN_REPORT', 0)}
• Нет оплаты: {stats.get('NO_PAYMENT_FOUND', 0)}
• Лишние платежи: {stats.get('EXCESS_PAYMENT', 0)}
• Несовпадение сумм: {stats.get('PAYMENT_MISMATCH', 0)}
• Нет фискальных чеков: {stats.get('FISCAL_MISSING', 0)}

🕐 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}

Требуется проверка данных!
            """.strip()
            
            await self.send_message(message)
    
    async def send_daily_report(self, report_date: Optional[date] = None):
        """Отправка ежедневного отчета"""
        if not self.enabled or not self.db:
            return
        
        if report_date is None:
            report_date = date.today()
        
        try:
            # Получаем статистику за день
            daily_stats = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_orders,
                    COUNT(CASE WHEN error_type = 'OK' THEN 1 END) as successful_orders,
                    COUNT(CASE WHEN error_type = 'NO_MATCH_IN_REPORT' THEN 1 END) as no_match_in_report,
                    COUNT(CASE WHEN error_type = 'NO_PAYMENT_FOUND' THEN 1 END) as no_payment_found,
                    COUNT(CASE WHEN error_type = 'FISCAL_MISSING' THEN 1 END) as fiscal_missing,
                    SUM(order_price) as total_amount,
                    SUM(CASE WHEN error_type = 'OK' THEN order_price ELSE 0 END) as successful_amount
                FROM orders 
                WHERE DATE(creation_time) = ?
            """, (report_date,))
            
            if not daily_stats or daily_stats[0]['total_orders'] == 0:
                return
            
            stats = daily_stats[0]
            success_rate = (stats['successful_orders'] / stats['total_orders'] * 100) if stats['total_orders'] > 0 else 0
            
            message = f"""
📈 <b>ЕЖЕДНЕВНЫЙ ОТЧЕТ СВЕРКИ</b>

📅 <b>Дата:</b> {report_date.strftime('%d.%m.%Y')}

📊 <b>Общая статистика:</b>
• Всего заказов: {stats['total_orders']}
• Успешных: {stats['successful_orders']} ({success_rate:.1f}%)
• Общая сумма: {stats['total_amount']:,.0f} сум
• Сверенная сумма: {stats['successful_amount']:,.0f} сум

⚠️ <b>Проблемы:</b>
• Нет во внутреннем учете: {stats['no_match_in_report']}
• Нет оплаты: {stats['no_payment_found']}
• Нет фискальных чеков: {stats['fiscal_missing']}

🕐 <b>Отчет сформирован:</b> {datetime.now().strftime('%H:%M')}
            """.strip()
            
            await self.send_message(message)
            
        except Exception as e:
            print(f"Error sending daily report: {e}")
    
    async def send_processing_complete(self, session_id: str, stats: Dict[str, int], files_count: int):
        """Уведомление о завершении обработки"""
        if not self.enabled:
            return
        
        total_orders = sum(stats.values())
        success_rate = (stats.get('OK', 0) / total_orders * 100) if total_orders > 0 else 0
        
        message = f"""
✅ <b>ОБРАБОТКА ЗАВЕРШЕНА</b>

📁 <b>Файлов обработано:</b> {files_count}
📊 <b>Заказов обработано:</b> {total_orders}
📈 <b>Успешность сверки:</b> {success_rate:.1f}%

<b>Результаты:</b>
✅ Успешных: {stats.get('OK', 0)}
❌ Ошибок: {total_orders - stats.get('OK', 0)}

🆔 <b>Сессия:</b> {session_id[:8]}...
🕐 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """.strip()
        
        await self.send_message(message)
    
    async def send_machine_issues_alert(self, machine_code: str, error_count: int, error_rate: float):
        """Уведомление о проблемах с конкретным автоматом"""
        if not self.enabled:
            return
        
        if error_rate > 50:  # Более 50% ошибок
            message = f"""
🚨 <b>ПРОБЛЕМЫ С АВТОМАТОМ</b>

🏪 <b>Автомат:</b> {machine_code}
❌ <b>Ошибок:</b> {error_count}
📊 <b>Процент ошибок:</b> {error_rate:.1f}%

Требуется проверка автомата!
🕐 <b>Время:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}
            """.strip()
            
            await self.send_message(message)
    
    def send_sync(self, message: str):
        """Синхронная отправка сообщения"""
        if not self.enabled:
            return False
        
        try:
            asyncio.run(self.send_message(message))
            return True
        except Exception as e:
            print(f"Error sending sync message: {e}")
            return False


class TelegramBot:
    """
    Основной класс Telegram бота для управления системой
    Позволяет менеджерам получать отчеты и управлять системой
    """
    
    def __init__(self, db):
        self.db = db
        self.notifier = TelegramNotifier(db)
    
    async def handle_command(self, command: str, chat_id: str) -> str:
        """Обработка команд от пользователей"""
        command = command.lower().strip()
        
        if command == '/start':
            return """
🤖 <b>VHM24R - Система сверки заказов</b>

Доступные команды:
/stats - Текущая статистика
/today - Отчет за сегодня
/machines - Проблемные автоматы
/help - Справка
            """.strip()
        
        elif command == '/stats':
            return await self._get_current_stats()
        
        elif command == '/today':
            return await self._get_today_report()
        
        elif command == '/machines':
            return await self._get_machine_issues()
        
        elif command == '/help':
            return """
📖 <b>Справка по командам:</b>

/stats - Общая статистика системы
/today - Подробный отчет за сегодня
/machines - Список автоматов с проблемами
/help - Эта справка

🔔 Система автоматически отправляет уведомления о критических ошибках.
            """.strip()
        
        else:
            return "❓ Неизвестная команда. Используйте /help для справки."
    
    async def _get_current_stats(self) -> str:
        """Получение текущей статистики"""
        try:
            stats = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_orders,
                    COUNT(CASE WHEN error_type = 'OK' THEN 1 END) as successful_orders,
                    COUNT(CASE WHEN error_type != 'OK' AND error_type != 'UNPROCESSED' THEN 1 END) as error_orders
                FROM orders 
                WHERE creation_time >= CURRENT_DATE - INTERVAL '7 days'
            """)
            
            if stats:
                stat = stats[0]
                success_rate = (stat['successful_orders'] / stat['total_orders'] * 100) if stat['total_orders'] > 0 else 0
                
                return f"""
📊 <b>СТАТИСТИКА ЗА 7 ДНЕЙ</b>

📈 Всего заказов: {stat['total_orders']}
✅ Успешных: {stat['successful_orders']} ({success_rate:.1f}%)
❌ С ошибками: {stat['error_orders']}

🕐 Обновлено: {datetime.now().strftime('%d.%m.%Y %H:%M')}
                """.strip()
            else:
                return "📊 Нет данных для отображения статистики."
                
        except Exception as e:
            return f"❌ Ошибка получения статистики: {str(e)}"
    
    async def _get_today_report(self) -> str:
        """Получение отчета за сегодня"""
        try:
            today_stats = self.db.execute_query("""
                SELECT 
                    COUNT(*) as total_orders,
                    COUNT(CASE WHEN error_type = 'OK' THEN 1 END) as successful_orders,
                    COUNT(CASE WHEN error_type = 'NO_MATCH_IN_REPORT' THEN 1 END) as no_match_in_report,
                    COUNT(CASE WHEN error_type = 'NO_PAYMENT_FOUND' THEN 1 END) as no_payment_found,
                    COUNT(CASE WHEN error_type = 'FISCAL_MISSING' THEN 1 END) as fiscal_missing,
                    SUM(order_price) as total_amount
                FROM orders 
                WHERE DATE(creation_time) = CURRENT_DATE
            """)
            
            if today_stats and today_stats[0]['total_orders'] > 0:
                stat = today_stats[0]
                success_rate = (stat['successful_orders'] / stat['total_orders'] * 100) if stat['total_orders'] > 0 else 0
                
                return f"""
📅 <b>ОТЧЕТ ЗА СЕГОДНЯ</b>

📊 Всего заказов: {stat['total_orders']}
✅ Успешных: {stat['successful_orders']} ({success_rate:.1f}%)
💰 Общая сумма: {stat['total_amount']:,.0f} сум

❌ Проблемы:
• Нет во внутреннем учете: {stat['no_match_in_report']}
• Нет оплаты: {stat['no_payment_found']}
• Нет фискальных чеков: {stat['fiscal_missing']}

🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}
                """.strip()
            else:
                return "📅 Сегодня заказов пока нет."
                
        except Exception as e:
            return f"❌ Ошибка получения отчета: {str(e)}"
    
    async def _get_machine_issues(self) -> str:
        """Получение списка проблемных автоматов"""
        try:
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
                    AND creation_time >= CURRENT_DATE - INTERVAL '3 days'
                GROUP BY machine_code
                HAVING COUNT(CASE WHEN error_type != 'OK' THEN 1 END) > 0
                ORDER BY error_rate DESC
                LIMIT 10
            """)
            
            if machine_issues:
                message = "🏪 <b>ПРОБЛЕМНЫЕ АВТОМАТЫ (3 дня)</b>\n\n"
                
                for issue in machine_issues:
                    status_icon = "🚨" if issue['error_rate'] > 50 else "⚠️" if issue['error_rate'] > 20 else "🔸"
                    message += f"{status_icon} <b>{issue['machine_code']}</b>: {issue['error_orders']}/{issue['total_orders']} ({issue['error_rate']}%)\n"
                
                message += f"\n🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
                return message
            else:
                return "✅ Проблемных автоматов не найдено."
                
        except Exception as e:
            return f"❌ Ошибка получения данных об автоматах: {str(e)}"


# Глобальный экземпляр для использования в приложении
telegram_notifier = None
telegram_bot = None

def init_telegram(db):
    """Инициализация Telegram модулей"""
    global telegram_notifier, telegram_bot
    telegram_notifier = TelegramNotifier(db)
    telegram_bot = TelegramBot(db)
    return telegram_notifier, telegram_bot
