FROM python:3.11-slim

WORKDIR /app

# Copiamos requirements e instalamos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiamos el código
COPY main.py .

# Creamos directorio para la DB persistente
RUN mkdir /data

# Comando de ejecución
CMD ["python", "main.py"]
