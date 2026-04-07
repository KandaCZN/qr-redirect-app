from flask import Flask, request, render_template_string
import requests
import pandas as pd
import os
from io import BytesIO

app = Flask(__name__)

# --- НАСТРОЙКИ ---
# Эти переменные берутся из Environment Variables в Render
YANDEX_TOKEN = os.environ.get("YANDEX_TOKEN")
FILE_KEY = os.environ.get("FILE_KEY")  # Ключ файла (из ссылки)
SHEET_NAME = os.environ.get("SHEET_NAME", "Sheet1")  # Имя листа
ID_COLUMN = os.environ.get("ID_COLUMN", "C")  # Столбец для поиска (C)
# ------------------

@app.route('/search')
def search():
    id_to_find = request.args.get('id')
    if not id_to_find:
        return "Ошибка: Не указан параметр ?id=..."

    try:
        # 1. Сначала получаем ссылку на скачивание файла
        public_url = f"https://disk.yandex.ru/i/{FILE_KEY}"
        api_url = f"https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={public_url}"
        headers = {"Authorization": f"OAuth {YANDEX_TOKEN}"}

        # Запрашиваем ссылку на скачивание
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()  # Проверим, нет ли ошибок HTTP

        # Извлекаем ссылку на скачивание
        download_url = response.json().get("href")

        # 2. Скачиваем файл в память
        file_response = requests.get(download_url)
        df = pd.read_excel(BytesIO(file_response.content), sheet_name=SHEET_NAME)

        # 3. Ищем ID в нужном столбце
        # Приводим оба значения к одному типу и убираем пробелы для точности
        mask = df[ID_COLUMN].astype(str).str.strip() == str(id_to_find).strip()

        if mask.any():  # Если нашли хотя бы одну строку
            # Находим первую подходящую строку
            row_index = df[mask].index[0]
            row_number = row_index + 1  # Нумерация строк в Excel начинается с 1

            # 4. Формируем ссылку на ячейку
            final_url = f"https://disk.yandex.ru/i/{FILE_KEY}#cell:{SHEET_NAME}!{ID_COLUMN}{row_number}"

            # 5. Генерируем HTML-страницу с редиректом
            html = f"""
            <html>
              <head><meta http-equiv="refresh" content="0; url={final_url}" /></head>
              <body style="font-family: sans-serif; text-align:center; padding-top:100px;">
                <h2>Объект №{id_to_find} найден!</h2>
                <p>Перенаправляем к строке {row_number}...</p>
                <a href="{final_url}" style="display:inline-block; padding:10px 20px; background:#4285f4; color:white; text-decoration:none; border-radius:5px;">
                  Нажмите, если переход не произошел
                </a>
              </body>
            </html>
            """
            return html

        # Если ничего не найдено
        return f"Объект №{id_to_find} не найден в столбце {ID_COLUMN}."

    except requests.exceptions.RequestException as e:
        return f"Произошла ошибка при обращении к API: {str(e)}"
    except Exception as e:
        return f"Произошла внутренняя ошибка: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0')
