#!/bin/bash
set -e

# Ставим системные зависимости для браузеров
python3 -m playwright install-deps

# Ставим Chromium вместо Firefox
python3 -m playwright install chromium

# Запуск бота
python3 main.py
