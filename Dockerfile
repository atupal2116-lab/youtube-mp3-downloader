# Hafif ve hızlı Python sürümü
FROM python:3.9-slim

# Render'da logların anlık akması için
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# FFMPEG kuruyoruz (MP3 dönüşümü için)
RUN apt-get update && \
    apt-get install -y ffmpeg && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render otomatik port atar, biz 10000 varsayalım ama kodda değişkenden alacağız
EXPOSE 10000

# DİKKAT: Render 'PORT' değişkenini kendisi verir, kod onu dinlemeli
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]