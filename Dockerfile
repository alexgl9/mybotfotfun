# Вказуємо базовий образ
FROM python:3.11

# Встановлюємо робочу директорію
WORKDIR /app

# Копіюємо файли проекту
COPY . .

# Встановлюємо залежності
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Команда для запуску програми
CMD ["python", "main.py"]
