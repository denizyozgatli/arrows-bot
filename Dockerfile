FROM python:3.11-slim

# adb client + opencv'nin ihtiyaç duyduğu sistem kütüphaneleri
RUN apt-get update && apt-get install -y --no-install-recommends \
    android-tools-adb \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/

ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "arrows_bot.main"]
