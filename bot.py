import os
import random
from telebot import TeleBot, types
from telebot.util import smart_split
import logging
import pickle

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
TOKEN = '7305892783:AAEPYSCoF2PQuUxdTToS1zlEYvR9yZv4gjs'
bot = TeleBot(TOKEN)

# Словарь для хранения данных о группах
groups = {}

# Словарь для хранения данных о рассылке
mailing_data = {}

# Функция для сохранения данных
def save_data():
    with open('bot_data.pkl', 'wb') as f:
        pickle.dump((groups, mailing_data), f)

# Функция для загрузки данных
def load_data():
    global groups, mailing_data
    if os.path.exists('bot_data.pkl'):
        with open('bot_data.pkl', 'rb') as f:
            groups, mailing_data = pickle.load(f)

# Загрузка данных при запуске
load_data()

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("Рассылка", callback_data="mailing"))
    markup.row(types.InlineKeyboardButton("Группы", callback_data="groups"))
    bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data == "mailing":
        show_mailing_options(call.message)
    elif call.data == "groups":
        show_groups(call.message)
    elif call.data.startswith("mailing_"):
        percentage = call.data.split("_")[1]
        ask_for_mailing_text(call.message, percentage)
    elif call.data == "back":
        start(call.message)
    elif call.data.startswith("group_"):
        group_id = int(call.data.split("_")[1])
        show_group_info(call.message, group_id)
    elif call.data == "add_media":
        ask_for_media(call.message)
    elif call.data == "add_button":
        ask_for_button(call.message)
    elif call.data == "start_mailing":
        select_group_for_mailing(call.message)
    elif call.data == "preview_post":
        preview_post(call.message)
    elif call.data.startswith("select_group_"):
        group_id = int(call.data.split("_")[2])
        start_mailing(call.message, group_id)

def show_mailing_options(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("Всем", callback_data="mailing_100"))
    markup.row(types.InlineKeyboardButton("50%", callback_data="mailing_50"))
    markup.row(types.InlineKeyboardButton("10%", callback_data="mailing_10"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    bot.edit_message_text("Выберите получателей рассылки:", message.chat.id, message.message_id, reply_markup=markup)

def ask_for_mailing_text(message, percentage):
    bot.edit_message_text(f"Введите текст для рассылки {percentage}% участников:", message.chat.id, message.message_id)
    bot.register_next_step_handler(message, process_mailing_text, percentage)

def process_mailing_text(message, percentage):
    mailing_text = message.text
    mailing_data[message.chat.id] = {"text": mailing_text, "percentage": percentage}
    save_data()
    show_mailing_actions(message)

def show_mailing_actions(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("Добавить кнопку с ссылкой", callback_data="add_button"))
    markup.row(types.InlineKeyboardButton("Добавить медиа", callback_data="add_media"))
    markup.row(types.InlineKeyboardButton("Предпросмотр", callback_data="preview_post"))
    markup.row(types.InlineKeyboardButton("Начать рассылку", callback_data="start_mailing"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

def ask_for_button(message):
    bot.send_message(message.chat.id, "Введите текст и ссылку для кнопки в формате: текст|ссылка")
    bot.register_next_step_handler(message, process_button)

def process_button(message):
    try:
        text, url = message.text.split('|')
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text.strip(), url=url.strip()))
        mailing_data[message.chat.id]['markup'] = markup
        save_data()
        bot.send_message(message.chat.id, "Кнопка успешно добавлена.")
        show_mailing_actions(message)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат. Попробуйте еще раз.")
        ask_for_button(message)

def ask_for_media(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("Фото", callback_data="media_photo"))
    markup.row(types.InlineKeyboardButton("Видео", callback_data="media_video"))
    markup.row(types.InlineKeyboardButton("GIF", callback_data="media_gif"))
    markup.row(types.InlineKeyboardButton("Стикер", callback_data="media_sticker"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back_to_mailing"))
    bot.edit_message_text("Выберите тип медиа для добавления:", message.chat.id, message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("media_"))
def handle_media_type(call):
    media_type = call.data.split("_")[1]
    bot.answer_callback_query(call.id)
    bot.edit_message_text(f"Отправьте {media_type} для добавления к рассылке:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(call.message, process_media, media_type)

def process_media(message, media_type):
    if message.content_type == media_type or (media_type == 'gif' and message.content_type == 'document'):
        if media_type == 'photo':
            mailing_data[message.chat.id]["media"] = message.photo[-1].file_id
        elif media_type == 'video':
            mailing_data[message.chat.id]["media"] = message.video.file_id
        elif media_type == 'gif':
            mailing_data[message.chat.id]["media"] = message.document.file_id
        elif media_type == 'sticker':
            mailing_data[message.chat.id]["media"] = message.sticker.file_id
        save_data()
        bot.send_message(message.chat.id, f"{media_type.capitalize()} добавлен к рассылке.")
        show_mailing_actions(message)
    else:
        bot.send_message(message.chat.id, f"Пожалуйста, отправьте {media_type}.")
        ask_for_media(message)

def preview_post(message):
    chat_id = message.chat.id
    if chat_id not in mailing_data:
        bot.send_message(chat_id, "Ошибка: данные для рассылки не найдены.")
        return

    mailing_info = mailing_data[chat_id]
    text = mailing_info["text"]
    markup = mailing_info.get("markup")
    media = mailing_info.get("media")

    if media:
        if "photo" in media:
            bot.send_photo(chat_id, media, caption=text, reply_markup=markup)
        elif "video" in media:
            bot.send_video(chat_id, media, caption=text, reply_markup=markup)
        elif "animation" in media:
            bot.send_animation(chat_id, media, caption=text, reply_markup=markup)
        elif "sticker" in media:
            bot.send_sticker(chat_id, media)
            if text or markup:
                bot.send_message(chat_id, text, reply_markup=markup)
    else:
        bot.send_message(chat_id, text, reply_markup=markup)

    show_mailing_actions(message)

def select_group_for_mailing(message):
    markup = types.InlineKeyboardMarkup()
    for group_id, group_info in groups.items():
        markup.row(types.InlineKeyboardButton(group_info['title'], callback_data=f"select_group_{group_id}"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    bot.edit_message_text("Выберите группу для рассылки:", message.chat.id, message.message_id, reply_markup=markup)

def start_mailing(message, group_id):
    chat_id = message.chat.id
    if chat_id not in mailing_data:
        bot.send_message(chat_id, "Ошибка: данные для рассылки не найдены.")
        return

    mailing_info = mailing_data[chat_id]
    percentage = int(mailing_info["percentage"])
    text = mailing_info["text"]
    markup = mailing_info.get("markup")
    media = mailing_info.get("media")

    bot.send_message(chat_id, f"Начинаем рассылку {percentage}% участников в выбранную группу...")

    group_info = groups[group_id]
    members = list(group_info['members'])
    num_recipients = int(len(members) * percentage / 100)
    recipients = random.sample(members, num_recipients)

    for user_id in recipients:
        try:
            # Добавляем ID пользователя в текст сообщения
            user_text = f"{text}\n\n{user_id}"
            if media:
                if "photo" in media:
                    bot.send_photo(group_id, media, caption=user_text, reply_markup=markup)
                elif "video" in media:
                    bot.send_video(group_id, media, caption=user_text, reply_markup=markup)
                elif "animation" in media:
                    bot.send_animation(group_id, media, caption=user_text, reply_markup=markup)
                elif "sticker" in media:
                    bot.send_sticker(group_id, media)
                    if user_text or markup:
                        bot.send_message(group_id, user_text, reply_markup=markup)
            else:
                bot.send_message(group_id, user_text, reply_markup=markup)
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения в группу {group_id}: {e}")

    bot.send_message(chat_id, "Рассылка завершена!")
    del mailing_data[chat_id]
    save_data()

def show_groups(message):
    markup = types.InlineKeyboardMarkup()
    for group_id, group_info in groups.items():
        markup.row(types.InlineKeyboardButton(group_info['title'], callback_data=f"group_{group_id}"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    bot.edit_message_text("Выберите группу:", message.chat.id, message.message_id, reply_markup=markup)

def show_group_info(message, group_id):
    group_info = groups[group_id]
    info_text = f"Информация о группе:\n\nНазвание: {group_info['title']}\nID: {group_id}\nКоличество участников: {len(group_info['members'])}"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("Отправить сообщение в группу", callback_data=f"send_to_group_{group_id}"))
    markup.row(types.InlineKeyboardButton("🔙 Назад к группам", callback_data="groups"))
    bot.edit_message_text(info_text, message.chat.id, message.message_id, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("send_to_group_"))
def ask_for_group_message(call):
    group_id = int(call.data.split("_")[3])
    bot.edit_message_text("Введите сообщение для отправки в группу:", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(call.message, send_message_to_group, group_id)

def send_message_to_group(message, group_id):
    try:
        bot.send_message(group_id, message.text)
        bot.send_message(message.chat.id, "Сообщение успешно отправлено в группу!")
    except Exception as e:
        bot.send_message(message.chat.id, f"Ошибка при отправке сообщения в группу: {e}")

@bot.my_chat_member_handler()
def handle_my_chat_member(message):
    if message.new_chat_member.status == 'administrator':
        group_id = message.chat.id
        groups[group_id] = {
            'title': message.chat.title,
            'members': set(),
            'owner_id': message.from_user.id
        }
        save_data()
        bot.send_message(message.chat.id, "Спасибо за назначение меня администратором! Я готов к работе.")
        update_group_members(group_id)
    elif message.new_chat_member.status == 'member':
        bot.send_message(message.chat.id, "Для корректной работы мне нужны права администратора.")

def update_group_members(group_id):
    try:
        members = bot.get_chat_members_count(group_id)
        groups[group_id]['members'] = set(range(members))  # Просто для примера, так как мы не можем получить реальные ID
        save_data()
    except Exception as e:
        logger.error(f"Ошибка при обновлении списка участников группы {group_id}: {e}")

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_chat_members(message):
    group_id = message.chat.id
    if group_id in groups:
        for new_member in message.new_chat_members:
            groups[group_id]['members'].add(new_member.id)
        save_data()

@bot.message_handler(content_types=['left_chat_member'])
def handle_left_chat_member(message):
    group_id = message.chat.id
    if group_id in groups:
        groups[group_id]['members'].discard(message.left_chat_member.id)
        save_data()

if __name__ == '__main__':
    bot.polling(none_stop=True)