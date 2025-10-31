import argparse
import os
from datetime import datetime, timedelta, UTC

from src.persistencia.sql import init_db, crear_usuario, crear_atleta, crear_evento

DB_PATH = "base.db"

def init():
    """Inicializa la base de datos (crea tablas si no existen)."""
    init_db()
    print("✅ Base de datos inicializada.")

def reset():
    """Elimina base.db y la recrea desde cero."""
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("🗑️ base.db eliminada.")
    init_db()
    print("✅ Base de datos regenerada.")

def seed():
    """Inserta datos de prueba (usuarios, atletas, eventos)."""
    # Crear usuarios
    u1 = crear_usuario("Admin", "admin@example.com", "admin")
    u2 = crear_usuario("Entrenadora", "coach@example.com", "entrenadora")

    # Crear atletas
    a1 = crear_atleta(nombre="Carlos", apellidos="Pérez", edad=25, deporte="Ciclismo", nivel="Avanzado", equipo="Team Aragón")
    a2 = crear_atleta(nombre="Lucía", apellidos="Martínez", edad=19, deporte="Natación", nivel="Elite", equipo="CN Zaragoza")

    # Crear eventos de prueba con fechas en UTC
    crear_evento(
        id_atleta=a1.id_atleta,
        titulo="Entrenamiento de montaña",
        fecha=datetime.now(UTC) + timedelta(days=1),   # ← actualizado
        lugar="Pirineos",
        tipo="Entrenamiento",
    )
    crear_evento(
        id_atleta=a2.id_atleta,
        titulo="Competición regional",
        fecha=datetime.now(UTC) + timedelta(days=7),   # ← actualizado
        lugar="Piscina Olímpica",
        tipo="Competición",
    )

    print("🌱 Datos de prueba insertados.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gestión de la base de datos")
    parser.add_argument("accion", choices=["init", "reset", "seed"], help="Acción a ejecutar")
    args = parser.parse_args()

    if args.accion == "init":
        init()
    elif args.accion == "reset":
        reset()
    elif args.accion == "seed":
        seed()