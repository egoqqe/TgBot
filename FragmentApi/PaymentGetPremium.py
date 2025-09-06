import requests
from re import search
import logging
from wallet.WalletUtils import WalletUtils
from urllib.parse import urlencode
import json
import base64


class PaymentGetPremium:
    def __init__(self):
        self.WalletUtils = WalletUtils()
        with open('cookies.json', 'r') as file:
            loaded_cookies = json.load(file)

        self.cookies = loaded_cookies
        self.headers = {
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "https://fragment.com/stars/buy",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36 OPR/117.0.0.0 (Edition Yx GX)"
        }

    def _hash_get(self):
        response = requests.get("https://fragment.com/stars/buy", cookies=self.cookies)
        if response.status_code == 200:
            return search(r'api\?hash=([a-zA-Z0-9]+)', response.text).group(1)

    def _update_url(self):
        return f"https://fragment.com/api?hash={self._hash_get()}"

    def _payload_get(self, req_id, mnemonics):
        payload = {
            "account": json.dumps({
                "chain": "-239",
                "publicKey": self.WalletUtils.wallet_from_mnemonics(mnemonics)[0]["public_key"]
            }),
            "device": json.dumps({
                "platform": "web",
                "appName": "telegram-wallet",
                "appVersion": "1",
                "maxProtocolVersion": 2,
                "features": ["SendTransaction", {"name": "SendTransaction", "maxMessages": 4}]
            }),
            "transaction": 1,
            "id": req_id,
            "show_sender": 0,
            "method": "getBuyStarsLink"
        }
        return urlencode(payload)

    @staticmethod
    def _message_decode(encoded_payload):
        padding_needed = len(encoded_payload) % 4
        if padding_needed != 0:
            encoded_payload += '=' * (4 - padding_needed)
        decoded_payload = base64.b64decode(encoded_payload)
        text_part = decoded_payload.split(b"\x00")[-1].decode("utf-8")

        return text_part

    def get_data_for_payment(self, recipient, duration_months, mnemonics):
        """
        Получает данные для покупки Telegram Premium
        Использует тот же API, что и для звезд, но с параметрами Premium
        
        Args:
            recipient: никнейм получателя (без @)
            duration_months: длительность подписки в месяцах (1, 3, 6, 12)
            mnemonics: мнемоника кошелька
        """
        logging.warning(f"Sending {duration_months} months premium to @{recipient}...")

        url = self._update_url()

        # Поиск получателя - используем метод для звезд
        recipient_id_dirt = requests.post(url, headers=self.headers, cookies=self.cookies,
                                          data=f"query={recipient}&quantity=&method=searchStarsRecipient")
        
        # Добавляем отладочную информацию для поиска получателя
        logging.info(f"📡 Ответ поиска получателя: {recipient_id_dirt.text}")
        
        recipient_response = recipient_id_dirt.json()
        logging.info(f"📊 JSON ответ поиска: {recipient_response}")
        
        recipient_id = recipient_response.get("found", {}).get("recipient", "")

        if not recipient_id:
            logging.error(f"❌ Получатель @{recipient} не найден. Ответ API: {recipient_response}")
            raise Exception(f"Получатель @{recipient} не найден")

        # Инициализация запроса - используем метод для звезд, но с параметрами Premium
        # Возможно, нужно передавать duration_months как quantity
        req_id_dirt = requests.post(url, headers=self.headers, cookies=self.cookies,
                                    data=f"recipient={recipient_id}&quantity={duration_months}&method=initBuyStarsRequest")
        
        # Добавляем отладочную информацию для инициализации
        logging.info(f"📡 Ответ инициализации: {req_id_dirt.text}")
        
        init_response = req_id_dirt.json()
        logging.info(f"📊 JSON ответ инициализации: {init_response}")
        
        req_id = init_response.get("req_id", "")

        if not req_id:
            logging.error(f"❌ Не удалось получить req_id для покупки Premium. Ответ: {init_response}")
            raise Exception("Не удалось инициализировать запрос на покупку Premium")

        encoded_payload = self._payload_get(req_id, mnemonics)

        buy_payload_dirt = requests.post(url, headers=self.headers, cookies=self.cookies, data=encoded_payload)
        
        # Добавляем отладочную информацию
        logging.info(f"📡 Ответ Fragment API для Premium: {buy_payload_dirt.text}")
        
        response_json = buy_payload_dirt.json()
        logging.info(f"📊 JSON ответ для Premium: {response_json}")
        
        # Проверяем структуру ответа
        if "transaction" in response_json and "messages" in response_json["transaction"]:
            buy_payload = response_json["transaction"]["messages"][0]
        elif "messages" in response_json:
            buy_payload = response_json["messages"][0]
        else:
            # Если структура другая, ищем нужные поля
            logging.error(f"❌ Неожиданная структура ответа для Premium: {response_json}")
            raise Exception(f"Неожиданная структура ответа Fragment API для Premium: {response_json}")

        address, amount, encoded_message = buy_payload["address"], buy_payload["amount"], buy_payload["payload"]
        payload = self._message_decode(encoded_message)
        logging.info("Premium payment data received!")
        logging.warning("Waiting to send transaction...")
        return address, amount, payload
