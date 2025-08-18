FROM python:3.11-slim

# --- Устанавливаем системные зависимости ---
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    wget \
    gnupg \
    libssl-dev \
    libffi-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    libc-dev \
    libjpeg-dev \
    libpng-dev \
    && rm -rf /var/lib/apt/lists/*

# --- Устанавливаем зависимости Python ---
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# --- Устанавливаем Playwright и Chromium ---
RUN playwright install --with-deps chromium

# --- Копируем исходники ---
COPY . .

CMD ["python", "main.py"]
