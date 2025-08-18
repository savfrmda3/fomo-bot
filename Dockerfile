# --- Базовый Python образ ---
FROM python:3.12-slim

# --- Установка системных зависимостей для Playwright ---
RUN apt-get update && apt-get install -y wget curl unzip && rm -rf /var/lib/apt/lists/*

# --- Рабочая директория ---
WORKDIR /app

# --- Копируем requirements и устанавливаем зависимости ---
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# --- Устанавливаем Playwright и Chromium ---
RUN pip install --no-cache-dir playwright
RUN playwright install-deps chromium && playwright install chromium

# --- Копируем весь проект ---
COPY . .

# --- Переменные окружения ---
ENV PYTHONUNBUFFERED=1

# --- Запуск приложения ---
CMD ["python", "main.py"]
