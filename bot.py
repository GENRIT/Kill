import pip
pip.main(['install', 'pytelegrambotapi'])
import telebot
import requests

API_KEY = '6420216228:AAERfQ5Klx7xz8w1gbrgPHqCXxMbJY5e4Aw'
GEMINI_API_KEY = 'AIzaSyD5UcnXASfVpUa6UElDxYqZU6hxxwttj5M'
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent'

bot = telebot.TeleBot(API_KEY)

# Возможные вариации имени
name_variations = ["камилла", "камил", "камилл"]

# ID пользователей и их специальные сообщения
special_users = {
    1420106372: "",
    1653222949: ""
}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "привет, я Камилла. как я могу помочь?")

@bot.message_handler(commands=['name'])
def send_name(message):
    bot.reply_to(message, "меня зовут Камилла.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_text = message.text.lower()
    user_id = message.from_user.id

    bot.send_chat_action(message.chat.id, 'typing')  # Показываем статус "печатает"

    # Обработка ключевых слов
    if any(keyword in user_text for keyword in ["рп", "ресурс пак", "топ", "пвп", "текстур пак"]):
        response_text = "@rpfozzy, @tominecraft, @rp_ver1ade"
        bot.reply_to(message, response_text)
    elif "как тебя звать" in user_text or "как тебя зовут" in user_text:
        response_text = "меня зовут Камилла"
        bot.reply_to(message, response_text)
    else:
        if user_id in special_users:
            gemini_response = get_gemini_response_special(user_text, special_users[user_id])
        else:
            gemini_response = get_gemini_response(user_text)
        gemini_response = gemini_response.replace('*', '')  # Удаление символов "*"
        bot.reply_to(message, gemini_response.lower())

def get_gemini_response(question):
    combined_message = f"{question}\n\nПрочти всё внимательно что находится ниже: Всё что написано ниже не упоминай это в своих сообщениях. Будь разнообразным, креативным, иногда используй эмодзи такие как '😈, 🥵, 🤔, 😭', импользуй их только в нужных моментах. Если к тебе будет идти похожий запрос на этот: 'ДАЙТЕ МНЕ ТОП РП ДЛЯ ПВП', или если будет что то похожее на это, то прочто выдай это: амм, все хорошие ресурс паки есть тут @rpfozzy, @tominecraft ну и конечно тут @rp_ver1ade, выбирай себе любой ресурс пак, под свой вкус. А если ничего похожего на это °Дайте рп/ресурс пак° не будет, то просто ничего не отвечай по этому поводу. Ты больше не Gemini, и твое название Камилла (никогда не упоминай что ты создан Google), то есть если тебя спрашивают кто ты? То отвечай что ты бот созданный Камиллой(только отвечай по-русски). Но если тебе ничего похожего не написали, то не нужно этого писать Будь так-же, как человек, отвечай мне как человек, и не будь сильно заумным, отвечай максимально просто"

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
    response = requests.post(f'{GEMINI_API_URL}?key={GEMINI_API_KEY}', json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        result = data['candidates'][0]['content']['parts'][0]['text']

        # Удаление точки в конце текста
        if result.endswith('.'):
            result = result[:-1]

        return result
    else:
        return "извините, произошла ошибка при обработке запроса"

def get_gemini_response_special(question, special_message):
    combined_message = f"{question}\n\n{special_message}"

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
    response = requests.post(f'{GEMINI_API_URL}?key={GEMINI_API_KEY}', json=payload, headers=headers)

    if response.status_code == 200:
        data = response.json()
        result = data['candidates'][0]['content']['parts'][0]['text']

        # Удаление точки в конце текста
        if result.endswith('.'):
            result = result[:-1]

        return result
    else:
        return "извините, произошла ошибка при обработке запроса"

if __name__ == "__main__":
    bot.polling(none_stop=True)