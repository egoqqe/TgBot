#!/usr/bin/env python3
"""
Webhook сервер для обработки уведомлений от APays
Запускается отдельно от основного бота
"""

import json
import logging
from flask import Flask, request, jsonify
from FragmentApi.APaysPayment import APaysPayment
from config import APAYS_CLIENT_ID, APAYS_SECRET_KEY, APAYS_BASE_URL

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Инициализация Flask приложения
app = Flask(__name__)

# Инициализация APays клиента
apays = APaysPayment(
    client_id=APAYS_CLIENT_ID,
    secret_key=APAYS_SECRET_KEY,
    base_url=APAYS_BASE_URL
)

# Словарь для хранения данных о платежах (в продакшене используйте базу данных)
pending_payments = {}


@app.route('/webhook/apays', methods=['POST'])
def apays_webhook():
    """
    Обработчик webhook от APays
    """
    try:
        # Получаем данные webhook
        webhook_data = request.get_json()
        
        if not webhook_data:
            logger.error("❌ Пустые данные webhook")
            return jsonify({'error': 'Empty webhook data'}), 400
        
        logger.info(f"📨 Получен webhook от APays: {webhook_data}")
        
        # Обрабатываем webhook
        result = apays.process_webhook(webhook_data)
        
        if result['success']:
            order_id = result['order_id']
            status = result['status']
            
            # Здесь можно добавить логику обработки платежа
            # Например, пополнение баланса пользователя в базе данных
            
            if status == 'approved':
                logger.info(f"✅ Платеж одобрен: {order_id}")
                # TODO: Пополнить баланс пользователя
                # TODO: Отправить уведомление пользователю
                
            elif status == 'declined':
                logger.info(f"❌ Платеж отклонен: {order_id}")
                # TODO: Уведомить пользователя об отклонении
                
            return jsonify({'status': 'ok'}), 200
        else:
            logger.error(f"❌ Ошибка обработки webhook: {result['message']}")
            return jsonify({'error': result['message']}), 400
            
    except Exception as e:
        logger.error(f"❌ Критическая ошибка webhook: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """
    Проверка здоровья сервера
    """
    return jsonify({'status': 'ok', 'service': 'apays-webhook'})


@app.route('/', methods=['GET'])
def index():
    """
    Главная страница
    """
    return jsonify({
        'service': 'APays Webhook Server',
        'version': '1.0.0',
        'endpoints': {
            'webhook': '/webhook/apays',
            'health': '/health'
        }
    })


if __name__ == '__main__':
    logger.info("🚀 Запуск webhook сервера для APays...")
    logger.info(f"📡 Webhook URL: http://localhost:5000/webhook/apays")
    
    # Запуск сервера
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False,
        threaded=True
    )


