import os
import random
import asyncio
from telebot.async_telebot import AsyncTeleBot
from telebot import types
import logging
import pickle

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
TOKEN = '7305892783:AAEPYSCoF2PQuUxdTToS1zlEYvR9yZv4gjs'
bot = AsyncTeleBot(TOKEN)

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
async def start(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("Рассылка", callback_data="mailing"))
    markup.row(types.InlineKeyboardButton("Группы", callback_data="groups"))
    await bot.send_message(message.chat.id, "Привет! Выберите действие:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
async def callback_query(call):
    if call.data == "mailing":
        await show_mailing_options(call.message)
    elif call.data == "groups":
        await show_groups(call.message)
    elif call.data.startswith("mailing_"):
        percentage = call.data.split("_")[1]
        await ask_for_mailing_text(call.message, percentage)
    elif call.data == "back":
        await start(call.message)
    elif call.data.startswith("group_"):
        group_id = int(call.data.split("_")[1])
        await show_group_info(call.message, group_id)
    elif call.data == "start_mailing":
        await select_group_for_mailing(call.message)
    elif call.data.startswith("select_group_"):
        group_id = int(call.data.split("_")[2])
        await start_mailing(call.message, group_id)

async def show_mailing_options(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("Всем", callback_data="mailing_100"))
    markup.row(types.InlineKeyboardButton("50%", callback_data="mailing_50"))
    markup.row(types.InlineKeyboardButton("10%", callback_data="mailing_10"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    await bot.edit_message_text("Выберите получателей рассылки:", message.chat.id, message.message_id, reply_markup=markup)

async def ask_for_mailing_text(message, percentage):
    await bot.edit_message_text(f"Введите текст для рассылки {percentage}% участников:", message.chat.id, message.message_id)
    bot.register_next_step_handler(message, process_mailing_text, percentage)

async def process_mailing_text(message, percentage):
    mailing_text = message.text
    mailing_data[message.chat.id] = {"text": mailing_text, "percentage": percentage}
    save_data()
    await show_mailing_actions(message)

async def show_mailing_actions(message):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("Начать рассылку", callback_data="start_mailing"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    await bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)

async def select_group_for_mailing(message):
    markup = types.InlineKeyboardMarkup()
    for group_id, group_info in groups.items():
        markup.row(types.InlineKeyboardButton(group_info['title'], callback_data=f"select_group_{group_id}"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    await bot.edit_message_text("Выберите группу для рассылки:", message.chat.id, message.message_id, reply_markup=markup)

async def start_mailing(message, group_id):
    chat_id = message.chat.id
    if chat_id not in mailing_data:
        await bot.send_message(chat_id, "Ошибка: данные для рассылки не найдены.")
        return

    mailing_info = mailing_data[chat_id]
    percentage = int(mailing_info["percentage"])
    text = mailing_info["text"]

    await bot.send_message(chat_id, f"Начинаем рассылку {percentage}% участников в выбранную группу...")

    group_info = groups[group_id]
    members = list(group_info['members'])
    num_recipients = int(len(members) * percentage / 100)
    recipients = random.sample(members, num_recipients)

    sent_message = await bot.send_message(group_id, text)
    
    while True:
        for i, user_id in enumerate(recipients):
            updated_text = ""
            for j, char in enumerate(text):
                if j < len(recipients):
                    updated_text += f"[{char}](tg://user?id={recipients[j]})"
                else:
                    updated_text += char
            
            try:
                await bot.edit_message_text(updated_text, group_id, sent_message.message_id, parse_mode='Markdown')
            except Exception as e:
                logger.error(f"Ошибка при обновлении сообщения в группе {group_id}: {e}")
            
            await asyncio.sleep(0.1)
        
        if i == len(recipients) - 1:
            break
    
    await bot.edit_message_text(text, group_id, sent_message.message_id)
    await bot.send_message(chat_id, "Рассылка завершена!")
    del mailing_data[chat_id]
    save_data()

async def show_groups(message):
    markup = types.InlineKeyboardMarkup()
    for group_id, group_info in groups.items():
        markup.row(types.InlineKeyboardButton(group_info['title'], callback_data=f"group_{group_id}"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    await bot.edit_message_text("Выберите группу:", message.chat.id, message.message_id, reply_markup=markup)

async def show_group_info(message, group_id):
    group_info = groups[group_id]
    info_text = f"Информация о группе:\n\nНазвание: {group_info['title']}\nID: {group_id}\nКоличество участников: {len(group_info['members'])}"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Назад к группам", callback_data="groups"))
    await bot.edit_message_text(info_text, message.chat.id, message.message_id, reply_markup=markup)

@bot.my_chat_member_handler()
async def handle_my_chat_member(message):
    if message.new_chat_member.status == 'administrator':
        group_id = message.chat.id
        groups[group_id] = {
            'title': message.chat.title,
            'members': set(),
            'owner_id': message.from_user.id
        }
        save_data()
        await bot.send_message(message.chat.id, "Спасибо за назначение меня администратором! Я готов к работе.")
        await update_group_members(group_id)
    elif message.new_chat_member.status == 'member':
        await bot.send_message(message.chat.id, "Для корректной работы мне нужны права администратора.")

async def update_group_members(group_id):
    try:
        members = await bot.get_chat_members_count(group_id)
        groups[group_id]['members'] = set(range(members))  # Просто для примера, так как мы не можем получить реальные ID
        save_data()
    except Exception as e:
        logger.error(f"Ошибка при обновлении списка участников группы {group_id}: {e}")

@bot.message_handler(content_types=['new_chat_members'])
async def handle_new_chat_members(message):
    group_id = message.chat.id
    if group_id in groups:
        for new_member in message.new_chat_members:
            groups[group_id]['members'].add(new_member.id)
        save_data()

@bot.message_handler(content_types=['left_chat_member'])
async def handle_left_chat_member(message):
    group_id = message.chat.id
    if group_id in groups:
        groups[group_id]['members'].discard(message.left_chat_member.id)
        save_data()

if __name__ == '__main__':
    asyncio.run(bot.polling())