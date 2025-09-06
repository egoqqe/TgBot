# wallet/Transactions.py
import logging
import requests

# --- Импорт TonTools для версии 2.1.2 ---
TONTOOLS_AVAILABLE = False
Wallet = None
TonCenterClient = None

try:
    from TonTools import Wallet, TonCenterClient
    TONTOOLS_AVAILABLE = True
    logging.info("✅ TonTools (версия 2.1.2) доступен")
except ImportError as e:
    logging.error(f"❌ Не удалось импортировать TonTools: {e}")
    logging.warning("⚠️ TonTools НЕДОСТУПЕН.")

import asyncio
from tonsdk.utils import from_nano, to_nano
from tonsdk.contract.wallet import Wallets, WalletVersionEnum


class Transactions:
    def __init__(self, config):
        self.config = config
        self.testnet = config.get('testnet', False)
        # Предполагаем, что TON_CENTER_API_URL и TON_CENTER_API_KEY доступны глобально или через config
        # Для простоты, можно передавать их в config или импортировать из config.py
        # Здесь будем использовать прямые импорты, как в вашем коде
        try:
            from config import TON_CENTER_API_URL, TON_CENTER_API_KEY
            self.ton_center_api_url = TON_CENTER_API_URL.rstrip('/') # Убираем слэш в конце, если есть
            self.ton_center_api_key = TON_CENTER_API_KEY
        except ImportError:
            logging.error("❌ Не удалось импортировать TON_CENTER_API_URL или TON_CENTER_API_KEY из config.py")
            self.ton_center_api_url = "https://toncenter.com/api/v2"
            self.ton_center_api_key = None

    async def get_balance(self, mnemonics, version='v4r2'):
        """
        Асинхронно получает баланс TON кошелька.
        """
        if not TONTOOLS_AVAILABLE:
            logging.error("❌ TonTools не доступен для получения баланса.")
            return {"success": False, "message": "TonTools не установлен", "error": "TonTools library not available", "balance_ton": 0}

        try:
            # 1. Создаем кошелек из мнемоники для получения адреса
            wallet_version_enum = getattr(WalletVersionEnum, version, WalletVersionEnum.v4r2)
            _, _, _, wallet_obj = Wallets.from_mnemonics(mnemonics=mnemonics, version=wallet_version_enum, workchain=0)
            wallet_address = wallet_obj.address.to_string(True, True, True)
            logging.info(f"👛 Адрес кошелька для проверки баланса: {wallet_address}")

            # 2. Запрашиваем баланс через TON Center API
            balance_url = f"{self.ton_center_api_url}/getAddressBalance"
            # ВАЖНО: params должны быть словарем, и api_key добавляется только если он есть и не "YOUR_API_KEY_HERE"
            balance_params = {'address': wallet_address}
            if self.ton_center_api_key and self.ton_center_api_key != "YOUR_API_KEY_HERE":
                 balance_params['api_key'] = self.ton_center_api_key
            elif self.ton_center_api_key == "YOUR_API_KEY_HERE":
                 logging.warning("⚠️ TON Center API ключ не настроен в config.py!")

            logging.info(f"📡 Запрос баланса: GET {balance_url} с параметрами {balance_params}")
            balance_response = requests.get(balance_url, params=balance_params)

            if balance_response.status_code == 200:
                balance_data = balance_response.json()
                logging.info(f"📥 Ответ TON Center API (баланс): {balance_data}")
                if balance_data.get("ok"):
                    balance_nano = int(balance_data["result"])
                    balance_ton = from_nano(balance_nano, "ton")
                    logging.info(f"💰 Баланс кошелька: {balance_ton} TON ({balance_nano} нанотон)")
                    return {"success": True, "message": "Баланс получен", "balance_ton": balance_ton, "balance_nano": balance_nano}
                else:
                    error_msg = f"❌ Ошибка получения баланса от TON Center API: {balance_data}"
                    logging.error(error_msg)
                    return {"success": False, "message": "Ошибка API", "error": error_msg, "balance_ton": 0}
            else:
                error_msg = f"❌ HTTP ошибка при получении баланса: {balance_response.status_code}, {balance_response.text}"
                logging.error(error_msg)
                return {"success": False, "message": "HTTP ошибка", "error": error_msg, "balance_ton": 0}

        except Exception as e:
            logging.error(f"❌ Критическая ошибка в get_balance: {e}", exc_info=True)
            return {"success": False, "message": "Критическая ошибка", "error": str(e), "balance_ton": 0}


    async def _send_ton_async(self, mnemonics, destination_address, amount, payload="", nano_amount=True, version='v4r2', send_mode=0):
        """
        Асинхронно отправляет TON используя TonTools 2.1.2.
        """
        if not TONTOOLS_AVAILABLE:
            logging.error("❌ TonTools не доступен для отправки транзакции.")
            return {"success": False, "message": "TonTools не установлен", "error": "TonTools library not available"}

        try:
            # 1. Обработка суммы
            try:
                if nano_amount:
                    amount_nano = int(amount) # amount уже в нанотонах (строка или int)
                    amount_ton = from_nano(amount_nano, 'ton')
                else:
                    amount_ton = float(amount) # amount в TON (строка или float)
                    amount_nano = to_nano(amount_ton, 'ton')
            except (ValueError, TypeError) as e:
                logging.error(f"❌ Неверный формат суммы: {e}")
                return {"success": False, "message": "Неверный формат суммы", "error": str(e)}

            logging.info(f"💰 Сумма к отправке: {amount_ton} TON ({amount_nano} нанотон)")

            # 2. Подготовка payload (comment)
            clean_payload = payload.replace("\n", " ") if payload else ""
            logging.info(f"📄 Payload (comment): {clean_payload}")

            # 3. Создаем провайдер и кошелек
            provider = TonCenterClient(testnet=self.testnet)
            wallet = Wallet(mnemonics=mnemonics, version=version, provider=provider)

            # 4. Отправляем транзакцию
            logging.info(f"🚀 Отправка {amount_ton} TON на {destination_address}...")
            
            # В TonTools 2.1.2 используем новый API
            result = await wallet.transfer_ton(
                destination_address=destination_address,
                amount=amount_ton,  # Сумма в TON
                message=clean_payload,
                send_mode=send_mode
            )
            
            logging.info("✅ Транзакция отправлена успешно!")
            
            # Попытка извлечь хэш
            tx_hash = "unknown"
            if isinstance(result, dict):
                tx_hash = result.get('hash') or result.get('@extra') or str(result)
            elif hasattr(result, 'hash'):
                tx_hash = result.hash
            
            return {"success": True, "message": "Транзакция отправлена", "tx_hash": tx_hash}
                
        except Exception as e:
            logging.error(f"❌ Ошибка в _send_ton_async: {e}", exc_info=True)
            return {"success": False, "message": "Ошибка отправки", "error": str(e)}

    async def send_ton(self, mnemonics, destination_address, amount, payload="", nano_amount=True, version='v4r2', send_mode=0):
        """
        Асинхронный метод для отправки TON.
        Сначала проверяет баланс, затем отправляет.
        """
        logging.info("💸 Отправляем TON транзакцию (TonTools 2.1.2)...")

        # 1. Проверяем баланс перед отправкой
        # Предполагаем, что amount уже в нанотонах, если nano_amount=True
        try:
            if nano_amount:
                required_amount_nano = int(amount)
            else:
                required_amount_nano = to_nano(float(amount), 'ton')
        except (ValueError, TypeError) as e:
            logging.error(f"❌ Неверный формат суммы для проверки баланса: {e}")
            return {"success": False, "message": "Неверный формат суммы", "error": str(e)}

        required_amount_ton = from_nano(required_amount_nano, 'ton')
        # Добавим немного на комиссию (примерно 0.05 TON)
        estimated_fee_nano = to_nano(0.07, 'ton')
        total_required_nano = required_amount_nano + estimated_fee_nano
        total_required_ton = from_nano(total_required_nano, 'ton')

        logging.info(f"🔍 Проверка баланса перед отправкой: требуется {total_required_ton} TON (сумма + комиссия)")

        balance_result = await self.get_balance(mnemonics, version)
        if not balance_result.get('success'):
             logging.error(f"❌ Не удалось получить баланс для проверки перед отправкой: {balance_result}")
             return balance_result # Возвращаем ошибку получения баланса

        current_balance_ton = balance_result.get('balance_ton', 0)
        current_balance_nano = balance_result.get('balance_nano', 0)

        logging.info(f"💰 Текущий баланс: {current_balance_ton} TON")
        logging.info(f"💰 Требуется: {total_required_ton} TON")

        if current_balance_nano < total_required_nano:
            error_msg = (f"Недостаточно средств на TON кошельке. "
                         f"Требуется: {total_required_ton} TON, "
                         f"Доступно: {current_balance_ton} TON")
            logging.error(f"❌ {error_msg}")
            return {"success": False, "message": "Недостаточно средств", "error": error_msg}

        logging.info("✅ Баланс достаточен для отправки транзакции.")

        # 2. Если баланс достаточен, отправляем транзакцию
        result = await self._send_ton_async(mnemonics, destination_address, amount, payload, nano_amount, version, send_mode)
        return result
