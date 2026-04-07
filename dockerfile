# Образ с Python 3.11 и старым GCC
FROM python:3.11-bookworm

# Рабочая директория
WORKDIR /app

# Копируем файлы проекта
COPY . /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Экспонируем порт
EXPOSE 8080

# Запускаем приложение
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]
