from FragmentApi.PaymentGet import PaymentGet
from wallet.Transactions import Transactions
import logging
from config import TON_CENTER_API_KEY, TON_CENTER_API_URL, TON_NETWORK


async def buy_stars(recipient, amount, mnemonics, version="v4r2", testnet=False, send_mode=1, test_mode=False):
    """
    АСИНХРОННАЯ функция покупки звезд.
    """
    try:
        logging.info(f"🚀 Начинаем покупку {amount} звезд для @{recipient}")
        
        payment = PaymentGet()
        
        # Создаем config для Transactions
        config = {
            'testnet': testnet,
            'TON_NETWORK': 'mainnet' if not testnet else 'testnet'
        }
        
        # Создаем объект Transactions с config
        transactions = Transactions(config)
        
        logging.info("📡 Получаем данные для платежа...")
        payment_address, payment_amount, payload = payment.get_data_for_payment(recipient=recipient, quantity=amount,
                                                                                mnemonics=mnemonics)
        
        if not payment_address or not payment_amount:
            logging.error("❌ Не удалось получить данные для платежа от Fragment API")
            return False

        logging.info(f"✅ Данные получены: адрес={payment_address}, сумма={payment_amount}")

        # Отправляем TON транзакцию АСИНХРОННО
        logging.info("💸 Отправляем TON транзакцию...")
        ton_result = await transactions.send_ton(
            mnemonics=mnemonics,
            destination_address=payment_address,
            amount=payment_amount,
            payload=payload,
            nano_amount=True,  # PaymentGet возвращает amount в нанотонах
            version=version,
            send_mode=send_mode
        )
        
        logging.info(f"📊 Результат отправки: {ton_result}")
        
        # Возвращаем результат
        if not ton_result.get("success"):
            logging.error(f"❌ Ошибка отправки TON: {ton_result}")
            # Возвращаем детали ошибки вместо False
            # Это позволит боту показать конкретную причину ошибки
            return ton_result
        else:
            return True
            
    except Exception as e:
        logging.error(f"❌ Ошибка в buy_stars: {e}", exc_info=True)
        return False
