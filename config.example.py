# Пример конфигурации Telegram бота для покупки звезд на Fragment
# Скопируйте этот файл в config.py и заполните своими данными

# Токен вашего бота (получите у @BotFather)
BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"

# Настройки Fragment API
FRAGMENT_API_URL = "https://fragment.com/api"
FRAGMENT_STARS_URL = "https://fragment.com/stars/buy"
FRAGMENT_BOT_USERNAME = "fragment"

# Стоимость звезд в рублях
STAR_PRICE_RUB = 10

# Настройки TON сети
TON_NETWORK = "mainnet"  # Основная сеть TON
TON_VERSION = "v4r2"

# TON Center API (получите бесплатный ключ на https://toncenter.com)
TON_CENTER_API_KEY = "YOUR_TON_CENTER_API_KEY_HERE"
TON_CENTER_API_URL = "https://toncenter.com/api/v2"  # Mainnet URL (без /jsonRPC)

# Настройки кошелька TON
WALLET_MNEMONICS = [
    "word1", "word2", "word3", "word4", "word5", "word6", "word7", "word8", 
    "word9", "word10", "word11", "word12", "word13", "word14", "word15", "word16", 
    "word17", "word18", "word19", "word20", "word21", "word22", "word23", "word24"
]
WALLET_ADDRESS = "YOUR_WALLET_ADDRESS_HERE"
WALLET_PUBLIC_KEY = "YOUR_WALLET_PUBLIC_KEY_HERE"
WALLET_PRIVATE_KEY = "YOUR_WALLET_PRIVATE_KEY_HERE"

# Настройки кошелька
WALLET_FEATURES = ["SendTransaction", {"name": "SendTransaction", "maxMessages": 4}]
WALLET_APP_NAME = "telegram-wallet"
WALLET_APP_VERSION = "1"
WALLET_MAX_PROTOCOL_VERSION = 2

# Настройки платежей
PAYMENT_METHODS = {
    "card": {
        "enabled": True,
        "name": "💳 Банковская карта",
        "fee_percent": 2.5,
        "min_amount": 100,
        "max_amount": 50000
    },
    "crypto": {
        "enabled": True,
        "name": "₿ Криптовалюта",
        "fee_percent": 1.0,
        "min_amount": 500,
        "max_amount": 100000,
        "supported_coins": ["TON", "BTC", "ETH", "USDT"]
    }
}

# Настройки премиум подписок
PREMIUM_PLANS = {
    "3_months": {
        "name": "🔥 Премиум 3 месяца",
        "duration_days": 90,
        "price_rub": 2500,
        "discount_percent": 10,
        "features": [
            "⭐ Скидка 10% на звезды",
            "🎯 Приоритетная поддержка",
            "📊 Расширенная статистика",
            "🔒 Безопасные транзакции"
        ]
    },
    "6_months": {
        "name": "🔥 Премиум 6 месяцев",
        "duration_days": 180,
        "price_rub": 4500,
        "discount_percent": 15,
        "features": [
            "⭐ Скидка 15% на звезды",
            "🎯 Приоритетная поддержка",
            "📊 Расширенная статистика",
            "🔒 Безопасные транзакции",
            "🎁 Бонусные звезды"
        ]
    },
    "12_months": {
        "name": "🔥 Премиум 12 месяцев",
        "duration_days": 365,
        "price_rub": 8000,
        "discount_percent": 20,
        "features": [
            "⭐ Скидка 20% на звезды",
            "🎯 Приоритетная поддержка",
            "📊 Расширенная статистика",
            "🔒 Безопасные транзакции",
            "🎁 Бонусные звезды",
            "👑 VIP статус"
        ]
    }
}

# Настройки логирования
LOG_LEVEL = "INFO"
LOG_FILE = "bot.log"

# Настройки безопасности
ENCRYPT_MNEMONICS = False  # В продакшене должно быть True
SESSION_TIMEOUT = 3600  # 1 час в секундах

# Настройки интерфейса
MAX_STARS_PER_TRANSACTION = 100
MIN_STARS_PER_TRANSACTION = 1
MAX_BALANCE = 100000  # Максимальный баланс в рублях

# Настройки автоматизации
AUTO_BUY_STARS = True  # Автоматическая покупка звезд при достаточном балансе
MIN_BALANCE_FOR_AUTO_BUY = 50  # Минимальный баланс для автопокупки
AUTO_BUY_INTERVAL = 300  # Интервал проверки автопокупки в секундах

# Эмодзи для интерфейса
EMOJIS = {
    "welcome": "👋",
    "balance": "💰",
    "registration": "📅",
    "time": "🕐",
    "stars": "⭐",
    "premium": "🔥",
    "topup": "💌",
    "profile": "👤",
    "info": "ℹ️",
    "success": "✅",
    "error": "❌",
    "warning": "⚠️",
    "loading": "⏳",
    "processing": "🔄",
    "buy": "🛒",
    "back": "🔙",
    "wallet": "🔑",
    "edit": "✏️",
    "confirm": "✅",
    "cancel": "❌",
    "card": "💳",
    "crypto": "₿",
    "payment": "💸",
    "subscription": "📱",
    "vip": "👑",
    "referral": "👥",
    "earnings": "💵",
    "withdrawn": "📥",
    "history": "📋",
    "support": "💬"
}

# Настройки техподдержки
SUPPORT_USERNAME = "@YOUR_SUPPORT_USERNAME"  # Username техподдержки
SUPPORT_CHAT_ID = 1234567890  # Числовой chat_id техподдержки

# Настройки APays
APAYS_CLIENT_ID = 1234  # Ваш client_id
APAYS_SECRET_KEY = "YOUR_APAYS_SECRET_KEY_HERE"  # Ваш секретный ключ
APAYS_BASE_URL = "https://apays.io"
APAYS_WEBHOOK_URL = "https://your-domain.com/webhook/apays"  # URL для webhook уведомлений
APAYS_ENABLED = True  # APays включен

# Настройки платежей
PAYMENT_MIN_AMOUNT = 100  # Минимальная сумма пополнения в рублях
PAYMENT_MAX_AMOUNT = 50000  # Максимальная сумма пополнения в рублях

# Настройки TON кошелька для прямых переводов
TON_WALLET_ADDRESS = "YOUR_TON_WALLET_ADDRESS_HERE"  # Кошелек для пополнений и покупки звезд
TON_COMMISSION_PERCENT = 0  # Комиссия за прямой перевод (0%)
APAYS_COMMISSION_PERCENT = 7  # Комиссия APays (7%)
