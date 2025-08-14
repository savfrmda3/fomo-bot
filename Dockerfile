## Используем официальный Playwright образ с Python и Chromium
FROM mcr.microsoft.com/playwright/python:v1.43.0-focal

# Рабочая директория
WORKDIR /app

# Копируем зависимости и ставим их
COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь проект, включая локальную библиотеку portalsmp
COPY . .

# Запуск бота
CMD ["python", "main.py"]
