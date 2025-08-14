FROM mcr.microsoft.com/playwright/python:v1.38.0-focal

WORKDIR /app
COPY . /app

# Установка зависимостей
RUN pip install --upgrade pip
RUN pip install pyrogram tgcrypto python-dotenv portalsmp

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]
