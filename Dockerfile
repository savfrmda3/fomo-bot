FROM python:3.12-slim

# --- Системные зависимости для сборки Python пакетов и Chromium ---
RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
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

WORKDIR /app

# --- Копируем и устанавливаем зависимости ---
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# --- Устанавливаем Playwright и Chromium ---
RUN pip install --no-cache-dir playwright && playwright install --with-deps chromium

# --- Копируем проект ---
COPY . .

CMD ["python", "main.py"]
