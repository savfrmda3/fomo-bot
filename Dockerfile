# --- Base Python image ---
FROM python:3.11-slim

# --- Prevent Python from writing pyc files, force stdout flushing ---
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# --- Install system dependencies for Playwright & Chromium ---
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpangocairo-1.0-0 \
    libxdamage1 \
    libpango-1.0-0 \
    libcups2 \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# --- Set working directory ---
WORKDIR /app

# --- Copy requirements and install Python deps ---
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# --- Install Playwright browsers (Chromium only) ---
RUN playwright install --with-deps chromium

# --- Copy the rest of the application ---
COPY . .

# --- Run the bot ---
CMD ["python", "main.py"]
