# Используем свежий Python 3.11
FROM python:3.11-slim

# Устанавливаем зависимости для Playwright/браузеров
RUN apt-get update && apt-get install -y \
    curl \
    unzip \
    wget \
    gnupg \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# Создаем рабочую директорию
WORKDIR /app

# Сначала копируем только requirements.txt (чтобы кэшировать слои)
COPY requirements.txt ./

# Обновляем pip и ставим зависимости
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект
COPY . .

# Устанавливаем playwright и chromium
RUN pip install playwright
RUN playwright install --with-deps chromium

# Запускаем main.py
CMD ["python", "main.py"]
