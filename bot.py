import os
import random
from telebot import TeleBot, types
from telebot.util import smart_split
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
TOKEN = os.environ.get('7305892783:AAEPYSCoF2PQuUxdTToS1zlEYvR9yZv4gjs')
bot = TeleBot(TOKEN)

# Словарь для хранения данных о группах
groups = {}

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
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("Добавить кнопку с ссылкой", callback_data=f"add_button_{percentage}"))
    markup.row(types.InlineKeyboardButton("Начать рассылку", callback_data=f"start_mailing_{percentage}"))
    bot.send_message(message.chat.id, "Текст рассылки получен. Выберите действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_button_"))
def add_button_to_mailing(call):
    percentage = call.data.split("_")[2]
    bot.edit_message_text("Введите текст для кнопки и ссылку в формате 'текст|ссылка':", call.message.chat.id, call.message.message_id)
    bot.register_next_step_handler(call.message, process_button_info, percentage)

def process_button_info(message, percentage):
    try:
        button_text, button_url = message.text.split("|")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton(text=button_text.strip(), url=button_url.strip()))
        bot.send_message(message.chat.id, "Кнопка добавлена. Начинаем рассылку?", reply_markup=markup)
        bot.register_next_step_handler(message, start_mailing_with_button, percentage, markup)
    except ValueError:
        bot.send_message(message.chat.id, "Неверный формат. Попробуйте еще раз.")
        add_button_to_mailing(types.CallbackQuery(data=f"add_button_{percentage}", message=message))

def start_mailing_with_button(message, percentage, markup):
    if message.text.lower() == "да":
        start_mailing(message, percentage, markup)
    else:
        bot.send_message(message.chat.id, "Рассылка отменена.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("start_mailing_"))
def start_mailing_callback(call):
    percentage = call.data.split("_")[2]
    start_mailing(call.message, percentage)

def start_mailing(message, percentage, markup=None):
    bot.send_message(message.chat.id, f"Начинаем рассылку {percentage}% участников...")
    for group_id, group_info in groups.items():
        members = list(group_info['members'])
        num_recipients = int(len(members) * int(percentage) / 100)
        recipients = random.sample(members, num_recipients)
        for user_id in recipients:
            try:
                if markup:
                    bot.send_message(user_id, f"Рассылка: Привет, участник группы {group_info['title']}! Ваш ID: {user_id}", reply_markup=markup)
                else:
                    bot.send_message(user_id, f"Рассылка: Привет, участник группы {group_info['title']}! Ваш ID: {user_id}")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
    bot.send_message(message.chat.id, "Рассылка завершена!")

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
    elif message.new_chat_member.status == 'member':
        bot.send_message(message.chat.id, "Для корректной работы мне нужны права администратора.")

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