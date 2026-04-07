# Базовый образ с Python 3.11
FROM python:3.11-slim-bullseye

# Рабочая директория
WORKDIR /app

# Копируем файлы проекта
COPY . /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt \
    && pip install --only-binary=pandas pandas

# Экспонируем порт
EXPOSE 8080

# Запускаем приложение
CMD ["flask", "run", "--host=0.0.0.0", "--port=8080"]
