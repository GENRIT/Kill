import os
import random
import asyncio
import logging
import pickle
from telegram import Update, ReplyKeyboardMarkup, ParseMode
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, ConversationHandler

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Инициализация бота
TOKEN = '7305892783:AAEPYSCoF2PQuUxdTToS1zlEYvR9yZv4gjs'

# Словарь для хранения данных о группах
groups = {}

# Словарь для хранения данных о рассылке
mailing_data = {}

# Состояния для ConversationHandler
SELECTING_PERCENTAGE, ENTERING_TEXT, SELECTING_GROUP = range(3)

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

def start(update: Update, context: CallbackContext) -> None:
    update.message.reply_text("Привет! Для начала работы используйте команды:\n/mailing - Рассылка\n/groups - Группы")

def show_mailing_options(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [['Всем', '50%', '10%'], ['🔙 Назад']]
    update.message.reply_text(
        "Выберите получателей рассылки:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return SELECTING_PERCENTAGE

def ask_for_mailing_text(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    percentage = 100 if text == 'Всем' else int(text.replace('%', ''))
    context.user_data['percentage'] = percentage
    update.message.reply_text(f"Введите текст для рассылки {percentage}% участников:")
    return ENTERING_TEXT

def process_mailing_text(update: Update, context: CallbackContext) -> int:
    mailing_text = update.message.text
    percentage = context.user_data['percentage']
    mailing_data[update.effective_user.id] = {"text": mailing_text, "percentage": percentage}
    save_data()
    reply_keyboard = [['Начать рассылку'], ['🔙 Назад']]
    update.message.reply_text(
        "Выберите действие:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return SELECTING_GROUP

def select_group_for_mailing(update: Update, context: CallbackContext) -> int:
    reply_keyboard = [[group_info['title'] for group_id, group_info in groups.items()], ['🔙 Назад']]
    update.message.reply_text(
        "Выберите группу для рассылки:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return ConversationHandler.END

async def start_mailing(update: Update, context: CallbackContext) -> None:
    group_title = update.message.text
    group_id = next(gid for gid, ginfo in groups.items() if ginfo['title'] == group_title)
    user_id = update.effective_user.id
    
    if user_id not in mailing_data:
        update.message.reply_text("Ошибка: данные для рассылки не найдены.")
        return

    mailing_info = mailing_data[user_id]
    percentage = int(mailing_info["percentage"])
    text = mailing_info["text"]

    update.message.reply_text(f"Начинаем рассылку {percentage}% участников в выбранную группу...")

    group_info = groups[group_id]
    members = list(group_info['members'])
    num_recipients = int(len(members) * percentage / 100)
    recipients = random.sample(members, num_recipients)

    sent_message = await context.bot.send_message(group_id, text)

    try:
        while True:
            updated_text = "".join(f"[{char}](tg://user?id={recipients[i]})" if i < len(recipients) else char for i, char in enumerate(text))

            await context.bot.edit_message_text(updated_text, group_id, sent_message.message_id, parse_mode=ParseMode.MARKDOWN)
            await asyncio.sleep(0.1)

            if all(char.isalnum() or char.isspace() for char in updated_text):
                break
    except Exception as e:
        logger.error(f"Ошибка при обновлении сообщения: {e}")

    update.message.reply_text("Рассылка завершена!")
    del mailing_data[user_id]
    save_data()

def show_groups(update: Update, context: CallbackContext) -> None:
    reply_keyboard = [[group_info['title'] for group_id, group_info in groups.items()], ['🔙 Назад']]
    update.message.reply_text(
        "Выберите группу:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )

def show_group_info(update: Update, context: CallbackContext) -> None:
    group_title = update.message.text
    group_id = next(gid for gid, ginfo in groups.items() if ginfo['title'] == group_title)
    group_info = groups[group_id]
    info_text = f"Информация о группе:\n\nНазвание: {group_info['title']}\nID: {group_id}\nКоличество участников: {len(group_info['members'])}"
    reply_keyboard = [['🔙 Назад к группам']]
    update.message.reply_text(
        info_text,
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )

def handle_my_chat_member(update: Update, context: CallbackContext) -> None:
    new_chat_member = update.my_chat_member.new_chat_member
    if new_chat_member.status == 'administrator':
        group_id = update.effective_chat.id
        groups[group_id] = {
            'title': update.effective_chat.title,
            'members': set(),
            'owner_id': update.effective_user.id
        }
        save_data()
        context.bot.send_message(update.effective_chat.id, "Спасибо за назначение меня администратором! Я готов к работе.")
        update_group_members(context, group_id)
    elif new_chat_member.status == 'member':
        context.bot.send_message(update.effective_chat.id, "Для корректной работы мне нужны права администратора.")

def update_group_members(context: CallbackContext, group_id: int) -> None:
    try:
        members = context.bot.get_chat_member_count(group_id)
        groups[group_id]['members'] = set(range(members))  # Просто для примера, так как мы не можем получить реальные ID
        save_data()
    except Exception as e:
        logger.error(f"Ошибка при обновлении списка участников группы {group_id}: {e}")

def handle_new_chat_members(update: Update, context: CallbackContext) -> None:
    group_id = update.effective_chat.id
    if group_id in groups:
        for new_member in update.message.new_chat_members:
            groups[group_id]['members'].add(new_member.id)
        save_data()

def handle_left_chat_member(update: Update, context: CallbackContext) -> None:
    group_id = update.effective_chat.id
    if group_id in groups:
        groups[group_id]['members'].discard(update.message.left_chat_member.id)
        save_data()

def main() -> None:
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('mailing', show_mailing_options)],
        states={
            SELECTING_PERCENTAGE: [MessageHandler(Filters.regex('^(Всем|50%|10%)$'), ask_for_mailing_text)],
            ENTERING_TEXT: [MessageHandler(Filters.text & ~Filters.command, process_mailing_text)],
            SELECTING_GROUP: [MessageHandler(Filters.regex('^Начать рассылку$'), select_group_for_mailing)]
        },
        fallbacks=[MessageHandler(Filters.regex('^🔙 Назад$'), start)]
    )

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(conv_handler)
    dp.add_handler(CommandHandler("groups", show_groups))
    dp.add_handler(MessageHandler(Filters.regex('^🔙 Назад к группам$'), show_groups))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, show_group_info))
    dp.add_handler(MessageHandler(Filters.status_update.new_chat_members, handle_new_chat_members))
    dp.add_handler(MessageHandler(Filters.status_update.left_chat_member, handle_left_chat_member))
    dp.add_handler(MessageHandler(Filters.status_update.chat_member, handle_my_chat_member))

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()