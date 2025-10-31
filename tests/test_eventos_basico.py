from datetime import datetime, timedelta, UTC
from src.persistencia.sql import (
    init_db,
    crear_usuario,
    crear_atleta,
    crear_evento,
    obtener_usuarios,
    obtener_atletas,
    obtener_eventos,
    obtener_eventos_por_atleta,
)

def main():
    print("🔄 Inicializando base de datos...")
    init_db()

    print("👤 Creando usuario...")
    u = crear_usuario("Admin", "admin@example.com", "admin")
    print("Usuario creado:", u.id_usuario, u.nombre, u.email)

    print("🏃 Creando atleta...")
    a = crear_atleta(nombre="Carlos", apellidos="Pérez", edad=25, deporte="Ciclismo", nivel="Avanzado")
    print("Atleta creado:", a.id_atleta, a.nombre, a.deporte)

    print("📅 Creando evento...")
    e = crear_evento(
        id_atleta=a.id_atleta,
        titulo="Entrenamiento de prueba",
        fecha=datetime.utcnow() + timedelta(days=1),
        lugar="Gimnasio",
        tipo="Entrenamiento",
    )
    print("Evento creado:", e.id_evento, e.titulo, e.fecha)

    print("📋 Listando usuarios:", [u.nombre for u in obtener_usuarios()])
    print("📋 Listando atletas:", [a.nombre for a in obtener_atletas()])
    print("📋 Listando eventos:", [ev.titulo for ev in obtener_eventos()])
    print("📋 Eventos del atleta:", [ev.titulo for ev in obtener_eventos_por_atleta(a.id_atleta)])

if __name__ == "__main__":
    main()