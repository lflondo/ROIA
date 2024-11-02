from flask import Flask, flash, redirect, render_template, request, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from utils.calculo_reordenamiento import DijkstraClarkeWrightOptimizer
from utils.geocoding_handler import GeocodingHandler
from services.api_google_maps import AsyncGoogleMapsAPI
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from config.config import config
from forms.forms import LoginForm, RegisterForm, RutaForm, EditarRutaForm, CSVUploadForm  # Importar formularios
from models.modelruta import ModelRuta
from models.modeluser import ModelUser
from models.entities.user import User
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from werkzeug.utils import secure_filename
from io import TextIOWrapper
from aiocache import cached
from flask_cors import CORS
import csv
import time
import os
import json
import uuid
import re
import logging
import asyncio


# Cargar variables de entorno
load_dotenv()

# Inicializar la aplicación Flask
app = Flask(__name__)
CORS(app)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')


# Configurar la aplicación con el archivo de configuración
app.config.from_object(config['development'])
# Proteger contra CSRF
csrf = CSRFProtect(app)
#el tiempo de expiración del token CSRF, por ejemplo, a 2 horas (7200 segundos)
app.config['WTF_CSRF_TIME_LIMIT'] = 10800  # 3 horas de expiración para el token

# Conectar la base de datos MySQL
db = SQLAlchemy(app)
   
# Variables globales
admin_initialized = False

@app.route('/test_encoding')
def test_encoding():
    result = db.session.execute("SHOW server_encoding").fetchall()
    return jsonify(result)

# Inicializar el logger
logging.basicConfig(level=logging.INFO)

@app.before_request
def initialize_admin():
    global admin_initialized
    if not admin_initialized:
        ModelUser.create_admin_if_not_exists(db)
        admin_initialized = True
        
@app.after_request
def add_no_cache_headers(response):    
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, password=form.password.data)
        logged_user = ModelUser.login(db, user)
        if logged_user:
            session['user_id'] = logged_user.uuid
            session['username'] = logged_user.username
            session['rol'] = logged_user.rol
            return redirect(url_for('home'))
        else:
            flash("Datos incorrectos", 'danger')
            return redirect(url_for('login'))  # Redirige para limpiar el formulario
    else:
        return render_template('auth/login.html', form=form)

@app.route('/home')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = ModelUser.get_by_id(db, session['user_id'])
    if user:
        return render_template('home.html', username=user.username, rol=user.rol)
    else:
        flash("Error al cargar usuario", 'danger')
        return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = RegisterForm()
    if form.validate_on_submit():
         # Verificamos si el usuario ya existe antes de proceder
        if ModelUser.user_exists(db, form.username.data):
            flash("Este nombre de usuario ya está registrado", 'danger')
            # Redirigir a la misma página de registro para limpiar el formulario
            return redirect(url_for('register'))
        else:
            new_user = User(username=form.username.data, password=form.password.data,
                            fullname=form.fullname.data, rol=form.rol.data)
            try:
                new_user.password = new_user.hash_password(form.password.data)
                ModelUser.create_user(db, new_user)
                flash("Usuario registrado exitosamente!", 'success')
                # Redirigir a la misma página de registro para limpiar el formulario
                return redirect(url_for('register'))
            except Exception as ex:
                print(f"Error al registrar usuario: {ex}")
                flash("Error al registrar usuario.", 'danger')
                return redirect(url_for('register'))
    else:
        # Si hay errores de validación, mostramos los mensajes de error
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", 'danger')
                return redirect(url_for('register'))
    return render_template('auth/register.html', form=form)

def limpiar_texto(texto):
    # Elimina espacios al principio y al final, y convierte a mayúsculas
    texto = texto.strip().upper()
    # Permitir letras acentuadas y caracteres especiales comunes
    return re.sub(r'[^A-Z0-9ÑÁÉÍÓÚÜ\s\.,;:-]', '', texto)

@app.route('/rutas', methods=['GET', 'POST'])
def rutas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    form = RutaForm()
    
    if form.validate_on_submit():  # Este método valida el formulario
        try:
            # Depuración: Ver los datos crudos enviados por el formulario
            print(f"Datos del formulario: {request.form}")
            
            # Limpiamos el texto
            numero_pedido = limpiar_texto(form.pedido.data)
            nombre_cliente = limpiar_texto(form.cliente.data)
            direccion = limpiar_texto(form.direccion.data)
            telefono = limpiar_texto(form.telefono.data)
            barrio = limpiar_texto(form.barrio.data)
            ciudad = limpiar_texto(form.ciudad.data)
            departamento = limpiar_texto(form.departamento.data)
            pais = limpiar_texto(form.pais.data)
                   
                 
            # Verificación de la longitud del teléfono
            if len(telefono) != 10:
                flash("El teléfono debe tener exactamente 10 dígitos", 'danger')
                pedidos = ModelRuta.get_all_rutas(db)
                return render_template('source/rutas.html', form=form, pedidos=pedidos)

            # Verificar si el número de pedido ya existe
            if ModelRuta.pedido_existe(db, numero_pedido):
                flash(f"El número de pedido {numero_pedido} ya está registrado", 'danger')
                pedidos = ModelRuta.get_all_rutas(db)
                return render_template('source/rutas.html', form=form, pedidos=pedidos)

            # Insertar la nueva ruta si todos los datos son válidos
            ruta_uuid = str(uuid.uuid4())
            if ModelRuta.insert_ruta(db, ruta_uuid, numero_pedido, nombre_cliente, direccion, telefono, barrio, ciudad, departamento, pais):
                flash("Registro agregado exitosamente", 'success')
            else:
                flash("Error al agregar el registro", 'danger')
            return redirect(url_for('rutas'))

        except ValueError as e:
            flash(str(e), 'danger')
        except Exception as e:
            flash(f"Error al agregar el despacho: {str(e)}", 'danger')
        return redirect(url_for('rutas'))

    try:
        # Obtener los pedidos de la base de datos
        pedidos = ModelRuta.get_all_rutas(db)
        return render_template('source/rutas.html', form=form, pedidos=pedidos)
    except Exception as e:
        flash(f"Error al obtener la lista de los despachos: {str(e)}", 'danger')
        return redirect(url_for('home'))

@app.route('/buscar_barrio', methods=['GET'])
def buscar_barrio():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    query = request.args.get('q', '').strip()  # Limpiamos la entrada
    print(f"Parámetro de búsqueda recibido: {query}")  # Log para depuración

    try:
        barrios = ModelRuta.buscar_barrio(db, query)
        return jsonify(barrios)  # Devolvemos como JSON

    except Exception as e:
        print(f"Error en buscar_barrio: {str(e)}")  # Log del error
        return jsonify({'error': str(e)}), 500

@app.route('/editar_ruta/<string:numero_pedido>', methods=['GET', 'POST'])
def editar_ruta(numero_pedido):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    ruta = ModelRuta.obtener_ruta(db, numero_pedido)
    if not ruta:
        flash(f"No se encontró el número de pedido {numero_pedido}", 'danger')
        return redirect(url_for('rutas'))

    form = EditarRutaForm()
    
    if form.validate_on_submit():  # Si el formulario es válido
        nuevo_numero_pedido = form.nuevo_numero_pedido.data.strip().upper()
        cliente = form.cliente.data.strip().upper()
        direccion = form.direccion.data.strip().upper()
        telefono = form.telefono.data.strip().upper()
        barrio = form.barrio.data.strip().upper()
        ciudad = form.ciudad.data.strip().upper()
        departamento = form.departamento.data.strip().upper()
        pais = form.pais.data.strip().upper()

        try:
            ModelRuta.actualizar_ruta(db, nuevo_numero_pedido, numero_pedido, cliente, direccion, telefono, barrio, ciudad, departamento, pais)
            flash('Registro actualizado exitosamente', 'success')
            return redirect(url_for('rutas'))
        except Exception as e:
            flash(f"Error al actualizar el registro: {e}", 'danger')

    form.nuevo_numero_pedido.data = ruta[0]
    form.cliente.data = ruta[1]
    form.direccion.data = ruta[2]
    form.telefono.data = ruta[3]
    form.barrio.data = ruta[4]
    form.ciudad.data = ruta[5]
    form.departamento.data = ruta[6]
    form.pais.data = ruta[7]

    return render_template('source/editar_ruta.html', form=form)

@app.route('/eliminar/<string:numero_pedido>', methods=['POST'])
def eliminar_ruta(numero_pedido):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        try:
            ModelRuta.eliminar_ruta(db, numero_pedido)
            flash(f"Número de pedido '{numero_pedido}' eliminada exitosamente", 'success')
        except Exception as e:
            flash(f"Error al eliminar el pedido: {str(e)}", 'danger')
    return redirect(url_for('rutas'))

@app.route('/nueva_ruta', methods=['GET'])
def nueva_ruta():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        # Limpiar todas las rutas existentes
        ModelRuta.clear_all_routes(db)
        flash("Se ha iniciado una nueva ruta correctamente", 'success')
        
        # Crear nuevo formulario vacío
        form = RutaForm()
        
        # Obtener la lista vacía de pedidos
        pedidos = ModelRuta.get_all_rutas(db)
        
        return render_template('source/rutas.html', form=form, pedidos=pedidos)
        
    except Exception as e:
        flash(f"Error al crear nueva ruta: {str(e)}", 'danger')
        return redirect(url_for('rutas_optimizadas'))

@app.route('/optimizar_rutas', methods=['POST'])
async def optimizar_rutas():
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401
    
    try:
        # Obtener la dirección de inicio del cuerpo de la solicitud
        data = request.get_json()
        logging.debug(f"Data: {data}")
        start_location = data.get('start_location')
        skip_geocoding = data.get('skip_geocoding', False)
        logging.debug(f"Dirección de inicio: {start_location}")

        if not start_location:
            raise ValueError("La ubicación de inicio es requerida para optimizar la ruta")
        
        # Inicializar la API de Google Maps
        api_key = app.config.get('GOOGLE_MAPS_API_KEY')
        if not api_key:
            raise ValueError("No se pudo cargar la clave API de Google Maps")
        
        google_maps_api = AsyncGoogleMapsAPI(api_key)
        geocoding_handler = GeocodingHandler(api_key)
        
        # Si skip_geocoding es True, usamos la dirección directamente
        if skip_geocoding:
            start_location_data = {
                'address': start_location,
                # Usamos coordenadas por defecto o las más cercanas al área de servicio
                'lat': 6.2442,  # Coordenada por defecto (ejemplo: Medellín)
                'lng': -75.5812  # Coordenada por defecto (ejemplo: Medellín)
            }
        else:
            # Geocodificar la dirección de inicio (comportamiento original)
            async def geocode_start_location():
                return await google_maps_api.geocode(start_location)
        
        # Geocodificar la dirección de inicio
        async def geocode_start_location():
            return await google_maps_api.geocode(start_location)
        
        start_coords = await geocode_start_location()
        
        # Manejo unificado de las coordenadas de inicio
        if not start_coords:
            raise ValueError("No se pudo geocodificar la dirección de inicio")
            
        # Asegurarse de que tenemos coordenadas en el formato correcto
        if isinstance(start_coords, tuple):
            user_lat, user_lng = start_coords
        elif isinstance(start_coords, dict) and 'lat' in start_coords and 'lng' in start_coords:
            user_lat = float(start_coords['lat'])
            user_lng = float(start_coords['lng'])
        else:
            raise ValueError("Formato de coordenadas de inicio inválido")
        
         # Después de obtener las coordenadas de inicio exitosamente:
        start_location_data = {
            'lat': user_lat,
            'lng': user_lng,
            'address': start_location
        }
        
        # Guardar el punto de inicio en la sesión
        session['start_location'] = start_location_data
        
        # Obtener todas las rutas de la base de datos
        pedidos = ModelRuta.get_all_rutas(db)
        if not pedidos:
            raise ValueError("No hay pedidos para optimizar")
        
        # Obtener las coordenadas de cada dirección de forma asíncrona
        async def get_locations(pedidos, geocoding_handler):
            locations = []
            for pedido in pedidos:
                direccion_completa = f"{pedido['direccion']}, {pedido['ciudad']}, {pedido['departamento']}, {pedido['pais']}"
                try:
                    coords = await geocoding_handler.get_coordinates(direccion_completa, pedido['ciudad'])
                    if isinstance(coords, dict) and 'lat' in coords and 'lng' in coords:
                        locations.append((float(coords['lat']), float(coords['lng'])))
                    elif isinstance(coords, tuple) and len(coords) == 2:
                        locations.append(coords)
                except Exception as e:
                    logging.error(f"Error procesando dirección {direccion_completa}: {str(e)}")
                    continue
            return locations
        
        
        locations = await get_locations(pedidos, geocoding_handler)
        
        # Verificar que tenemos suficientes ubicaciones válidas
        if not locations:
            raise ValueError("No se pudo geocodificar ninguna dirección")

        # Añadir la ubicación del usuario al inicio
        locations.insert(0, (user_lat, user_lng))
        
        # Inicializar el optimizador
        optimizer = DijkstraClarkeWrightOptimizer(locations, google_maps_api)
        await optimizer.calculate_matrices()
        
        # Obtener la ruta optimizada
        try:
            optimized_route = await optimizer.optimize_route(start_location=locations[0])
        except ValueError as e:
            #logging.error(f"Error en optimize_route: {e}")
            return jsonify({'error': str(e)}), 400
        
        # Asegurarse de que la ruta optimizada sea válida
        if not optimized_route or len(optimized_route) < 2:
            raise ValueError("No se pudo generar una ruta optimizada válida")
            
        # Convertir la ruta optimizada en una lista de pedidos optimizados
        pedidos_optimizados = [pedidos[i-1] for i in optimized_route[1:]]  # Excluimos el punto de inicio

        # Preparar datos para la ruta de Google Maps
        origin = locations[0]
        destination = locations[optimized_route[-1]]
        waypoints = [locations[i] for i in optimized_route[1:-1]]
        
        # Obtener datos de la ruta
        async def get_route_data():
            try:
                return await google_maps_api.get_route_data(origin, destination, waypoints)
            except Exception as e:
                logging.error(f"Error al obtener datos de la ruta: {str(e)}")
                return None, None

        legs, mapa_ruta = await get_route_data()
        
        # Modificar la estructura de mapa_ruta para excluir el punto de inicio
        if legs and mapa_ruta:
            mapa_ruta['legs'] = legs[1:]  # Excluir el primer segmento que conecta con el punto de inicio
        
        if not legs or not mapa_ruta:
            raise ValueError("No se pudieron obtener los datos de la ruta")

        # Insertar ruta en la base de datos
        ruta_optimizada_id = ModelRuta.insert_ruta_optimizada(
            db,
            session['user_id'],
            pedidos_optimizados,
            legs, 
            mapa_ruta,
            start_location_data
        )
        
        # Logging para debug
        logging.info(f"Ruta optimizada creada con ID: {ruta_optimizada_id}")
        logging.debug(f"Pedidos optimizados: {pedidos_optimizados}")
        logging.debug(f"Datos de ruta: {legs}")
        logging.debug(f"Datos de mapa: {mapa_ruta}")

        # Guardar el ID en la sesión
        session['ruta_optimizada_id'] = ruta_optimizada_id
        
        return jsonify({'redirect': url_for('mostrar_rutas_optimizadas')})
    
    except ValueError as ve:
        logging.error(f"Error de validación: {str(ve)}")
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logging.error(f"Error al optimizar rutas: {str(e)}")
        return jsonify({'error': str(e)}), 500
    

@app.route('/mostrar_rutas_optimizadas')
def mostrar_rutas_optimizadas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # Obtener ruta_optimizada_id de la sesión
    ruta_optimizada_id = session.get('ruta_optimizada_id')
    # start_location = session.get('start_location')  # Recuperar punto de inicio de la sesión
    # logging.info(f"ID de ruta optimizada recuperado de la sesión: {ruta_optimizada_id}")
    
    if not ruta_optimizada_id:
        logging.warning("El ID de ruta optimizada no está presente en la sesión.")
        flash('No se encontró una ruta optimizada', 'warning')
        return redirect(url_for('home'))

    try:
        # Llamar al método para obtener la ruta optimizada
        # logging.info(f"Llamando a get_ruta_optimizada con ruta_optimizada_id: {ruta_optimizada_id}")
        ruta_optimizada = ModelRuta.get_ruta_optimizada(db, ruta_optimizada_id)
        # logging.info(f"Ruta optimizada recuperada: {ruta_optimizada}")

        if not ruta_optimizada:
            flash('No se encontró la ruta optimizada', 'warning')
            return redirect(url_for('home'))

        pedidos = ruta_optimizada[2]
        ruta_data = ruta_optimizada[3]
        mapa_ruta = ruta_optimizada[4]
        start_location= ruta_optimizada[6]

        # logging.debug(f"Datos a pasar a la plantilla - pedidos: {pedidos}")
        # logging.debug(f"Datos a pasar a la plantilla - ruta_data: {ruta_data}")
        # logging.debug(f"Datos a pasar a la plantilla - mapa_ruta: {mapa_ruta}")
        # logging.debug(f"Datos a pasar a la plantilla - start_location: {start_location}")}")

        return render_template(
            'source/rutas_optimizadas.html', 
             pedidos=pedidos, 
             ruta_data=ruta_data, 
             mapa_ruta_c=mapa_ruta, 
             start_location=start_location
             )

    except Exception as e:
        logging.error(f"Error al mostrar rutas optimizadas: {str(e)}", exc_info=True)
        flash('Ocurrió un error al mostrar las rutas optimizadas', 'danger')
        return redirect(url_for('home'))

@app.route('/verificar_ruta/<string:ruta_id>', methods=['GET'])
def verificar_ruta(ruta_id):
    if 'user_id' not in session:
        return jsonify({'error': 'No autorizado'}), 401  # Asegúrate de que devuelve JSON para errores de autorización
    
    try:
        exists = ModelRuta.verificar_ruta_optimizada(db, ruta_id)
        return jsonify({'exists': exists})
    except Exception as e:
        return jsonify({'error': str(e)}), 400  # Asegúrate de que siempre devuelve JSON en caso de error

    
@app.route('/rutas_optimizadas/<string:ruta_id>')
def ver_ruta_optimizada(ruta_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    
    try:
        # Obtener datos de la ruta optimizada
        ruta_data = ModelRuta.get_ruta_optimizada(db, ruta_id)
        
        if not ruta_data:
            flash('Ruta no encontrada', 'danger')
            return redirect(url_for('home'))

        pedidos = ruta_data[2]
        ruta_data_details = ruta_data[3]
        mapa_ruta = ruta_data[4]
        start_location = ruta_data[6]
        
        return render_template(
            'source/rutas_optimizadas.html', 
            pedidos=pedidos, 
            ruta_data=ruta_data_details, 
            mapa_ruta_c=mapa_ruta, 
            start_location=start_location  # o especifica start_location si está en otra posición
        )
    except Exception as e:
        flash(f'Error al cargar la ruta: {str(e)}', 'danger')
        return redirect(url_for('home'))

@app.route('/procesar_rutas_masivas', methods=['POST'])
def procesar_rutas_masivas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    form = CSVUploadForm()
    if form.validate_on_submit():
        file = request.files.get('file')
        if not file or file.filename == '':
            flash("No se seleccionó un archivo", 'danger')
            return redirect(url_for('rutasmasivas'))
        
        if not file.filename.lower().endswith('.csv'):
            flash("Archivo no válido. Por favor, carga un archivo con extensión .csv", 'danger')
            return redirect(url_for('rutasmasivas'))
        
    errores = 0  # Contador para errores de filas

    try:
        # Eliminar los registros existentes en la tabla
        ModelRuta.clear_all_routes(db)

        # Leer el archivo CSV y procesar las filas
        csv_file = TextIOWrapper(file, encoding='utf-8')
        csv_reader = csv.reader(csv_file)

        for i, row in enumerate(csv_reader, start=1):
            try:
                numero_pedido, nombre_cliente, direccion, telefono, barrio, ciudad, departamento, pais = row
                ModelRuta.insert_ruta(
                    db,
                    uuid=str(uuid.uuid4()),
                    numero_pedido=numero_pedido,
                    nombre_cliente=nombre_cliente,
                    direccion=direccion,
                    telefono=telefono,
                    barrio=barrio,
                    ciudad=ciudad,
                    departamento=departamento,
                    pais=pais
                )
            
            except (ValueError, Exception):
                    errores += 1  # Incrementar contador de errores si hay problema en la fila

        # Mensajes finales
        if errores == 0:
                flash("Archivo procesado y rutas cargadas exitosamente.", 'success')
        elif errores > 0:
                flash("Archivo procesado con algunos errores.", 'warning')    
    except Exception as e:
            flash(f"Error al procesar el archivo: {str(e)}", 'danger')
            return redirect(url_for('rutasmasivas'))   

    return redirect(url_for('rutas'))

@app.route('/rutasmasivas', methods=['GET'])
def rutasmasivas():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    form = CSVUploadForm()
    
    return render_template('source/rutasmasivas.html', form=form)


@app.route('/logout', methods=['POST'])
@csrf.exempt
def logout():
    session.clear()
    flash("Sesión cerrada correctamente", 'success')
    return redirect(url_for('login'))


if __name__ == "__main__":
    app.config.from_object(config['development'])
    app.run()
