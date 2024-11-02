
FROM python:3.13-bookworm

ENV PYTHONUNBUFFERED True

ENV APP_HOME /back-end

# Establece el directorio de trabajo en /app
WORKDIR $APP_HOME

COPY . ./

# Configurar el entorno Flask para producción
ENV FLASK_ENV=production
# Copia los archivos de requerimientos al contenedor
RUN pip install --no-cache-dir --upgrade pip


RUN pip install --no-cache-dir -r requirements.txt


# Instala las dependencias del proyecto
RUN pip install --no-cache-dir -r requirements.txt

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:appy