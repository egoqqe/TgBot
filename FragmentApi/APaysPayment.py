import requests
import hashlib
import logging
import json
import time
from typing import Dict, Any, Optional


class APaysPayment:
    """
    Класс для работы с APays API
    Документация: https://docs.apays.io/lets-start/api
    """
    
    def __init__(self, client_id: int, secret_key: str, base_url: str = "https://apays.io"):
        """
        Инициализация APays клиента
        
        Args:
            client_id: ID клиента от APays
            secret_key: Секретный ключ от APays
            base_url: Базовый URL API (по умолчанию https://apays.io)
        """
        self.client_id = client_id
        self.secret_key = secret_key
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        
        # Настройка заголовков
        self.session.headers.update({
            'User-Agent': 'FragmentBot/1.0',
            'Accept': 'application/json'
        })
        
        logging.info("✅ APays клиент инициализирован")
    
    def _generate_sign(self, order_id: str, amount: Optional[int] = None) -> str:
        """
        Генерирует подпись для запроса
        
        Args:
            order_id: ID заказа
            amount: Сумма в копейках (опционально)
            
        Returns:
            MD5 подпись
        """
        if amount is not None:
            # Для создания заказа: md5(order_id:amount:secret_key)
            sign_string = f"{order_id}:{amount}:{self.secret_key}"
        else:
            # Для проверки статуса: md5(order_id:secret_key)
            sign_string = f"{order_id}:{self.secret_key}"
        
        return hashlib.md5(sign_string.encode('utf-8')).hexdigest()
    
    def create_order(self, order_id: str, amount: int, callback_url: str = "") -> Dict[str, Any]:
        """
        Создает новый заказ на оплату
        
        Args:
            order_id: Уникальный ID заказа
            amount: Сумма в копейках
            callback_url: URL для webhook уведомлений (опционально)
            
        Returns:
            Данные заказа с URL для оплаты
            
        Raises:
            Exception: При ошибке создания заказа
        """
        sign = self._generate_sign(order_id, amount)
        
        params = {
            'client_id': self.client_id,
            'order_id': order_id,
            'amount': amount,
            'sign': sign
        }
        
        if callback_url:
            params['callback_url'] = callback_url
        
        try:
            logging.info(f"📡 APays создание заказа: order_id={order_id}, amount={amount} копеек")
            
            response = self.session.get(f"{self.base_url}/backend/create_order", params=params)
            response.raise_for_status()
            result = response.json()
            
            logging.info(f"✅ APays заказ создан: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Ошибка создания заказа APays: {e}")
            raise Exception(f"Ошибка создания заказа APays: {e}")
        except json.JSONDecodeError as e:
            logging.error(f"❌ Ошибка парсинга JSON ответа APays: {e}")
            raise Exception(f"Ошибка парсинга ответа APays: {e}")
    
    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """
        Получает статус заказа
        
        Args:
            order_id: ID заказа
            
        Returns:
            Статус заказа
            
        Raises:
            Exception: При ошибке получения статуса
        """
        sign = self._generate_sign(order_id)
        
        params = {
            'client_id': self.client_id,
            'order_id': order_id,
            'sign': sign
        }
        
        try:
            logging.info(f"📡 APays проверка статуса: order_id={order_id}")
            
            response = self.session.get(f"{self.base_url}/backend/get_order", params=params)
            response.raise_for_status()
            result = response.json()
            
            logging.info(f"✅ APays статус заказа: {result}")
            return result
            
        except requests.exceptions.RequestException as e:
            logging.error(f"❌ Ошибка получения статуса APays: {e}")
            raise Exception(f"Ошибка получения статуса APays: {e}")
        except json.JSONDecodeError as e:
            logging.error(f"❌ Ошибка парсинга JSON ответа APays: {e}")
            raise Exception(f"Ошибка парсинга ответа APays: {e}")
    
    def verify_webhook_signature(self, order_id: str, status: str, sign: str) -> bool:
        """
        Проверяет подпись webhook
        
        Args:
            order_id: ID заказа
            status: Статус заказа
            sign: Подпись из webhook
            
        Returns:
            True если подпись верна
        """
        expected_sign = hashlib.md5(f"{order_id}:{status}:{self.secret_key}".encode('utf-8')).hexdigest()
        return sign == expected_sign
    
    def process_webhook(self, webhook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Обрабатывает webhook от APays
        
        Args:
            webhook_data: Данные webhook
            
        Returns:
            Результат обработки
        """
        try:
            order_id = webhook_data.get('order_id')
            status = webhook_data.get('status')
            sign = webhook_data.get('sign')
            
            logging.info(f"📨 APays webhook: order_id={order_id}, status={status}")
            
            # Проверяем подпись
            if not self.verify_webhook_signature(order_id, status, sign):
                logging.error(f"❌ Неверная подпись webhook APays: {order_id}")
                return {
                    'success': False,
                    'message': 'Invalid signature'
                }
            
            # Обрабатываем статус
            if status == 'approved':
                logging.info(f"✅ Платеж APays одобрен: {order_id}")
                # Здесь можно добавить логику обработки успешного платежа
                # Например, пополнение баланса пользователя
                
            elif status == 'declined':
                logging.info(f"❌ Платеж APays отклонен: {order_id}")
                # Здесь можно добавить логику обработки отклоненного платежа
                
            return {
                'success': True,
                'message': 'Webhook processed successfully',
                'order_id': order_id,
                'status': status
            }
            
        except Exception as e:
            logging.error(f"❌ Ошибка обработки APays webhook: {e}")
            return {
                'success': False,
                'message': f'Error processing webhook: {e}'
            }
    
    def rubles_to_kopecks(self, rubles: float) -> int:
        """
        Конвертирует рубли в копейки
        
        Args:
            rubles: Сумма в рублях
            
        Returns:
            Сумма в копейках
        """
        return int(rubles * 100)
    
    def kopecks_to_rubles(self, kopecks: int) -> float:
        """
        Конвертирует копейки в рубли
        
        Args:
            kopecks: Сумма в копейках
            
        Returns:
            Сумма в рублях
        """
        return kopecks / 100


# Пример использования
if __name__ == "__main__":
    # Инициализация (в реальном проекте используйте переменные окружения)
    apays = APaysPayment(
        client_id=123,  # Замените на ваш client_id
        secret_key="your_secret_key_here"  # Замените на ваш secret_key
    )
    
    try:
        # Создание заказа
        order_id = f"order_{int(time.time())}"
        amount_kopecks = apays.rubles_to_kopecks(100.0)  # 100 рублей
        
        order = apays.create_order(
            order_id=order_id,
            amount=amount_kopecks,
            callback_url="https://your-domain.com/webhook/apays"
        )
        print(f"Заказ создан: {order}")
        
        # Проверка статуса
        status = apays.get_order_status(order_id)
        print(f"Статус заказа: {status}")
        
    except Exception as e:
        print(f"Ошибка: {e}")


