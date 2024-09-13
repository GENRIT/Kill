import os
import asyncio
import random
from aiogram import Bot, Dispatcher, types
from aiogram.utils import exceptions
import logging
import pickle

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
TOKEN = '7305892783:AAEPYSCoF2PQuUxdTToS1zlEYvR9yZv4gjs'
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Словарь для хранения данных о группах
groups = {}

# Функция для сохранения данных
def save_data():
    with open('bot_data.pkl', 'wb') as f:
        pickle.dump(groups, f)

# Функция для загрузки данных
def load_data():
    global groups
    if os.path.exists('bot_data.pkl'):
        with open('bot_data.pkl', 'rb') as f:
            groups = pickle.load(f)

# Загрузка данных при запуске
load_data()

@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("Начать рассылку", callback_data="start_mailing"))
    await message.answer("Привет! Нажмите кнопку, чтобы начать рассылку:", reply_markup=markup)

@dp.callback_query_handler(lambda c: c.data == 'start_mailing')
async def start_mailing(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)
    await bot.send_message(callback_query.from_user.id, "Введите текст для рассылки:")
    await dp.current_state(user=callback_query.from_user.id).set_state('waiting_for_text')

@dp.message_handler(state='waiting_for_text')
async def process_mailing_text(message: types.Message):
    mailing_text = message.text
    chat_id = message.chat.id
    
    if chat_id not in groups:
        await message.answer("Ошибка: группа не найдена.")
        return

    group_info = groups[chat_id]
    members = list(group_info['members'])
    
    sent_message = await message.answer("Подготовка к рассылке...")
    
    iterations = 0
    max_iterations = 100  # Максимальное количество итераций
    
    while iterations < max_iterations:
        updated_text = ""
        for char in mailing_text:
            if members:
                user_id = random.choice(members)
                updated_text += f"[{char}](tg://user?id={user_id})"
            else:
                updated_text += char
        
        try:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=sent_message.message_id,
                text=updated_text,
                parse_mode="Markdown"
            )
        except exceptions.MessageNotModified:
            pass
        except Exception as e:
            logger.error(f"Ошибка при обновлении сообщения: {e}")
        
        await asyncio.sleep(0.1)
        iterations += 1
    
    # Отправка финального сообщения без упоминаний
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=sent_message.message_id,
        text=mailing_text
    )
    
    await message.answer("Рассылка завершена!")

@dp.my_chat_member_handler()
async def handle_my_chat_member(update: types.ChatMemberUpdated):
    if update.new_chat_member.status == 'administrator':
        group_id = update.chat.id
        groups[group_id] = {
            'title': update.chat.title,
            'members': set(),
            'owner_id': update.from_user.id
        }
        save_data()
        await bot.send_message(group_id, "Спасибо за назначение меня администратором! Я готов к работе.")
        await update_group_members(group_id)
    elif update.new_chat_member.status == 'member':
        await bot.send_message(update.chat.id, "Для корректной работы мне нужны права администратора.")

async def update_group_members(group_id):
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
    executor.start_polling(dp, skip_updates=True)