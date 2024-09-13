import os
import random
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
import logging
import pickle

# Настройка логирования
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Инициализация бота
TOKEN = '7305892783:AAEPYSCoF2PQuUxdTToS1zlEYvR9yZv4gjs'
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

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

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    logger.debug("Received /start command")
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("Рассылка", callback_data="mailing"))
    markup.row(types.InlineKeyboardButton("Группы", callback_data="groups"))
    await message.answer("Привет! Выберите действие:", reply_markup=markup)
    logger.debug("Sent start message with markup")

@dp.callback_query_handler(lambda c: True)
async def callback_query(call: types.CallbackQuery):
    logger.debug(f"Received callback query with data: {call.data}")
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

async def show_mailing_options(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("Всем", callback_data="mailing_100"))
    markup.row(types.InlineKeyboardButton("50%", callback_data="mailing_50"))
    markup.row(types.InlineKeyboardButton("10%", callback_data="mailing_10"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    await message.edit_text("Выберите получателей рассылки:", reply_markup=markup)

async def ask_for_mailing_text(message: types.Message, percentage: str):
    await message.edit_text(f"Введите текст для рассылки {percentage}% участников:")
    await dp.current_state(user=message.chat.id).set_state('waiting_for_mailing_text')
    await dp.current_state(user=message.chat.id).update_data(percentage=percentage)

@dp.message_handler(state='waiting_for_mailing_text')
async def process_mailing_text(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        percentage = data['percentage']
    mailing_text = message.text
    mailing_data[message.chat.id] = {"text": mailing_text, "percentage": percentage}
    save_data()
    await state.finish()
    await show_mailing_actions(message)

async def show_mailing_actions(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("Начать рассылку", callback_data="start_mailing"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    await message.answer("Выберите действие:", reply_markup=markup)

async def select_group_for_mailing(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    for group_id, group_info in groups.items():
        markup.row(types.InlineKeyboardButton(group_info['title'], callback_data=f"select_group_{group_id}"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    await message.edit_text("Выберите группу для рассылки:", reply_markup=markup)

async def start_mailing(message: types.Message, group_id: int):
    chat_id = message.chat.id
    if chat_id not in mailing_data:
        await message.answer("Ошибка: данные для рассылки не найдены.")
        return

    mailing_info = mailing_data[chat_id]
    percentage = int(mailing_info["percentage"])
    text = mailing_info["text"]

    await message.answer(f"Начинаем рассылку {percentage}% участников в выбранную группу...")

    group_info = groups[group_id]
    members = list(group_info['members'])
    num_recipients = int(len(members) * percentage / 100)
    recipients = random.sample(members, num_recipients)

    sent_message = await bot.send_message(group_id, text)

    try:
        while True:
            updated_text = ""
            for i, char in enumerate(text):
                if i < len(recipients):
                    updated_text += f"[{char}](tg://user?id={recipients[i]})"
                else:
                    updated_text += char

            await bot.edit_message_text(updated_text, group_id, sent_message.message_id, parse_mode='Markdown')
            await asyncio.sleep(0.1)

            if all(char.isalnum() or char.isspace() for char in updated_text):
                break
    except Exception as e:
        logger.error(f"Ошибка при обновлении сообщения: {e}")

    await message.answer("Рассылка завершена!")
    del mailing_data[chat_id]
    save_data()

async def show_groups(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    for group_id, group_info in groups.items():
        markup.row(types.InlineKeyboardButton(group_info['title'], callback_data=f"group_{group_id}"))
    markup.row(types.InlineKeyboardButton("🔙 Назад", callback_data="back"))
    await message.edit_text("Выберите группу:", reply_markup=markup)

async def show_group_info(message: types.Message, group_id: int):
    group_info = groups[group_id]
    info_text = f"Информация о группе:\n\nНазвание: {group_info['title']}\nID: {group_id}\nКоличество участников: {len(group_info['members'])}"
    markup = types.InlineKeyboardMarkup()
    markup.row(types.InlineKeyboardButton("🔙 Назад к группам", callback_data="groups"))
    await message.edit_text(info_text, reply_markup=markup)

@dp.my_chat_member_handler()
async def handle_my_chat_member(message: types.ChatMemberUpdated):
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

async def update_group_members(group_id: int):
    try:
        members = await bot.get_chat_members_count(group_id)
        groups[group_id]['members'] = set(range(members))  # Просто для примера, так как мы не можем получить реальные ID
        save_data()
    except Exception as e:
        logger.error(f"Ошибка при обновлении списка участников группы {group_id}: {e}")

@dp.message_handler(content_types=['new_chat_members'])
async def handle_new_chat_members(message: types.Message):
    group_id = message.chat.id
    if group_id in groups:
        for new_member in message.new_chat_members:
            groups[group_id]['members'].add(new_member.id)
        save_data()

@dp.message_handler(content_types=['left_chat_member'])
async def handle_left_chat_member(message: types.Message):
    group_id = message.chat.id
    if group_id in groups:
        groups[group_id]['members'].discard(message.left_chat_member.id)
        save_data()

if __name__ == '__main__':
    from aiogram import executor
    logger.info("Starting bot")
    executor.start_polling(dp, skip_updates=True)