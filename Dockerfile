# --- Базовый Python образ ---
FROM python:3.11-slim

# --- Рабочая директория ---
WORKDIR /app

# --- Устанавливаем системные зависимости для Chromium ---
RUN apt-get update && apt-get install -y \
    libxkbcommon0 \
    libx11-6 \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libdbus-1-3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    libatspi2.0-0 \
    libgtk-3-0 \
    wget \
    curl \
    unzip \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

# --- Копируем requirements и устанавливаем зависимости ---
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# --- Устанавливаем Playwright и Chromium ---
RUN pip install playwright
RUN playwright install chromium

# --- Копируем весь проект ---
COPY . .

# --- Запуск приложения ---
CMD ["python", "main.py"]
