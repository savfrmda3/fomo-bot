# --- Используем официальный Python образ ---
FROM python:3.12-slim

# --- Обновляем систему и ставим нужные библиотеки для Playwright/Chromium ---
RUN apt-get update && apt-get install -y \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libxshmfence1 \
    wget \
    ca-certificates \
    fonts-liberation \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# --- Устанавливаем рабочую директорию ---
WORKDIR /app

# --- Копируем файлы проекта ---
COPY requirements.txt ./

# --- Ставим Python зависимости ---
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# --- Устанавливаем Playwright и Chromium ---
RUN pip install --no-cache-dir playwright && playwright install --with-deps chromium

# --- Копируем весь проект ---
COPY . .

# --- Запуск вашего скрипта ---
CMD ["python", "main.py"]
