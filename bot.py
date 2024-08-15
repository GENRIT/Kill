import os
import time
import random
import logging
import requests
from PIL import Image, ImageDraw, ImageFont
from telebot import TeleBot

# Конфигурация
CONFIG = {
    'API_KEY': '7416204500:AAHfx67vXqCgcrwpp2uzoXEIvC2fwiQSp5o',
    'GEMINI_API_KEY': 'AIzaSyD5UcnXASfVpUa6UElDxYqZU6hxxwttj5M',
    'GEMINI_API_URL': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent',
    'CHANNEL_ID': '1803184345',
    'USER_ID': '1420106372',
    'DEFAULT_INTERVAL': 15,
    'FONT_PATH': "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    'FONT_SIZE': 24
}

# Инициализация бота и логгера
bot = TeleBot(CONFIG['API_KEY'])
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Глобальные переменные
publishing = False
interval = CONFIG['DEFAULT_INTERVAL']
cached_image_path = None

def generate_gemini_text():
    prompts = [
        "Психология отношений: о любви, о девушках, о парнях, о музыке и жизни. Кратко и по делу.",
        "Секреты психологии: что думают мужчины и женщины. Жёстко, коротко, без воды.",
        "Короткие советы по психологии: об отношениях, людях и музыке. Без лишних слов.",
        "Психология в действии: о том, что важно в жизни и отношениях. Конкретно и ясно."
    ]
    prompt = random.choice(prompts)
    
    payload = {
        "prompt": prompt,
        "temperature": 0.7,
        "maxOutputTokens": 60
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {CONFIG["GEMINI_API_KEY"]}'
    }
    
    try:
        response = requests.post(CONFIG['GEMINI_API_URL'], json=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        return result['candidates'][0]['output']
    except requests.RequestException as e:
        logging.error(f"Ошибка при обращении к Gemini API: {e}")
        return "Ошибка при генерации текста."

def add_text_to_image(image_path, topic, text):
    try:
        with Image.open(image_path) as image:
            draw = ImageDraw.Draw(image)
            font = ImageFont.truetype(CONFIG['FONT_PATH'], CONFIG['FONT_SIZE'])
            
            width, height = image.size
            text_width, text_height = draw.textsize(text, font=font)
            topic_width, topic_height = draw.textsize(topic, font=font)
            
            text_x = (width - text_width) // 2
            text_y = height - text_height - 10
            topic_x = (width - topic_width) // 2
            topic_y = 10
            
            outline_color = "black"
            text_color = "white"
            
            def draw_outlined_text(x, y, text, fill):
                for dx, dy in [(-2, -2), (2, -2), (-2, 2), (2, 2)]:
                    draw.text((x+dx, y+dy), text, font=font, fill=outline_color)
                draw.text((x, y), text, font=font, fill=fill)
            
            draw_outlined_text(topic_x, topic_y, topic, text_color)
            draw_outlined_text(text_x, text_y, text, text_color)
            
            output_path = "output_image.jpg"
            image.save(output_path)
            return output_path
    except Exception as e:
        logging.error(f"Ошибка при добавлении текста на изображение: {e}")
        return None

def delete_temp_files(*files):
    for file in files:
        if file and os.path.exists(file):
            try:
                os.remove(file)
                logging.info(f"Файл {file} удален.")
            except Exception as e:
                logging.error(f"Ошибка при удалении файла {file}: {e}")

def publish_post():
    global cached_image_path
    try:
        text = generate_gemini_text()
        topic = "Тема публикации"
        
        if cached_image_path:
            output_image_path = add_text_to_image(cached_image_path, topic, text)
            
            if output_image_path:
                with open(output_image_path, 'rb') as photo:
                    sent_message = bot.send_photo(CONFIG['USER_ID'], photo, caption=text)
                
                bot.forward_message(CONFIG['CHANNEL_ID'], CONFIG['USER_ID'], sent_message.message_id)
                delete_temp_files(output_image_path)
            else:
                bot.send_message(CONFIG['USER_ID'], text)
        else:
            bot.send_message(CONFIG['USER_ID'], "Пожалуйста, загрузите изображение для публикации.")
        
    except Exception as e:
        logging.error(f"Ошибка при публикации поста: {e}")
        bot.send_message(CONFIG['USER_ID'], f"Произошла ошибка при публикации поста: {e}")

@bot.message_handler(commands=['start'])
def start_publishing(message):
    global publishing
    if message.chat.id == int(CONFIG['USER_ID']):
        publishing = True
        bot.send_message(CONFIG['USER_ID'], "Публикация постов запущена.")
        while publishing:
            publish_post()
            time.sleep(interval)

@bot.message_handler(commands=['stop'])
def stop_publishing(message):
    global publishing
    if message.chat.id == int(CONFIG['USER_ID']):
        publishing = False
        bot.send_message(CONFIG['USER_ID'], "Публикация постов остановлена.")

@bot.message_handler(commands=['publish'])
def manual_publish(message):
    if message.chat.id == int(CONFIG['USER_ID']):
        publish_post()

@bot.message_handler(commands=['set_interval'])
def set_interval(message):
    global interval
    if message.chat.id == int(CONFIG['USER_ID']):
        try:
            new_interval = int(message.text.split()[1])
            interval = new_interval
            bot.send_message(CONFIG['USER_ID'], f"Интервал публикации установлен на {interval} секунд.")
        except (IndexError, ValueError):
            bot.send_message(CONFIG['USER_ID'], "Неверный формат команды. Используйте: /set_interval <секунды>")

@bot.message_handler(commands=['clear_cache'])
def clear_cache(message):
    global cached_image_path
    if message.chat.id == int(CONFIG['USER_ID']):
        delete_temp_files(cached_image_path)
        cached_image_path = None
        bot.send_message(CONFIG['USER_ID'], "Кэш изображений очищен.")

@bot.message_handler(content_types=['photo'])
def handle_image(message):
    global cached_image_path
    if message.chat.id == int(CONFIG['USER_ID']):
        try:
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            cached_image_path = "cached_image.jpg"
            
            with open(cached_image_path, 'wb') as new_file:
                new_file.write(downloaded_file)
            
            bot.send_message(CONFIG['USER_ID'], "Изображение получено и сохранено. Вы можете начать публикацию.")
        except Exception as e:
            logging.error(f"Ошибка при сохранении изображения: {e}")
            bot.send_message(CONFIG['USER_ID'], f"Ошибка при сохранении изображения: {e}")

if __name__ == "__main__":
    bot.polling(none_stop=True)