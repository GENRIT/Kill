import os
import random
from telebot import TeleBot, types
from telebot.util import smart_split
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация бота
TOKEN = os.environ.get('7305892783:AAEPYSCoF2PQuUxdTToS1zlEYvR9yZv4gjs')
if not TOKEN:
    logger.error("No token provided. Please set the BOT_TOKEN environment variable.")
    exit(1)

bot = TeleBot(TOKEN)

# Словарь для хранения данных о группах
groups = {}

@bot.message_handler(commands=['start'])
def start(message):
    try:
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("Рассылка", callback_data="mailing"))
        markup.row(types.InlineKeyboardButton("Группы", callback_data="groups"))
        bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=markup)
    except Exception as e:
        logger.error(f"Error in start function: {e}")

@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    try:
        if call.data == "mailing":
            show_mailing_options(call.message)
        elif call.data == "groups":
            show_groups(call.message)
        elif call.data.startswith("mailing_"):
            percentage = call.data.split("_")[1]
            start_mailing(call.message, percentage)
        elif call.data == "back":
            start(call.message)
        elif call.data.startswith("group_"):
            group_id = int(call.data.split("_")[1])
            show_group_info(call.message, group_id)
        
        # Отвечаем на callback query, чтобы убрать "часики" на кнопке
        bot.answer_callback_query(call.id)
    except Exception as e:
        logger.error(f"Error in callback_query function: {e}")

def show_mailing_options(message):
    try:
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("Всем", callback_data="mailing_100"))
        markup.row(types.InlineKeyboardButton("50%", callback_data="mailing_50"))
        markup.row(types.InlineKeyboardButton("10%", callback_data="mailing_10"))
        markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
        bot.edit_message_text("Выберите получателей рассылки:", message.chat.id, message.message_id, reply_markup=markup)
    except Exception as e:
        logger.error(f"Error in show_mailing_options function: {e}")

def start_mailing(message, percentage):
    try:
        bot.edit_message_text(f"Начинаем рассылку {percentage}% участников...", message.chat.id, message.message_id)
        for group_id, group_info in groups.items():
            members = list(group_info['members'])
            num_recipients = int(len(members) * int(percentage) / 100)
            recipients = random.sample(members, min(num_recipients, len(members)))
            for user_id in recipients:
                try:
                    bot.send_message(user_id, f"Рассылка: Привет, участник группы {group_info['title']}! Ваш ID: {user_id}")
                except Exception as e:
                    logger.error(f"Ошибка при отправке сообщения пользователю {user_id}: {e}")
        bot.edit_message_text("Рассылка завершена!", message.chat.id, message.message_id)
    except Exception as e:
        logger.error(f"Error in start_mailing function: {e}")

def show_groups(message):
    try:
        markup = types.InlineKeyboardMarkup()
        if not groups:
            bot.edit_message_text("У бота нет групп, где он администратор.", message.chat.id, message.message_id)
            return
        for group_id, group_info in groups.items():
            markup.row(types.InlineKeyboardButton(group_info['title'], callback_data=f"group_{group_id}"))
        markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
        bot.edit_message_text("Выберите группу:", message.chat.id, message.message_id, reply_markup=markup)
    except Exception as e:
        logger.error(f"Error in show_groups function: {e}")

def show_group_info(message, group_id):
    try:
        group_info = groups.get(group_id)
        if not group_info:
            bot.edit_message_text("Информация о группе не найдена.", message.chat.id, message.message_id)
            return
        info_text = f"Информация о группе:\n\nНазвание: {group_info['title']}\nID: {group_id}\nКоличество участников: {len(group_info['members'])}"
        markup = types.InlineKeyboardMarkup()
        markup.row(types.InlineKeyboardButton("🔙 Назад к группам", callback_data="groups"))
        bot.edit_message_text(info_text, message.chat.id, message.message_id, reply_markup=markup)
    except Exception as e:
        logger.error(f"Error in show_group_info function: {e}")

@bot.my_chat_member_handler()
def handle_my_chat_member(message):
    try:
        if message.new_chat_member.status == 'administrator':
            group_id = message.chat.id
            groups[group_id] = {
                'title': message.chat.title,
                'members': set()
            }
            bot.send_message(message.chat.id, "Спасибо за назначение меня администратором! Я готов к работе.")
        elif message.new_chat_member.status == 'member':
            bot.send_message(message.chat.id, "Для корректной работы мне нужны права администратора.")
    except Exception as e:
        logger.error(f"Error in handle_my_chat_member function: {e}")

@bot.message_handler(content_types=['new_chat_members'])
def handle_new_chat_members(message):
    try:
        group_id = message.chat.id
        if group_id in groups:
            for new_member in message.new_chat_members:
                groups[group_id]['members'].add(new_member.id)
    except Exception as e:
        logger.error(f"Error in handle_new_chat_members function: {e}")

@bot.message_handler(content_types=['left_chat_member'])
def handle_left_chat_member(message):
    try:
        group_id = message.chat.id
        if group_id in groups:
            groups[group_id]['members'].discard(message.left_chat_member.id)
    except Exception as e:
        logger.error(f"Error in handle_left_chat_member function: {e}")

if __name__ == '__main__':
    logger.info("Starting bot...")
    bot.polling(none_stop=True, interval=0, timeout=20)