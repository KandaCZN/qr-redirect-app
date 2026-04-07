from flask import Flask, request, render_template_string
import requests
import os

app = Flask(__name__)

# --- НАСТРОЙКИ ---
# Эти переменные мы будем задавать через Environment Variables в Render
YANDEX_TOKEN = os.environ.get("YANDEX_TOKEN")
FILE_KEY = os.environ.get("FILE_KEY") # Ключ файла (из ссылки)
SHEET_NAME = os.environ.get("SHEET_NAME", "Table 1") # Имя листа
ID_COLUMN = os.environ.get("ID_COLUMN", "C") # Столбец для поиска (C)
# ------------------

@app.route('/search')
def search():
    id_to_find = request.args.get('id')
    if not id_to_find:
        return "Ошибка: Не указан параметр ?id=..."

    try:
        # 1. Формируем запрос к API поиска
        url = "https://cloud-api.yandex.net/v1/disk/search/resources"
        headers = {"Authorization": f"OAuth {YANDEX_TOKEN}"}
        
        # Параметры поиска:
        # - query: ищем точное значение в формате "sheet_name!C123"
        # Но так как мы не знаем номер строки, ищем просто по значению в столбце
        params = {
            "query": f"{id_to_find}",
            "file_extensions": "xlsx",
            "limit": 1,
            "offset": 0,
            "sort": "modified"
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status() # Проверим, нет ли ошибок HTTP

        data = response.json()
        
        # 2. Проверяем, найдены ли результаты
        if data.get("items") and len(data["items"]) > 0:
            found_item = data["items"][0]
            
            # Извлекаем номер строки из пути (path)
            # path выглядит примерно так: 'disk:/Файлы/Таблица.xlsx/Sheet1!C42'
            path = found_item.get("path", "")
            
            # Находим номер строки (все символы после буквы столбца)
            import re
            match = re.search(rf"{ID_COLUMN}(\d+)", path)
            
            if match:
                row_number = match.group(1)
                
                # 3. Формируем ссылку на таблицу с якорем на нужную ячейку
                final_url = f"https://disk.yandex.ru/i/{FILE_KEY}#cell:{SHEET_NAME}!{ID_COLUMN}{row_number}"
                
                # Возвращаем HTML-страницу с редиректом
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

        # Если ничего не найдено или не удалось извлечь номер строки
        return f"Объект №{id_to_find} не найден в столбце {ID_COLUMN}."

    except requests.exceptions.RequestException as e:
        return f"Произошла ошибка при обращении к API: {str(e)}"
    except Exception as e:
        return f"Произошла внутренняя ошибка: {str(e)}"

if __name__ == '__main__':
    app.run()