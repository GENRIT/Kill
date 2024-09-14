from flask import Flask, render_template, request, jsonify
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time

app = Flask(__name__)

# Настройка Selenium
chrome_options = Options()
chrome_options.add_argument("--headless")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    query = request.form['query']
    driver = webdriver.Chrome(options=chrome_options)
    driver.get(f"https://yandex.ru/search/?text={query}")

    results = []
    for i in range(15):
        try:
            result = driver.find_elements(By.CSS_SELECTOR, '.serp-item')[i]
            title = result.find_element(By.CSS_SELECTOR, '.organic__url-text').text
            link = result.find_element(By.CSS_SELECTOR, '.path__item').get_attribute('href')
            results.append({'title': title, 'link': link})
        except:
            break

    driver.quit()
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)