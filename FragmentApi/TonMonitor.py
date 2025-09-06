"""
Модуль для мониторинга TON транзакций
"""
import requests
import time
import logging
from typing import Dict, List, Optional
from config import TON_WALLET_ADDRESS

class TonMonitor:
    """Класс для мониторинга TON транзакций"""
    
    def __init__(self):
        self.wallet_address = TON_WALLET_ADDRESS
        self.api_url = "https://toncenter.com/api/v2"
        logging.info("✅ TON Monitor инициализирован")
    
    def get_wallet_transactions(self, limit: int = 10) -> List[Dict]:
        """Получает последние транзакции кошелька"""
        try:
            # Используем TON Center API для получения транзакций
            url = f"{self.api_url}/getTransactions"
            params = {
                "address": self.wallet_address,
                "limit": limit,
                "archival": True
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("ok"):
                    return data.get("result", [])
                else:
                    logging.error(f"TON Center API error: {data.get('error', 'Unknown error')}")
                    return []
            else:
                logging.error(f"TON Center API HTTP error: {response.status_code}")
                return []
                
        except Exception as e:
            logging.error(f"Ошибка получения TON транзакций: {e}")
            return []
    
    def check_payment_by_amount(self, expected_amount_ton: float, tolerance: float = 0.001) -> Optional[Dict]:
        """Проверяет поступление платежа по сумме"""
        try:
            transactions = self.get_wallet_transactions(20)
            
            for tx in transactions:
                if tx.get("in_msg"):
                    in_msg = tx["in_msg"]
                    if in_msg.get("value"):
                        # Конвертируем nanoTON в TON
                        received_amount = int(in_msg["value"]) / 1000000000
                        
                        # Проверяем соответствие суммы с допуском
                        if abs(received_amount - expected_amount_ton) <= tolerance:
                            return {
                                "status": "approved",
                                "transaction": tx,
                                "amount": received_amount,
                                "from_address": in_msg.get("source", ""),
                                "tx_hash": tx.get("transaction_id", {}).get("hash", "")
                            }
            
            return {"status": "not_found"}
            
        except Exception as e:
            logging.error(f"Ошибка проверки TON платежа: {e}")
            return {"status": "error", "error": str(e)}
    
    def format_transaction_info(self, tx_data: Dict) -> str:
        """Форматирует информацию о транзакции"""
        if tx_data.get("status") == "approved":
            tx = tx_data.get("transaction", {})
            in_msg = tx.get("in_msg", {})
            
            return f"""
✅ TON платеж подтвержден!

💰 Сумма: {tx_data['amount']:.4f} TON
📤 От: {tx_data['from_address'][:10]}...{tx_data['from_address'][-10:]}
🔗 Хеш: {tx_data['tx_hash'][:20]}...
⏰ Время: {time.strftime('%H:%M:%S', time.localtime())}
            """.strip()
        
        return "❌ Платеж не найден"
