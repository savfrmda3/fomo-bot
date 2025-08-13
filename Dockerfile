# --- Базовый образ с Python ---
FROM python:3.11-slim

# --- Установка системных зависимостей для Chromium ---
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnspr4 \
    libnss3 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libxcb1 \
    libxkbcommon0 \
    libasound2 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# --- Установка зависимостей Python ---
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Установка Playwright и Chromium ---
RUN playwright install chromium

# --- Копируем весь проект ---
COPY . .

# --- Запуск бота ---
CMD ["python", "main.py"]
