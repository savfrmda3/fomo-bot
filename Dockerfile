# Берём официальный Playwright образ с Python и Chromium
FROM mcr.microsoft.com/playwright/python:v1.43.0-focal

# Рабочая директория
WORKDIR /app

# Копируем зависимости и устанавливаем
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект (включая portalsmp)
COPY . .

# Указываем порт для Cloud Run
ENV PORT=8080

# Запуск бота через gunicorn (для HTTP endpoint)
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "main:app"]
