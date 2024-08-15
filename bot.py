import telebot
import requests
import time
import logging
from PIL import Image, ImageDraw, ImageFont
import os

API_KEY = '7416204500:AAHfx67vXqCgcrwpp2uzoXEIvC2fwiQSp5o'
GEMINI_API_KEY = 'AIzaSyD5UcnXASfVpUa6UElDxYqZU6hxxwttj5M'
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'
CHANNEL_ID = '1803184345'  # Замените на ID вашего канала

bot = telebot.TeleBot(API_KEY)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def generate_gemini_text():
    # Текст запроса для Gemini API
    prompt = "Тема канала Психология на разные темы, например о любви, о девушках, о парнях, о музыке и т.п, о том о сём многим будет лень читать, так что пиши как можно меньше, но с большей конкретикой, без воды, пиши как жёсткий хлоднорокровный дикий мужик"
    
    payload = {
        "prompt": prompt,
        "temperature": 0.7,
        "maxOutputTokens": 60
    }
    
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {GEMINI_API_KEY}'
    }
    
    response = requests.post(GEMINI_API_URL, json=payload, headers=headers)
    
    if response.status_code == 200:
        result = response.json()
        return result['candidates'][0]['output']
    else:
        logging.error(f"Ошибка при обращении к Gemini API: {response.status_code} - {response.text}")
        return "Ошибка при генерации текста."

def add_text_to_image(image_path, text):
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)
    
    # Настройка шрифта и размера текста
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"  # Убедитесь, что путь к шрифту корректный
    font_size = 24
    font = ImageFont.truetype(font_path, font_size)
    
    # Размер изображения и текста
    width, height = image.size
    text_width, text_height = draw.textsize(text, font=font)
    
    # Позиция текста на изображении (по центру)
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2
    
    # Цвет текста и обводка
    outline_color = "black"
    draw.text((text_x-2, text_y-2), text, font=font, fill=outline_color)
    draw.text((text_x+2, text_y-2), text, font=font, fill=outline_color)
    draw.text((text_x-2, text_y+2), text, font=font, fill=outline_color)
    draw.text((text_x+2, text_y+2), text, font=font, fill=outline_color)
    
    # Основной текст
    draw.text((text_x, text_y), text, font=font, fill="white")
    
    # Сохранение нового изображения
    output_path = "output_image.jpg"
    image.save(output_path)
    
    return output_path

def publish_post():
    try:
        # Генерация текста через API Gemini
        text = generate_gemini_text()
        
        # Добавление текста на изображение
        image_url = 'https://graph.org/file/0024dfb620c1075941d00.jpg'
        image_path = "image.jpg"
        response = requests.get(image_url)
        with open(image_path, 'wb') as f:
            f.write(response.content)
        
        output_image_path = add_text_to_image(image_path, text)
        
        # Публикация в Telegram канал
        with open(output_image_path, 'rb') as photo:
            bot.send_photo(CHANNEL_ID, photo, caption=text)
        
        # Удаление временных файлов
        os.remove(image_path)
        os.remove(output_image_path)
        
    except Exception as e:
        logging.error(f"Ошибка при публикации поста: {e}")

if __name__ == "__main__":
    while True:
        publish_post()
        time.sleep(15)  # Публикация каждые 15 секунд
