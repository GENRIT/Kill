import telebot
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
from flask import Flask

# Замените на ваш токен Telegram бота
TOKEN = '7332817569:AAG3l2IJugs0geomZCaT9k-YoVcwBXcHAgs'

# URL сайта с ChatGPT (замените на нужный URL)
CHATGPT_URL = 'https://ChatGPT.com/chat'

bot = telebot.TeleBot(TOKEN)

# Инициализация драйвера Selenium с использованием webdriver-manager
chrome_options = Options()
chrome_options.add_argument("--headless")  # Запуск Chrome в фоновом режиме
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
service = Service(ChromeDriverManager().install())
driver = webdriver.Chrome(service=service, options=chrome_options)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! Я бот, который может общаться с ChatGPT. Просто отправь мне сообщение, и я передам его ChatGPT.")

@bot.message_handler(func=lambda message: True)
def echo_all(message):
    response = send_to_chatgpt(message.text)
    bot.reply_to(message, response)

def send_to_chatgpt(message):
    try:
        # Открываем страницу ChatGPT
        driver.get(CHATGPT_URL)

        # Ждем, пока не появится поле ввода
        input_box = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//textarea[contains(@placeholder, 'Сообщить ChatGPT')]"))
        )

        # Вводим сообщение
        input_box.send_keys(message)

        # Находим и нажимаем кнопку отправки
        send_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Отправить сообщение']"))
        )
        send_button.click()

        # Ждем ответа от ChatGPT
        response_element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'markdown')]"))
        )

        # Получаем текст ответа
        response = response_element.text

        return response
    except Exception as e:
        return f"Произошла ошибка при обращении к ChatGPT: {str(e)}"

# Создаем экземпляр Flask приложения
app = Flask(__name__)

@app.route('/')
def home():
    return "Telegram Bot is running!"

if __name__ == '__main__':
    # Запускаем Flask приложение в отдельном потоке
    import threading
    threading.Thread(target=app.run, kwargs={'host': '0.0.0.0', 'port': 80, 'debug': True, 'use_reloader': False}).start()

    # Запускаем бота
    bot.polling(none_stop=True)