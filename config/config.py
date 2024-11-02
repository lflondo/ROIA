from dotenv import load_dotenv
import os

load_dotenv()

class config:
    SECRET_KEY = os.getenv('SECRET_KEY')


class DevelopmentConfig(config):
    DEBUG = True
    POSTGRES_HOST = os.getenv('POSTGRES_HOST')
    POSTGRES_USER = os.getenv('POSTGRES_USER')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
    POSTGRES_DB = os.getenv('POSTGRES_DB')
    
    # URL de conexión para SQLAlchemy (PostgreSQL)
    SQLALCHEMY_DATABASE_URI = f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}/{POSTGRES_DB}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
   
    # Añadir la clave API de Google Maps en la configuración
    GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

config = {
    'development': DevelopmentConfig
}