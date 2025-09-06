import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, InputMediaPhoto
import json
import os
import time
from datetime import datetime
from config import BOT_TOKEN, EMOJIS, APAYS_CLIENT_ID, APAYS_SECRET_KEY, APAYS_BASE_URL, PAYMENT_MIN_AMOUNT, PAYMENT_MAX_AMOUNT, APAYS_ENABLED, TON_WALLET_ADDRESS, TON_COMMISSION_PERCENT, APAYS_COMMISSION_PERCENT
from FragmentApi.BuyStars import buy_stars
from FragmentApi.APaysPayment import APaysPayment
from FragmentApi.TonPayment import TonPayment
from Functions.LogInit import log_init
import logging

# Инициализация бота
bot = telebot.TeleBot(BOT_TOKEN)

# Инициализация APays клиента (только если включен)
apays = None
if APAYS_ENABLED and APAYS_CLIENT_ID:
    try:
        apays = APaysPayment(
            client_id=APAYS_CLIENT_ID,
            secret_key=APAYS_SECRET_KEY,
            base_url=APAYS_BASE_URL
        )
        logging.info("✅ APays клиент инициализирован")
    except Exception as e:
        logging.error(f"❌ Ошибка инициализации APays: {e}")
        apays = None
else:
    logging.info("⚠️ APays отключен. Для включения получите client_id и установите APAYS_ENABLED = True")

# Инициализация TON Payment
ton_payment = TonPayment()

# Импортируем константы поддержки
from config import SUPPORT_USERNAME, SUPPORT_CHAT_ID

# Функция для безопасного редактирования сообщений
def safe_edit_message(chat_id, message_id, text, reply_markup=None, photo_path=None):
    """
    Безопасно редактирует сообщение, определяя тип контента
    """
    try:
        if photo_path and os.path.exists(photo_path):
            # Если есть изображение, используем send_photo_with_text
            send_photo_with_text(chat_id, text, photo_path, reply_markup, message_id)
        else:
            # Если нет изображения, редактируем как текст
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                reply_markup=reply_markup,
                parse_mode='HTML'
            )
    except Exception as e:
        logging.error(f"Ошибка редактирования сообщения: {e}")
        # Fallback - отправляем новое сообщение
        try:
            if photo_path and os.path.exists(photo_path):
                with open(photo_path, 'rb') as photo:
                    bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
            else:
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        except Exception as fallback_error:
            logging.error(f"Ошибка fallback отправки сообщения: {fallback_error}")
            # Последняя попытка - простое сообщение без форматирования
            try:
                bot.send_message(
                    chat_id=chat_id,
                    text="Произошла ошибка. Попробуйте еще раз.",
                    reply_markup=create_main_menu()
                )
            except Exception as final_error:
                logging.error(f"Критическая ошибка отправки сообщения: {final_error}")

# Функция для отправки изображения с текстом
def send_photo_with_text(chat_id, text, photo_path, reply_markup=None, message_id=None):
    """
    Отправляет изображение с текстом
    """
    try:
        if os.path.exists(photo_path):
            if message_id:
                # Редактируем существующее сообщение
                with open(photo_path, 'rb') as photo:
                    try:
                        # Пытаемся редактировать медиа
                        bot.edit_message_media(
                            chat_id=chat_id,
                            message_id=message_id,
                            media=InputMediaPhoto(media=photo, caption=text, parse_mode='HTML'),
                            reply_markup=reply_markup
                        )
                    except Exception as media_error:
                        # Если не удалось редактировать медиа, пытаемся отредактировать только подпись
                        try:
                            bot.edit_message_caption(
                                chat_id=chat_id,
                                message_id=message_id,
                                caption=text,
                                reply_markup=reply_markup,
                                parse_mode='HTML'
                            )
                        except Exception as caption_error:
                            # Если и это не удалось, отправляем новое сообщение
                            logging.warning(f"Не удалось редактировать сообщение, отправляем новое: {media_error}, {caption_error}")
                            bot.send_photo(
                                chat_id=chat_id,
                                photo=photo,
                                caption=text,
                                reply_markup=reply_markup,
                                parse_mode='HTML'
                            )
            else:
                # Отправляем новое сообщение
                with open(photo_path, 'rb') as photo:
                    bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
        else:
            # Если изображение не найдено, отправляем только текст
            if message_id:
                try:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                except Exception as text_error:
                    # Если не удалось отредактировать текст, отправляем новое сообщение
                    logging.warning(f"Не удалось отредактировать текст, отправляем новое: {text_error}")
                    bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
            else:
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
    except Exception as e:
        logging.error(f"Ошибка отправки изображения: {e}")
        # Fallback - отправляем только текст
        try:
            if message_id:
                try:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=message_id,
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
                except:
                    bot.send_message(
                        chat_id=chat_id,
                        text=text,
                        reply_markup=reply_markup,
                        parse_mode='HTML'
                    )
            else:
                bot.send_message(
                    chat_id=chat_id,
                    text=text,
                    reply_markup=reply_markup,
                    parse_mode='HTML'
                )
        except Exception as fallback_error:
            logging.error(f"Критическая ошибка отправки сообщения: {fallback_error}")
            # Последняя попытка
            try:
                bot.send_message(
                    chat_id=chat_id,
                    text="Произошла ошибка. Попробуйте еще раз.",
                    reply_markup=create_main_menu()
                )
            except:
                pass  # Если даже это не работает, просто логируем

# Состояния пользователей для FSM
user_states = {}

# Функция для отправки сообщений в техподдержку
def send_to_support(message_text):
    # Список ID для отправки уведомлений
    support_ids = [SUPPORT_CHAT_ID, 339294188]
    
    # Отправляем на все ID
    for chat_id in support_ids:
        try:
            bot.send_message(chat_id=chat_id, text=message_text, parse_mode='HTML')
            logging.info(f"✅ Сообщение отправлено в техподдержку: {chat_id}")
        except Exception as e:
            logging.error(f"❌ Ошибка отправки в техподдержку {chat_id}: {e}")
    
    # Пытаемся отправить по username как резервный вариант
    try:
        bot.send_message(chat_id=SUPPORT_USERNAME, text=message_text, parse_mode='HTML')
        logging.info(f"✅ Сообщение отправлено в техподдержку: {SUPPORT_USERNAME}")
    except Exception as e:
        logging.error(f"❌ Ошибка отправки в техподдержку по username: {e}")



# Функция для проверки существования username
def check_username_exists(username):
    """
    Проверяет валидность формата юзернейма
    """
    try:
        # Убираем @ если есть
        clean_username = username.lstrip('@')
        
        # 1. Проверка длины
        if not clean_username or len(clean_username) < 1 or len(clean_username) > 32:
            return False, "Некорректный формат username"
        
        # 2. Проверка допустимых символов
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', clean_username):
            return False, "Username содержит недопустимые символы"
        
        # 3. Проверка, не является ли это ID (цифры)
        if clean_username.isdigit():
            return False, "Это похоже на ID, а не на юзернейм"
        
        # ✅ Формат корректен
        return True, None
        
    except Exception as e:
        logging.error(f"Ошибка проверки username '{username}': {e}")
        return False, "Ошибка проверки username"

# Константа цены за звезду
STAR_PRICE = 1.35  # ₽ за звезду

# Загружаем данные пользователей
def load_users_data():
    try:
        with open('users_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

# Сохраняем данные пользователей
def save_users_data(data):
    with open('users_data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Обновляем структуру пользователя, добавляя недостающие поля
def update_user_structure(user_data, user_id):
    if "stars_bought" not in user_data:
        user_data["stars_bought"] = 0
    if "subscriptions_bought" not in user_data:
        user_data["subscriptions_bought"] = 0
    if "total_spent" not in user_data:
        user_data["total_spent"] = 0.0
    if "referrals" not in user_data:
        user_data["referrals"] = []
    if "referral_earnings" not in user_data:
        user_data["referral_earnings"] = 0.0
    if "referral_withdrawn" not in user_data:
        user_data["referral_withdrawn"] = 0.0
    if "referral_code" not in user_data:
        user_data["referral_code"] = f"ref_{user_id}"
    if "purchases" not in user_data:
        user_data["purchases"] = []
    
    # Вычисляем total_spent из существующих покупок
    if user_data["purchases"]:
        total_spent = sum(purchase.get("cost", 0) for purchase in user_data["purchases"])
        user_data["total_spent"] = total_spent
        
        # Вычисляем stars_bought из существующих покупок
        stars_bought = sum(purchase.get("stars", 0) for purchase in user_data["purchases"])
        user_data["stars_bought"] = stars_bought
    
    return user_data

# Создаем главное меню
def create_main_menu():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(f"{EMOJIS['stars']} Звезды", callback_data="stars"),
        InlineKeyboardButton(f"{EMOJIS['premium']} Премиум", callback_data="premium")
    )
    keyboard.add(
        InlineKeyboardButton(f"{EMOJIS['topup']} Пополнить баланс", callback_data="topup"),
        InlineKeyboardButton(f"{EMOJIS['profile']} Профиль", callback_data="profile")
    )
    keyboard.add(
        InlineKeyboardButton(f"{EMOJIS['info']} Информация", callback_data="info")
    )
    return keyboard

# Создаем клавиатуру с кнопкой "Отмена"
def create_cancel_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel"))
    return keyboard

# Создаем клавиатуру с кнопками "Себе" и "Отмена"
def create_recipient_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("👤 Себе", callback_data="recipient_self"),
        InlineKeyboardButton("❌ Отменить", callback_data="cancel")
    )
    return keyboard

# Создаем клавиатуру "Назад"
def create_back_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(f"{EMOJIS['back']} Назад", callback_data="back_main"))
    return keyboard

# Создаем клавиатуру подтверждения покупки
def create_confirm_purchase_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_purchase"),
        InlineKeyboardButton("❌ Отменить", callback_data="cancel")
    )
    return keyboard

# Создаем клавиатуру подтверждения покупки себе
def create_confirm_self_purchase_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_self_purchase"),
        InlineKeyboardButton("❌ Отменить", callback_data="cancel")
    )
    return keyboard

# Создаем клавиатуру для профиля
def create_profile_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📋 История покупок", callback_data="purchase_history"),
        InlineKeyboardButton(f"{EMOJIS['back']} Назад", callback_data="back_main")
    )
    return keyboard

# Создаем клавиатуру для информации
def create_info_keyboard():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton(f"{EMOJIS['back']} Назад", callback_data="back_main")
    )
    return keyboard

# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message: Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or message.from_user.first_name
    
    # Загружаем данные пользователей
    users_data = load_users_data()
    
    # Создаем нового пользователя, если его нет
    if user_id not in users_data:
        users_data[user_id] = {
            "username": username,
            "balance": 0.0,  # Начальный баланс
            "stars_bought": 0,
            "subscriptions_bought": 0,
            "total_spent": 0.0,
            "referrals": [],
            "referral_earnings": 0.0,
            "referral_withdrawn": 0.0,
            "referral_code": f"ref_{user_id}",
            "purchases": []
        }
        save_users_data(users_data)
    else:
        # Обновляем существующего пользователя
        users_data[user_id] = update_user_structure(users_data[user_id], user_id)
        users_data[user_id]["username"] = username
        save_users_data(users_data)
    
    # Очищаем состояние пользователя
    user_states.pop(user_id, None)
    
    # Подсчитываем общее количество купленных звезд
    total_stars = sum(user.get('stars_bought', 0) for user in users_data.values())
    total_rub = total_stars * STAR_PRICE
    
    welcome_text = (
        f"👋 Добро пожаловать\n\n"
        f"✨ Здесь можно приобрести Telegram звезды & premium без верификации и дешевле чем в приложении\n\n"
        f"📈 Курс: 1 Stars = {STAR_PRICE} RUB\n\n"
        f"С помощью бота куплено:\n"
        f"{total_stars:,} ⭐️ (~ {total_rub:,.1f} RUB)"
    )
    
    # Отправляем изображение старт.jpeg с приветственным сообщением
    send_photo_with_text(
        chat_id=message.chat.id,
        text=welcome_text,
        photo_path="старт.jpeg",
        reply_markup=create_main_menu()
    )

# Обработчик callback запросов
@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call: CallbackQuery):
    user_id = str(call.from_user.id)
    users_data = load_users_data()
    
    # Сначала отвечаем на callback, чтобы избежать timeout
    try:
        bot.answer_callback_query(call.id)
    except Exception as e:
        logging.warning(f"⚠️ Не удалось ответить на callback: {e}")
    
    if call.data == "stars":
        # Показываем меню покупки звезд
        stars_text = (
            "⭐️ Покупка Telegram Stars\n\n"
            f"💰 Цена: {STAR_PRICE} ₽ за звезду\n"
            f"💳 Баланс: {users_data.get(user_id, {}).get('balance', 0):.2f} ₽\n\n"
            "Введите количество звезд (50-50000):"
        )
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=stars_text,
            reply_markup=create_cancel_keyboard()
        )
        user_states[user_id] = {"state": "waiting_stars_amount"}
        
    elif call.data == "premium":
        # Показываем меню премиум подписок
        premium_text = (
            "🌟 Премиум подписки\n\n"
            "🚀 Ускоренная доставка\n"
            "💎 Приоритетная поддержка\n"
            "🎁 Эксклюзивные предложения\n\n"
            "Скоро будет доступно!"
        )
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=premium_text,
            reply_markup=create_back_keyboard()
        )
        
    elif call.data == "topup":
        # Показываем меню выбора способа оплаты
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        
        topup_text = (
            "💳 Пополнение баланса\n\n"
            f"💰 Текущий баланс: {user_data.get('balance', 0):.2f} ₽\n"
            f"💸 Минимальная сумма: {PAYMENT_MIN_AMOUNT} ₽\n"
            f"💸 Максимальная сумма: {PAYMENT_MAX_AMOUNT} ₽\n\n"
            "🔽 Выберите способ оплаты:"
        )
        
        # Создаем клавиатуру с выбором способа оплаты
        keyboard = InlineKeyboardMarkup()
        if APAYS_ENABLED and apays:
            keyboard.add(
                InlineKeyboardButton(f"💳 APays (+{APAYS_COMMISSION_PERCENT}%)", callback_data="payment_method_apays")
            )
        keyboard.add(
            InlineKeyboardButton(f"⚡ Прямой перевод TON (Без комиссии)", callback_data="payment_method_ton")
        )
        keyboard.add(
            InlineKeyboardButton("❌ Отменить", callback_data="back_main")
        )
        
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=topup_text,
            reply_markup=keyboard
        )
        
    elif call.data == "payment_method_apays":
        # Выбран APays
        user_states[user_id] = {
            "state": "waiting_topup_amount",
            "payment_method": "apays"
        }
        
        topup_text = (
            "⚪️ Выбран метод: APays\n\n"
            "✏️ Введите, сколько вы хотите пополнить RUB:"
        )
        
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=topup_text,
            reply_markup=create_cancel_keyboard()
        )
        
    elif call.data == "payment_method_ton":
        # Выбран TON перевод
        user_states[user_id] = {
            "state": "waiting_topup_amount",
            "payment_method": "ton"
        }
        
        topup_text = (
            "⚪️ Выбран метод: Прямой перевод TON\n\n"
            "✏️ Введите, сколько вы хотите пополнить RUB:"
        )
        
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=topup_text,
            reply_markup=create_cancel_keyboard()
        )
        
    elif call.data == "profile":
        # Показываем профиль пользователя
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        
        profile_text = (
            f"👤 Профиль @{user_data.get('username', 'Unknown')}\n\n"
            f"💰 Баланс: {user_data.get('balance', 0):.2f} ₽\n"
            f"⭐️ Куплено звезд: {user_data.get('stars_bought', 0)}\n"
            f"💎 Премиум подписок: {user_data.get('subscriptions_bought', 0)}\n"
            f"💸 Всего потрачено: {user_data.get('total_spent', 0):.2f} ₽\n"
            f"👥 Рефералов: {len(user_data.get('referrals', []))}\n"
            f"🎁 Реферальные начисления: {user_data.get('referral_earnings', 0):.2f} ₽\n"
            f"📤 Выведено: {user_data.get('referral_withdrawn', 0):.2f} ₽\n"
            f"🔗 Реферальный код: {user_data.get('referral_code', 'ref_' + user_id)}"
        )
        
        # Отправляем изображение ава.jpeg с информацией профиля
        send_photo_with_text(
            chat_id=call.message.chat.id,
            text=profile_text,
            photo_path="ава.jpeg",
            reply_markup=create_profile_keyboard(),
            message_id=call.message.message_id
        )
        
    elif call.data == "info":
        # Показываем информацию о боте
        info_text = (
            "ℹ️ Информация о боте\n\n"
            "🤖 Название: StarShop\n"
            "💰 Цена: 1.35 ₽ за звезду\n"
            "📞 Поддержка: @StarShopsup"
        )
        
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=info_text,
            reply_markup=create_info_keyboard()
        )
        
    elif call.data == "purchase_history":
        # Показываем историю покупок
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        
        purchases = user_data.get('purchases', [])
        if not purchases:
            history_text = "📋 История покупок пуста"
        else:
            history_text = "📋 История покупок:\n\n"
            for purchase in purchases[-10:]:  # Показываем последние 10 покупок
                history_text += (
                    f"🆔 #{purchase['id']} | {purchase['date']}\n"
                    f"⭐️ {purchase['stars']} звезд | 💰 {purchase['cost']:.2f} ₽\n"
                    f"👤 {purchase['recipient']} | {purchase['status']}\n\n"
                )
        
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=history_text,
            reply_markup=create_profile_keyboard()
        )
        

        
    elif call.data == "cancel":
        # Отменяем текущее действие и возвращаемся в главное меню
        user_states.pop(user_id, None)
        main_menu_text = (
            "🏠 Главное меню\n\n"
            "Добро пожаловать в StarShop! 🌟\n\n"
            "Выберите действие:"
        )
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=main_menu_text,
            reply_markup=create_main_menu()
        )
        
    elif call.data == "back_main":
        # Возвращаемся в главное меню
        user_states.pop(user_id, None)
        main_menu_text = (
            "🏠 Главное меню\n\n"
            f"💰 Баланс: {users_data.get(user_id, {}).get('balance', 0):.2f} ₽\n"
            "Выберите действие:"
        )
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=main_menu_text,
            reply_markup=create_main_menu()
        )
        
    elif call.data == "recipient_self":
        # Покупаем звезды себе
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        
        stars_amount = user_states.get(user_id, {}).get('stars_amount', 0)
        
        if stars_amount == 0:
            bot.answer_callback_query(call.id, "❌ Ошибка: количество звезд не указано")
            return
        
        # Проверяем баланс
        cost = stars_amount * STAR_PRICE  # 1.35 ₽ за звезду
        if user_data.get('balance', 0) < cost:
            bot.answer_callback_query(call.id, f"❌ Недостаточно средств. Нужно: {cost:.2f} ₽")
            return
        
        # Автоматически подставляем СВОЙ юзернейм
        recipient = user_data['username']
        
        # Сохраняем в общий state confirm_purchase
        user_states[user_id] = {
            "state": "confirm_purchase",
            "stars_amount": stars_amount,
            "cost": cost,
            "recipient": recipient
        }
        
        # Логируем сохранение состояния для отладки
        logging.info(f"✅ Состояние сохранено для пользователя {user_id}: {user_states[user_id]}")
        
        # Показываем подтверждение покупки
        confirm_text = (
            f"📋 Подтверждение покупки:\n\n"
            f"👤 Получатель: @{recipient}\n"
            f"⭐ Количество: {stars_amount} звезд\n"
            f"💰 Стоимость: {cost:.2f} ₽\n\n"
            f"🔐 Отправить транзакцию?"
        )
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=confirm_text,
            reply_markup=create_confirm_purchase_keyboard()
        )
        
    elif call.data == "confirm_purchase":
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        purchase_data = user_states.get(user_id, {})

        if not purchase_data or purchase_data.get("state") != "confirm_purchase":
            bot.answer_callback_query(call.id, "❌ Сессия устарела")
            safe_edit_message(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ Сессия устарела. Начните сначала.",
                reply_markup=create_main_menu()
            )
            user_states.pop(user_id, None)
            return

        stars_amount = purchase_data["stars_amount"]
        cost = purchase_data["cost"]
        recipient = purchase_data["recipient"]

        # Проверяем существование username ещё раз
        username_exists, error_message = check_username_exists(recipient)
        if not username_exists:
            bot.answer_callback_query(call.id, f"❌ {error_message}")
            error_text = (
                f"❌ {error_message}\n\n"
                f"Проверьте правильность написания username и попробуйте снова."
            )
            safe_edit_message(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=error_text,
                reply_markup=create_back_keyboard()
            )
            user_states.pop(user_id, None)
            return

        # Проверка баланса (ещё раз)
        if user_data.get('balance', 0) < cost:
            bot.answer_callback_query(call.id, f"❌ Недостаточно средств")
            balance_error_text = f"❌ Недостаточно средств. Нужно: {cost:.2f} ₽"
            safe_edit_message(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=balance_error_text,
                reply_markup=create_back_keyboard()
            )
            user_states.pop(user_id, None)
            return

        # Загрузка мнемоники
        wallet_file = "created_wallets/wallets_data.txt"
        if not os.path.exists(wallet_file):
            safe_edit_message(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ Файл с данными кошелька не найден!",
                reply_markup=create_back_keyboard()
            )
            user_states.pop(user_id, None)
            return

        try:
            with open(wallet_file, "r", encoding="utf-8") as f:
                wallet_data = json.load(f)
                mnemonics = wallet_data['mnemonics']
                wallet_address = wallet_data['wallet_address']
                logging.info(f"✅ Кошелек загружен: {wallet_address}")
        except Exception as e:
            logging.error(f"Ошибка загрузки кошелька: {e}")
            wallet_error_text = f"❌ Ошибка загрузки кошелька: {e}"
            safe_edit_message(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=wallet_error_text,
                reply_markup=create_back_keyboard()
            )
            user_states.pop(user_id, None)
            return

        # Отправка транзакции
        sending_text = f"🚀 Отправляем {stars_amount} звёзд пользователю @{recipient}..."
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=sending_text,
            reply_markup=None
        )

        try:
            import asyncio
            result = asyncio.run(
                buy_stars(
                    recipient=recipient,
                    amount=stars_amount,
                    mnemonics=mnemonics,
                    version='v4r2',
                    testnet=False,
                    send_mode=1,
                    test_mode=False
                )
            )
            logging.info(f"📊 Результат покупки: {result}")

            # Проверяем результат более детально
            success = False
            if isinstance(result, bool):
                success = result
            elif isinstance(result, dict):
                success = result.get('success', False)
            else:
                success = bool(result)
            
            if success:
                # Успешно
                user_data['balance'] -= cost
                user_data['stars_bought'] += stars_amount
                user_data['total_spent'] += cost
                user_data['purchases'].append({
                    "id": len(user_data['purchases']) + 1,
                    "date": datetime.now().strftime("%d.%m.%Y %H:%M"),
                    "stars": stars_amount,
                    "cost": cost,
                    "recipient": f"@{recipient}",
                    "status": "completed"
                })
                users_data[user_id] = user_data
                save_users_data(users_data)

                # Отправляем изображение чек.jpeg с сообщением об успешной покупке
                success_text = (
                    f"✅ Успешно! {stars_amount} звёзд отправлены пользователю @{recipient}\n"
                    f"💸 Списано: {cost:.2f} ₽"
                )
                send_photo_with_text(
                    chat_id=call.message.chat.id,
                    text=success_text,
                    photo_path="чек.jpeg",
                    reply_markup=create_back_keyboard(),
                    message_id=call.message.message_id
                )
            else:
                # Получаем детальную информацию об ошибке
                error_details = "Неизвестная ошибка"
                if isinstance(result, dict):
                    error_details = result.get('error', result.get('message', 'Неизвестная ошибка'))
                elif isinstance(result, str):
                    error_details = result
                
                # Проверяем, является ли ошибка связанной с невалидным username
                if isinstance(result, dict) and "username" in error_details.lower():
                    # Показываем сообщение о невалидном username
                    safe_edit_message(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="❌ Некорректный username получателя. Проверьте правильность написания.",
                        reply_markup=create_back_keyboard()
                    )
                else:
                    # Отправляем детальное сообщение админу только для других ошибок
                    support_message = (
                        f"⚠️ Ошибка покупки звезд!\n"
                        f"Пользователь ID: {user_id}\n"
                        f"Получатель: @{recipient}\n"
                        f"Количество звезд: {stars_amount}\n"
                        f"Стоимость: {cost:.2f} ₽\n"
                        f"Детали ошибки: {error_details}"
                    )
                    send_to_support(support_message)
                    
                    # Показываем простое сообщение пользователю
                    safe_edit_message(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="Проблема на нашей стороне. Обратитесь в техническую поддержку @StarShopsup",
                        reply_markup=create_back_keyboard()
                    )
        except Exception as e:
            logging.error(f"Ошибка при покупке: {e}")
            
            # Отправляем детальное сообщение админу
            support_message = (
                f"⚠️ Ошибка покупки звезд!\n"
                f"Пользователь ID: {user_id}\n"
                f"Получатель: @{recipient}\n"
                f"Количество звезд: {stars_amount}\n"
                f"Стоимость: {cost:.2f} ₽\n"
                f"Детали ошибки: {str(e)}"
            )
            send_to_support(support_message)
            
            # Показываем простое сообщение пользователю
            safe_edit_message(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Проблема на нашей стороне. Обратитесь в техническую поддержку @StarShopsup",
                reply_markup=create_back_keyboard()
            )

        user_states.pop(user_id, None)

    elif call.data == "check_payment":
        # Проверяем статус платежа
        payment_data = user_states.get(user_id, {})
        if payment_data.get("state") == "payment_created":
            order_id = payment_data.get("order_id")
            amount = payment_data.get("amount")
            
            try:
                # Проверяем статус заказа
                status_result = apays.get_order_status(order_id)
                
                if status_result.get('status') and status_result.get('order_status'):
                    order_status = status_result['order_status']
                    
                    if order_status == 'approve':
                        # Платеж успешен - пополняем баланс
                        user_data = users_data.get(user_id, {})
                        user_data = update_user_structure(user_data, user_id)
                        
                        user_data['balance'] += amount
                        users_data[user_id] = user_data
                        save_users_data(users_data)
                        
                        # Очищаем состояние
                        user_states.pop(user_id, None)
                        
                        success_text = (
                            f"✅ Платеж успешно обработан!\n\n"
                            f"💰 Пополнено: {amount:.2f} ₽\n"
                            f"💳 Новый баланс: {user_data['balance']:.2f} ₽\n"
                            f"🆔 ID заказа: {order_id}"
                        )
                        
                        safe_edit_message(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=success_text,
                            reply_markup=create_back_keyboard()
                        )
                        
                    elif order_status == 'pending':
                        # Платеж еще обрабатывается
                        pending_text = (
                            f"⏳ Платеж обрабатывается...\n\n"
                            f"💰 Сумма: {amount:.2f} ₽\n"
                            f"🆔 ID заказа: {order_id}\n\n"
                            f"Попробуйте проверить еще раз через несколько минут."
                        )
                        
                        safe_edit_message(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=pending_text,
                            reply_markup=create_cancel_keyboard()
                        )
                        
                    elif order_status == 'decline':
                        # Платеж отклонен
                        decline_text = (
                            f"❌ Платеж отклонен\n\n"
                            f"💰 Сумма: {amount:.2f} ₽\n"
                            f"🆔 ID заказа: {order_id}\n\n"
                            f"Обратитесь в поддержку для уточнения деталей."
                        )
                        
                        safe_edit_message(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=decline_text,
                            reply_markup=create_back_keyboard()
                        )
                        
                        # Очищаем состояние
                        user_states.pop(user_id, None)
                        
                    elif order_status == 'expired':
                        # Срок платежа истек
                        expired_text = (
                            f"⏰ Срок платежа истек\n\n"
                            f"💰 Сумма: {amount:.2f} ₽\n"
                            f"🆔 ID заказа: {order_id}\n\n"
                            f"Создайте новый заказ для пополнения."
                        )
                        
                        safe_edit_message(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=expired_text,
                            reply_markup=create_back_keyboard()
                        )
                        
                        # Очищаем состояние
                        user_states.pop(user_id, None)
                        
                else:
                    # Ошибка получения статуса
                    error_text = "❌ Ошибка проверки статуса платежа. Попробуйте еще раз."
                    safe_edit_message(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=error_text,
                        reply_markup=create_cancel_keyboard()
                    )
                    
            except Exception as e:
                logging.error(f"Ошибка проверки статуса платежа: {e}")
                error_text = "❌ Ошибка проверки статуса платежа. Попробуйте еще раз."
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=error_text,
                    reply_markup=create_cancel_keyboard()
                )
        else:
            bot.answer_callback_query(call.id, "❌ Нет активного платежа для проверки")

    elif call.data == "check_ton_payment":
        # Проверяем статус TON платежа
        payment_data = user_states.get(user_id, {})
        if payment_data.get("state") == "payment_created" and payment_data.get("payment_method") == "ton":
            order_id = payment_data.get("order_id")
            amount = payment_data.get("amount")
            
            try:
                # Получаем ожидаемый комментарий
                payment_info = payment_data.get("payment_data", {})
                expected_comment = payment_info.get("comment")
                
                # Проверяем статус TON транзакции
                status_result = ton_payment.check_ton_transaction(order_id, expected_comment)
                
                if status_result.get("status") == "approved":
                    # Платеж успешен - пополняем баланс
                    user_data = users_data.get(user_id, {})
                    user_data = update_user_structure(user_data, user_id)
                    
                    user_data['balance'] += amount
                    users_data[user_id] = user_data
                    save_users_data(users_data)
                    
                    # Очищаем состояние
                    user_states.pop(user_id, None)
                    
                    success_text = (
                        f"✅ TON платеж успешно обработан!\n\n"
                        f"💰 Пополнено: {amount:.2f} ₽\n"
                        f"💳 Новый баланс: {user_data['balance']:.2f} ₽\n"
                        f"🆔 ID заказа: {order_id}"
                    )
                    
                    safe_edit_message(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=success_text,
                        reply_markup=create_back_keyboard()
                    )
                    
                elif status_result.get("status") == "pending":
                    # Платеж еще обрабатывается
                    pending_text = (
                        f"⏳ TON платеж обрабатывается...\n\n"
                        f"💰 Сумма: {amount:.2f} ₽\n"
                        f"🆔 ID заказа: {order_id}\n\n"
                        f"Попробуйте проверить еще раз через несколько минут."
                    )
                    
                    safe_edit_message(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=pending_text,
                        reply_markup=create_cancel_keyboard()
                    )
                    
                else:
                    # Платеж не найден или отклонен
                    not_found_text = (
                        f"❌ TON платеж не найден\n\n"
                        f"💰 Сумма: {amount:.2f} ₽\n"
                        f"🆔 ID заказа: {order_id}\n\n"
                        f"Убедитесь, что вы отправили правильную сумму на указанный адрес."
                    )
                    
                    safe_edit_message(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=not_found_text,
                        reply_markup=create_cancel_keyboard()
                    )
                    
            except Exception as e:
                logging.error(f"Ошибка проверки TON платежа: {e}")
                error_text = "❌ Ошибка проверки TON платежа. Попробуйте еще раз."
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=error_text,
                    reply_markup=create_cancel_keyboard()
                )
        else:
            bot.answer_callback_query(call.id, "❌ Нет активного TON платежа для проверки")

    # Callback уже отвечен в начале функции

# Обработчик текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_text(message: Message):
    user_id = str(message.from_user.id)
    user_state = user_states.get(user_id, {})
    users_data = load_users_data()
    user_data = users_data.get(user_id, {})
    user_data = update_user_structure(user_data, user_id)

    if user_state.get("state") == "waiting_topup_amount":
        payment_method = user_state.get("payment_method", "apays")
        
        try:
            amount = float(message.text)
            if PAYMENT_MIN_AMOUNT <= amount <= PAYMENT_MAX_AMOUNT:
                
                if payment_method == "apays":
                    # Обработка APays
                    if not APAYS_ENABLED or not apays:
                        bot.reply_to(
                            message,
                            "⚠️ APays временно недоступен. Выберите другой способ оплаты.",
                            reply_markup=create_cancel_keyboard()
                        )
                        return
                    
                    # Добавляем комиссию APays
                    commission = amount * (APAYS_COMMISSION_PERCENT / 100)
                    total_amount = amount + commission
                    
                    order_id = f"apays_{user_id}_{int(time.time())}"
                    amount_kopecks = apays.rubles_to_kopecks(total_amount)
                    
                    try:
                        order = apays.create_order(
                            order_id=order_id,
                            amount=amount_kopecks
                        )
                        
                        if order.get('status') and order.get('url'):
                            user_states[user_id] = {
                                "state": "payment_created",
                                "order_id": order_id,
                                "amount": amount,
                                "total_amount": total_amount,
                                "commission": commission,
                                "payment_method": "apays",
                                "payment_url": order['url']
                            }
                            
                            keyboard = InlineKeyboardMarkup()
                            keyboard.add(InlineKeyboardButton("💳 Перейти к оплате", url=order['url']))
                            keyboard.add(InlineKeyboardButton("🔄 Проверить оплату", callback_data="check_payment"))
                            keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel"))
                            
                            payment_text = (
                                f"📋 Платеж сформирован\n\n"
                                f"🆔 ID: {order_id}\n"
                                f"📥 Метод: ⚪️ APays\n"
                                f"💰 К получению: {amount:.2f} RUB\n"
                                f"💸 Комиссия: {commission:.2f} RUB\n"
                                f"💳 К оплате: {total_amount:.2f} RUB"
                            )
                            
                            bot.reply_to(
                                message,
                                payment_text,
                                reply_markup=keyboard,
                                parse_mode='HTML'
                            )
                        else:
                            bot.reply_to(
                                message,
                                "❌ Ошибка создания заказа APays. Попробуйте еще раз.",
                                reply_markup=create_cancel_keyboard()
                            )
                            
                    except Exception as e:
                        logging.error(f"Ошибка создания заказа APays: {e}")
                        bot.reply_to(
                            message,
                            "❌ Ошибка создания заказа APays. Попробуйте еще раз.",
                            reply_markup=create_cancel_keyboard()
                        )
                
                elif payment_method == "ton":
                    # Обработка TON перевода
                    payment_data = ton_payment.create_payment_request(user_id, amount)
                    
                    if "error" not in payment_data:
                        user_states[user_id] = {
                            "state": "payment_created",
                            "order_id": payment_data["payment_id"],
                            "amount": amount,
                            "payment_method": "ton",
                            "payment_data": payment_data
                        }
                        
                        keyboard = InlineKeyboardMarkup()
                        keyboard.add(InlineKeyboardButton("🔄 Проверить оплату", callback_data="check_ton_payment"))
                        keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel"))
                        
                        payment_text = ton_payment.format_payment_info(payment_data)
                        
                        bot.reply_to(
                            message,
                            payment_text,
                            reply_markup=keyboard,
                            parse_mode='Markdown'
                        )
                    else:
                        bot.reply_to(
                            message,
                            f"❌ Ошибка создания TON платежа: {payment_data['error']}",
                            reply_markup=create_cancel_keyboard()
                        )
            else:
                bot.reply_to(
                    message,
                    f"❌ Сумма должна быть от {PAYMENT_MIN_AMOUNT} до {PAYMENT_MAX_AMOUNT} ₽!",
                    reply_markup=create_cancel_keyboard()
                )
        except ValueError:
            bot.reply_to(
                message,
                "❌ Введите корректную сумму!",
                reply_markup=create_cancel_keyboard()
            )

    elif user_state.get("state") == "waiting_stars_amount":
        try:
            stars_amount = int(message.text)
            if 50 <= stars_amount <= 50000:
                cost = stars_amount * STAR_PRICE
                if user_data.get('balance', 0) < cost:
                    bot.reply_to(
                        message,
                        f"❌ Недостаточно средств. Нужно: {cost:.2f} ₽",
                        reply_markup=create_cancel_keyboard()
                    )
                    return
                user_states[user_id] = {
                    "state": "waiting_recipient_username",
                    "stars_amount": stars_amount,
                    "cost": cost
                }
                bot.reply_to(
                    message,
                    f"⭐️ Количество: {stars_amount} звезд\n"
                    f"💰 Стоимость: {cost:.2f} ₽\n"
                    "👤 Введите юзернейм получателя (например: @username или username):",
                    reply_markup=create_recipient_keyboard()
                )
            else:
                bot.reply_to(
                    message,
                    "❌ Количество звёзд должно быть от 50 до 50000!",
                    reply_markup=create_cancel_keyboard()
                )
        except ValueError:
            bot.reply_to(
                message,
                "❌ Введите корректное число!",
                reply_markup=create_cancel_keyboard()
            )

    elif user_state.get("state") == "waiting_recipient_username":
        recipient = message.text.strip().lstrip('@')
        
        # Проверяем существование username
        username_exists, error_message = check_username_exists(recipient)
        if not username_exists:
            bot.reply_to(
                message,
                f"❌ {error_message}\n\n"
                f"Проверьте правильность написания username и попробуйте снова.",
                reply_markup=create_cancel_keyboard()
            )
            return

        stars_amount = user_state["stars_amount"]
        cost = user_state["cost"]

        # Сохраняем получателя и переходим к подтверждению
        user_states[user_id] = {
            "state": "confirm_purchase",
            "stars_amount": stars_amount,
            "cost": cost,
            "recipient": recipient
        }

        keyboard = create_confirm_purchase_keyboard()
        confirm_text = (
            f"📋 Подтверждение покупки:\n"
            f"⭐ Количество: {stars_amount} звёзд\n"
            f"💰 Стоимость: {cost:.2f} ₽\n"
            f"👤 Получатель: @{recipient}\n"
            f"🔐 Отправить транзакцию?"
        )
        bot.reply_to(
            message,
            confirm_text,
            reply_markup=keyboard
        )

    else:
        try:
            bot.reply_to(
                message,
                "❓ Неизвестная команда. Используйте /start для начала работы.",
                reply_markup=create_main_menu(),
                parse_mode='HTML'
            )
        except Exception as e:
            logging.error(f"❌ Ошибка отправки ответа на неизвестную команду: {e}")
            # Fallback - простое сообщение
            try:
                bot.send_message(
                    message.chat.id,
                    "❓ Неизвестная команда. Используйте /start для начала работы.",
                    reply_markup=create_main_menu()
                )
            except Exception as fallback_error:
                logging.error(f"❌ Критическая ошибка отправки fallback сообщения: {fallback_error}")

# Инициализация логирования
log_init()

# Запуск бота
if __name__ == "__main__":
    print("🤖 Telegram бот запущен...")
    try:
        bot_info = bot.get_me()
        print(f"👤 Username: @{bot_info.username}")
    except Exception as e:
        print(f"❌ Ошибка получения информации о боте: {e}")
        print("Проверьте правильность BOT_TOKEN в config.py")
        exit(1)
    
    # Запуск с обработкой ошибок соединения
    while True:
        try:
            print("🔄 Запуск polling...")
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            logging.error(f"❌ Ошибка polling: {e}")
            print(f"❌ Ошибка соединения: {e}")
            print("🔄 Перезапуск через 5 секунд...")
            import time
            time.sleep(5)
            