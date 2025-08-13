# --- Используем официальный Python 3.11 ---
FROM python:3.11-slim

# --- Устанавливаем зависимости для Chromium ---
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libnss3 \
    libnspr4 \
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
    wget \
    curl \
    ca-certificates \
    fonts-liberation \
    lsb-release \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# --- Устанавливаем зависимости Python ---
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- Устанавливаем Playwright Browsers ---
RUN playwright install chromium

# --- Копируем код бота ---
COPY . .

# --- Указываем переменные окружения Railway (или можно задать в Railway UI) ---
# ENV SESSION_STRING=твой_session_string
# ENV API_ID=123456
# ENV API_HASH=your_api_hash
# ENV CHANNEL=@твoй_канал

# --- Команда запуска бота ---
CMD ["python", "main.py"]
