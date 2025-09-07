import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, InputMediaPhoto
import json
import os
import time
from datetime import datetime
from config import BOT_TOKEN, EMOJIS, APAYS_CLIENT_ID, APAYS_SECRET_KEY, APAYS_BASE_URL, PAYMENT_MIN_AMOUNT, PAYMENT_MAX_AMOUNT, APAYS_ENABLED, TON_WALLET_ADDRESS, TON_COMMISSION_PERCENT, TON_ENABLED, APAYS_COMMISSION_PERCENT
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



# Функция для проверки существования username через Fragment API
def check_username_exists(username):
    """
    Проверяет существование и доступность username через Fragment GraphQL API
    """
    try:
        import requests
        
        # Убираем @ если есть
        clean_username = username.lstrip('@')
        
        # 1. Базовая проверка формата
        if not clean_username or len(clean_username) < 1 or len(clean_username) > 32:
            return False, "Некорректный формат username"
        
        # 2. Проверка допустимых символов
        import re
        if not re.match(r'^[a-zA-Z0-9_]+$', clean_username):
            return False, "Username содержит недопустимые символы"
        
        # 3. Проверка, не является ли это ID (цифры)
        if clean_username.isdigit():
            return False, "Это похоже на ID, а не на юзернейм"
        
        # 4. Проверка существования через Fragment API
        logging.info(f"🔍 Проверяем username: {clean_username}")
        
        # TODO: Добавить реальную проверку через Fragment API когда он станет доступен
        # Пример кода для будущей реализации:
        # query = "query ($name: String!) { domain(name: $name) { name state owner { wallet } } }"
        # response = requests.post("https://fragment.com/graphql", json={"query": query, "variables": {"name": clean_username}})
        # if domain["state"] == "OPEN": return True, None  # Доступен для покупки
        # else: return False, f"Username @{clean_username} уже занят"
        
        # Пока используем базовую проверку формата
        logging.info(f"✅ Username {clean_username} прошел базовую проверку")
        return True, None
        
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Ошибка запроса к Fragment API: {e}")
        return True, None  # Если API недоступен, пропускаем проверку
    except Exception as e:
        logging.error(f"❌ Ошибка проверки username '{username}': {e}")
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
    if "purchases" not in user_data:
        user_data["purchases"] = []
    
    # Реферальная система
    if "referrals" not in user_data:
        user_data["referrals"] = []
    if "referral_earnings" not in user_data:
        user_data["referral_earnings"] = 0.0
    if "referral_withdrawn" not in user_data:
        user_data["referral_withdrawn"] = 0.0
    if "referral_code" not in user_data:
        user_data["referral_code"] = f"ref_{user_id}"
    if "referred_by" not in user_data:
        user_data["referred_by"] = None
    if "referral_discount" not in user_data:
        user_data["referral_discount"] = 0.0  # Скидка в рублях за звезду
    
    # Вычисляем total_spent из существующих покупок
    if user_data["purchases"]:
        total_spent = sum(purchase.get("cost", 0) for purchase in user_data["purchases"])
        user_data["total_spent"] = total_spent
        
        # Вычисляем stars_bought из существующих покупок
        stars_bought = sum(purchase.get("stars", 0) for purchase in user_data["purchases"])
        user_data["stars_bought"] = stars_bought
    
    return user_data

# Функции для работы с реферальной системой
def get_referral_discount(user_data):
    """
    Вычисляет скидку на основе количества приглашенных друзей, пополнивших баланс на 500+ рублей
    Скидка только при наличии ровно 3 квалифицированных рефералов
    """
    referrals = user_data.get("referrals", [])
    qualified_referrals = 0
    
    for referral in referrals:
        if referral.get("total_spent", 0) >= 500.0:
            qualified_referrals += 1
    
    # Скидка только при наличии ровно 3 квалифицированных рефералов
    if qualified_referrals >= 3:
        return 0.05  # Скидка 0.05 рубля за звезду (цена становится 1.30 ₽)
    else:
        return 0.0  # Без скидки

def update_referral_discount(user_data):
    """
    Обновляет скидку пользователя на основе его рефералов
    """
    user_data["referral_discount"] = get_referral_discount(user_data)
    return user_data

def add_referral(referrer_id, referred_id, users_data):
    """
    Добавляет реферала к пользователю
    """
    if referrer_id not in users_data:
        return False
    
    referrer_data = users_data[referrer_id]
    referred_data = users_data.get(referred_id, {})
    
    # Проверяем, что пользователь еще не является рефералом
    existing_referrals = [ref["user_id"] for ref in referrer_data.get("referrals", [])]
    if referred_id in existing_referrals:
        return False
    
    # Добавляем реферала
    referral_info = {
        "user_id": referred_id,
        "username": referred_data.get("username", "Unknown"),
        "registration_date": datetime.now().strftime("%d.%m.%Y %H:%M"),
        "total_spent": 0.0,
        "stars_bought": 0
    }
    
    referrer_data["referrals"].append(referral_info)
    
    # Обновляем скидку реферера
    referrer_data = update_referral_discount(referrer_data)
    users_data[referrer_id] = referrer_data
    
    # Устанавливаем связь для реферала
    referred_data["referred_by"] = referrer_id
    users_data[referred_id] = referred_data
    
    return True

def update_referral_stats(referred_id, users_data):
    """
    Обновляет статистику реферала при покупке
    """
    referred_data = users_data.get(referred_id, {})
    referrer_id = referred_data.get("referred_by")
    
    if not referrer_id or referrer_id not in users_data:
        return
    
    referrer_data = users_data[referrer_id]
    referrals = referrer_data.get("referrals", [])
    
    # Находим реферала в списке
    for referral in referrals:
        if referral["user_id"] == referred_id:
            referral["total_spent"] = referred_data.get("total_spent", 0)
            referral["stars_bought"] = referred_data.get("stars_bought", 0)
            break
    
    # Обновляем скидку реферера
    referrer_data = update_referral_discount(referrer_data)
    users_data[referrer_id] = referrer_data

def get_effective_star_price(user_data):
    """
    Возвращает эффективную цену за звезду с учетом скидки
    """
    base_price = STAR_PRICE
    discount = user_data.get("referral_discount", 0.0)
    return max(base_price - discount, 0.1)  # Минимальная цена 0.1 рубля

# Создаем главное меню
def create_main_menu(user_balance=None):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(f"{EMOJIS['stars']} Звезды", callback_data="stars")
    )
    keyboard.add(
        InlineKeyboardButton(f"{EMOJIS['topup']} Пополнить баланс", callback_data="topup"),
        InlineKeyboardButton(f"{EMOJIS['profile']} Профиль", callback_data="profile")
    )
    keyboard.add(
        InlineKeyboardButton("🎁 Реферальная программа", callback_data="referral")
    )
    keyboard.add(
        InlineKeyboardButton(f"{EMOJIS['info']} Информация", callback_data="info")
    )
    return keyboard

# Создаем текст главного меню с балансом
def create_main_menu_text(user_balance=0):
    return (
        f"🏠 Главное меню\n\n"
        f"💰 Баланс: {user_balance:.2f} ₽\n\n"
        f"Выберите действие:"
    )

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

# Создаем клавиатуру для пополнения баланса
def create_topup_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💳 APays (+7%)", callback_data="topup_apays"),
        InlineKeyboardButton("⚡ TON", callback_data="topup_ton")
    )
    keyboard.add(
        InlineKeyboardButton(f"{EMOJIS['back']} Назад", callback_data="back_main")
    )
    return keyboard

# Создаем клавиатуру для изменения суммы пополнения
def create_amount_change_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("💰 Другая сумма", callback_data="change_amount"),
        InlineKeyboardButton(f"{EMOJIS['back']} Назад", callback_data="back_main")
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

# Создаем клавиатуру для реферальной программы
def create_referral_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📋 Мои рефералы", callback_data="my_referrals"),
        InlineKeyboardButton("🔗 Моя ссылка", callback_data="my_referral_link")
    )
    keyboard.add(
        InlineKeyboardButton("📊 Статистика", callback_data="referral_stats"),
        InlineKeyboardButton("💰 Заработок", callback_data="referral_earnings")
    )
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
    
    # Проверяем реферальную ссылку
    referrer_id = None
    if len(message.text.split()) > 1:
        referral_code = message.text.split()[1]
        if referral_code.startswith('ref_'):
            referrer_id = referral_code.replace('ref_', '')
    
    # Создаем нового пользователя, если его нет
    if user_id not in users_data:
        users_data[user_id] = {
            "username": username,
            "balance": 0.0,  # Начальный баланс
            "stars_bought": 0,
            "subscriptions_bought": 0,
            "total_spent": 0.0,
            "purchases": []
        }
        
        # Если есть реферальная ссылка, добавляем реферала
        if referrer_id and referrer_id != user_id:
            add_referral(referrer_id, user_id, users_data)
            logging.info(f"✅ Пользователь {user_id} зарегистрирован по реферальной ссылке от {referrer_id}")
        
        save_users_data(users_data)
    else:
        # Обновляем существующего пользователя
        users_data[user_id] = update_user_structure(users_data[user_id], user_id)
        users_data[user_id]["username"] = username
        save_users_data(users_data)
    
    # Очищаем состояние пользователя
    user_states.pop(user_id, None)
    
    # Получаем данные пользователя
    user_data = users_data.get(user_id, {})
    user_data = update_user_structure(user_data, user_id)
    user_balance = user_data.get('balance', 0)
    
    # Подсчитываем общее количество купленных звезд
    total_stars = 13430 + sum(user.get('stars_bought', 0) for user in users_data.values()) #для хайпа немного приврём
    total_rub = total_stars * STAR_PRICE
    
    # Получаем эффективную цену с учетом скидки
    effective_price = get_effective_star_price(user_data)
    discount = user_data.get("referral_discount", 0.0)
    qualified_referrals = sum(1 for ref in user_data.get("referrals", []) if ref.get("total_spent", 0) >= 500.0)
    
    welcome_text = (
        f"👋 Добро пожаловать в сервис\n\n"
        f"💰 Текущий баланс: {user_balance:.2f} ₽\n\n"
        f"✨ Приобретайте Telegram Stars без верификации по выгодным ценам\n\n"
        f"📈 Текущий курс: 1 Stars = {effective_price:.2f} RUB"
    )
    
    if discount > 0:
        welcome_text += f"\n🎉 Специальная цена активирована!"
    elif qualified_referrals > 0:
        welcome_text += f"\n⏳ Прогресс: {qualified_referrals}/3 рефералов (требуется для специальной цены)"
    
    welcome_text += (
        f"\n\nС помощью бота куплено:\n"
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
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        effective_price = get_effective_star_price(user_data)
        discount = user_data.get("referral_discount", 0.0)
        qualified_referrals = sum(1 for ref in user_data.get("referrals", []) if ref.get("total_spent", 0) >= 500.0)
        
        stars_text = (
            "⭐️ Приобретение Telegram Stars\n\n"
            f"💰 Текущая цена: {effective_price:.2f} ₽ за звезду"
        )
        
        if discount > 0:
            stars_text += f"\n🎉 Специальная цена активирована!"
        elif qualified_referrals > 0:
            stars_text += f"\n⏳ Прогресс: {qualified_referrals}/3 рефералов (требуется для специальной цены)"
        
        stars_text += (
            f"\n💳 Баланс: {user_data.get('balance', 0):.2f} ₽\n\n"
            "Введите количество звезд (50-50000):"
        )
        
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=stars_text,
            reply_markup=create_cancel_keyboard()
        )
        user_states[user_id] = {"state": "waiting_stars_amount"}
        
        
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
        user_state = user_states.get(user_id, {})
        custom_amount = user_state.get("custom_amount")
        
        if custom_amount:
            # Если есть пользовательская сумма, сразу переходим к пополнению
            amount = custom_amount
            
            # Напрямую вызываем логику пополнения APays
            if not APAYS_ENABLED or not apays:
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ APays временно недоступен",
                    reply_markup=create_back_keyboard()
                )
                return
            
            # Создаем платеж
            payment_data = apays.create_payment(amount)
            if payment_data and "payment_url" in payment_data:
                # Сохраняем данные платежа
                user_states[user_id] = {
                    "state": "waiting_payment_confirmation",
                    "payment_method": "apays",
                    "payment_id": payment_data["payment_id"],
                    "amount": amount
                }
                
                payment_text = (
                    f"💳 APays платеж создан\n\n"
                    f"💰 Сумма: {amount:.2f} ₽\n"
                    f"🆔 ID платежа: {payment_data['payment_id']}\n\n"
                    f"🔗 Ссылка для оплаты:\n{payment_data['payment_url']}\n\n"
                    f"⏳ Ожидаем подтверждения платежа..."
                )
                
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=payment_text,
                    reply_markup=create_cancel_keyboard()
                )
            else:
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ Ошибка создания платежа APays",
                    reply_markup=create_back_keyboard()
                )
        else:
            # Обычный процесс ввода суммы
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
        user_state = user_states.get(user_id, {})
        custom_amount = user_state.get("custom_amount")
        
        if custom_amount:
            # Если есть пользовательская сумма, сразу переходим к пополнению
            amount = custom_amount
            
            # Напрямую вызываем логику пополнения TON
            if not TON_ENABLED or not ton_payment:
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ TON платежи временно недоступны",
                    reply_markup=create_back_keyboard()
                )
                return
            
            # Генерируем уникальный комментарий для платежа
            comment = f"topup_{user_id}_{int(time.time())}"
            
            # Получаем информацию о кошельке
            wallet_info = ton_payment.get_wallet_info()
            if wallet_info:
                # Сохраняем данные платежа
                user_states[user_id] = {
                    "state": "waiting_payment_confirmation",
                    "payment_method": "ton",
                    "amount": amount,
                    "comment": comment
                }
                
                payment_text = (
                    f"⚡ TON платеж\n\n"
                    f"💰 Сумма: {amount:.2f} ₽\n"
                    f"💬 Комментарий: <code>{comment}</code>\n\n"
                    f"🏦 Адрес кошелька:\n<code>{wallet_info['address']}</code>\n\n"
                    f"⚠️ ВАЖНО: Обязательно укажите комментарий при переводе!\n"
                    f"⏳ Ожидаем подтверждения платежа..."
                )
                
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=payment_text,
                    parse_mode='HTML',
                    reply_markup=create_cancel_keyboard()
                )
            else:
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ Ошибка получения информации о кошельке",
                    reply_markup=create_back_keyboard()
                )
        else:
            # Обычный процесс ввода суммы
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
        
        referrals = user_data.get("referrals", [])
        qualified_referrals = sum(1 for ref in referrals if ref.get("total_spent", 0) >= 500.0)
        discount = user_data.get("referral_discount", 0.0)
        
        if qualified_referrals >= 3:
            referral_status = "1.30 ₽ за звезду (активирована)"
        else:
            referral_status = f"{STAR_PRICE:.2f} ₽ за звезду ({qualified_referrals}/3 рефералов)"
        
        profile_text = (
            f"👤 Профиль пользователя @{user_data.get('username', 'Unknown')}\n\n"
            f"💰 Текущий баланс: {user_data.get('balance', 0):.2f} ₽\n"
            f"⭐️ Приобретено звезд: {user_data.get('stars_bought', 0)}\n"
            f"💸 Общие расходы: {user_data.get('total_spent', 0):.2f} ₽\n\n"
            f"🎁 Реферальная программа:\n"
            f"👥 Приглашенных пользователей: {len(referrals)}\n"
            f"✅ Квалифицированных рефералов: {qualified_referrals}\n"
            f"🎯 Цена за звезду: {referral_status}"
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
        
        # Получаем баланс пользователя
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        user_balance = user_data.get('balance', 0)
        
        main_menu_text = create_main_menu_text(user_balance)
        
        # Отправляем фото с главным меню
        send_photo_with_text(
            chat_id=call.message.chat.id,
            text=main_menu_text,
            photo_path="старт.jpeg",
            reply_markup=create_main_menu()
        )
        
    elif call.data == "back_main":
        # Возвращаемся в главное меню
        user_states.pop(user_id, None)
        
        # Получаем баланс пользователя
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        user_balance = user_data.get('balance', 0)
        
        main_menu_text = create_main_menu_text(user_balance)
        
        # Отправляем фото с главным меню
        send_photo_with_text(
            chat_id=call.message.chat.id,
            text=main_menu_text,
            photo_path="старт.jpeg",
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

        # Загрузка мнемоники из config.py
        try:
            from config import WALLET_MNEMONICS, WALLET_ADDRESS
            mnemonics = WALLET_MNEMONICS
            wallet_address = WALLET_ADDRESS
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
                
                # Обновляем статистику рефералов
                update_referral_stats(user_id, users_data)
                
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
                        
                        # Обновляем статистику рефералов
                        update_referral_stats(user_id, users_data)
                        
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
                        
                        # Создаем клавиатуру с кнопкой "Проверить еще раз"
                        keyboard = InlineKeyboardMarkup()
                        keyboard.add(InlineKeyboardButton("🔄 Проверить еще раз", callback_data="check_payment"))
                        keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel"))
                        
                        safe_edit_message(
                            chat_id=call.message.chat.id,
                            message_id=call.message.message_id,
                            text=pending_text,
                            reply_markup=keyboard
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
                    
                    # Создаем клавиатуру с кнопкой "Проверить еще раз"
                    keyboard = InlineKeyboardMarkup()
                    keyboard.add(InlineKeyboardButton("🔄 Проверить еще раз", callback_data="check_payment"))
                    keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel"))
                    
                    safe_edit_message(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=error_text,
                        reply_markup=keyboard
                    )
                    
            except Exception as e:
                logging.error(f"Ошибка проверки статуса платежа: {e}")
                error_text = "❌ Ошибка проверки статуса платежа. Попробуйте еще раз."
                
                # Создаем клавиатуру с кнопкой "Проверить еще раз"
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton("🔄 Проверить еще раз", callback_data="check_payment"))
                keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel"))
                
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=error_text,
                    reply_markup=keyboard
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
                    
                    # Обновляем статистику рефералов
                    update_referral_stats(user_id, users_data)
                    
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
                    # Платеж еще обрабатывается - показываем детали оплаты
                    ton_amount = payment_info.get("amount_ton", 0)
                    wallet_address = payment_info.get("wallet_address", "")
                    comment = payment_info.get("comment", "")
                    
                    pending_text = (
                        f"⏳ TON платеж обрабатывается...\n\n"
                        f"💰 Сумма: {amount:.2f} ₽\n"
                        f"🆔 ID заказа: {order_id}\n\n"
                        f"💸 Сумма к отправке: {ton_amount:.4f} TON\n"
                        f"💳 Адрес для оплаты: <code>{wallet_address}</code>\n"
                        f"⚠️ Комментарий: <code>{comment}</code>\n\n"
                        f"‼️ Обязательно указывайте комментарий при отправке монет!\n\n"
                        f"Попробуйте проверить еще раз через несколько минут."
                    )
                    
                    # Создаем клавиатуру с кнопкой "Проверить еще раз"
                    keyboard = InlineKeyboardMarkup()
                    keyboard.add(InlineKeyboardButton("🔄 Проверить еще раз", callback_data="check_ton_payment"))
                    keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel"))
                    
                    safe_edit_message(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=pending_text,
                        reply_markup=keyboard
                    )
                    
                else:
                    # Платеж не найден или отклонен - показываем детали оплаты
                    ton_amount = payment_info.get("amount_ton", 0)
                    wallet_address = payment_info.get("wallet_address", "")
                    comment = payment_info.get("comment", "")
                    
                    not_found_text = (
                        f"❌ TON платеж не найден\n\n"
                        f"💰 Сумма: {amount:.2f} ₽\n"
                        f"🆔 ID заказа: {order_id}\n\n"
                        f"💸 Сумма к отправке: {ton_amount:.4f} TON\n"
                        f"💳 Адрес для оплаты: <code>{wallet_address}</code>\n"
                        f"⚠️ Комментарий: <code>{comment}</code>\n\n"
                        f"‼️ Обязательно указывайте комментарий при отправке монет!\n\n"
                        f"Убедитесь, что вы отправили правильную сумму на указанный адрес."
                    )
                    
                    # Создаем клавиатуру с кнопкой "Проверить еще раз"
                    keyboard = InlineKeyboardMarkup()
                    keyboard.add(InlineKeyboardButton("🔄 Проверить еще раз", callback_data="check_ton_payment"))
                    keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel"))
                    
                    safe_edit_message(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text=not_found_text,
                        reply_markup=keyboard
                    )
                    
            except Exception as e:
                logging.error(f"Ошибка проверки TON платежа: {e}")
                
                # Получаем детали оплаты для отображения
                payment_info = payment_data.get("payment_data", {})
                ton_amount = payment_info.get("amount_ton", 0)
                wallet_address = payment_info.get("wallet_address", "")
                comment = payment_info.get("comment", "")
                
                error_text = (
                    f"❌ Ошибка проверки TON платежа. Попробуйте еще раз.\n\n"
                    f"💰 Сумма: {amount:.2f} ₽\n"
                    f"🆔 ID заказа: {order_id}\n\n"
                    f"💸 Сумма к отправке: {ton_amount:.4f} TON\n"
                    f"💳 Адрес для оплаты: <code>{wallet_address}</code>\n"
                    f"⚠️ Комментарий: <code>{comment}</code>\n\n"
                    f"‼️ Обязательно указывайте комментарий при отправке монет!"
                )
                
                # Создаем клавиатуру с кнопкой "Проверить еще раз"
                keyboard = InlineKeyboardMarkup()
                keyboard.add(InlineKeyboardButton("🔄 Проверить еще раз", callback_data="check_ton_payment"))
                keyboard.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel"))
                
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=error_text,
                    reply_markup=keyboard
                )
        else:
            bot.answer_callback_query(call.id, "❌ Нет активного TON платежа для проверки")

    elif call.data == "confirm_self_purchase":
        # Покупка звезд себе
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        purchase_data = user_states.get(user_id, {})
        
        if not purchase_data:
            bot.answer_callback_query(call.id, "❌ Нет данных о покупке")
            return
        
        stars_amount = purchase_data.get("stars_amount")
        cost = purchase_data.get("cost")
        recipient = user_data['username']  # Покупаем себе
        
        # Проверяем баланс (ещё раз)
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

        # Загрузка мнемоники из config.py
        try:
            from config import WALLET_MNEMONICS, WALLET_ADDRESS
            mnemonics = WALLET_MNEMONICS
            wallet_address = WALLET_ADDRESS
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
            # Покупка звезд
            result = asyncio.run(buy_stars(
                recipient=recipient,
                amount=stars_amount,
                mnemonics=mnemonics
            ))
            
            if result:
                # Успешная покупка
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
                
                # Обновляем статистику рефералов
                update_referral_stats(user_id, users_data)
                
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
                    reply_markup=create_back_keyboard()
                )
                
                # Отправляем уведомление в техподдержку
                support_message = (
                    f"✅ Успешная покупка звезд!\n"
                    f"Пользователь ID: {user_id}\n"
                    f"Получатель: @{recipient}\n"
                    f"Количество звезд: {stars_amount}\n"
                    f"Стоимость: {cost:.2f} ₽\n"
                    f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
                )
                send_to_support(support_message)
                
            else:
                # Ошибка покупки
                error_details = result if isinstance(result, str) else "Неизвестная ошибка"
                
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
                    # Общая ошибка
                    safe_edit_message(
                        chat_id=call.message.chat.id,
                        message_id=call.message.message_id,
                        text="Проблема на нашей стороне. Обратитесь в техническую поддержку @StarShopsup",
                        reply_markup=create_back_keyboard()
                    )
                
                # Отправляем уведомление в техподдержку
                support_message = (
                    f"⚠️ Ошибка покупки звезд!\n"
                    f"Пользователь ID: {user_id}\n"
                    f"Получатель: @{recipient}\n"
                    f"Количество звезд: {stars_amount}\n"
                    f"Стоимость: {cost:.2f} ₽\n"
                    f"Ошибка: {error_details}\n"
                    f"Время: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}"
                )
                send_to_support(support_message)
                
        except Exception as e:
            logging.error(f"Ошибка покупки звезд: {e}")
            safe_edit_message(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="Проблема на нашей стороне. Обратитесь в техническую поддержку @StarShopsup",
                reply_markup=create_back_keyboard()
            )
        
        # Очищаем состояние пользователя
        user_states.pop(user_id, None)

    elif call.data == "referral":
        # Показываем реферальную программу
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        
        referrals = user_data.get("referrals", [])
        qualified_referrals = sum(1 for ref in referrals if ref.get("total_spent", 0) >= 500.0)
        discount = user_data.get("referral_discount", 0.0)
        
        if qualified_referrals >= 3:
            price_text = "1.30 ₽ за звезду"
            status_text = "🎉 Активирована!"
        else:
            price_text = f"{STAR_PRICE:.2f} ₽ за звезду"
            status_text = f"⏳ Нужно еще {3 - qualified_referrals} рефералов"
        
        referral_text = (
            "🎁 Реферальная программа\n\n"
            f"📊 Статистика:\n"
            f"👥 Всего приглашенных: {len(referrals)}\n"
            f"✅ Квалифицированных: {qualified_referrals}\n"
            f"💰 Текущая цена: {price_text}\n"
            f"🎯 Статус программы: {status_text}\n\n"
            f"📋 Условия участия:\n"
            f"• Пригласите 3 активных пользователей\n"
            f"• Каждый должен пополнить баланс на 500+ ₽\n"
            f"• Получите специальную цену 1.30 ₽ за звезду\n"
            f"• Стандартная цена: {STAR_PRICE:.2f} ₽ за звезду\n\n"
            f"🔗 Ваша реферальная ссылка:\n"
            f"https://t.me/{bot.get_me().username}?start={user_data.get('referral_code', f'ref_{user_id}')}"
        )
        
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=referral_text,
            reply_markup=create_referral_keyboard()
        )
        
    elif call.data == "my_referrals":
        # Показываем список рефералов
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        
        referrals = user_data.get("referrals", [])
        if not referrals:
            referrals_text = "📋 У вас пока нет рефералов\n\nПригласите друзей по вашей реферальной ссылке!"
        else:
            referrals_text = "📋 Ваши рефералы:\n\n"
            for i, referral in enumerate(referrals, 1):
                status = "✅" if referral.get("total_spent", 0) >= 250.0 else "⏳"
                referrals_text += (
                    f"{i}. {status} @{referral.get('username', 'Unknown')}\n"
                    f"   💰 Потрачено: {referral.get('total_spent', 0):.2f} ₽\n"
                    f"   ⭐ Звезд: {referral.get('stars_bought', 0)}\n"
                    f"   📅 Регистрация: {referral.get('registration_date', 'Unknown')}\n\n"
                )
        
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=referrals_text,
            reply_markup=create_referral_keyboard()
        )
        
    elif call.data == "my_referral_link":
        # Показываем реферальную ссылку
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        
        referral_code = user_data.get('referral_code', f'ref_{user_id}')
        referral_link = f"https://t.me/{bot.get_me().username}?start={referral_code}"
        
        link_text = (
            "🔗 Реферальная ссылка\n\n"
            f"<code>{referral_link}</code>\n\n"
            f"📋 Уникальный код: <code>{referral_code}</code>\n\n"
            f"💼 Инструкция по использованию:\n"
            f"• Поделитесь ссылкой с потенциальными клиентами\n"
            f"• Пригласите 3 активных пользователей\n"
            f"• Каждый должен пополнить баланс на 500+ ₽\n"
            f"• Получите специальную цену 1.30 ₽ за звезду\n"
            f"• Стандартная цена: {STAR_PRICE:.2f} ₽ за звезду"
        )
        
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=link_text,
            reply_markup=create_referral_keyboard()
        )
        
    elif call.data == "referral_stats":
        # Показываем статистику рефералов
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        
        referrals = user_data.get("referrals", [])
        total_referrals = len(referrals)
        qualified_referrals = sum(1 for ref in referrals if ref.get("total_spent", 0) >= 500.0)
        total_spent_by_referrals = sum(ref.get("total_spent", 0) for ref in referrals)
        total_stars_by_referrals = sum(ref.get("stars_bought", 0) for ref in referrals)
        discount = user_data.get("referral_discount", 0.0)
        
        if qualified_referrals >= 3:
            price_status = "1.30 ₽ за звезду (активирована)"
        else:
            price_status = f"{STAR_PRICE:.2f} ₽ за звезду (нужно еще {3 - qualified_referrals} рефералов)"
        
        stats_text = (
            "📊 Детальная статистика\n\n"
            f"👥 Всего приглашенных: {total_referrals}\n"
            f"✅ Квалифицированных: {qualified_referrals}\n"
            f"💰 Общий оборот рефералов: {total_spent_by_referrals:.2f} ₽\n"
            f"⭐ Приобретено звезд: {total_stars_by_referrals}\n"
            f"🎯 Ваша цена за звезду: {price_status}\n\n"
            f"📋 Критерии квалификации:\n"
            f"• Минимальное пополнение: 500 ₽\n"
            f"• Требуется для активации: 3 квалифицированных реферала\n"
            f"• Специальная цена: 1.30 ₽ за звезду"
        )
        
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=stats_text,
            reply_markup=create_referral_keyboard()
        )
        
    elif call.data == "referral_earnings":
        # Показываем информацию о заработке
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        
        discount = user_data.get("referral_discount", 0.0)
        stars_bought = user_data.get("stars_bought", 0)
        total_saved = stars_bought * discount
        qualified_referrals = sum(1 for ref in user_data.get("referrals", []) if ref.get("total_spent", 0) >= 500.0)
        
        if discount > 0:
            savings_text = f"💵 Всего сэкономлено: {total_saved:.2f} ₽"
            status_text = "🎉 Скидка активирована!"
        else:
            savings_text = f"💵 Для получения скидки нужно 3 реферала"
            status_text = f"⏳ Квалифицированных рефералов: {qualified_referrals}/3"
        
        earnings_text = (
            "💰 Финансовая выгода\n\n"
            f"🎯 Статус программы: {status_text}\n"
            f"⭐ Приобретено звезд: {stars_bought}\n"
            f"{savings_text}\n\n"
            f"💼 Условия получения выгоды:\n"
            f"• Пригласите 3 активных пользователей\n"
            f"• Каждый должен пополнить баланс на 500+ ₽\n"
            f"• Получите специальную цену 1.30 ₽ за звезду\n"
            f"• Стандартная цена: {STAR_PRICE:.2f} ₽ за звезду"
        )
        
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=earnings_text,
            reply_markup=create_referral_keyboard()
        )
        
    elif call.data == "topup_apays":
        # Переходим к пополнению через APays с нужной суммой
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        
        # Получаем нужную сумму из состояния пользователя (если есть)
        user_state = user_states.get(user_id, {})
        needed_amount = user_state.get("needed_amount", 0)
        
        # Отладочная информация
        logging.info(f"topup_apays: user_state = {user_state}, needed_amount = {needed_amount}")
        
        if needed_amount > 0:
            # Рассчитываем сумму с комиссией APays
            commission_rate = APAYS_COMMISSION_PERCENT / 100
            amount_with_commission = needed_amount / (1 - commission_rate)
            amount_with_commission = round(amount_with_commission, 2)
            
            topup_text = (
                f"⚪️ Выбран метод: APays\n\n"
                f"💰 Текущий баланс: {user_data.get('balance', 0):.2f} ₽\n"
                f"💸 Нужно пополнить: {needed_amount:.2f} ₽\n"
                f"💳 К оплате (с комиссией {APAYS_COMMISSION_PERCENT}%): {amount_with_commission:.2f} ₽\n\n"
                f"🔽 Выберите действие:"
            )
            
            # Сохраняем данные для пополнения
            user_states[user_id] = {
                "state": "waiting_topup_amount",
                "payment_method": "apays",
                "needed_amount": needed_amount,
                "amount_with_commission": amount_with_commission
            }
            
            # Создаем клавиатуру с возможностью изменить сумму
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton(f"💳 Пополнить {amount_with_commission:.2f} ₽", callback_data="confirm_topup_apays")
            )
            keyboard.add(
                InlineKeyboardButton("💰 Другая сумма", callback_data="change_amount")
            )
            keyboard.add(
                InlineKeyboardButton(f"{EMOJIS['back']} Назад", callback_data="back_main")
            )
        else:
            # Если нет нужной суммы, показываем обычное меню
            topup_text = (
                "💳 Пополнение баланса\n\n"
                f"💰 Текущий баланс: {user_data.get('balance', 0):.2f} ₽\n"
                f"💸 Минимальная сумма: {PAYMENT_MIN_AMOUNT} ₽\n"
                f"💸 Максимальная сумма: {PAYMENT_MAX_AMOUNT} ₽\n\n"
                "🔽 Выберите способ оплаты:"
            )
            
            keyboard = InlineKeyboardMarkup()
            if APAYS_ENABLED and apays:
                keyboard.add(
                    InlineKeyboardButton(f"💳 APays (+{APAYS_COMMISSION_PERCENT}%)", callback_data="payment_method_apays")
                )
            keyboard.add(
                InlineKeyboardButton(f"⚡ Прямой перевод TON (Без комиссии)", callback_data="payment_method_ton")
            )
            keyboard.add(
                InlineKeyboardButton(f"{EMOJIS['back']} Назад", callback_data="back_main")
            )
        
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=topup_text,
            reply_markup=keyboard
        )
        
    elif call.data == "topup_ton":
        # Переходим к пополнению через TON с нужной суммой
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        
        # Получаем нужную сумму из состояния пользователя (если есть)
        user_state = user_states.get(user_id, {})
        needed_amount = user_state.get("needed_amount", 0)
        
        if needed_amount > 0:
            topup_text = (
                f"⚪️ Выбран метод: TON\n\n"
                f"💰 Текущий баланс: {user_data.get('balance', 0):.2f} ₽\n"
                f"💸 Нужно пополнить: {needed_amount:.2f} ₽\n"
                f"⚡ К доплате (без комиссии): {needed_amount:.2f} ₽\n\n"
                f"🔽 Выберите действие:"
            )
            
            # Сохраняем данные для пополнения
            user_states[user_id] = {
                "state": "waiting_topup_amount",
                "payment_method": "ton",
                "needed_amount": needed_amount
            }
            
            # Создаем клавиатуру с возможностью изменить сумму
            keyboard = InlineKeyboardMarkup()
            keyboard.add(
                InlineKeyboardButton(f"⚡ Пополнить {needed_amount:.2f} ₽", callback_data="confirm_topup_ton")
            )
            keyboard.add(
                InlineKeyboardButton("💰 Другая сумма", callback_data="change_amount")
            )
            keyboard.add(
                InlineKeyboardButton(f"{EMOJIS['back']} Назад", callback_data="back_main")
            )
        else:
            # Если нет нужной суммы, показываем обычное меню
            topup_text = (
                "💳 Пополнение баланса\n\n"
                f"💰 Текущий баланс: {user_data.get('balance', 0):.2f} ₽\n"
                f"💸 Минимальная сумма: {PAYMENT_MIN_AMOUNT} ₽\n"
                f"💸 Максимальная сумма: {PAYMENT_MAX_AMOUNT} ₽\n\n"
                "🔽 Выберите способ оплаты:"
            )
            
            keyboard = InlineKeyboardMarkup()
            if APAYS_ENABLED and apays:
                keyboard.add(
                    InlineKeyboardButton(f"💳 APays (+{APAYS_COMMISSION_PERCENT}%)", callback_data="payment_method_apays")
                )
            keyboard.add(
                InlineKeyboardButton(f"⚡ Прямой перевод TON (Без комиссии)", callback_data="payment_method_ton")
            )
            keyboard.add(
                InlineKeyboardButton(f"{EMOJIS['back']} Назад", callback_data="back_main")
            )
        
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=topup_text,
            reply_markup=keyboard
        )
        
    elif call.data == "change_amount":
        # Переходим к вводу другой суммы
        user_data = users_data.get(user_id, {})
        user_data = update_user_structure(user_data, user_id)
        
        change_text = (
            "💰 Введите сумму пополнения\n\n"
            f"💰 Текущий баланс: {user_data.get('balance', 0):.2f} ₽\n"
            f"💸 Минимальная сумма: {PAYMENT_MIN_AMOUNT} ₽\n"
            f"💸 Максимальная сумма: {PAYMENT_MAX_AMOUNT} ₽\n\n"
            f"Введите сумму в рублях:"
        )
        
        # Устанавливаем состояние ожидания ввода суммы
        user_states[user_id] = {
            "state": "waiting_custom_topup_amount"
        }
        
        safe_edit_message(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=change_text,
            reply_markup=create_cancel_keyboard()
        )
        
    elif call.data == "confirm_topup_apays":
        # Подтверждаем пополнение через APays
        user_state = user_states.get(user_id, {})
        amount = user_state.get("amount_with_commission", 0)
        
        # Отладочная информация
        logging.info(f"confirm_topup_apays: user_state = {user_state}, amount = {amount}")
        
        if amount > 0:
            # Напрямую вызываем логику пополнения APays
            if not APAYS_ENABLED or not apays:
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ APays временно недоступен",
                    reply_markup=create_back_keyboard()
                )
                return
            
            # Создаем платеж
            payment_data = apays.create_payment(amount)
            if payment_data and "payment_url" in payment_data:
                # Сохраняем данные платежа
                user_states[user_id] = {
                    "state": "waiting_payment_confirmation",
                    "payment_method": "apays",
                    "payment_id": payment_data["payment_id"],
                    "amount": amount
                }
                
                payment_text = (
                    f"💳 APays платеж создан\n\n"
                    f"💰 Сумма: {amount:.2f} ₽\n"
                    f"🆔 ID платежа: {payment_data['payment_id']}\n\n"
                    f"🔗 Ссылка для оплаты:\n{payment_data['payment_url']}\n\n"
                    f"⏳ Ожидаем подтверждения платежа..."
                )
                
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=payment_text,
                    reply_markup=create_cancel_keyboard()
                )
            else:
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ Ошибка создания платежа APays",
                    reply_markup=create_back_keyboard()
                )
        else:
            safe_edit_message(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ Ошибка: сумма не определена",
                reply_markup=create_back_keyboard()
            )
            
    elif call.data == "confirm_topup_ton":
        # Подтверждаем пополнение через TON
        user_state = user_states.get(user_id, {})
        amount = user_state.get("needed_amount", 0)
        
        if amount > 0:
            # Напрямую вызываем логику пополнения TON
            if not TON_ENABLED or not ton_payment:
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ TON платежи временно недоступны",
                    reply_markup=create_back_keyboard()
                )
                return
            
            # Генерируем уникальный комментарий для платежа
            comment = f"topup_{user_id}_{int(time.time())}"
            
            # Получаем информацию о кошельке
            wallet_info = ton_payment.get_wallet_info()
            if wallet_info:
                # Сохраняем данные платежа
                user_states[user_id] = {
                    "state": "waiting_payment_confirmation",
                    "payment_method": "ton",
                    "amount": amount,
                    "comment": comment
                }
                
                payment_text = (
                    f"⚡ TON платеж\n\n"
                    f"💰 Сумма: {amount:.2f} ₽\n"
                    f"💬 Комментарий: <code>{comment}</code>\n\n"
                    f"🏦 Адрес кошелька:\n<code>{wallet_info['address']}</code>\n\n"
                    f"⚠️ ВАЖНО: Обязательно укажите комментарий при переводе!\n"
                    f"⏳ Ожидаем подтверждения платежа..."
                )
                
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text=payment_text,
                    parse_mode='HTML',
                    reply_markup=create_cancel_keyboard()
                )
            else:
                safe_edit_message(
                    chat_id=call.message.chat.id,
                    message_id=call.message.message_id,
                    text="❌ Ошибка получения информации о кошельке",
                    reply_markup=create_back_keyboard()
                )
        else:
            safe_edit_message(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ Ошибка: сумма не определена",
                reply_markup=create_back_keyboard()
            )

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
                            parse_mode='HTML'
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
                # Используем эффективную цену с учетом скидки
                effective_price = get_effective_star_price(user_data)
                cost = stars_amount * effective_price
                
                if user_data.get('balance', 0) < cost:
                    needed_amount = cost - user_data.get('balance', 0)
                    
                    # Сохраняем нужную сумму в состоянии пользователя
                    user_states[user_id] = {
                        "state": "insufficient_balance",
                        "needed_amount": needed_amount,
                        "stars_amount": stars_amount,
                        "cost": cost
                    }
                    
                    insufficient_text = (
                        f"❌ Недостаточно средств для покупки\n\n"
                        f"💰 Текущий баланс: {user_data.get('balance', 0):.2f} ₽\n"
                        f"💸 Требуется: {cost:.2f} ₽\n"
                        f"💸 Не хватает: {needed_amount:.2f} ₽\n\n"
                        f"💳 Пополните баланс для продолжения покупки"
                    )
                    bot.reply_to(
                        message,
                        insufficient_text,
                        reply_markup=create_topup_keyboard()
                    )
                    return
                    
                user_states[user_id] = {
                    "state": "waiting_recipient_username",
                    "stars_amount": stars_amount,
                    "cost": cost
                }
                
                discount = user_data.get("referral_discount", 0.0)
                qualified_referrals = sum(1 for ref in user_data.get("referrals", []) if ref.get("total_spent", 0) >= 500.0)
                
                reply_text = (
                    f"⭐️ Количество: {stars_amount} звезд\n"
                    f"💰 Общая стоимость: {cost:.2f} ₽"
                )
                
                if discount > 0:
                    original_cost = stars_amount * STAR_PRICE
                    saved = original_cost - cost
                    reply_text += f"\n🎉 Специальная цена: экономия {saved:.2f} ₽"
                elif qualified_referrals > 0:
                    reply_text += f"\n⏳ Прогресс: {qualified_referrals}/3 рефералов (требуется для специальной цены)"
                
                reply_text += "\n👤 Введите юзернейм получателя (например: @username или username):"
                
                bot.reply_to(
                    message,
                    reply_text,
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

    elif user_state.get("state") == "insufficient_balance":
        # Обработка состояния недостаточного баланса
        # Это состояние не должно обрабатываться в handle_text
        # Оно обрабатывается через callback'и
        pass
        
    elif user_state.get("state") == "waiting_payment_method":
        # Обработка выбора способа оплаты с пользовательской суммой
        # Это состояние не должно обрабатываться в handle_text
        # Оно обрабатывается через callback'и
        pass
        
    elif user_state.get("state") == "waiting_custom_topup_amount":
        # Обработка ввода пользовательской суммы пополнения
        try:
            amount = float(message.text)
            if PAYMENT_MIN_AMOUNT <= amount <= PAYMENT_MAX_AMOUNT:
                # Показываем меню выбора способа оплаты с введенной суммой
                user_data = users_data.get(user_id, {})
                user_data = update_user_structure(user_data, user_id)
                
                topup_text = (
                    "💳 Пополнение баланса\n\n"
                    f"💰 Текущий баланс: {user_data.get('balance', 0):.2f} ₽\n"
                    f"💸 Сумма пополнения: {amount:.2f} ₽\n\n"
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
                    InlineKeyboardButton(f"{EMOJIS['back']} Назад", callback_data="back_main")
                )
                
                # Сохраняем сумму в состоянии
                user_states[user_id] = {
                    "state": "waiting_payment_method",
                    "custom_amount": amount
                }
                
                bot.reply_to(
                    message,
                    topup_text,
                    reply_markup=keyboard
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
    
    # Очищаем webhook перед запуском polling
    try:
        print("🧹 Очистка webhook...")
        bot.remove_webhook()
        print("✅ Webhook очищен")
    except Exception as e:
        print(f"⚠️ Не удалось очистить webhook: {e}")
    
    # Запуск с обработкой ошибок соединения
    while True:
        try:
            print("🔄 Запуск polling...")
            bot.polling(none_stop=True, interval=1, timeout=20)
        except Exception as e:
            logging.error(f"❌ Ошибка polling: {e}")
            print(f"❌ Ошибка соединения: {e}")
            
            # Если это ошибка 409 (конфликт), ждем дольше
            if "409" in str(e) or "Conflict" in str(e):
                print("⚠️ Обнаружен конфликт - другой экземпляр бота запущен")
                print("🔄 Ожидание 30 секунд перед перезапуском...")
                import time
                time.sleep(30)
            else:
                print("🔄 Перезапуск через 5 секунд...")
                import time
                time.sleep(5)
            