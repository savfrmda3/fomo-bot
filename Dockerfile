# --- Базовый Python образ ---
FROM python:3.12-slim

# --- Установка системных зависимостей для Chromium и Playwright ---
RUN apt-get update && apt-get install -y \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxcb1 \
    libxkbcommon0 \
    libatspi2.0-0 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    wget \
    curl \
    unzip \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# --- Рабочая директория ---
WORKDIR /app

# --- Копируем requirements и устанавливаем зависимости ---
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# --- Устанавливаем Playwright и Chromium ---
RUN pip install --no-cache-dir playwright
RUN playwright install --with-deps chromium

# --- Копируем весь проект ---
COPY . .

# --- Переменные окружения ---
ENV PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1
# Для unbuffered output в логи
ENV PYTHONUNBUFFERED=1

# --- Запуск приложения ---
CMD ["python", "main.py"]
