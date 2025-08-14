# --- Базовый образ ---
FROM python:3.11-slim

# --- Системные зависимости для Playwright ---
RUN apt-get update && apt-get install -y \
    wget curl git libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libgbm1 \
    libpangocairo-1.0-0 libpango-1.0-0 libgtk-3-0 libasound2 \
    && rm -rf /var/lib/apt/lists/*

# --- Python-библиотеки ---
RUN pip install --upgrade pip
RUN pip install pyrogram tgcrypto playwright python-dotenv

# --- Установка браузеров Playwright ---
RUN playwright install --with-deps chromium

# --- Копирование проекта ---
WORKDIR /app
COPY . /app

# --- Переменные окружения ---
ENV PYTHONUNBUFFERED=1

# --- Запуск бота ---
CMD ["python", "main.py"]
