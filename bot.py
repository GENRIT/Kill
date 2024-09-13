import os
import random
from telebot import TeleBot, types
from telebot.util import smart_split
import logging

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
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("Добавить кнопку с ссылкой", callback_data=f"add_button"))
    markup.row(types.InlineKeyboardButton("Добавить медиа", callback_data="add_media"))
    markup.row(types.InlineKeyboardButton("Начать рассылку", callback_data=f"start_mailing"))
    bot.send_message(message.chat.id, "Текст рассылки получен. Выберите действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "add_button")
def add_button_to_mailing(call):
    bot.edit_message_text("Введите текст для кнопки и ссылку в формате 'текст|ссылка':", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(call.message, process_button_info)

def process_button_info(message):
    try:
        button_text, button_url = message.text.split("|")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text=button_text.strip(), url=button_url.strip()))
        mailing_data[message.chat.id]["markup"] = markup
        bot.send_message(message.chat.id, "Кнопка добавлена. Выберите дальнейшее действие:", reply_markup=get_mailing_markup())
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат. Попробуйте еще раз.")
        add_button_to_mailing(types.CallbackQuery(data="add_button", message=message))

def ask_for_media(message):
    bot.edit_message_text("Отправьте изображение, GIF или видео для добавления к рассылке:", message.chat.id, message.message_id)
    bot.register_next_step_handler(message, process_media)

def process_media(message):
    if message.content_type in ['photo', 'video', 'animation']:
        if message.content_type == 'photo':
            mailing_data[message.chat.id]["media"] = message.photo[-1].file_id
        elif message.content_type == 'video':
            mailing_data[message.chat.id]["media"] = message.video.file_id
        elif message.content_type == 'animation':
            mailing_data[message.chat.id]["media"] = message.animation.file_id
        bot.send_message(message.chat.id, "Медиа добавлено к рассылке. Выберите дальнейшее действие:", reply_markup=get_mailing_markup())
    else:
        bot.send_message(message.chat.id, "Пожалуйста, отправьте изображение, GIF или видео.")
        ask_for_media(message)

def get_mailing_markup():
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("Добавить кнопку с ссылкой", callback_data="add_button"))
    markup.row(types.InlineKeyboardButton("Добавить медиа", callback_data="add_media"))
    markup.row(types.InlineKeyboardButton("Начать рассылку", callback_data="start_mailing"))
    return markup

@bot.callback_query_handler(func=lambda call: call.data == "start_mailing")
def start_mailing_callback(call):
    start_mailing(call.message)

def start_mailing(message):
    chat_id = message.chat.id
    if chat_id not in mailing_data:
        bot.send_message(chat_id, "Ошибка: данные для рассылки не найдены.")
        return

    mailing_info = mailing_data[chat_id]
    percentage = int(mailing_info["percentage"])
    text = mailing_info["text"]
    markup = mailing_info.get("markup")
    media = mailing_info.get("media")

    bot.send_message(chat_id, f"Начинаем рассылку {percentage}% участников...")
    
    for group_id, group_info in groups.items():
        members = list(group_info['members'])
        num_recipients = int(len(members) * percentage / 100)
        recipients = random.sample(members, num_recipients)
        
        for user_id in recipients:
            try:
                if media:
                    if "photo" in media:
                        bot.send_photo(user_id, media, caption=text, reply_markup=markup)
                    elif "video" in media:
                        bot.send_video(user_id, media, caption=text, reply_markup=markup)
                    elif "animation" in media:
                        bot.send_animation(user_id, media, caption=text, reply_markup=markup)
                else:
                    bot.send_message(user_id, text, reply_markup=markup)
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")

    bot.send_message(chat_id, "Рассылка завершена!")
    del mailing_data[chat_id]

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
        bot.send_message(message.chat.id, "Спасибо за назначение меня администратором! Я готов к работе.")
        update_group_members(group_id)
    elif message.new_chat_member.status == 'member':
        bot.send_message(message.chat.id, "Для корректной работы мне нужны права администратора.")

def update_group_members(group_id):
    try:
        members = bot.get_chat_members_count(group_id)
        groups[group_id]['members'] = set(range(members))  # Просто для примера, так как мы не можем получить реальные ID
    except Exception as e:
        logger.error(f"Ошибка при обновлении списка участников группы {group_id}: {e}")

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_chat_members(message):
    group_id = message.chat.id
    if group_id in groups:
        for new_member in message.new_chat_members:
            groups[group_id]['members'].add(new_member.id)

@bot.message_handler(content_types=['left_chat_member'])
def handle_left_chat_member(message):
    group_id = message.chat.id
    if group_id in groups:
        groups[group_id]['members'].discard(message.left_chat_member.id)

if __name__ == '__main__':
    bot.polling(none_stop=True)