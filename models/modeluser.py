from .entities.user import User
from sqlalchemy import text
class ModelUser:
    @classmethod
    def login(cls, db, user):
        try:
            sql = text("""SELECT uuid, username, password, fullname, rol 
                     FROM usuario 
                     WHERE username = :username""")
            result = db.session.execute(sql, {'username': user.username})
            row = result.fetchone()

            if row:
                # Crear el objeto User con la contraseña hasheada de la base de datos
                user_from_db = User(
                    username=row[1],
                    password=row[2],  # Contraseña hasheada de la base de datos
                    fullname=row[3],
                    uuid=row[0],
                    rol=row[4],
                    is_hashed=True  # Indicamos que esta contraseña ya está hasheada
                )

                # Imprimir la contraseña hasheada y la ingresada
                print(f"Contraseña hasheada de la BD: {user_from_db.password}")
                print(f"Contraseña ingresada por el usuario: {user.password}")

                # Validar la contraseña ingresada en texto plano con el hash almacenado
                if User.check_password(user_from_db.password, user.password):
                    return user_from_db  # Contraseña correcta, devuelve el usuario
                else:
                    return None  # Contraseña incorrecta
            else:
                print("No se encontro el usuario en la base de datos")
                return None  # Usuario no encontrado
        except Exception as ex:
            print(f"Error durante el login: {ex}")
            raise Exception(ex)
        

    @classmethod
    def get_by_id(cls, db, user_id):
        """Obtiene un usuario por su uuid (ID)"""
        try:
            sql = text("""SELECT uuid, username, fullname, rol 
                     FROM usuario 
                     WHERE uuid = :user_id""")
            row = db.session.execute(sql, {'user_id': user_id}).fetchone()

            if row:
                # Crear y devolver un objeto User
                return User(
                    uuid=row[0],
                    username=row[1], # tupla row
                    fullname=row[2],
                    rol=row[3]
                )
            return None
        except Exception as ex:
            print(f"Error al obtener usuario por ID: {ex}")
            raise Exception(ex)
        
    @classmethod
    def user_exists(cls, db, username):
        try:
            sql = text("SELECT * FROM usuario WHERE username = :username")
            result = db.session.execute(sql, {'username': username}).fetchone()
            return result is not None
        except Exception as ex:
            print(f"Error al verificar si el usuario existe: {ex}")
            raise Exception(ex)

    @classmethod
    def create_user(cls, db, user):
        try:
            sql = text("""INSERT INTO usuario (uuid, username, password, fullname, rol)
                     VALUES (:uuid, :username, :password, :fullname, :rol)""")
            db.session.execute(sql, {
                'uuid': user.uuid,
                'username': user.username,
                'password': user.password,
                'fullname': user.fullname,
                'rol': user.rol
            })
            db.session.commit()
        except Exception as ex:
            print(f"Error al crear el usuario: {ex}")
            db.session.rollback()
            raise Exception(ex)


    @classmethod
    def create_admin_if_not_exists(cls, db):
        try:
            # Verificar si el administrador ya existe
            sql = text("SELECT * FROM usuario WHERE username = 'admin'")
            row = db.session.execute(sql).fetchone()

            if row is None:
                # Si no existe el administrador, crearlo
                admin_password = 'admin'  # Contraseña del administrador en texto plano
                admin_user = User(username='admin', password=admin_password, fullname='Administrador', rol='administrador')
                admin_user.password = admin_user.hash_password(admin_password)  # Hasheamos la contraseña aquí

                # Imprimir la contraseña hasheada
                print(f"Contraseña hasheada para el admin: {admin_user.password}")

                # Insertar el administrador con la contraseña ya hasheada
                sql_insert = text("""INSERT INTO usuario (uuid, username, password, fullname, rol)
                                VALUES (:uuid, :username, :password, :fullname, :rol)""")
                db.session.execute(sql_insert, {
                    'uuid': admin_user.uuid,
                    'username': admin_user.username,
                    'password': admin_user.password,  # La contraseña ya hasheada
                    'fullname': admin_user.fullname,
                    'rol': admin_user.rol
                })
                db.session.commit()
                print("Usuario administrador creado.")
            else:
                print("Usuario administrador ya existe.")
        except Exception as ex:
            print(f"Error al crear el administrador: {ex}")
            raise Exception(ex)

