import telebot
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Замените на ваш токен Telegram бота
TOKEN = 'ваш_токен_telegram_бота'

# URL сайта с ChatGPT (замените на нужный URL)
CHATGPT_URL = 'https://ChatGPT.com/chat'

bot = telebot.TeleBot(TOKEN)

# Инициализация драйвера Selenium
driver = webdriver.Chrome()  # Убедитесь, что у вас установлен ChromeDriver

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "Привет! чем могу помочь?")

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
        input_box.send_keys(Keys.RETURN)
        
        # Ждем ответа от ChatGPT
        response_element = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'chatgpt-response')]"))
        )
        
        # Получаем текст ответа
        response = response_element.text
        
        return response
    except Exception as e:
        return f"Мне очень мало, но мне закрыли рот: {str(e)}"

# Запускаем бота
bot.polling()