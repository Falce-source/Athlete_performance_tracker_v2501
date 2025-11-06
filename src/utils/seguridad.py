import bcrypt
from src.utils.seguridad import hash_password
from src.persistencia import sql

def hash_password(plain: str) -> str:
    return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def check_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

# Crear admin inicial
ph = hash_password("admin123")  # elige tu contraseña inicial
sql.crear_usuario(nombre="Administrador", email="admin@demo.com", rol="admin", password_hash=ph)
