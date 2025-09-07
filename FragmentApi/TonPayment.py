"""
Модуль для обработки прямых TON переводов
"""
import requests
import time
import logging
from typing import Dict, Optional, List
from config import TON_WALLET_ADDRESS, TON_COMMISSION_PERCENT, TON_CENTER_API_KEY, TON_CENTER_API_URL

class TonPayment:
    """Класс для работы с прямыми TON переводами"""
    
    def __init__(self):
        self.wallet_address = TON_WALLET_ADDRESS
        self.commission_percent = TON_COMMISSION_PERCENT
        self.api_key = TON_CENTER_API_KEY
        self.api_url = TON_CENTER_API_URL
        logging.info("✅ TON Payment инициализирован")
    
    def get_wallet_transactions(self, limit: int = 50) -> List[Dict]:
        """Получает последние транзакции кошелька через TON Center API"""
        try:
            headers = {
                'X-API-Key': self.api_key
            }
            
            # Получаем последние транзакции
            response = requests.get(
                f"{self.api_url}/getTransactions",
                params={
                    'address': self.wallet_address,
                    'limit': limit,
                    'archival': True
                },
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('ok'):
                    return data.get('result', [])
                else:
                    logging.error(f"TON Center API error: {data.get('error', 'Unknown error')}")
                    return []
            else:
                logging.error(f"TON Center API HTTP error: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Ошибка получения транзакций: {e}")
            return []
    
    def rubles_to_ton(self, rubles: float) -> float:
        """Конвертирует рубли в TON по текущему курсу"""
        try:
            # Получаем курс TON к рублю
            response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=rub")
            if response.status_code == 200:
                data = response.json()
                ton_price_rub = data.get("the-open-network", {}).get("rub", 0)
                if ton_price_rub > 0:
                    ton_amount = rubles / ton_price_rub
                    return round(ton_amount, 4)
            
            # Fallback курс (примерно 200 рублей за TON)
            fallback_rate = 200
            return round(rubles / fallback_rate, 4)
            
        except Exception as e:
            logging.error(f"Ошибка получения курса TON: {e}")
            # Fallback курс
            fallback_rate = 200
            return round(rubles / fallback_rate, 4)
    
    def ton_to_rubles(self, ton_amount: float) -> float:
        """Конвертирует TON в рубли по текущему курсу"""
        try:
            response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=the-open-network&vs_currencies=rub")
            if response.status_code == 200:
                data = response.json()
                ton_price_rub = data.get("the-open-network", {}).get("rub", 0)
                if ton_price_rub > 0:
                    return round(ton_amount * ton_price_rub, 2)
            
            # Fallback курс
            fallback_rate = 200
            return round(ton_amount * fallback_rate, 2)
            
        except Exception as e:
            logging.error(f"Ошибка получения курса TON: {e}")
            fallback_rate = 200
            return round(ton_amount * fallback_rate, 2)
    
    def create_payment_request(self, user_id: int, amount_rub: float) -> Dict:
        """Создает запрос на пополнение через TON"""
        try:
            ton_amount = self.rubles_to_ton(amount_rub)
            payment_id = f"ton_{user_id}_{int(time.time())}"
            
            # Создаем короткий уникальный комментарий для идентификации платежа
            # Используем последние 3 цифры user_id + последние 3 цифры timestamp для краткости
            user_suffix = str(user_id)[-3:]  # Последние 3 цифры user_id
            time_suffix = str(int(time.time()))[-3:]  # Последние 3 цифры timestamp
            comment = f"T{user_suffix}{time_suffix}"  # Например: T188065
            
            payment_data = {
                "payment_id": payment_id,
                "user_id": user_id,
                "amount_rub": amount_rub,
                "amount_ton": ton_amount,
                "wallet_address": self.wallet_address,
                "commission_percent": self.commission_percent,
                "comment": comment,
                "status": "pending",
                "created_at": int(time.time())
            }
            
            logging.info(f"📡 TON платеж создан: {payment_id}, {amount_rub} RUB = {ton_amount} TON, комментарий: {comment}")
            return payment_data
            
        except Exception as e:
            logging.error(f"Ошибка создания TON платежа: {e}")
            return {"error": str(e)}
    
    def check_ton_transaction(self, payment_id: str, expected_comment: str = None) -> Dict:
        """Проверяет поступление TON на кошелек по комментарию"""
        try:
            # Получаем последние транзакции
            transactions = self.get_wallet_transactions(50)
            
            if transactions:
                # Проверяем все транзакции за последние 30 минут
                current_time = int(time.time())
                
                logging.info(f"🔍 Проверяем {len(transactions)} транзакций для платежа {payment_id}")
                logging.info(f"🔍 Ожидаемый комментарий: {expected_comment}")
                
                for tx in transactions:
                    if tx.get("in_msg"):
                        in_msg = tx["in_msg"]
                        if in_msg.get("value"):
                            received_amount = int(in_msg["value"]) / 1000000000
                            
                            # Проверяем время транзакции (последние 30 минут)
                            tx_time = tx.get("utime", 0)
                            if current_time - tx_time < 1800:  # 30 минут
                                
                                # Проверяем комментарий в транзакции
                                tx_comment = in_msg.get("message", "")
                                
                                logging.info(f"🔍 Транзакция: сумма {received_amount:.4f} TON, комментарий: '{tx_comment}', время: {tx_time}")
                                
                                # Если указан ожидаемый комментарий, проверяем его
                                if expected_comment and expected_comment in tx_comment:
                                    logging.info(f"✅ Найден платеж с комментарием: {expected_comment}, сумма: {received_amount:.4f} TON")
                                    return {
                                        "status": "approved",
                                        "amount": received_amount,
                                        "comment": tx_comment,
                                        "expected_comment": expected_comment,
                                        "transaction": tx
                                    }
                                # Дополнительная проверка: ищем платежи с похожими комментариями (начинающимися с T)
                                elif expected_comment and expected_comment.startswith("T") and tx_comment.startswith("T") and len(tx_comment) >= 4:
                                    # Проверяем, совпадают ли последние цифры
                                    if expected_comment[-3:] in tx_comment or tx_comment[-3:] in expected_comment:
                                        logging.info(f"✅ Найден платеж с похожим комментарием: {tx_comment} (ожидался: {expected_comment}), сумма: {received_amount:.4f} TON")
                                        return {
                                            "status": "approved",
                                            "amount": received_amount,
                                            "comment": tx_comment,
                                            "expected_comment": expected_comment,
                                            "transaction": tx
                                        }
                                elif not expected_comment and received_amount > 0:
                                    # Если комментарий не указан, считаем любой входящий платеж успешным
                                    logging.info(f"✅ Найден платеж без комментария, сумма: {received_amount:.4f} TON")
                                    return {
                                        "status": "approved",
                                        "amount": received_amount,
                                        "comment": tx_comment,
                                        "transaction": tx
                                    }
            
            logging.info(f"⏳ Платеж {payment_id} не найден среди последних транзакций")
            return {
                "status": "pending",
                "message": "Ожидается поступление TON с правильным комментарием"
            }
            
        except Exception as e:
            logging.error(f"Ошибка проверки TON транзакции: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_wallet_qr_code(self, amount_ton: float) -> str:
        """Генерирует QR код для оплаты"""
        # Формируем ссылку для оплаты в TON кошельке
        ton_link = f"ton://transfer/{self.wallet_address}?amount={int(amount_ton * 1000000000)}"
        return ton_link
    
    def get_wallet_info(self) -> Dict:
        """Получает информацию о кошельке"""
        try:
            return {
                "address": self.wallet_address,
                "commission_percent": self.commission_percent,
                "api_configured": bool(self.api_key and self.api_url)
            }
        except Exception as e:
            logging.error(f"Ошибка получения информации о кошельке: {e}")
            return None
    
    def format_payment_info(self, payment_data: Dict) -> str:
        """Форматирует информацию о платеже"""
        return f"""
📋 Платеж сформирован

💸 Сумма к отправке: {payment_data['amount_ton']:.4f} TON
⚠️ Комментарий: <code>{payment_data['comment']}</code>
💳 Адрес для оплаты: <code>{self.wallet_address}</code>

‼️ Обязательно указывайте комментарий при отправке монет, в противном случае - пополнение не будет засчитано
‼️ Окончательная сумма к получению будет рассчитана в момент получения монет

📱 Для оплаты:
1. Откройте TON кошелек
2. Отправьте {payment_data['amount_ton']:.4f} TON на указанный адрес
3. В комментарии укажите: <code>{payment_data['comment']}</code>
4. Нажмите "Проверить оплату" после перевода
        """.strip()
