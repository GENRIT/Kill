from aiogram import Bot, Dispatcher, executor, types
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Замените на ваш токен Telegram бота
TOKEN = '7332817569:AAG3l2IJugs0geomZCaT9k-YoVcwBXcHAgs'

# URL сайта с ChatGPT (замените на нужный URL)
CHATGPT_URL = 'https://ChatGPT.com/chat'

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Инициализация драйвера Selenium
driver = webdriver.Chrome()  # Убедитесь, что у вас установлен ChromeDriver

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.reply("Привет! чем могу помочь?")

@dp.message_handler()
async def echo_all(message: types.Message):
    response = send_to_chatgpt(message.text)
    await message.reply(response)

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

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)