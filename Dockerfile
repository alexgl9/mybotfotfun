FROM python:3.9-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc python3-dev

# Оновлюємо pip перед встановленням залежностей
RUN pip install --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
