import bcrypt
from uuid import uuid4

class User:
    def __init__(self, username, password=None, fullname="", uuid=None, rol="user", is_hashed=False) -> None:
        self.uuid = uuid or str(uuid4())
        self.username = username
        if is_hashed:
            self.password = password  # La contraseña ya está hasheada (viene de la base de datos)
        else:
            self.password = password  # Mantener la contraseña en texto plano para el login
        self.fullname = fullname
        self.rol = rol

    def hash_password(self, password):
        """Genera un hash seguro de la contraseña usando bcrypt."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')  # Hashea la contraseña con el salt

    @staticmethod
    def check_password(hashed_password, password):
        """Compara la contraseña en texto plano con la contraseña hasheada."""
        try:
            # Asegurarse de que ambos sean bytes
            if isinstance(password, str):
                password = password.encode('utf-8')
            if isinstance(hashed_password, str):
                hashed_password = hashed_password.encode('utf-8')
            return bcrypt.checkpw(password, hashed_password)
        except ValueError as e:
            print(f"Error al verificar la contraseña: {e}")
            return False
