from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import requests
import logging
import time
import os
from collections import defaultdict

API_KEY = '7147982361:AAGL-P3mQ7ETcK5qBu3LwRVINnLAT9gMISw'
GEMINI_API_KEY = 'AIzaSyD5UcnXASfVpUa6UElDxYqZU6hxxwttj5M'
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'

bot = telebot.TeleBot(API_KEY)
user_count = set()
user_request_count = defaultdict(int)
request_limit = 5

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ADDITIONAL_TEXT_PRIVATE = (
    "Я твой хладнокровный ассистент по текстур пакам, РП и модификациям для Minecraft. "
    "Не размениваюсь на болтовню. Вопросы – коротко и по делу. "
    "Вся информация по проекту в Telegram @tominecraft и на сайте OxyMod (Oxymod.netlify.app). "
    "Для рекламы или других вопросов пиши напрямую в бота @OxyMod_bot. "
    "Минимум слов – максимум конкретики."
)

def create_ad_watch_link(user_id):
    unique_url = f"https://oxymod.netlify.app/ads?user_id={user_id}"
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("Смотреть рекламу", url=unique_url))
    return keyboard

@bot.message_handler(commands=['start'])
def send_welcome(message):
    if message.chat.type != 'private':
        return
    user_count.add(message.from_user.id)
    bot.reply_to(message, "Я Камилла. Вопросы по делу – отвечу. Всё, что нужно – получишь без лишних слов.")

@bot.message_handler(commands=['stats'])
def send_stats(message):
    if message.chat.type != 'private':
        return
    bot.reply_to(message, f"Количество уникальных пользователей: {len(user_count)}")

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    if message.chat.type != 'private':
        return
    user_count.add(message.from_user.id)

    if user_request_count[message.from_user.id] >= request_limit:
        bot.reply_to(message, "Достигнут лимит запросов. Чтобы получить еще 5 запросов, посмотрите рекламу.", reply_markup=create_ad_watch_link(message.from_user.id))
        return

    file_id = message.photo[-1].file_id
    file_info = bot.get_file(file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    image_path = f"temp_{file_id}.jpg"
    with open(image_path, 'wb') as new_file:
        new_file.write(downloaded_file)

    response = get_gemini_image_response(image_path)

    os.remove(image_path)

    bot.reply_to(message, response)
    user_request_count[message.from_user.id] += 1

@bot.message_handler(func=lambda message: message.text.lower() == 'ad_watched')
def handle_ad_watched(message):
    if message.chat.type != 'private':
        return
    user_id = message.from_user.id
    user_request_count[user_id] = 0  # Сбрасываем счетчик запросов до 0
    bot.reply_to(message, "Реклама просмотрена. Вам доступно 5 новых запросов.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    if message.chat.type != 'private':
        return

    user_id = message.from_user.id
    user_count.add(user_id)

    if user_request_count[user_id] >= request_limit:
        bot.reply_to(message, "Достигнут лимит запросов. Чтобы получить еще 5 запросов, посмотрите рекламу.", reply_markup=create_ad_watch_link(user_id))
        return

    bot.send_chat_action(message.chat.id, 'typing')

    user_text = message.text.lower()

    response = get_gemini_response(user_text, ADDITIONAL_TEXT_PRIVATE)
    bot.reply_to(message, response)
    user_request_count[user_id] += 1

def get_gemini_response(question, additional_text):
    combined_message = f"{question}\n\n{additional_text}"

    payload = {
        "contents": [{
            "parts": [{
                "text": combined_message
            }]
        }]
    }
    headers = {
        'Content-Type': 'application/json',
    }
    try:
        response = requests.post(f'{GEMINI_API_URL}?key={GEMINI_API_KEY}', json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        result = data['candidates'][0]['content']['parts'][0]['text']

        if result.endswith('.'):
            result = result[:-1]

        return result
    except Exception as e:
        logging.error(f"Ошибка при обращении к Gemini API: {e}")
        return "Ошибка при обработке запроса."

def get_gemini_image_response(image_path):
    with open(image_path, 'rb') as image_file:
        image_data = image_file.read()

    headers = {
        'Content-Type': 'application/json',
    }
    payload = {
        'requests': [
            {
                'image': {
                    'content': image_data
                },
                'features': [
                    {
                        'type': 'LABEL_DETECTION',
                    }
                ],
            }
        ]
    }
    try:
        response = requests.post(f'{GEMINI_API_URL}?key={GEMINI_API_KEY}', json=payload, headers=headers)
        response.raise_for_status()
        data = response.json()
        labels = data['responses'][0]['labelAnnotations']
        label_descriptions = [label['description'] for label in labels]
        return f"На изображении вижу: {', '.join(label_descriptions)}"
    except Exception as e:
        logging.error(f"Ошибка при обработке изображения через Gemini API: {e}")
        return "Ошибка при обработке изображения."

if __name__ == "__main__":
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            logging.error(f"Ошибка в основном цикле: {e}")
            time.sleep(15)