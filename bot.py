import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters, CallbackContext
import requests

# Логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Конфигурация
GEMINI_API_KEY = 'AIzaSyD5UcnXASfVpUa6UElDxYqZU6hxxwttj5M'
TELEGRAM_BOT_TOKEN = '7416204500:AAHfx67vXqCgcrwpp2uzoXEIvC2fwiQSp5o'
TELEGRAM_CHAT_ID = '@Cothid'

def start(update: Update, context: CallbackContext):
    """Отправляет сообщение с инлайн-кнопкой при вводе команды /start."""
    keyboard = [[InlineKeyboardButton("Публиковать", callback_data='publish')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text('Нажмите "Публиковать", чтобы отправить запрос к API Gemini и опубликовать сообщение в канал.', reply_markup=reply_markup)

def button(update: Update, context: CallbackContext):
    """Обрабатывает нажатие на инлайн-кнопку."""
    query = update.callback_query
    query.answer()
    
    if query.data == 'publish':
        query.edit_message_text(text="Введите ваш запрос для публикации.")
        context.user_data['awaiting_input'] = True

def handle_message(update: Update, context: CallbackContext):
    """Обрабатывает ввод пользователя и публикует сообщение в канал."""
    if context.user_data.get('awaiting_input'):
        prompt = update.message.text
        response_text = get_gemini_response(prompt)
        
        post_to_telegram(response_text)
        update.message.reply_text("Сообщение опубликовано!")
        context.user_data['awaiting_input'] = False
    else:
        update.message.reply_text("Введите команду /start для начала.")

def get_gemini_response(prompt):
    """Отправляет запрос к API Gemini и получает ответ."""
    url = f"https://api.gemini.com/v1/models/1.5-pro/generate"
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt,
        "max_tokens": 100
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        return response.json().get('text', '')
    else:
        return "Ошибка при генерации текста."

def post_to_telegram(message):
    """Публикует сообщение в Telegram канал."""
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=message)

def main():
    """Запускает бота."""
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)
    
    dp = updater.dispatcher

    # Команды
    dp.add_handler(CommandHandler("start", start))

    # Обработчики сообщений и нажатий кнопок
    dp.add_handler(CallbackQueryHandler(button))
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))

    # Запуск бота
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
