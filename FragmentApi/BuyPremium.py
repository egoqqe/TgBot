from FragmentApi.PaymentGetPremium import PaymentGetPremium
from wallet.Transactions import Transactions
import logging
from config import TON_CENTER_API_KEY, TON_CENTER_API_URL, TON_NETWORK


async def buy_premium(recipient, duration_months, mnemonics, version="v4r2", testnet=False, send_mode=1, test_mode=False):
    """
    АСИНХРОННАЯ функция покупки Telegram Premium.
    
    Args:
        recipient: никнейм получателя (без @)
        duration_months: длительность подписки в месяцах (1, 3, 6, 12)
        mnemonics: мнемоника кошелька
        version: версия кошелька
        testnet: использовать testnet
        send_mode: режим отправки
        test_mode: тестовый режим
    """
    try:
        logging.info(f"🚀 Начинаем покупку {duration_months} месяцев Premium для @{recipient}")
        
        payment = PaymentGetPremium()
        
        # Создаем config для Transactions
        config = {
            'testnet': testnet,
            'TON_NETWORK': 'mainnet' if not testnet else 'testnet'
        }
        
        # Создаем объект Transactions с config
        transactions = Transactions(config)
        
        logging.info("📡 Получаем данные для платежа Premium...")
        try:
            payment_address, payment_amount, payload = payment.get_data_for_payment(
                recipient=recipient, 
                duration_months=duration_months,
                mnemonics=mnemonics
            )
        except Exception as payment_error:
            logging.error(f"❌ Ошибка получения данных платежа: {payment_error}")
            return {"success": False, "error": str(payment_error)}
        
        if not payment_address or not payment_amount:
            logging.error("❌ Не удалось получить данные для платежа Premium от Fragment API")
            return False

        logging.info(f"✅ Данные получены: адрес={payment_address}, сумма={payment_amount}")

        # Отправляем TON транзакцию АСИНХРОННО
        logging.info("💸 Отправляем TON транзакцию для Premium...")
        ton_result = await transactions.send_ton(
            mnemonics=mnemonics,
            destination_address=payment_address,
            amount=payment_amount,
            payload=payload,
            nano_amount=True,  # PaymentGet возвращает amount в нанотонах
            version=version,
            send_mode=send_mode
        )
        
        logging.info(f"📊 Результат отправки Premium: {ton_result}")
        
        # Возвращаем результат
        if not ton_result.get("success"):
            logging.error(f"❌ Ошибка отправки TON для Premium: {ton_result}")
            # Возвращаем детали ошибки вместо False
            # Это позволит боту показать конкретную причину ошибки
            return ton_result
        else:
            return True
            
    except Exception as e:
        logging.error(f"❌ Ошибка при покупке Premium: {e}")
        return {"success": False, "error": str(e)}
