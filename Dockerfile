FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Instalo cosas basicas para compilar deps si alguna lo necesita
RUN apt-get update && apt-get install -y build-essential && rm -rf /var/lib/apt/lists/*

# Copio requirements e instalo dependencias
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copio el resto del codigo de la app
COPY . .

# Variables por defecto para Flask
ENV FLASK_APP=app
ENV FLASK_RUN_HOST=0.0.0.0
ENV FLASK_RUN_PORT=5000

# Comando por defecto del contenedor web
CMD ["flask", "run"]
