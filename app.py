from flask import Flask, request, render_template_string
import requests
import pandas as pd
import os
from io import BytesIO
import logging  # Импортируем модуль логирования

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# --- НАСТРОЙКИ ---
# Эти переменные берутся из Environment Variables в Render
YANDEX_TOKEN = os.environ.get("YANDEX_TOKEN")
FILE_KEY = os.environ.get("FILE_KEY")  # Ключ файла (из ссылки)
SHEET_NAME = os.environ.get("SHEET_NAME", "Sheet1")  # Имя листа
BASE_YANDEX_URL = f"https://disk.yandex.ru/i/{FILE_KEY}"  # Базовая ссылка на файл
# ------------------

@app.route('/search')
def search():
    logging.info("Начало обработки запроса")  # Логируем начало

    id_to_find = request.args.get('id')
    if not id_to_find:
        return "Ошибка: Не указан параметр ?id=..."

    try:
        # Скачиваем файл с Яндекс.Диска
        logging.info("Начинаем скачивание файла...")
        download_url = f"https://cloud-api.yandex.net/v1/disk/public/resources/download?public_key={BASE_YANDEX_URL}"
        headers = {"Authorization": f"OAuth {YANDEX_TOKEN}"}
        response = requests.get(download_url, headers=headers)
        download_link = response.json().get("href")

        # Читаем файл в память
        logging.info("Читаем файл в память...")
        file_response = requests.get(download_link)
        df = pd.read_excel(BytesIO(file_response.content), sheet_name=SHEET_NAME)

        # Выведем подробную информацию о таблице для диагностики
        logging.info(f"Список всех столбцов: {df.columns.values}")

        # Ищем значение во ВСЕЙ таблице
        logging.info(f"Поиск значения '{id_to_find}' во всей таблице...")

        # Преобразуем искомое значение в строку и убираем пробелы
        id_to_find_clean = str(id_to_find).strip()

        # Проходим по всем столбцам таблицы
        for column in df.columns:
            # Проверяем, есть ли совпадения в текущем столбце
            mask = df[column].astype(str).str.strip() == id_to_find_clean

            if mask.any():  # Если нашли хотя бы одно совпадение
                # Находим первую подходящую строку
                row_index = df[mask].index[0]
                row_number = row_index + 1  # Нумерация строк в Excel начинается с 1

                # Определяем букву столбца (Excel нумерует столбцы буквами)
                col_letter = chr(ord('A') + df.columns.get_loc(column))

                # Формируем ссылку на ячейку
                final_url = f"https://disk.yandex.ru/i/{FILE_KEY}#cell:{SHEET_NAME}!{col_letter}{row_number}"

                # Генерируем HTML-страницу с редиректом
                html = f"""
                <html>
                  <head><meta http-equiv="refresh" content="0; url={final_url}" /></head>
                  <body style="font-family: sans-serif; text-align:center; padding-top:100px;">
                    <h2>Объект №{id_to_find} найден в ячейке {col_letter}{row_number}!</h2>
                    <p>Перенаправляем к ячейке...</p>
                    <a href="{final_url}" style="display:inline-block; padding:10px 20px; background:#4285f4; color:white; text-decoration:none; border-radius:5px;">
                      Нажмите, если переход не произошел
                    </a>
                  </body>
                </html>
                """
                return html

        # Если ничего не найдено
        return f"Объект №{id_to_find} не найден в таблице."

    except requests.exceptions.RequestException as e:
        logging.error(f"Ошибка при обращении к API: {str(e)}")
        return f"Произошла ошибка при обращении к API: {str(e)}"
    except Exception as e:
        logging.error(f"Внутренняя ошибка: {str(e)}")
        return f"Произошла внутренняя ошибка: {str(e)}"

if __name__ == '__main__':
    app.run(host='0.0.0.0')
