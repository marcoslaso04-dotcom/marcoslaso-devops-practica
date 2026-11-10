# Imagen base ligera con Python
FROM python:3.12-slim

# No generar ficheros .pyc y mostrar los logs al momento
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Carpeta de trabajo dentro del contenedor
WORKDIR /app

# Usuario sin privilegios para ejecutar la aplicación (no usar root)
RUN useradd --create-home appuser

# Primero las dependencias, para aprovechar la caché de capas de Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código fuente de la API
COPY src/ .

# Permisos: el usuario appuser es el dueño del código y puede ejecutarlo
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Arranca la API con uvicorn escuchando en todas las interfaces
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
